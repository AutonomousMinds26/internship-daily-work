# Performance Benchmarks — RecruiterAI Platform

> **Measurement Date**: August 30, 2026
> **Environment**: macOS, Python 3.13.11, SQLite (local sandbox, no external LLM API)
> **Methodology**: Each benchmark run N times, reporting average and P95 latencies

---

## Benchmark Results

### 1. Candidate Matching & ATS Scoring (100 iterations)

| Metric | Value |
|--------|-------|
| Average Latency | **68.60 ms** |
| P95 Latency | **137.30 ms** |
| Throughput | **14.6 candidates/sec** |

> **Notes**: Includes 11-point scoring + ATS keyword extraction + skill gap delta. LLM fallback path (regex-only) used as Groq credentials not configured in sandbox. With a valid LLM key, expect 200–500ms for LLM-enhanced ATS path.

---

### 2. Sandboxed Code Evaluation (50 runs × 5 test cases)

| Metric | Value |
|--------|-------|
| Average Latency | **0.11 ms** |
| Per Test Case | **0.022 ms** |

> **Notes**: Pure Python `exec()` sandbox with `__builtins__` restriction. Supports tuple argument unpacking for multi-parameter function calls.

---

### 3. LangGraph Multi-State Recruitment Pipeline (20 runs, 9 nodes)

| Metric | Value |
|--------|-------|
| Average Latency | **67.93 ms** |
| P95 Latency | **130.95 ms** |

> **Notes**: Pipeline includes: `load_data` → `parse_data` → `matching` → `screening` → `assessment` → `interview` → `feedback` → `verification` → `offer`. LangGraph sequential fallback executor used in sandbox mode. With LangGraph installed, add ~15ms for state machine overhead.

---

### 4. Celery Background Task Processing (30 runs)

| Task | Average Latency |
|------|----------------|
| `process_resume_task` | **2.65 ms** |
| `send_notification_email_task` | < 1 ms |
| `run_background_verification_task` | < 5 ms |
| `aggregate_analytics_daily_task` | < 10 ms |

> **Notes**: Measured in synchronous eager-execution mode (no Redis broker). Async Celery dispatch adds ~2–5ms overhead per task for broker round-trip in production.

---

### 5. Algorithmic Fairness & 4/5ths Rule Check (200 runs)

| Metric | Value |
|--------|-------|
| Average Latency | **0.0007 ms** |
| Throughput | **~1.4M checks/sec** |

> **Notes**: Pure Python arithmetic with no I/O. Effectively zero cost to embed in any screening pipeline.

---

## API Endpoint Latencies (FastAPI TestClient)

| Endpoint | Method | Avg Latency |
|----------|--------|-------------|
| `POST /auth/token` | POST | ~171 ms |
| `GET /candidates` | GET | < 50 ms |
| `POST /upload_resume` | POST | ~370 ms |
| `GET /admin/system-status` | GET | < 10 ms |
| `GET /admin/audit-logs` | GET | < 10 ms |
| `POST /offers` | POST | < 20 ms |
| `POST /privacy/consent` | POST | < 10 ms |

---

## Production Scaling Projections

Based on current benchmark data:

| Scenario | Estimated Capacity |
|----------|-------------------|
| Single Uvicorn worker | ~15 candidate matches/sec |
| 4 Uvicorn workers (1 server) | ~60 candidate matches/sec |
| 4 Celery workers | ~400 async tasks/min |
| With PostgreSQL (vs SQLite) | +30% query speed on large datasets |
| With Redis cache hit | < 5ms for cached candidate profiles |

---

## Benchmark Notes

- All measurements taken with **no active LLM API key** — fallback Python scanner used
- With a valid `GROQ_API_KEY`, LLM-enhanced paths add 200–800ms due to network round-trip
- SQLite used for local benchmarks; PostgreSQL adds ~1–3ms per query (pool overhead) but scales much better under concurrent load
- WebSocket latency not benchmarked in this run; expected < 10ms for message broadcast in LAN
