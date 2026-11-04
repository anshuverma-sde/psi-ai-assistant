"""Graph nodes. Each is thin: it calls one component and records timing.

  [S1]  = System 1 decision model (fast, deterministic/statistical, no LLM)
  [LLM] = generative model
  [APP] = application logic
"""

import functools
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from langgraph.types import Send

from app.infra.llm.base import LLMOutputError, LLMUnavailableError
from app.modules.knowledge_base.retrieval.service import RetrievalService
from app.modules.reasoning.context import EvidenceContext
from app.modules.reasoning.decisions.combiner import combine_results
from app.modules.reasoning.decisions.engine import DecisionEvaluationError, evaluate_task
from app.modules.reasoning.generation.answer_generator import AnswerGenerator
from app.modules.reasoning.generation.citation_validator import clean_citations
from app.modules.reasoning.generation.templates import NO_ANSWER, excerpts_answer, verdict_answer
from app.modules.reasoning.graph.state import AskState, EvaluateInput
from app.modules.reasoning.understanding.answerability import evaluate_answerability
from app.modules.reasoning.understanding.classifier.model import ELIGIBILITY_CUE, QuestionClassifier
from app.modules.reasoning.understanding.decomposer import QuestionDecomposer
from app.modules.reasoning.understanding.query_planner import comparison_subqueries

logger = logging.getLogger(__name__)
Node = Callable[[Any], Awaitable[dict[str, Any]]]


def timed(name: str) -> Callable[[Node], Node]:
    def wrap(fn: Node) -> Node:
        @functools.wraps(fn)
        async def inner(*args: Any) -> dict[str, Any]:
            state = args[-1]  # (self, state) for methods
            start = time.perf_counter()
            update = await fn(*args)
            key = name if name != "evaluate" else f"evaluate:{state['task'].id}"
            update.setdefault("timings", {})[key] = round((time.perf_counter() - start) * 1000, 1)
            return update

        return inner

    return wrap


