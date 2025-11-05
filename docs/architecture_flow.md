# Architecture Flow — QuickDoc Chatbot

This file provides a compact set of diagrams to help visualize the big-picture architecture and runtime flows for the Doctor Scheduling Assistant Chatbot.

## 1) System Flow (WebSocket + HTTP)

```mermaid
graph LR
    A[React Frontend]
    M[main.py]
    Auth[auth.py]
    ChatEP[chat_endpoints.py]
    ChatSvc[chat_service.py]
    Retrieval[retrieval_service.py]
    LangChain[langchain_setup.py]
    Vector[vectorStore_setup.py]
    SQL[database_setup.py]
    LLM[Azure OpenAI]

    A -->|WebSocket| M
    A -->|HTTP| M
    M -->|validate| Auth
    M --> ChatEP
    ChatEP --> ChatSvc
    ChatSvc --> Retrieval
    Retrieval --> Vector
    Retrieval --> SQL
    ChatSvc --> LangChain
    LangChain --> LLM
    LLM --> ChatSvc
    ChatSvc --> ChatEP
    ChatEP --> M
    M --> A
```

Notes:
- WebSocket flow is used for streaming chat, partial tokens, and low-latency messages.
- HTTP endpoints are used for CRUD operations and non-streaming requests.

## 2) Component Interaction Diagram (layered view)

```mermaid
graph TB
    UI[React UI]
    API[FastAPI / Uvicorn]
    AUTH[auth.py]
    SVC[services layer]
    VDB[Vector DB]
    RDB[SQL DB]
    LLM[Azure OpenAI]
    LC[LangChain]

    UI -->|WS/HTTP| API
    API --> AUTH
    API --> SVC
    SVC --> VDB
    SVC --> RDB
    SVC --> LC
    LC --> LLM
```

This shows vertical separation: presentation, API, auth, service logic, and infra components.

## 3) Data & Indexing Pipeline

```mermaid
graph LR
    Docs[Documents] --> Preproc[Preprocessing]
    Preproc --> Embed[Embedding]
    Embed --> VectorDB[Vector DB]
    VectorDB --> Retrieval[retrieval_service]
    Retrieval --> LangChain[LangChain]
    LangChain --> LLM[Azure OpenAI]
    LLM --> ChatSvc[chat_service]
```

Notes:
- Embedding model can be the same provider as LLM or a separate model.
- Re-index when docs change or model changes.

## 4) Deployment Topology (suggested)

```mermaid
graph LR
    LB[Load Balancer]
    BE1[API Container 1]
    BE2[API Container 2]
    VDBsrv[Vector DB]
    RDBsrv[SQL DB]
    OBJ[Storage]
    LLM[Azure OpenAI]

    LB --> BE1
    LB --> BE2
    BE1 --> VDBsrv
    BE1 --> RDBsrv
    BE1 --> OBJ
    BE2 --> VDBsrv
    BE2 --> RDBsrv
    BE2 --> OBJ
    BE1 --> LLM
    BE2 --> LLM
```

Recommendations:
- Use sticky sessions or a shared connection manager for WebSocket connections (or offload to a dedicated WebSocket gateway).
- Use a managed vector DB when possible for easier scaling.

## 5) Quick Mapping to Folder Structure

- `app/main.py`: App entry, router registration, startup/shutdown.
- `app/auth.py`: Token helpers and FastAPI dependency.
- `app/routers/*.py`: Endpoint definitions (WebSocket + REST).
- `app/services/*.py`: Business logic and orchestration.
- `app/core/*.py`: Infra wiring (LLM client, vector store, db sessions).

---

Open this file in VS Code and use a Mermaid preview extension to view the diagrams. If you want a PNG/SVG export or a whiteboard-style diagram, I can generate SVG files or a PlantUML version as well.
