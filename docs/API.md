# RecruiterAI Platform — REST API Reference

**Base URL**: `http://localhost:8000`
**Authentication**: All endpoints (unless noted) require `Authorization: Bearer <JWT_TOKEN>`

---

## Authentication

### POST /auth/token
Login and obtain a JWT access token.

**Request** (form-data):
```
username=recruiter_user
password=password123
```

**Response** `200 OK`:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

---

### POST /auth/register
Register a new user account.

**Request**:
```json
{
  "username": "new_recruiter",
  "password": "securepass123",
  "role": "Recruiter"
}
```

**Response** `201 Created`: Returns the created User object.

---

### POST /auth/logout
Revoke the current access token. Adds token to Redis blacklist.

**Response** `200 OK`:
```json
{ "message": "Logged out successfully." }
```

---

## Candidates

### GET /candidates
List all candidates (Recruiters and above). Hiring scope limited for Hiring Managers.

**Query params**: `search`, `status`, `min_score`, `location`, `skills`

**Response** `200 OK`: Array of enriched Candidate objects.

---

### POST /candidates
Create a candidate manually.

**Request**:
```json
{
  "name": "Priya Rajan",
  "email": "priya.rajan@example.com",
  "phone": "9876543210",
  "skills": ["Python", "FastAPI"],
  "experience": 3,
  "education": "B.Tech CSE",
  "location": "Pune"
}
```

---

### POST /upload_resume
Upload a resume file (PDF/TXT/DOCX) for automatic AI extraction and scoring.

**Form data**: `file` (multipart), optional `job_id` query parameter.

**Response** `201 Created`: Full candidate profile with extracted fields and ATS score.

---

### POST /bulk_upload
Upload multiple resumes at once (ZIP or multiple files).

---

### GET /candidates/{id}
Get a single candidate profile by ID.

---

### PUT /candidates/{id}
Update candidate fields (Recruiter/Admin only).

---

### PUT /candidates/{id}/status
Update the pipeline stage of a candidate.

**Request**:
```json
{ "status": "Interview" }
```

Valid statuses: `Applied`, `Screening`, `Shortlisted`, `Interview`, `Selected`, `Hired`, `Rejected`

---

## Jobs

### POST /jobs
Create a job requisition.

**Request**:
```json
{
  "title": "Senior Python Developer",
  "description": "Build high-scale microservices...",
  "requirements": ["Python", "FastAPI", "PostgreSQL"],
  "experience_required": 3
}
```

### GET /jobs
List all open job positions.

### GET /jobs/{id}
Get details for a specific job including ranked candidate matches.

---

## AI Screening & Scoring

### POST /score/{candidate_id}/{job_id}
Run the 11-point scoring algorithm for a candidate against a job.

### POST /ai_summary/{candidate_id}
Generate an AI summary of the candidate's profile.

### POST /skill_gap/{candidate_id}/{job_id}
Produce a skill gap analysis and upskilling roadmap.

### POST /interview_questions/{candidate_id}/{job_id}
Generate tailored interview questions.

### POST /recommendation/{candidate_id}/{job_id}
Generate an explainable shortlist/reject recommendation with reason chain.

### POST /screen
Run batch AI screening with configurable thresholds.

---

## Offers

### POST /offers
Extend an offer to a candidate.

**Request**:
```json
{
  "candidate_id": 1,
  "job_id": 1,
  "base_salary": 1800000.0,
  "bonus": 200000.0,
  "currency": "INR"
}
```

**Response** `201 Created`: Created Offer record.

### GET /offers
List all offers (Recruiter/Admin).

### GET /offers/candidate/{id}
List all offers for a specific candidate.

### PUT /offers/{id}
Update offer status.

**Valid statuses**: `Draft`, `Sent`, `Accepted`, `Declined`, `Expired`, `Revoked`

---

## Admin & RBAC

### GET /admin/users
List all platform users. **Admin only**.

### POST /admin/users
Create a new user account. **Admin only**.

### PUT /admin/users/{id}/role
Update user role or active status. **Admin only**.

### GET /admin/integrations
List all external integration configurations.

### POST /admin/integrations
Configure a new integration.

### GET /admin/audit-logs
Retrieve the complete audit trail. Optional `?action=` filter.

### GET /admin/system-status
Get real-time health metrics: database, Redis, Celery worker.

---

## Privacy (GDPR / Indian DPDP)

### POST /privacy/consent
Record candidate consent.

**Request**:
```json
{
  "candidate_id": 1,
  "consent_type": "resume_processing",
  "granted": true
}
```

**Response** `201 Created`.

### GET /privacy/candidates/{id}/export
Export all data for a candidate (DSAR). Returns complete structured JSON.

### DELETE /privacy/candidates/{id}/delete
Hard-delete all personal data for a candidate. Irreversible.

---

## Interviews

### POST /interviews
Schedule an interview slot.

### GET /interviews
List all scheduled interviews.

### GET /interviews/calendar
Get calendar view of upcoming interviews.

---

## Real-time WebSockets

### WS /ws/collaboration
WebSocket endpoint for real-time team collaboration.

**Message format** (JSON):
```json
{
  "type": "STATUS_UPDATE",
  "payload": { "candidate_id": 42, "status": "Interview" },
  "sender": "recruiter_user"
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Validation Error — request body malformed |
| 401 | Unauthorized — missing or invalid JWT |
| 403 | Forbidden — insufficient role permissions |
| 404 | Not Found — resource does not exist |
| 409 | Conflict — duplicate candidate (same email/phone/resume) |
| 422 | Unprocessable — schema validation failed |
| 500 | Internal Server Error |