class AskNodes:
    def __init__(self, *, classifier: QuestionClassifier, retrieval: RetrievalService,
                 decomposer: QuestionDecomposer, generator: AnswerGenerator,
                 gate_strong: float, gate_min: float, top_k: int) -> None:
        self.classifier = classifier
        self.retrieval = retrieval
        self.decomposer = decomposer
        self.generator = generator
        self.gate_strong = gate_strong
        self.gate_min = gate_min
        self.top_k = top_k

    # ---- [S1] what kind of question is this? ---------------------------------------------------
    @timed("classify")
    async def classify(self, state: AskState) -> dict[str, Any]:
        return {"classification": await self.classifier.classify(state["question"])}

    # ---- [APP] org-scoped hybrid retrieval (parallel sub-queries for comparisons) --------------
    @timed("retrieve")
    async def retrieve(self, state: AskState) -> dict[str, Any]:
        question = state["question"]
        queries = comparison_subqueries(question) if state["classification"].label == "comparison" else [question]
        if len(queries) > 1:
            result = await self.retrieval.retrieve_many(state["org_id"], queries, per_query_k=3)
        else:
            result = await self.retrieval.retrieve(state["org_id"], question, self.top_k)
        return {"retrieval": result, "context": EvidenceContext(result.chunks)}

    # ---- [S1] Boolean: is the answer in the knowledge base at all? -----------------------------
    @timed("gate")
    async def gate(self, state: AskState) -> dict[str, Any]:
        return {"gate": evaluate_answerability(state["question"], state["retrieval"],
                                               strong=self.gate_strong, minimum=self.gate_min)}

    @staticmethod
    def route_after_gate(state: AskState) -> str:
        if not state["gate"].answerable:
            return "no_answer"
        if state["classification"].label == "eligibility" or ELIGIBILITY_CUE.search(state["question"]):
            return "decompose"
        return "generate"

    # ---- [LLM] decompose the question into typed decisions -------------------------------------
    @timed("decompose")
    async def decompose(self, state: AskState) -> dict[str, Any]:
        try:
            plan = await self.decomposer.decompose(state["question"], state["context"])
        except LLMUnavailableError:
            return {"plan": None, "notices": ["decomposition_unavailable"]}
        except LLMOutputError as exc:
            logger.warning("Decomposition rejected: %s", exc)
            return {"plan": None, "notices": ["decomposition_invalid"]}
        return {"plan": plan}

    @staticmethod
    def route_after_decompose(state: AskState) -> list[Send] | str:
        plan = state.get("plan")
        if not plan or not plan.needs_decisions or not plan.decisions:
            return "generate"
        facts = plan.fact_map()
        # Fan out: every decision is evaluated independently and in parallel.
        return [Send("evaluate", {"task": task, "facts": facts}) for task in plan.decisions]

    # ---- [S1] evaluate ONE decision (runs as parallel branches) --------------------------------
    @timed("evaluate")
    async def evaluate(self, payload: EvaluateInput) -> dict[str, Any]:
        try:
            return {"decision_results": [evaluate_task(payload["task"], payload["facts"])]}
        except DecisionEvaluationError as exc:
            return {"decision_errors": [f"{payload['task'].id}: {exc}"]}

    # ---- [APP] combine independent results into one verdict -----------------------------------
    @timed("combine")
    async def combine(self, state: AskState) -> dict[str, Any]:
        if state.get("decision_errors"):
            return {"verdict": None, "notices": ["decision_failed"]}
        plan = state.get("plan")
        return {"verdict": combine_results(state.get("decision_results", []), plan.subject if plan else "")}

    # ---- [LLM] grounded answer (+ deterministic fallbacks) -------------------------------------
    @timed("generate")
    async def generate(self, state: AskState) -> dict[str, Any]:
        context: EvidenceContext = state["context"]
        verdict = state.get("verdict")
        results = sorted(state.get("decision_results", []), key=lambda r: r.id)
        notices: list[str] = []
        # An eligibility question answered without the rules engine is flagged for review, whatever the cause.
        decision_failed = bool({"decision_failed", "decomposition_invalid", "decomposition_unavailable"}
                               & set(state.get("notices", [])))

        try:
            generated = await self.generator.generate(
                org_name=state["org_name"], question=state["question"],
                question_type=state["classification"].label, context=context,
                verdict=verdict, results=results,
            )
        except (LLMUnavailableError, LLMOutputError) as exc:
            logger.warning("Answer generation failed: %s", exc)
            if verdict is not None:
                answer, cited = verdict_answer(verdict, results)
                return self._final(verdict, answer, cited, ["generation_fallback_template"])
            answer, cited = excerpts_answer(context)
            return {"status": "needs_review", "answer": answer, "cited": cited,
                    "notices": ["llm_unavailable"]}

        if not generated.answerable or not generated.answer.strip():
            if verdict is not None:  # the rules engine has a grounded result; trust it
                answer, cited = verdict_answer(verdict, results)
                return self._final(verdict, answer, cited, ["generation_declined_template"])
            return {"status": "no_answer", "answer": NO_ANSWER.format(org=state["org_name"]), "cited": [],
                    "notices": ["llm_found_no_answer"]}

        answer, cited = clean_citations(generated.answer, context)
        if not cited:
            cited = [c for c in generated.citations if c in context] or (context.ids[:1])
            notices.append("citations_inferred")
        if decision_failed:
            return {"status": "needs_review", "answer": answer, "cited": cited,
                    "notices": [*notices, "answered_without_decision_engine"]}
        return self._final(verdict, answer, cited, notices)

    @staticmethod
    def _final(verdict, answer: str, cited: list[str], notices: list[str]) -> dict[str, Any]:
        status = "needs_info" if verdict is not None and verdict.outcome == "NEEDS_INFO" else "answered"
        return {"status": status, "answer": answer, "cited": cited, "notices": notices}

    # ---- [APP] refuse instead of hallucinating -------------------------------------------------
    @timed("no_answer")
    async def no_answer(self, state: AskState) -> dict[str, Any]:
        return {"status": "no_answer", "answer": NO_ANSWER.format(org=state["org_name"]), "cited": []}
