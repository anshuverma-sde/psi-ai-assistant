"""Runs samples/test_questions.json against the live API and prints a pass/fail table.

Run after seed.py:  apps/api/.venv/bin/python samples/scripts/run_eval.py [--api http://localhost:8000] [--verbose]
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def check(expect: dict, data: dict) -> list[str]:
    problems = []
    if data["status"] != expect["status"]:
        problems.append(f"status {data['status']} ≠ {expect['status']}")
    verdict = (data.get("verdict") or {}).get("outcome")
    if "verdict" in expect and verdict != expect["verdict"]:
        problems.append(f"verdict {verdict} ≠ {expect['verdict']}")
    if len(data["decisions"]) < expect.get("min_decisions", 0):
        problems.append(f"{len(data['decisions'])} decisions < {expect['min_decisions']}")
    docs = {s["document"] for s in data["sources"]}
    for doc in expect.get("sources", []):
        if doc not in docs:
            problems.append(f"missing source {doc}")
    for doc in expect.get("forbidden_sources", []):
        if doc in docs:
            problems.append(f"LEAKED source {doc}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--only", help="comma-separated question ids")
    parser.add_argument("--delay", type=float, default=6.0, help="seconds between questions (LLM rate limits)")
    args = parser.parse_args()

    seed = json.loads((ROOT / ".seed-output.json").read_text())
    questions = json.loads((ROOT / "test_questions.json").read_text())
    if args.only:
        wanted = set(args.only.split(","))
        questions = [q for q in questions if q["id"] in wanted]

    passed = 0
    print(f"{'ID':4} {'category':16} {'status':13} {'verdict':14} {'type':12} {'ms':>6}  result")
    print("-" * 92)
    with httpx.Client(base_url=args.api, timeout=120) as client:
        for q in questions:
            started = time.perf_counter()
            resp = client.post("/api/ask", json={"token": seed[q["org"]]["token"], "question": q["question"]})
            ms = int((time.perf_counter() - started) * 1000)
            body = resp.json()
            if not body["success"]:
                print(f"{q['id']:4} {q['category']:16} ERROR {body['error']['code']}: {body['error']['message']}")
                continue
            data = body["data"]
            problems = check(q["expect"], data)
            passed += not problems
            verdict = (data.get("verdict") or {}).get("outcome") or "-"
            qtype = (data.get("question_type") or {}).get("label", "-")
            mark = "PASS" if not problems else "FAIL: " + "; ".join(problems)
            print(f"{q['id']:4} {q['category']:16} {data['status']:13} {verdict:14} {qtype:12} {ms:>6}  {mark}")
            if args.verbose or problems:
                print(f"      Q: {q['question']}")
                print("      A: " + data["answer"].replace("\n", "\n         ")[:900])
                for d in data["decisions"]:
                    print(f"      · [{d['kind']}] {d['question']} → {d['outcome']}"
                          + "".join(f"\n          - {t['result']:7} {t['label']} (you: {t['actual']})" for t in d["trace"]))
                if data["sources"]:
                    print("      sources: " + ", ".join(f"{s['document']} p{s['page']}" for s in data["sources"]))
                if data["notices"]:
                    print(f"      notices: {data['notices']}")
            time.sleep(args.delay)

    print("-" * 92)
    print(f"{passed}/{len(questions)} passed")
    return 0 if passed == len(questions) else 1


if __name__ == "__main__":
    sys.exit(main())
