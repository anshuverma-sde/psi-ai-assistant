"""Rule-based sub-query planning for comparison questions (no LLM needed)."""

import re

_PATTERNS = [
    re.compile(r"difference(?:s)? between (?:the )?(?P<a>.+?) and (?:the )?(?P<b>.+?)[?.!]*$", re.I),
    re.compile(r"compare (?:the )?(?P<a>.+?) (?:and|with|to|vs\.?|versus) (?:the )?(?P<b>.+?)[?.!]*$", re.I),
    re.compile(r"(?:how does |how do )?(?:the )?(?P<a>.+?) (?:compare to|differ from) (?:the )?(?P<b>.+?)[?.!]*$", re.I),
    re.compile(r"(?P<a>.+?)\s+(?:vs\.?|versus)\s+(?P<b>.+?)(?:[?.!:—-].*)?$", re.I),
]


def comparison_subqueries(question: str) -> list[str]:
    """'merit vs need-based scholarship' → ['merit scholarship', 'need-based scholarship']."""
    for pattern in _PATTERNS:
        match = pattern.search(question.strip())
        if not match:
            continue
        a, b = match.group("a").strip(" ,"), match.group("b").strip(" ,")
        if not a or not b or len(a) > 80 or len(b) > 80:
            continue
        # Share a trailing head noun: "merit and need-based scholarships" → both get "scholarship".
        a_words, b_words = a.split(), b.split()
        if len(a_words) == 1 and len(b_words) > 1:
            a = f"{a} {b_words[-1]}"
        return [a, b, question]
    return [question]
