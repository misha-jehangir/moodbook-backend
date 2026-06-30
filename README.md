# MoodBook Backend

The companion backend service for the **MoodBook** application. It provides an Agentic RAG (Retrieval-Augmented Generation) wellness analytics assistant built with FastAPI, Firestore Native Vector Search, and Gemini 2.5 Flash.

## Architecture & Features

- **FastAPI Framework:** Lightweight, asynchronous REST API.
- **Firebase Auth Integration:** Verifies client request tokens against the Firebase Admin SDK to secure user data.
- **Agentic RAG Tool Calling:** Uses Gemini 2.5 Flash to dynamically select and execute data tools.
- **Deterministic Analytics Engine:** Runs native Python algorithms to calculate mood statistics, period-over-period comparisons, and activity/emotion correlations.
- **Firestore Vector Search:** Performs semantic search on user journal entries without a separate vector database.
- **Server-Sent Events (SSE):** Streams conversational responses to the Flutter client in real-time.

## Directory Structure

```
moodbook-backend/
├── app/
│   ├── auth/         # Security and Firebase authentication middleware
│   ├── routers/      # API routes (/chat, /health, etc.)
│   ├── services/     # External integrations (Firestore, Gemini)
│   ├── tools/        # Deterministic python analysis functions
│   ├── config.py     # Environment variables schema
│   └── main.py       # FastAPI application entry point
├── scripts/          # Helper scripts (synthetic data generation, etc.)
├── .gitignore
├── requirements.txt
└── README.md
```

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
4. Create a `.env` file based on configuration requirements.
5. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```