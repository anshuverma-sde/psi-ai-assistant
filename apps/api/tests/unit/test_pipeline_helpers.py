import pytest

from app.core.errors import AppError, ErrorCode
from app.modules.knowledge_base.documents.validators import sanitize_filename, validate_pdf
from app.modules.knowledge_base.ingestion.table_formatter import table_to_markdown
from app.modules.knowledge_base.retrieval.fusion import reciprocal_rank_fusion
from app.modules.knowledge_base.retrieval.schemas import RetrievalResult, RetrievedChunk
from app.modules.reasoning.context import EvidenceContext
from app.modules.reasoning.generation.citation_validator import build_sources, clean_citations
from app.modules.reasoning.understanding.answerability import evaluate_answerability
from app.modules.reasoning.understanding.query_planner import comparison_subqueries
from tests.pdf_factory import make_pdf


def chunk(cid, text="Merit scholarship requires GPA 3.5", page=2, sim=0.8):
    return RetrievedChunk(id=cid, document_id="doc", filename="Rules.pdf", page=page, text=text, vector_score=sim)


def test_rrf_rewards_agreement():
    scores = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a"]])
    assert max(scores, key=scores.get) in {"a", "b"} and scores["c"] < scores["b"]


def test_table_to_markdown():
    md = table_to_markdown([["Tier", "GPA"], ["Gold", "3.8 | 4.0"], [None, None]])
    assert md.splitlines() == ["| Tier | GPA |", "|---|---|", "| Gold | 3.8 / 4.0 |"]


def test_citations_drop_unknown_ids():
    ctx = EvidenceContext([chunk("a"), chunk("b", page=4)])
    text, used = clean_citations("Yes [s2]. Also [s9]. And [s1, s7].", ctx)
    assert text == "Yes [s2]. Also. And [s1]."
    assert used == ["s2", "s1"]
    sources = build_sources(used, ctx)
    assert [(s.document, s.page) for s in sources] == [("Rules.pdf", 4), ("Rules.pdf", 2)]


def test_citations_tolerate_spacing_and_case():
    ctx = EvidenceContext([chunk("a"), chunk("b")])
    text, used = clean_citations("Eligible [ s2 ] and Silver [S1]. Deadline 【s1】.", ctx)
    assert text == "Eligible [s2] and Silver [s1]. Deadline [s1]." and used == ["s2", "s1"]


def test_gate_refuses_weak_matches():
    strong = RetrievalResult(chunks=[chunk("a")], top_similarity=0.8, keyword_hits=1)
    weak = RetrievalResult(chunks=[chunk("a", text="Housing rules")], top_similarity=0.66, keyword_hits=1)
    assert evaluate_answerability("merit scholarship GPA", strong, strong=0.74, minimum=0.62).answerable
    assert not evaluate_answerability("current stock price", weak, strong=0.74, minimum=0.62).answerable
    empty = RetrievalResult(chunks=[], top_similarity=0, keyword_hits=0)
    assert evaluate_answerability("anything", empty, strong=0.74, minimum=0.62).reason == "no_matching_content"


def test_gate_accepts_short_queries_only_with_full_keyword_coverage():
    renewal = RetrievalResult(chunks=[chunk("a", text="9. Renewal. Scholarships are renewed each year.")],
                              top_similarity=0.59, keyword_hits=2)
    gate = evaluate_answerability("Renewal", renewal, strong=0.74, minimum=0.62)
    assert gate.answerable and gate.reason == "short_query_keyword_match"

    housing = RetrievalResult(chunks=[chunk("a", text="Room prices per semester. Quiet hours start at 10 pm.")],
                              top_similarity=0.53, keyword_hits=1)
    assert not evaluate_answerability("stock price", housing, strong=0.74, minimum=0.62).answerable  # 'stock' missing
    assert not evaluate_answerability("parking", housing, strong=0.74, minimum=0.62).answerable
    # Question-shape words ("process", "rules") don't count against coverage, but the topic word must match.
    apply = RetrievalResult(chunks=[chunk("a", text="How to Apply. Complete the Scholarship Application Form.")],
                            top_similarity=0.61, keyword_hits=3)
    assert evaluate_answerability("Application process", apply, strong=0.74, minimum=0.62).answerable
    assert not evaluate_answerability("visa process", apply, strong=0.74, minimum=0.62).answerable
    # Long questions never use the short-query rule, even with full coverage.
    long_q = "Are quiet hours and room prices the same every semester for everyone?"
    assert evaluate_answerability(long_q, housing, strong=0.74, minimum=0.62).reason == "weak_match"


@pytest.mark.parametrize("question, first_two", [
    ("What is the difference between the merit scholarship and the need-based grant?",
     ["merit scholarship", "need-based grant"]),
    ("How does sick leave compare to casual leave?", ["sick leave", "casual leave"]),
    ("Gold vs silver tier?", ["Gold tier", "silver tier"]),
])
def test_comparison_subqueries(question, first_two):
    assert comparison_subqueries(question)[:2] == first_two


def test_sanitize_filename():
    assert sanitize_filename("../../etc/passwd") == "passwd.pdf"
    assert sanitize_filename("Policy <v2>.PDF") == "Policy _v2_.PDF"


async def test_validate_pdf_limits():
    ok = await validate_pdf(make_pdf(n_pages=3), "a.pdf", max_pages=20)
    assert ok.page_count == 3
    with pytest.raises(AppError) as exc:
        await validate_pdf(make_pdf(n_pages=21), "big.pdf", max_pages=20)
    assert exc.value.code == ErrorCode.PDF_TOO_MANY_PAGES and exc.value.details["pages"] == 21
    with pytest.raises(AppError) as exc:
        await validate_pdf(b"%PDF-1.4 garbage", "x.pdf", max_pages=20)
    assert exc.value.code == ErrorCode.PDF_INVALID
    with pytest.raises(AppError) as exc:
        await validate_pdf(b"hello world", "x.pdf", max_pages=20)
    assert exc.value.code == ErrorCode.PDF_INVALID
    with pytest.raises(AppError) as exc:
        await validate_pdf(make_pdf(encrypt="secret"), "x.pdf", max_pages=20)
    assert exc.value.code == ErrorCode.PDF_ENCRYPTED
