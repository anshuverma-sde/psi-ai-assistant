import operator
import uuid
from typing import Annotated, Any, TypedDict

from app.modules.knowledge_base.retrieval.schemas import RetrievalResult
from app.modules.reasoning.context import EvidenceContext
from app.modules.reasoning.decisions.types import DecisionPlan, DecisionResult, DecisionTask, Scalar, Verdict
from app.modules.reasoning.understanding.answerability import GateResult
from app.modules.reasoning.understanding.classifier.model import Classification


def merge_dicts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {**(left or {}), **(right or {})}


class AskState(TypedDict, total=False):
    # input (already tenant-resolved by application logic)
    org_id: uuid.UUID
    org_name: str
    question: str
    # understanding / retrieval
    classification: Classification
    retrieval: RetrievalResult
    context: EvidenceContext
    gate: GateResult
    plan: DecisionPlan | None
    # decisions — parallel branches append here
    decision_results: Annotated[list[DecisionResult], operator.add]
    decision_errors: Annotated[list[str], operator.add]
    verdict: Verdict | None
    # output
    status: str
    answer: str
    cited: list[str]
    notices: Annotated[list[str], operator.add]
    timings: Annotated[dict[str, float], merge_dicts]


class EvaluateInput(TypedDict):
    """Payload of each parallel `Send` branch — one decision task."""

    task: DecisionTask
    facts: dict[str, Scalar]
