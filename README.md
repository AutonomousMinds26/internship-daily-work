# RecruiterAI Candidate Pipeline

A premium, modular AI-powered recruitment pipeline and applicant tracking system (ATS) built with FastAPI, Streamlit, PostgreSQL, Redis, and LangChain. 

This platform enables recruiters to parse resumes automatically, evaluate candidates against complex job descriptions using advanced LLM pipelines, and monitor candidates through an interactive dashboard.

---

## 🏗️ Architecture & Component Overview

The codebase is organized into three major layers:

```mermaid
graph TD
    subgraph Frontend [Streamlit UI]
        App[frontend/app.py]
    end

    subgraph Backend [FastAPI Application]
        Main[backend/app/main.py]
        Routes[API Routes: Candidates, Jobs, Auth, etc.]
        Services[Services: Extractor, Matcher, Redis Cache]
    end

    subgraph AI [AI Scoring Engine]
        Workflow[backend/AI/workflow.py]
        Parsers[Resume & Job Parsers]
        Scorer[Scoring & Ranking Logic]
    end

    subgraph Database [Storage & Cache]
        DB[(PostgreSQL / SQLite)]
        Cache[(Redis Cache)]
    end

    App -->|HTTP Requests / JSON| Main
    Main --> Routes
    Routes --> Services
    Services --> Workflow
    Workflow --> Parsers
    Workflow --> Scorer
    Routes --> DB
    Services --> Cache
```

### Key Modules:
- **[frontend/app.py](file:///Users/ayushsonawane/internship-daily-work/frontend/app.py)**: The main dashboard interface using Streamlit, featuring glassmorphism card components, custom metrics tracking, and Plotly interactive dashboards.
- **[backend/app/main.py](file:///Users/ayushsonawane/internship-daily-work/backend/app/main.py)**: Modular FastAPI backend entry point containing route registrations and DB migrations hook.
- **[backend/api.py](file:///Users/ayushsonawane/internship-daily-work/backend/api.py)**: Legacy consolidated FastAPI app containing schemas, fallback endpoints, and direct routes.
- **[backend/AI/workflow.py](file:///Users/ayushsonawane/internship-daily-work/backend/AI/workflow.py)**: Core AI pipeline matching engine orchestrating PDF/Word document extractors and composite evaluation.

---

## ✨ Features

- **AI Resume Parsing**: Multimodal document extraction (PDF + Word `.docx`) powered by `PyMuPDF` and `python-docx` paired with LLM JSON schema parsers.
- **ATS Composite Scoring**: Auto-calculates experience match, keyword overlaps, and role alignment to deliver normalized rankings.
- **Interactive Dashboard**: Sleek recruiter console featuring visual pipelines, hiring pipelines, and key metrics.
- **Secure Access Control**: Robust role-based JWT access tokens (`Admin`, `Recruiter`, `Hiring Manager`).
- **Caching Service**: Redis-backed cache layer for fast query retrievals on candidate metrics.

---

## ⚙️ Technology Stack

- **Frontend**: Streamlit, Pandas, Plotly Express
- **Backend API**: FastAPI, Uvicorn, Pydantic V2
- **ORM & Database**: SQLAlchemy 2.0, PostgreSQL (production) / SQLite (local dev)
- **Caching**: Redis
- **AI Processing**: LangChain, Groq API (LLM Integration)
- **Unit Tests**: Pytest, HTTPX client mock

---

## 🚀 Getting Started

### 📋 Prerequisites
Ensure you have the following installed on your system:
- Python 3.11 or 3.13
- PostgreSQL (optional, SQLite fallback is enabled)
- Redis

### 🔧 Environment Variables
Create a `.env` file in the `backend/` directory or export the following variables:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/RecruiterAI
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secure-jwt-secret-key
GROQ_API_KEY=your-groq-api-key
```

### 📦 Local Installation & Setup

1. **Clone the repository and set up backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Launch the FastAPI Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The interactive Swagger docs will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).*

3. **Set up and start the Streamlit Frontend:**
   *Open a new terminal session.*
   ```bash
   cd frontend
   pip install -r requirements.txt
   streamlit run app.py
   ```
   *The Streamlit App will launch on [http://localhost:8501](http://localhost:8501).*

---

## 🧪 Running Tests

Ensure local tests pass before proposing updates:

```bash
# Execute from the repository root directory
PYTHONPATH=backend pytest backend/tests
```

---

## 🤝 Contribution Guidelines

Please read [CONTRIBUTING.md](file:///Users/ayushsonawane/internship-daily-work/CONTRIBUTING.md) to understand our development workflow, semantic commit conventions, and local verification rules.
For security concerns, please refer directly to our [SECURITY.md](file:///Users/ayushsonawane/internship-daily-work/.github/SECURITY.md) guidelines.