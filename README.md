# RecruiterAI — AI-Powered Talent Acquisition Platform

[![CI/CD](https://github.com/AutonomousMinds26/internship-daily-work/actions/workflows/ci.yml/badge.svg)](https://github.com/AutonomousMinds26/internship-daily-work/actions)
[![Tests](https://img.shields.io/badge/tests-95%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

A production-grade, AI-powered recruitment platform covering the complete hiring lifecycle — from resume ingestion and 11-point AI scoring through to offer management and GDPR-compliant data governance.

---

## Features

- 🤖 **AI Resume Parsing** — Extracts candidate info from PDF/DOCX/TXT using LLM + regex fallback
- 📊 **11-Point Scoring** — Skills, experience, ATS keyword coverage, education, location, compensation and more
- 🔄 **LangGraph Recruitment Pipeline** — 9-node directed graph with conditional routing (reject/assess/interview/offer)
- ⚡ **Celery Background Workers** — 6 async tasks for resumes, screening, assessments, email, verification, analytics
- 🔐 **JWT Auth + RBAC** — Admin, Recruiter, Hiring Manager, Candidate roles
- 🧪 **Sandboxed Code Assessment** — Execute candidate code safely in Python/JS/Java/SQL
- 🌐 **Real-time Collaboration** — WebSocket broadcast for team candidate status updates
- 🔒 **GDPR / Indian DPDP** — Consent management, DSAR export, right-to-erasure
- ⚖️ **Bias Detection** — 4/5ths rule adverse impact analysis across all pipeline stages
- 📧 **Email Notifications** — SendGrid/SMTP with HTML templates and sandbox fallback
- 📅 **Calendar Integration** — Google Calendar / Outlook scheduling

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Redis (optional — sync fallback if unavailable)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Edit values as needed

# Run the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Default Credentials

The first startup seeds default admin and test users:
- **Admin**: `admin_user` / `admin_password`
- **Recruiter**: `recruiter_user` / `recruiter_password`

---

## Docker Compose

```bash
docker compose up -d
```

Services:
| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

---

## Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./recruiter_ai.db     # or PostgreSQL URL

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=change-me-in-production

# LLM Provider (groq, openai, anthropic, ollama, mock)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key

# Email (optional — mock if not set)
SENDGRID_API_KEY=

# External Integrations (optional — mock if not set)
HACKERRANK_API_KEY=
CHECKR_API_KEY=
USE_MOCK_APIS=true
```

See [`backend/.env.example`](backend/.env.example) for the full list.

---

## Running Tests

```bash
cd backend
PYTHONPATH=. python3 -m pytest
```

**Result**: 95 tests passing across 19 test modules.

---

## Architecture

```
Frontend (React/Vite/TypeScript)
          │
FastAPI Backend (Python 3.11)
          │
   ┌──────┴──────┐
AI Pipeline    Celery Workers
(LangGraph)    (6 async tasks)
   └──────┬──────┘
          │
    SQLite (dev) / PostgreSQL (prod)
    Redis (cache + broker)
```

---

## API Documentation

See [`docs/API.md`](docs/API.md) for the complete REST API reference.

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [`TRACK_B_COMPLIANCE.md`](TRACK_B_COMPLIANCE.md) | 50-requirement compliance matrix |
| [`docs/API.md`](docs/API.md) | REST API reference |
| [`docs/TECHNICAL_BLOG_POST.md`](docs/TECHNICAL_BLOG_POST.md) | Architecture deep dive |
| [`docs/PERFORMANCE_BENCHMARKS.md`](docs/PERFORMANCE_BENCHMARKS.md) | Empirical latency measurements |
| [`docs/SECURITY_ASSESSMENT.md`](docs/SECURITY_ASSESSMENT.md) | Security controls & recommendations |
| [`docs/RECRUITER_GUIDE.md`](docs/RECRUITER_GUIDE.md) | End-user guide for recruiters |
| [`docs/ADMIN_GUIDE.md`](docs/ADMIN_GUIDE.md) | Platform administration guide |
| [`docs/TRACK_B_FINAL_REPORT.md`](docs/TRACK_B_FINAL_REPORT.md) | Project final report |

---

## Tech Stack

**Backend**: FastAPI, SQLAlchemy, Alembic, Celery, Redis, LangGraph, LangChain

**Frontend**: React 18, TypeScript, Vite, Axios

**AI**: Groq (Llama 3), OpenAI GPT-4, Anthropic Claude (configurable), Ollama (local), Mock fallback

**Infrastructure**: Docker Compose, GitHub Actions, Railway, Render, Vercel

---

## License

MIT © 2026 RecruiterAI