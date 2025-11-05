## QuickDoc — High Level Design

This document is a concise, high-level design for the Doctor Scheduling Assistant Chatbot (QuickDoc). It describes how the React frontend and the Python backend (FastAPI + LangChain + WebSocket + DB) work together, maps the design to the current folder structure, and lists operational considerations and next steps.

---

## 1. Goals

- Real-time, context-aware chat for patients and staff.
- Hybrid retrieval: combine vector semantic search + SQL for structured data.
- Use LangChain + Azure OpenAI (or chosen LLM) for response generation and orchestration.
- Secure endpoints and WebSocket connections using token-based auth.
- Modular, testable backend with clear separation: core infra, routers, services.

---

## 2. Core Components (logical)

- Frontend (React)
  - UI for chat, message list, input box, attachments, and patient/appointment views.
  - Connects to backend over WebSocket for chat and HTTP for REST APIs.
  - Sends Authorization: Bearer <token> for protected REST and includes token for WebSocket handshake.

- Backend (FastAPI)
  - `main.py` — app factory, loads routers, middleware, connection startup/shutdown.
  - Routers (`app/routers`) — HTTP and WebSocket endpoint definitions (chat, patient APIs).
  - Services (`app/services`) — business logic (chat_service, retrieval_service).
  - Core (`app/core`) — infra setup: DB, Vector store, LangChain components, Azure OpenAI client, WebSocket utilities.
  - Auth (`app/auth.py`) — JWT token helpers and FastAPI authentication dependency.

- Persistence & Search
  - SQL Database — structured data (patients, appointments, messages, metadata).
  - Vector DB (Chroma/FAISS/other) — embeddings for semantic retrieval and RAG.
  - Data pipelines to create embeddings and store vector documents.

- LLM & Orchestration
  - LangChain chains/agents for RAG, prompt templating, multi-step reasoning.
  - Azure OpenAI client set up in core for completions/embeddings.

- Realtime Transport
  - WebSocket server handled by FastAPI/Uvicorn for interactive chat streams.
  - Message-level handling: authentication, message persistence, retrieval, and LLM calls.

---

## 3. High-level Data Flow (WebSocket chat)

1. React frontend opens WebSocket to backend and sends auth token during handshake or with the first message.
2. `main.py` / WebSocket handler validates token via `app/auth.py` (returns user identity).
3. Incoming message routed to `chat_endpoints` (socket router) which calls `chat_service`.
4. `chat_service` asks `retrieval_service` for context:
   - Query Vector DB for top-N similar documents (embeddings).
   - Query SQL DB for relevant structured records (patient info, appointments).
   - Combine and format context for the LLM prompt.
5. `chat_service` calls LangChain (pre-configured chain/agent) which in turn calls Azure OpenAI to produce a response.
6. The response is optionally saved to SQL DB (chat history) and then sent back to the frontend over the WebSocket.

Notes:
- Streaming: Use WebSocket streaming to forward partial tokens from the LLM (if supported).
- Token usage & billing: control prompt size, caching, and context windows.

---

## 4. High-level Data Flow (HTTP REST endpoints)

1. Frontend calls `patient_endpoints` for CRUD operations with `Authorization: Bearer <token>` header.
2. FastAPI endpoint uses `Depends(get_current_user)` (from `app/auth.py`) to ensure request is authorized.
3. Endpoint calls services in `app/services` which call `app/core/database_setup.py` and other core utilities.
4. Returns HTTP JSON to frontend.

---

## 5. Folder-to-Component Mapping

- `app/main.py` — App startup, include/attach routers and startup events.
- `app/config.py` (or env) — All environment-driven config: secrets, DB URLs, Azure/OpenAI keys, vector store settings.
- `app/auth.py` — JWT helpers, OAuth2PasswordBearer, `get_current_user` dependency.
- `app/core/azureOpenAI_setup.py` — LLM client, embedding, and model settings.
- `app/core/database_setup.py` — SQLAlchemy/DB session factory, models migrations hooks.
- `app/core/langchain_setup.py` — LangChain chains, prompt templates, reusable agents.
- `app/core/vectorStore_setup.py` — Embedding index creation and query helpers.
- `app/core/webSocket_setup.py` — WebSocket helper utilities and connection management.
- `app/routers/chat_endpoints.py` — WebSocket and HTTP endpoints for chat flows.
- `app/routers/patient_endpoints.py` — HTTP endpoints for patient CRUD and scheduling.
- `app/services/chat_service.py` — Business logic: orchestrate retrieval + LLM calls + response formatting.
- `app/services/retrieval_service.py` — Unified retrieval API that reads from vector store and SQL DB.

