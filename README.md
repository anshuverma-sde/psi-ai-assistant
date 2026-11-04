# Ask PSI

Organizations upload their policy PDFs and get an assistant they can share as a link or embed on their website. Visitors ask questions and get answers from that organization's documents only, with document and page references.

For questions like "am I eligible for X?", the LLM breaks the question into conditions, rule evaluators check each condition, and the app combines the results into a verdict. The LLM then writes the reply.

**Stack:** FastAPI, PostgreSQL + pgvector, LlamaIndex, LangGraph, scikit-learn, Groq, Next.js. Embeddings run locally (fastembed).

## Setup

Requires Docker, Python 3.10+ with [uv](https://docs.astral.sh/uv/), Node 20+ with pnpm, and a free [Groq API key](https://console.groq.com/keys).

```bash
make setup      # installs everything, creates apps/api/.env and apps/web/.env.local
                # add GROQ_API_KEY and a random JWT_SECRET to apps/api/.env
make db         # Postgres on port 5433
make migrate
make api        # http://localhost:8000
make web        # http://localhost:3000
make seed       # optional: two sample organizations with their PDFs
```

Sample logins: `admin@northbridge.example` / `Northbridge#2026` and `admin@acme.example` / `AcmeCorp#2026`.

`make test` runs the backend tests and `make eval` runs the 17 sample questions against the running API.

To embed an assistant, copy the script or iframe snippet from the Assistant page into any HTML page.

## Architecture

```
Admin   ── Next.js dashboard ─┐
                              ├─ /api (proxied) ──> FastAPI ──> Postgres + pgvector
Visitor ── chat page / embed ─┘                        └──────> Groq LLM
```

- **Web (Next.js):** dashboard, public chat page `/a/:token` and `widget.js`. The chat page is the only page that can be embedded.
- **API (FastAPI):** modules for auth, organizations, documents (upload, processing, search), assistant (token, embed code, `/api/ask`), the question pipeline and usage stats.
- **Postgres:** app data plus document chunks with vector and full-text indexes.

All endpoints return `{ success, data, error, meta }`.

## Documents

Uploads are checked for type, size (10 MB), pages (20), encryption, duplicates and the 10-document limit. Then, in the background:
1. pdfplumber extracts text per page; tables are kept as rows.
2. Each page is split into small chunks, so every chunk belongs to one page.
3. Chunks are embedded and stored with the organization, document and page number.

Search combines vector similarity and keyword search, both filtered to the asking organization.

## How a question is answered

1. The token identifies the organization.
2. A classifier labels the question type (direct, policy, procedural, eligibility, comparison).
3. Relevant chunks are retrieved. If nothing relevant is found, the assistant says so without calling the LLM.
4. For eligibility questions, the LLM extracts the user's facts and the conditions from the policy text.
5. Each decision is checked by a rule evaluator (yes/no, choice or score), in parallel.
6. The results are combined into eligible, not eligible or need more info.
7. The LLM writes the answer, which must match the verdict and cite its sources.

If facts are missing, the assistant asks for them and the visitor can reply with just the details. If the LLM is rate-limited, the next model in `LLM_FALLBACK_MODELS` is used.

## Security

- The organization always comes from the session cookie (admin) or the assistant token (public), never from the request body.
- Every query is filtered by organization; other organizations' documents return 404.
- Assistant tokens are random and only allow asking questions. Regenerating one disables the old link.
- Passwords use bcrypt, files are never served, and `/api/ask` is rate-limited.
- Isolation is covered by tests in `apps/api/tests/e2e/test_tenant_isolation.py`.

## API

| Method | Path | Auth |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login`, `/api/auth/logout` | – |
| GET | `/api/auth/me` | session |
| GET, POST | `/api/admin/documents` | session |
| GET, PUT, DELETE | `/api/admin/documents/{id}` | session |
| GET | `/api/admin/assistant` | session |
| POST | `/api/admin/assistant/regenerate` | session |
| GET | `/api/admin/usage` | session |
| POST | `/api/ask` | token |

Full docs: `http://localhost:8000/api/docs`.

## Limitations

- Processing runs as a background task, not a job queue.
- No OCR for scanned PDFs.
- Files are stored on local disk.
- The rate limit is in memory.
- The Groq free tier has daily token limits.
- Follow-ups only work for "need more info" answers.
