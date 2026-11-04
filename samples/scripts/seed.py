"""Seeds two demo organizations through the real HTTP API (register → upload → wait for indexing).

Run (API must be running):  apps/api/.venv/bin/python samples/scripts/seed.py [--api http://localhost:8000]
Writes assistant tokens to samples/.seed-output.json for run_eval.py.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / ".seed-output.json"

ORGS = [
    {"key": "northbridge-university", "organization_name": "Northbridge University",
     "email": "admin@northbridge.example", "password": "Northbridge#2026"},
    {"key": "acme-corp-hr", "organization_name": "Acme Corp HR",
     "email": "admin@acme.example", "password": "AcmeCorp#2026"},
]


def unwrap(resp: httpx.Response) -> dict:
    body = resp.json()
    if not body.get("success"):
        raise RuntimeError(f"{resp.request.method} {resp.request.url.path} → {body['error']}")
    return body["data"]


def login_or_register(client: httpx.Client, org: dict) -> None:
    resp = client.post("/api/auth/login", json={"email": org["email"], "password": org["password"]})
    if resp.status_code == 200:
        print(f"  • logged in as {org['email']}")
        return
    unwrap(client.post("/api/auth/register", json={k: org[k] for k in ("organization_name", "email", "password")}))
    print(f"  • registered {org['organization_name']} ({org['email']})")


def upload_documents(client: httpx.Client, org_key: str) -> None:
    existing = {d["original_name"] for d in unwrap(client.get("/api/admin/documents"))["documents"]}
    for pdf in sorted((ROOT / "pdfs" / org_key).glob("*.pdf")):
        if pdf.name in existing:
            print(f"  • {pdf.name} already uploaded")
            continue
        with pdf.open("rb") as fh:
            resp = client.post("/api/admin/documents", files={"file": (pdf.name, fh, "application/pdf")})
        unwrap(resp)
        print(f"  • uploaded {pdf.name}")


def wait_until_indexed(client: httpx.Client, timeout_s: int = 180) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        docs = unwrap(client.get("/api/admin/documents"))["documents"]
        pending = [d for d in docs if d["status"] in ("PENDING", "PROCESSING")]
        failed = [d for d in docs if d["status"] == "FAILED"]
        if failed:
            raise RuntimeError(f"Indexing failed: {[(d['original_name'], d['error_message']) for d in failed]}")
        if not pending:
            print(f"  • {len(docs)} documents ready ({sum(d['chunk_count'] for d in docs)} chunks)")
            return
        time.sleep(1.5)
    raise TimeoutError("Documents were not indexed in time")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()

    output = {}
    for org in ORGS:
        print(f"\n{org['organization_name']}")
        with httpx.Client(base_url=args.api, timeout=120) as client:
            login_or_register(client, org)
            upload_documents(client, org["key"])
            wait_until_indexed(client)
            assistant = unwrap(client.get("/api/admin/assistant"))
            output[org["key"]] = {"organization_name": org["organization_name"], "email": org["email"],
                                  "password": org["password"], "token": assistant["token"],
                                  "assistant_url": assistant["assistant_url"]}
            print(f"  • assistant: {assistant['assistant_url']}")

    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"\nSaved tokens to {OUTPUT_FILE.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
