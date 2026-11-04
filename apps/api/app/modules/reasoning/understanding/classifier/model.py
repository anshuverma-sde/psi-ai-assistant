"""System 1 classification model: logistic regression over local sentence embeddings.

Trains in < 1 s from the seed set, caches to disk, predicts in ~ms. No LLM involved.
"""

import hashlib
import json
import logging
import re
from pathlib import Path

import joblib
import numpy as np
from pydantic import BaseModel
from sklearn.linear_model import LogisticRegression

from app.infra.embeddings.base import EmbeddingProvider
from app.modules.reasoning.understanding.classifier.seed_data import QUESTION_TYPES, SEED_EXAMPLES

logger = logging.getLogger(__name__)

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "question_classifier.joblib"

# Explicit "does this apply to me?" phrasing — also used to route to the decision engine.
ELIGIBILITY_CUE = re.compile(r"\b(eligib\w*|qualif\w*|entitled|am i allowed|can i (get|claim|take))\b", re.I)

# Lightweight surface cues, used only when the statistical model is unsure.
_CUES: list[tuple[str, re.Pattern[str]]] = [
    ("comparison", re.compile(r"\b(vs\.?|versus|differen\w*|compare\w*|contrast)\b", re.I)),
    ("eligibility", ELIGIBILITY_CUE),
    ("procedural", re.compile(r"\b(how (do|can|should) i|steps?|process|procedure|apply|submit)\b", re.I)),
    ("policy", re.compile(r"\b(allowed|permitted|policy|rules?|can .* be)\b", re.I)),
]
LOW_CONFIDENCE = 0.45


class Classification(BaseModel):
    label: str
    confidence: float
    method: str  # "model" | "model+cue"
    probabilities: dict[str, float]


def _seed_fingerprint(model_name: str) -> str:
    payload = json.dumps({"model": model_name, "seed": SEED_EXAMPLES}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


class QuestionClassifier:
    def __init__(self, embeddings: EmbeddingProvider, clf: LogisticRegression) -> None:
        self.embeddings = embeddings
        self.clf = clf

    @classmethod
    def train(cls, embeddings: EmbeddingProvider) -> LogisticRegression:
        texts, labels = [], []
        for label in QUESTION_TYPES:
            texts += SEED_EXAMPLES[label]
            labels += [label] * len(SEED_EXAMPLES[label])
        X = np.array([embeddings.embed_query_sync(t) for t in texts])
        clf = LogisticRegression(max_iter=2000, C=4.0)
        clf.fit(X, labels)
        return clf

    @classmethod
    def load_or_train(cls, embeddings: EmbeddingProvider, model_name: str) -> "QuestionClassifier":
        fingerprint = _seed_fingerprint(model_name)
        if ARTIFACT_PATH.exists():
            try:
                bundle = joblib.load(ARTIFACT_PATH)
                if bundle.get("fingerprint") == fingerprint:
                    return cls(embeddings, bundle["clf"])
            except Exception:  # corrupt/incompatible artifact → retrain
                logger.warning("Classifier artifact unusable; retraining")
        logger.info("Training question classifier (%s seed examples)",
                    sum(len(v) for v in SEED_EXAMPLES.values()))
        clf = cls.train(embeddings)
        ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"fingerprint": fingerprint, "clf": clf}, ARTIFACT_PATH)
        return cls(embeddings, clf)

    async def classify(self, question: str) -> Classification:
        vector = np.array([await self.embeddings.embed_query(question)])
        probs = self.clf.predict_proba(vector)[0]
        ranked = sorted(zip(self.clf.classes_, probs, strict=True), key=lambda p: p[1], reverse=True)
        label, confidence = str(ranked[0][0]), float(ranked[0][1])
        method = "model"

        if confidence < LOW_CONFIDENCE:
            for cue_label, pattern in _CUES:
                if pattern.search(question):
                    label, method = cue_label, "model+cue"
                    break

        return Classification(
            label=label,
            confidence=round(confidence, 3),
            method=method,
            probabilities={str(k): round(float(v), 3) for k, v in ranked},
        )
