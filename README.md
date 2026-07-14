# DataWhisperer AI

Production-ready boilerplate for an AI data assistant built with a FastAPI backend and Streamlit frontend.

This repository currently contains project structure only. Application features are intentionally not implemented yet.

## Architecture

The backend follows Clean Architecture boundaries:

- `domain`: enterprise rules and entities
- `application`: use cases and application services
- `infrastructure`: external systems, persistence, providers, and framework adapters
- `interfaces`: API routes, request/response schemas, and HTTP-facing concerns
- `core`: configuration, logging, error handling, and app setup

## Project Structure

```text
datawhisperer-ai/
├── backend/
│   └── app/
│       ├── application/
│       ├── core/
│       ├── domain/
│       ├── infrastructure/
│       ├── interfaces/
│       └── main.py
├── frontend/
│   └── app.py
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Local Setup

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy environment variables:

```bash
cp .env.example .env
```

## Run The Backend

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs are available at:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## Run The Frontend

```bash
streamlit run frontend/app.py
```

The Streamlit app runs at:

- http://localhost:8501

## Docker

Build and run both services:

```bash
docker compose up --build
```

Services:

- Backend: http://localhost:8000
- Frontend: http://localhost:8501

## Development Notes

- Keep domain logic independent from FastAPI, Streamlit, databases, and third-party providers.
- Put use cases in `backend/app/application`.
- Put API-specific models and routes in `backend/app/interfaces`.
- Put provider/database implementations in `backend/app/infrastructure`.
- Use environment variables for all runtime configuration.

## Gemini Configuration

Set `GEMINI_API_KEY` in `.env` to enable AI chat responses through the backend Gemini service.

```bash
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.5-flash
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_RETRIES=3
GEMINI_TEMPERATURE=0.2
```
