# Ask PSI

A multi-tenant knowledge and decision assistant. An organization signs up, uploads its policy PDFs and gets a public assistant link (or an embed snippet) for its website. Visitors ask questions in plain language and get answers based only on that organization's documents, with document and page references.

Questions like "am I eligible for X?" are not answered by the LLM alone. The LLM turns the question into a set of conditions, small rule evaluators check each condition, and the app combines the results into a verdict before the LLM writes the final answer.

**Stack:** FastAPI, PostgreSQL + pgvector, LlamaIndex, LangGraph, scikit-learn, Groq (free tier), Next.js. Embeddings run locally with fastembed.

## Running it locally

You need Docker, Python 3.10+ with [uv](https://docs.astral.sh/uv/), Node 20+ with pnpm, and a free Groq API key from <https://console.groq.com/keys>.

```bash
make setup      # installs both apps and creates apps/api/.env and apps/web/.env.local
                # then put your GROQ_API_KEY and a random JWT_SECRET in apps/api/.env
make db         # Postgres + pgvector on port 5433
make migrate
make api        # http://localhost:8000  (first run downloads the embedding model, ~130 MB)
make web        # http://localhost:3000
```

To load the demo data, with the API running:

```bash
make seed       # creates two organizations and uploads their PDFs
make eval       # runs the 17 test questions and prints pass/fail
make demo       # serves demo/external-site.html on :5500 with both assistants embedded
```

Demo accounts created by `make seed`:

| Organization | Email | Password |
|---|---|---|
| Northbridge University | admin@northbridge.example | Northbridge#2026 |
| Acme Corp HR | admin@acme.example | AcmeCorp#2026 |

Main settings in `apps/api/.env` (see `.env.example` for the full list):

| Variable | Default |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://psi:psi@localhost:5433/psi` |
| `JWT_SECRET` | must be changed |
| `PUBLIC_APP_URL` | `http://localhost:3000` (used in assistant links) |
| `GROQ_API_KEY` | your key |
| `LLM_MODEL` | `openai/gpt-oss-120b` |
| `LLM_FALLBACK_MODELS` | `openai/gpt-oss-20b,qwen/qwen3.8-27b` |
| `MAX_DOCUMENTS` / `MAX_PAGES` / `MAX_FILE_MB` | `10` / `20` / `10` |

The web app only needs `API_URL` in `apps/web/.env.local`, so it never sees the backend secrets.

## How it fits together

```
 Admin ── Next.js dashboard ──┐
                              ├── /api/* (proxied by Next.js) ──> FastAPI ──> Postgres + pgvector
 Visitor ── chat page /a/:token ┘                                     │
   (opened directly, in an iframe, or via widget.js)                  └──> Groq LLM
```

- **Next.js** serves the dashboard, the public chat page and `widget.js`. It proxies `/api` to FastAPI so cookies work without CORS. Only the chat page is allowed to be framed by other sites.
- **FastAPI** is split into modules: `auth`, `organization`, `knowledge_base` (documents, ingestion, retrieval), `assistant` (token, embed code, public `/api/ask`), `reasoning` (the question pipeline) and `analytics`. Shared pieces live in `core` (config, errors, response format, auth) and `infra` (database, storage, LLM and embedding clients).
- **Postgres** stores organizations, users, documents and query logs, plus the chunk table with both a vector index and a full-text index.

Every endpoint returns the same shape:

```json
{ "success": true, "data": { ... }, "error": null, "meta": { "request_id": "...", "timestamp": "..." } }
```

Errors use `success: false` with an `error.code` such as `PDF_TOO_MANY_PAGES` or `TOKEN_INVALID` and a readable message.

## Documents

When a PDF is uploaded it is checked before anything is stored: file type, size (10 MB), page count (20), password protection, duplicates, and the 10-document limit. The limit check runs inside a row lock, so two parallel uploads can't go over it.

Processing then runs in the background:

1. **pdfplumber** extracts text page by page. Tables are pulled out separately and kept as markdown rows, because a lot of the actual rules (GPA tiers, expense limits) live in tables.
2. Each page is split into chunks of about 350 tokens, so every chunk belongs to exactly one page. That's what makes page references possible.
3. Chunks are embedded with `bge-small-en-v1.5` and stored with the organization id, document id, file name and page.

Search combines vector similarity and Postgres full-text search, merged with reciprocal rank fusion. Comparison questions ("merit vs need-based") are split so each side is searched separately.

Pages with no text (scanned PDFs) fail with a clear message. Replacing a document re-indexes it; deleting it removes the file and its chunks.

## Answering questions

`POST /api/ask` with `{ token, question }` goes through a LangGraph pipeline:

| Step | What does it | Notes |
|---|---|---|
| Find the organization | app | the token is looked up on the server |
| Classify the question | scikit-learn | direct / policy / procedural / eligibility / comparison |
| Search the documents | app | only this organization's chunks |
| Is the answer in there? | rule | similarity + keyword coverage; if not, reply "not in the documents" without calling the LLM |
| Break the question down | LLM | only for eligibility-type questions |
| Check each condition | rule evaluators | run in parallel |
| Combine | app | eligible / not eligible / need more info |
| Write the answer | LLM | must agree with the verdict and cite its sources |

The LLM is used for the two things it's good at: reading a question plus policy text, and writing a clear reply. Everything that is a yes/no decision is done by plain code so it is repeatable.

**Example (test Q04).** "I'm a full-time second-year student with a 3.7 GPA. My only other award is a sports scholarship (no need-based grant). Am I eligible for the merit scholarship, and which tier would I get?"

- The LLM extracts the facts (year 2, GPA 3.7, full-time, no need-based grant) and two checks, each citing the page it came from:
  - a yes/no check: year ≥ 2, GPA ≥ 3.5, full-time, no need-based grant (page 2 and page 4)
  - a choice: Gold for GPA ≥ 3.8, Silver for 3.5–3.79 (the table on page 3)
- The evaluators return **met** and **Silver**, and the combined verdict is **eligible**.
- The LLM writes the reply, citing `Scholarship_Rules.pdf` pages 2 and 3.

If a fact is missing (for example the student didn't mention the grant), that condition is "unknown". The verdict becomes "need more info" and the assistant asks for it instead of guessing. The visitor can then reply with just the details ("second year, GPA 3.7"). The chat sends the original question along as `previous_question`, and the server answers the two together.

The three kinds of decision used are **yes/no**, **choice** and **score**, plus the **classification** step at the start.

**When things go wrong:**
- If the LLM returns a plan that cites text that wasn't retrieved, it gets one retry. If it still fails, the answer is marked for review.
- If Groq is rate-limited, the next model in `LLM_FALLBACK_MODELS` is tried.
- If no model is available, a decision question gets an answer built from the verdict, and any other question gets the most relevant passages.

## Security and tenant isolation

- Admin routes get the organization id only from the signed session cookie, never from the request.
- Public routes get it only by looking up the assistant token on the server.
- Every document and chunk query filters by organization id. Retrieval also double-checks each result and drops any that belong to another organization.
- Asking for another organization's document by id returns 404.
- The assistant token is a random 256-bit value. It only allows asking questions; admin routes reject it. Regenerating it disables the old link immediately.
- Passwords are hashed with bcrypt. The session is a JWT in an httpOnly cookie.
- Uploaded files are stored outside the web root and there is no download endpoint. Answers only include short snippets.
- `/api/ask` is rate-limited per IP.

Isolation has its own tests in `apps/api/tests/e2e/test_tenant_isolation.py`:
- each assistant only answers from its own documents
- one organization can't read, replace or delete another's files
- the assistant token is rejected on admin routes
- a regenerated token disables the old one

Two of the evaluation questions (Q16, Q17) also ask one organization's assistant about the other's documents.

## API

| Method | Path | Auth | |
|---|---|---|---|
| POST | `/api/auth/register` | – | create organization + admin |
| POST | `/api/auth/login`, `/api/auth/logout` | – | |
| GET | `/api/auth/me` | session | |
| GET / POST | `/api/admin/documents` | session | list / upload |
| GET / PUT / DELETE | `/api/admin/documents/{id}` | session | view / replace / delete |
| GET | `/api/admin/assistant` | session | link and embed code |
| POST | `/api/admin/assistant/regenerate` | session | new token |
| GET | `/api/admin/usage` | session | question counts |
| GET | `/api/public/assistant/{token}` | token | name for the chat header |
| POST | `/api/ask` | token | ask a question (`previous_question` is optional, for follow-ups) |

Interactive docs are at `http://localhost:8000/api/docs`.

## Test data and tests

`samples/` has two organizations with three PDFs each:
- **Northbridge University:** scholarship rules, academic policies, student housing
- **Acme Corp HR:** leave policy, expense reimbursement, remote work

The PDFs are generated from the markdown files in `samples/source` (`make pdfs`).

`samples/test_questions.json` has 17 questions covering:
- direct, policy and procedural questions
- comparisons
- two multi-condition questions and two that need several decisions
- questions the documents can't answer
- cross-organization questions

`make eval` runs them against the API. The last full run passed 17/17.

`make test` runs 63 backend tests against a separate `psi_test` database:
- unit tests for the evaluators, combiner, retrieval helpers, PDF validation and model fallback
- end-to-end tests for auth, response format, upload limits, the question pipeline (with a fake LLM) and tenant isolation

## Limitations

- Ingestion runs as a FastAPI background task. A real deployment should use a job queue.
- Scanned PDFs need OCR, which isn't included.
- Files are stored on local disk rather than object storage.
- The rate limit is in memory and per process.
- Any site can embed an assistant; there is no per-domain allow list.
- Isolation is enforced in the application. Postgres row-level security would add a second layer.
- The question classifier is trained on a small seed set.
- Groq's free tier allows about 200k tokens per model per day, and a full `make eval` uses roughly 40–60k. Under heavy use, answers fall back to passages.
- Follow-ups only work for "need more info" answers. There is no general conversation memory.
- One admin per organization.

The UI colors are defined in `apps/web/src/shared/styles/theme.css`; changing `--primary` changes the whole theme.
