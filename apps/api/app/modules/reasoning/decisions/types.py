"""Typed contracts between the LLM (which writes a DecisionPlan) and System 1 (which evaluates it)."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Tri = Literal["TRUE", "FALSE", "UNKNOWN"]
Op = Literal["eq", "neq", "gt", "gte", "lt", "lte", "in", "not_in", "is_true", "is_false"]
Scalar = bool | int | float | str


def normalize_key(key: str) -> str:
    return "_".join(key.strip().lower().replace("-", " ").split())


class Fact(BaseModel):
    """Something the user stated about their own situation."""

    key: str
    value: Scalar

    @field_validator("key")
    @classmethod
    def _norm(cls, v: str) -> str:
        return normalize_key(v)


class Condition(BaseModel):
    id: str
    label: str = Field(description="Human-readable requirement, e.g. 'GPA of at least 3.5'")
    fact: str
    op: Op
    value: Scalar | list[Scalar] | None = None
    source_id: str

    @field_validator("fact")
    @classmethod
    def _norm(cls, v: str) -> str:
        return normalize_key(v)


class BooleanTask(BaseModel):
    kind: Literal["boolean"]
    id: str
    question: str
    conditions: list[Condition] = Field(min_length=1, max_length=8)
    combinator: Literal["all", "any"] = "all"
    required: bool = True


class ChoiceOption(BaseModel):
    label: str
    when: list[Condition] = Field(default_factory=list, max_length=6)  # empty = "otherwise" option


class ChoiceTask(BaseModel):
    kind: Literal["choice"]
    id: str
    question: str
    options: list[ChoiceOption] = Field(min_length=1, max_length=8)
    default: str | None = None
    required: bool = False

    @model_validator(mode="after")
    def _otherwise_option_becomes_default(self) -> "ChoiceTask":
        """LLMs often express a catch-all ("none of the above") as an option with no conditions."""
        catch_all = [o for o in self.options if not o.when]
        if catch_all:
            self.default = self.default or catch_all[0].label
            self.options = [o for o in self.options if o.when]
        if not self.options:
            raise ValueError("A choice needs at least one option with conditions")
        return self


class ScoreFactor(BaseModel):
    condition: Condition
    weight: float = Field(default=1.0, gt=0, le=10)


class ScoreTask(BaseModel):
    kind: Literal["score"]
    id: str
    question: str
    factors: list[ScoreFactor] = Field(min_length=1, max_length=8)
    threshold: float = Field(default=0.5, ge=0, le=1)
    required: bool = False


DecisionTask = Annotated[BooleanTask | ChoiceTask | ScoreTask, Field(discriminator="kind")]


class DecisionPlan(BaseModel):
    needs_decisions: bool = True
    subject: str = ""
    facts: list[Fact] = Field(default_factory=list)
    decisions: list[DecisionTask] = Field(default_factory=list, max_length=8)

    def fact_map(self) -> dict[str, Scalar]:
        return {f.key: f.value for f in self.facts}

    def all_conditions(self) -> list[Condition]:
        out: list[Condition] = []
        for task in self.decisions:
            if isinstance(task, BooleanTask):
                out += task.conditions
            elif isinstance(task, ChoiceTask):
                out += [c for o in task.options for c in o.when]
            else:
                out += [f.condition for f in task.factors]
        return out


class ConditionTrace(BaseModel):
    condition_id: str
    label: str
    fact: str
    op: Op
    expected: Scalar | list[Scalar] | None
    actual: Scalar | None
    result: Tri
    source_id: str
    group: str | None = None  # choice option label


class DecisionResult(BaseModel):
    id: str
    kind: Literal["boolean", "choice", "score"]
    question: str
    evaluator: str
    outcome: str                # TRUE/FALSE/UNKNOWN | option label | STRONG/MODERATE/WEAK
    passed: bool | None         # None = undetermined (missing facts)
    score: float | None = None
    confidence: float
    required: bool
    trace: list[ConditionTrace]
    missing_facts: list[str]
    source_ids: list[str]
    duration_ms: float = 0.0


VerdictOutcome = Literal["ELIGIBLE", "NOT_ELIGIBLE", "NEEDS_INFO", "INFORMATIONAL"]


class Verdict(BaseModel):
    outcome: VerdictOutcome
    summary: str
    subject: str = ""
    unmet: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    qualifiers: dict[str, str] = Field(default_factory=dict)
