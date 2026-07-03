# MoodBook Backend

The companion backend service for the **MoodBook** application. It provides an Agentic RAG (Retrieval-Augmented Generation) wellness analytics assistant built with FastAPI, Firestore Native Vector Search, and Gemini 2.5 Flash.

This repository serves as the API backend for the [MoodBook Flutter Application](https://github.com/khadeejab038/moodbook-app).

---

## System Flowchart

The following diagram illustrates the lifecycle of a user query, showcasing the Firebase authentication verification and the automatic loop of the Agentic RAG tool calling:

```mermaid
flowchart TD
    User([User Query]) -->|1. Type Message| Flutter[Flutter App <br/> moodbook-app]
    Flutter -->|2. Fetch ID Token| Auth[Firebase Auth SDK]
    Flutter -->|3. POST /chat + Bearer Token| FastAPI[FastAPI Backend]
    FastAPI -->|4. Verify Token| AdminSDK[Firebase Admin SDK]
    AdminSDK -->|5. Verified UID| FastAPI
    FastAPI -->|6. Start Generation| Gemini[Gemini 2.5 Flash]
    
    subgraph RAG_LOOP ["RAG Tool Loop (Automatic calling)"]
    Gemini -->|7. Decides Tool Calls| Tools{Tools Router}
    Tools -->|Search similar entries| VectorSearch[Firestore Vector Search]
    Tools -->|Calculate stats/trends| Analytics[Deterministic Analytics]
    VectorSearch -->|Return journal entries| Gemini
    Analytics -->|Return calculated numbers| Gemini
    end
    
    Gemini -->|8. Yield text stream| FastAPI
    FastAPI -->|9. Server-Sent Events| Flutter
    Flutter -->|10. Stream tokens to UI| User
    
    style Tools fill:#f9f,stroke:#333,stroke-width:2px,color:#000
    style Gemini fill:#bbf,stroke:#333,stroke-width:2px,color:#000
    style FastAPI fill:#bfb,stroke:#333,stroke-width:2px,color:#000
```

---

## Key Features

- **FastAPI Framework:** Lightweight, asynchronous, high-performance REST API.
- **Firebase Auth Security:** Verifies incoming client request tokens (`Authorization: Bearer <ID_TOKEN>`) against the Firebase Admin SDK to ensure secure user-scoped queries.
- **Agentic RAG Tool Calling:** Uses Gemini 2.5 Flash to dynamically select and execute data tools depending on user intent.
- **Deterministic Analytics Engine:** Runs native Python algorithms (mood averages, period comparisons, activity/emotion correlations) to return mathematically correct insights instead of letting the LLM estimate numbers.
- **Firestore Vector Search:** Performs semantic search directly on user journal entries using Firestore's native `find_nearest` vector indexes, removing the need for a separate Qdrant/Pinecone instance.
- **Server-Sent Events (SSE):** Streams the synthesized conversational response back to the client in real-time.

---

## Directory Structure

```
moodbook-backend/
├── app/
│   ├── auth/         # Security and Firebase ID token middleware
│   ├── routers/      # API routes (/chat, /health)
│   ├── services/     # External integrations (Firestore, Gemini)
│   ├── tools/        # Deterministic python analysis functions
│   ├── config.py     # Environment variables schema
│   └── main.py       # FastAPI application entry point
├── scripts/          # Helper scripts (synthetic data generation, embedding backfill)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Google AI Studio API Key (for Gemini)
- Firebase Admin SDK private key (`service-account.json`)

### Installation & Run

1. Clone this repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on configuration requirements:
   ```bash
   cp .env.example .env
   ```
   *Fill in your `GEMINI_API_KEY` and `FIREBASE_PROJECT_ID` in the `.env` file.*
5. Place your downloaded Firebase service account key in the root directory as `service-account.json`.
6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```