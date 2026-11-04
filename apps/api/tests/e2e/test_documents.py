"""Knowledge-base management: limits, validation errors, processing status, replace/delete."""

from tests.conftest import register_org, upload
from tests.e2e.test_auth_and_format import assert_error
from tests.pdf_factory import make_blank_pdf, make_pdf

POLICY = "Remote work policy.\nEmployees with 12 months of service may work remotely.\nThe stipend is $50 per month."


async def test_upload_list_replace_delete(app):
    org = await register_org(app, "Docs Org")
    resp = await upload(org, "Remote_Work.pdf", make_pdf([POLICY, "Page two text about equipment and laptops."]))
    assert resp.status_code == 201
    doc = resp.json()["data"]
    assert doc["page_count"] == 2 and doc["status"] == "PENDING"

    listing = (await org.get("/api/admin/documents")).json()["data"]
    assert listing["limits"] == {"max_documents": 10, "max_pages": 20, "max_file_mb": 10,
                                 "used_documents": 1, "remaining_documents": 9}
    stored = listing["documents"][0]
    assert stored["status"] == "READY" and stored["chunk_count"] >= 1  # background ingestion finished

    replaced = await org.put(f"/api/admin/documents/{doc['id']}",
                             files={"file": ("Remote_Work_v2.pdf", make_pdf([POLICY + "\nUpdated 2026."]), "application/pdf")})
    assert replaced.status_code == 200 and replaced.json()["data"]["original_name"] == "Remote_Work_v2.pdf"
    assert (await org.get(f"/api/admin/documents/{doc['id']}")).json()["data"]["status"] == "READY"

    deleted = await org.delete(f"/api/admin/documents/{doc['id']}")
    assert deleted.json()["data"] == {"id": doc["id"], "deleted": True}
    assert (await org.get("/api/admin/documents")).json()["data"]["documents"] == []


async def test_upload_validation_errors(app):
    org = await register_org(app, "Validation Org")
    assert_error(await upload(org, "big.pdf", b"%PDF-1.4\n" + b"0" * (10 * 1024 * 1024 + 10)), 413, "PDF_TOO_LARGE")
    resp = await upload(org, "long.pdf", make_pdf(n_pages=21))
    assert_error(resp, 400, "PDF_TOO_MANY_PAGES")
    assert "21 pages" in resp.json()["error"]["message"]
    assert_error(await upload(org, "fake.pdf", b"this is not a pdf"), 400, "PDF_INVALID")
    assert_error(await upload(org, "empty.pdf", b""), 400, "PDF_EMPTY")
    assert_error(await upload(org, "locked.pdf", make_pdf(encrypt="pw")), 400, "PDF_ENCRYPTED")

    data = make_pdf([POLICY])
    assert (await upload(org, "a.pdf", data)).status_code == 201
    assert_error(await upload(org, "copy.pdf", data), 409, "DOC_DUPLICATE")


async def test_scanned_pdf_fails_processing_with_reason(app):
    org = await register_org(app, "Scan Org")
    doc = (await upload(org, "scan.pdf", make_blank_pdf(2))).json()["data"]
    stored = (await org.get(f"/api/admin/documents/{doc['id']}")).json()["data"]
    assert stored["status"] == "FAILED" and stored["error_code"] == "PDF_NO_TEXT"


async def test_document_count_limit(app):
    org = await register_org(app, "Limit Org")
    for i in range(10):
        resp = await upload(org, f"doc{i}.pdf", make_pdf([f"Policy number {i}. Unique content {i * 7919}."]))
        assert resp.status_code == 201
    resp = await upload(org, "eleventh.pdf", make_pdf(["One too many."]))
    assert_error(resp, 409, "DOC_LIMIT_REACHED")
