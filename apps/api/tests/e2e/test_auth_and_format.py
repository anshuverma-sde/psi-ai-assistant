"""Auth flows + the response envelope contract on success and every kind of failure."""

import uuid

ENVELOPE_KEYS = {"success", "data", "error", "meta"}


def assert_error(resp, status: int, code: str):
    body = resp.json()
    assert resp.status_code == status, body
    assert set(body) == ENVELOPE_KEYS
    assert body["success"] is False and body["data"] is None
    assert body["error"]["code"] == code and body["error"]["message"]
    assert body["meta"]["request_id"] == resp.headers["x-request-id"]


async def test_register_login_me_logout(client):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post("/api/auth/register", json={
        "organization_name": "  Test   Org ", "email": email, "password": "Password123!"})
    body = resp.json()
    assert resp.status_code == 201 and set(body) == ENVELOPE_KEYS and body["success"] is True
    assert body["data"]["organization"]["name"] == "Test Org"
    assert body["meta"]["request_id"].startswith("req_")
    assert "httponly" in resp.headers["set-cookie"].lower()

    me = await client.get("/api/auth/me")
    assert me.json()["data"]["user"]["email"] == email

    await client.post("/api/auth/logout")
    client.cookies.clear()
    assert_error(await client.get("/api/auth/me"), 401, "UNAUTHORIZED")

    login = await client.post("/api/auth/login", json={"email": email.upper(), "password": "Password123!"})
    assert login.status_code == 200


async def test_auth_errors(client):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    payload = {"organization_name": "Org", "email": email, "password": "Password123!"}
    await client.post("/api/auth/register", json=payload)
    assert_error(await client.post("/api/auth/register", json=payload), 409, "EMAIL_TAKEN")
    assert_error(await client.post("/api/auth/login", json={"email": email, "password": "wrong-pass"}),
                 401, "INVALID_CREDENTIALS")


async def test_validation_error_has_field_details(client):
    resp = await client.post("/api/auth/register", json={"organization_name": "X", "email": "nope", "password": "1"})
    assert_error(resp, 422, "VALIDATION_ERROR")
    fields = resp.json()["error"]["details"]["fields"]
    assert {"organization_name", "email", "password"} <= set(fields)


async def test_unknown_route_and_request_id_passthrough(client):
    assert_error(await client.get("/api/does-not-exist"), 404, "NOT_FOUND")
    resp = await client.get("/api/meta/limits", headers={"x-request-id": "my-trace-id-123"})
    assert resp.headers["x-request-id"] == "my-trace-id-123"
    assert resp.json()["data"] == {"max_documents": 10, "max_pages": 20, "max_file_mb": 10,
                                   "max_question_chars": 1000}