---

## 6. Message & API Contracts (examples)

- WebSocket message (client -> server):
```json
{
  "type": "message",
  "text": "I need to reschedule my appointment",
  "metadata": {"clientTimestamp": 1699999999}
}
```
- WebSocket server events (server -> client):
  - `message`: full chat message
  - `typing`: server is generating
  - `partial`: partial token chunks (if streaming)
  - `error`: error message

- Token endpoint (`POST /token`) — returns:
```json
{ "access_token": "<jwt>", "token_type": "bearer", "expires_in": 3600 }
```

- REST patient endpoint example: `GET /patients/{id}`
  - Requires Authorization header
  - Returns JSON with patient record and appointment list

---

## 7. Auth & Security

- JWT tokens (short TTL access tokens). Environment-based `SECRET_KEY`.
- Protect REST endpoints via `Depends(get_current_user)`.
- Protect WebSocket: validate token at handshake; attach user identity to connection scope.
- Input sanitation and rate limiting to protect LLM usage.
- Role-based checks (staff vs patient) inside service layer.

---

## 8. LangChain & RAG Strategy

- Retrieval step: `retrieval_service` returns context documents + structured data.
- Use a LangChain RAG chain that accepts:
  - System prompt templates (company/medical policy)
  - Retrieved docs as context
  - User message
- Post-processing: redact PII if responses may leak sensitive data.

---

## 9. Persistence & Indexing

- Two stores:
  - Vector store (for doc embeddings and semantic lookup).
  - SQL store (for structured, transactional data).
- Indexing pipeline: on document upload or schedule, compute embeddings and upsert into vector store.
- Periodic re-embedding policy for model upgrades.

---

## 10. Observability & Ops

- Logging: structured logs (timestamp, request id, user id, operation, prompt length, tokens used).
- Tracing: propagate request IDs through WebSocket & REST flows.
- Metrics: requests/sec, LLM calls, cost by model, vector DB latency.
- Alerts: high error rate, LLM failures, DB connectivity issues.

---

## 11. Testing Strategy

- Unit tests for `services/*` and `core/*` (mocks for LLM and vector DB).
- Integration tests for router <-> service behaviour using TestClient and in-memory DB.
- End-to-end test with a small LLM mock that returns predictable results.

---

## 12. Deployment & Scaling

- Containerize backend (Docker) with Uvicorn/Gunicorn.
- Horizontal scale of backend instances behind a load balancer.
- Vector DB: use managed vector store or dedicated host(s) with enough RAM.
- SQL DB: managed/replicated cluster.
- Use autoscaling based on LLM request rate and WebSocket connections.

---

## 13. Practical Next Steps (implementation checklist)

- [ ] Add `requirements.txt` entries: `fastapi`, `uvicorn`, `PyJWT` (or `python-jose`), `langchain`, `chromadb` (or chosen vector db client), `sqlalchemy`.
- [ ] Add `/token` endpoint and a simple user-check stub for onboarding.
- [ ] Wire auth into WebSocket handshake (validate token before accepting connection).
- [ ] Add tests: token creation/validation and a basic chat flow test.
- [ ] Add CI: linting, unit tests, and small integration test job.
- [ ] Run a security review for PII handling and rate limiting.

---

## 14. Where to document changes

- Keep architectural decisions in the repo root (`high_level_design.md`).
- Keep sequence flows in `sequence_diagram.md` (already present).
- Add per-component READMEs under `app/core/` and `app/services/` for operational notes and env vars.

---

## 15. Useful env variables (suggested)

- `SECRET_KEY` — JWT signing key
- `ALGORITHM` — JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DATABASE_URL`
- `VECTOR_DB_URL` / vector store path
- `AZURE_OPENAI_KEY` / `OPENAI_API_KEY`
- `LLM_MODEL_NAME` / `EMBEDDING_MODEL`

---

If you want, I can:
- Expand any section into a more detailed design (for example, a full sequence diagram showing token exchange and streaming),
- Create a `README.md` per component with env var lists and run commands,
- Add the `/token` endpoint and tests, and wire `app/auth.py` into `app/routers` and `app/main.py`.

Pick one next task and I will implement it.