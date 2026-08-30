# Admin Guide — RecruiterAI Platform

> Complete administration guide for platform administrators.

---

## Accessing the Admin Console

Log in with an **Admin** role account and click **"Administration"** in the sidebar.

The Admin Console has four tabs:
1. **Users** — Manage user accounts and roles
2. **Integrations** — Configure external service connections
3. **Audit Logs** — Review all platform activity
4. **System Status** — Monitor infrastructure health

---

## User Management

### Creating a New User

1. Go to **Admin → Users**
2. Click **"Add User"**
3. Fill in:
   - Username
   - Password (minimum 8 characters)
   - Role: `Admin`, `Recruiter`, `Hiring Manager`, or `Candidate`
4. Click **Create**

### Updating a User's Role

1. Find the user in the Users list
2. Click the **Edit** icon
3. Change the role dropdown
4. Toggle **Active** status if needed
5. Click **Save**

### Deactivating a User

Set the user's **Active** toggle to OFF. The user's JWT tokens remain in Redis blacklist on next logout attempt.

---

## Integration Configuration

### Configuring an LLM Provider

| Setting | Key | Example |
|---------|-----|---------|
| Provider | `LLM_PROVIDER` | `groq`, `openai`, `anthropic` |
| API Key | `GROQ_API_KEY` | `gsk_...` |

To change the LLM provider, update the `.env` file or set the environment variable in your deployment.

### Email Integration (SendGrid)

1. Create a SendGrid account at sendgrid.com
2. Generate an API key with "Mail Send" permissions
3. Set in `.env`:
```
SENDGRID_API_KEY=SG.your_key_here
SMTP_FROM_EMAIL=recruitment@yourdomain.com
```

### Calendar Integration (Google)

1. Create a Google Cloud project
2. Enable the Calendar API
3. Download OAuth2 credentials JSON
4. Set `GOOGLE_CALENDAR_CREDENTIALS=<path_or_json_string>`

### Assessment Providers

| Provider | Variable |
|----------|---------|
| HackerRank | `HACKERRANK_API_KEY` |
| Codility | `CODILITY_API_KEY` |
| Mettl | `METTL_API_KEY` |

If no key is set, the built-in code sandbox runner is used.

### Background Verification

| Provider | Variable |
|----------|---------|
| Checkr | `CHECKR_API_KEY` |
| SpringVerify | `SPRINGVERIFY_API_KEY` |

If no key is set, verification runs in mock simulation mode.

---

## Audit Logs

The audit log captures every sensitive action:

| Action Type | Triggered By |
|-------------|-------------|
| `user_login` | Any user login |
| `user_created` | Admin creates user |
| `role_updated` | Admin changes role |
| `candidate_status_updated` | Recruiter changes pipeline stage |
| `offer_extended` | Recruiter sends offer |
| `data_export` | DSAR data export |
| `data_deletion` | Right-to-erasure request |
| `integration_updated` | Admin changes integration config |

### Filtering Audit Logs

Use the **Action** filter dropdown to see specific event types. All times are displayed in UTC.

---

## System Status

The System Status panel shows real-time health:

| Component | Status | Details |
|-----------|--------|---------|
| Database | Healthy / Error | Connection test result |
| Background Worker | Active / Unavailable | Redis/Celery connectivity |
| LLM Provider | Configured / Mock | Active provider name |
| Email Service | Configured / Mock | Active email backend |

**Green** = Fully operational
**Yellow** = Degraded (using mock fallback)
**Red** = Error state (check logs)

---

## Database Management

### Local Development (SQLite)

SQLite migrations run automatically on startup. No action required.

### Production (PostgreSQL)

1. Set `DATABASE_URL=postgresql://user:pass@host:5432/db`
2. Run Alembic migrations:
```bash
cd backend
alembic upgrade head
```

To create a new migration after schema changes:
```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## Celery Worker Management

### Starting Workers

```bash
# Start worker with all queues
celery -A app.tasks.celery_app worker --loglevel=info

# Start worker for specific queue
celery -A app.tasks.celery_app worker -Q resumes,screening --loglevel=info
```

### Monitoring

```bash
# Real-time monitoring
celery -A app.tasks.celery_app flower

# Check worker status
celery -A app.tasks.celery_app inspect active
```

### Without Redis (Development)

If Redis is not running, all tasks execute synchronously in-process. No configuration needed for local development.

---

## Deployment Guide

### Docker Compose (Recommended)

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend

# Stop all services
docker compose down
```

Services started:
- `postgres` — Database
- `redis` — Cache & Celery broker
- `backend` — FastAPI server
- `celery_worker` — Background task processor
- `frontend` — React app on port 3000

### Environment Variables

Copy and configure `.env.example`:

```bash
cp backend/.env.example backend/.env
# Edit values as needed
```

---

## Backup & Recovery

### Database Backup (SQLite)

```bash
cp backend/recruiter_ai.db backend/recruiter_ai.db.backup.$(date +%Y%m%d)
```

### Database Backup (PostgreSQL)

```bash
pg_dump -h localhost -U postgres recruiter_ai > backup_$(date +%Y%m%d).sql
```
