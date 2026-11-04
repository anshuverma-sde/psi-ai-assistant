"""Tri-state condition comparator shared by every System 1 evaluator.

Missing or incomparable facts yield UNKNOWN — the system never guesses on the user's behalf.
"""

import math
import re

from app.modules.reasoning.decisions.types import Condition, ConditionTrace, Scalar, Tri

_TRUE_WORDS = {"true", "yes", "y", "1", "on"}
_FALSE_WORDS = {"false", "no", "n", "0", "off", "none"}
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def to_number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.replace(",", "")
        # Only treat strings like "3.7", "2nd", "$500", "60%" as numbers — not free text.
        match = _NUMBER.search(text)
        if match and len(text.strip()) - len(match.group()) <= 4:
            return float(match.group())
    return None


def to_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        word = value.strip().lower()
        if word in _TRUE_WORDS:
            return True
        if word in _FALSE_WORDS:
            return False
    return None


def _equals(actual: object, expected: object) -> bool | None:
    if isinstance(expected, bool):
        actual_bool = to_bool(actual)
        return None if actual_bool is None else actual_bool == expected
    a_num, e_num = to_number(actual), to_number(expected)
    if a_num is not None and e_num is not None:
        return math.isclose(a_num, e_num, rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(actual, str) and isinstance(expected, str):
        return actual.strip().casefold() == expected.strip().casefold()
    return None


def _compare(actual: object, op: str, expected: object) -> bool | None:
    if op in ("is_true", "is_false"):
        b = to_bool(actual)
        return None if b is None else (b if op == "is_true" else not b)
    if op in ("eq", "neq"):
        eq = _equals(actual, expected)
        return None if eq is None else (eq if op == "eq" else not eq)
    if op in ("in", "not_in"):
        options = expected if isinstance(expected, list) else [expected]
        matches = [_equals(actual, o) for o in options]
        if any(m is True for m in matches):
            hit = True
        elif all(m is False for m in matches):
            hit = False
        else:
            return None
        return hit if op == "in" else not hit
    a, e = to_number(actual), to_number(expected)
    if a is None or e is None:
        return None
    return {"gt": a > e, "gte": a >= e, "lt": a < e, "lte": a <= e}.get(op)


def evaluate_condition(condition: Condition, facts: dict[str, Scalar], group: str | None = None) -> ConditionTrace:
    actual = facts.get(condition.fact)
    if condition.fact not in facts:
        result: Tri = "UNKNOWN"
    else:
        outcome = _compare(actual, condition.op, condition.value)
        result = "UNKNOWN" if outcome is None else ("TRUE" if outcome else "FALSE")
    return ConditionTrace(
        condition_id=condition.id,
        label=condition.label,
        fact=condition.fact,
        op=condition.op,
        expected=condition.value,
        actual=actual,
        result=result,
        source_id=condition.source_id,
        group=group,
    )


def combine_all(results: list[Tri]) -> Tri:
    if "FALSE" in results:
        return "FALSE"
    if "UNKNOWN" in results:
        return "UNKNOWN"
    return "TRUE"


def combine_any(results: list[Tri]) -> Tri:
    if "TRUE" in results:
        return "TRUE"
    if "UNKNOWN" in results:
        return "UNKNOWN"
    return "FALSE"
