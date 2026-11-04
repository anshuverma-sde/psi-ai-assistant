"""System 1 Boolean gate: does the knowledge base plausibly contain the answer?

Runs before any LLM call, so out-of-scope questions are refused cheaply and can't be hallucinated.
"""

import re

from pydantic import BaseModel

from app.modules.knowledge_base.retrieval.schemas import RetrievalResult

_STOPWORDS = set(
    "a an the is are was were be been of to in on for at by with from and or not no do does did i me my "
    "we our you your it its this that these those what which who whom when where why how can could "
    "should would will shall may might must there here about into than then so if as any all much many "
    "get got have has had am".split()
)
# Words that describe the *kind* of question rather than its topic ("application process", "leave policy").
# Documents rarely contain them literally, so they shouldn't count against keyword coverage.
_QUESTION_SHAPE = set(
    "process processes procedure procedures step steps policy policies rule rules requirement requirements "
    "information info detail details explain tell please question questions".split()
)
_WORD = re.compile(r"[a-z0-9]+")

SHORT_QUERY_TERMS = 2
SHORT_QUERY_MIN_SIMILARITY = 0.5


class GateResult(BaseModel):
    answerable: bool
    confidence: float
    reason: str
    top_similarity: float
    term_coverage: float


def content_terms(text: str) -> set[str]:
    return {w[:6] for w in _WORD.findall(text.lower()) if len(w) > 2 and w not in _STOPWORDS}


def topic_terms(question: str) -> set[str]:
    """Content terms of a question minus question-shape words; falls back to all terms if nothing is left."""
    words = [w for w in _WORD.findall(question.lower()) if w not in _QUESTION_SHAPE]
    return content_terms(" ".join(words)) or content_terms(question)


def term_coverage(question: str, result: RetrievalResult, top_n: int = 3) -> float:
    terms = topic_terms(question)
    if not terms:
        return 0.0
    haystack = content_terms(" ".join(c.text for c in result.chunks[:top_n]))
    return round(len(terms & haystack) / len(terms), 2)


def evaluate_answerability(question: str, result: RetrievalResult, *, strong: float, minimum: float) -> GateResult:
    top = round(result.top_similarity, 3)
    coverage = term_coverage(question, result)

    if not result.chunks:
        return GateResult(answerable=False, confidence=1.0, reason="no_matching_content",
                          top_similarity=top, term_coverage=coverage)
    if top >= strong:
        return GateResult(answerable=True, confidence=0.9, reason="strong_semantic_match",
                          top_similarity=top, term_coverage=coverage)
    if top >= minimum and coverage >= 0.5:
        return GateResult(answerable=True, confidence=0.7, reason="semantic_and_keyword_match",
                          top_similarity=top, term_coverage=coverage)
    # One- or two-word queries ("Renewal", "appeals") embed weakly even when the exact topic is in the
    # documents. Accept them only when every word literally appears in the top chunks.
    if len(topic_terms(question)) <= SHORT_QUERY_TERMS and coverage == 1.0 and top >= SHORT_QUERY_MIN_SIMILARITY:
        return GateResult(answerable=True, confidence=0.6, reason="short_query_keyword_match",
                          top_similarity=top, term_coverage=coverage)
    return GateResult(answerable=False, confidence=0.75, reason="weak_match",
                      top_similarity=top, term_coverage=coverage)
