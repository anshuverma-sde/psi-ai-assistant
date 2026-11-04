"""Application logic that merges independent decision results into one verdict (no AI here)."""

from app.modules.reasoning.decisions.types import DecisionResult, Verdict


def _humanize(key: str) -> str:
    return key.replace("_", " ")


def combine_results(results: list[DecisionResult], subject: str = "") -> Verdict:
    results = sorted(results, key=lambda r: r.id)
    required = [r for r in results if r.required]
    qualifiers = {
        r.question: (f"{r.outcome} ({r.score:.2f})" if r.score is not None else r.outcome)
        for r in results if not r.required and r.passed is not None
    }

    if not required:
        missing = sorted({f for r in results for f in r.missing_facts})
        return Verdict(
            outcome="INFORMATIONAL",
            subject=subject,
            summary="Evaluated the applicable policy categories.",
            missing_facts=missing,
            qualifiers=qualifiers,
        )

    failed = [r for r in required if r.passed is False]
    undetermined = [r for r in required if r.passed is None]

    if failed:
        # One unmet requirement is decisive, even if other facts are missing.
        unmet = [t.label for r in failed for t in r.trace if t.result == "FALSE"] or [r.question for r in failed]
        return Verdict(
            outcome="NOT_ELIGIBLE",
            subject=subject,
            summary=f"{len(unmet)} requirement(s) not met: " + "; ".join(unmet) + ".",
            unmet=unmet,
            qualifiers=qualifiers,
        )

    if undetermined:
        missing = sorted({f for r in undetermined for f in r.missing_facts})
        return Verdict(
            outcome="NEEDS_INFO",
            subject=subject,
            summary="More information is needed: " + ", ".join(_humanize(m) for m in missing) + ".",
            missing_facts=missing,
            qualifiers=qualifiers,
        )

    return Verdict(
        outcome="ELIGIBLE",
        subject=subject,
        summary=f"All {len(required)} required check(s) are satisfied.",
        qualifiers=qualifiers,
    )
