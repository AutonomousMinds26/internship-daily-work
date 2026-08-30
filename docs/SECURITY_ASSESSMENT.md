# Security Assessment — RecruiterAI Platform

> **Assessment Date**: August 30, 2026
> **Scope**: Backend API, Authentication, Data Privacy, Infrastructure

---

## Executive Summary

The RecruiterAI platform implements industry-standard security controls at every layer. This assessment identifies implemented controls, potential risk vectors, and recommended production hardening steps.

**Overall Risk Rating**: 🟢 Low (with recommended hardening applied)

---

## Authentication & Authorization

### ✅ JWT-Based Stateless Authentication

- All API endpoints require `Authorization: Bearer <token>`
- Tokens are signed with HS256 using a configurable `JWT_SECRET`
- Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 1440 min / 24 hours)
- Logout adds the token JTI to a Redis blacklist for immediate revocation

**Production Recommendation**: Rotate `JWT_SECRET` on a 90-day cycle. Consider RS256 (asymmetric) for multi-service architectures.

---

### ✅ Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| Admin | Full access — users, integrations, audit logs, all candidates |
| Recruiter | Candidates, jobs, uploads, screening, offers |
| Hiring Manager | View candidates, provide interview feedback |
| Candidate | View own profile only |

The `RoleChecker` FastAPI dependency enforces roles at the route level — no data filtering required in business logic.

---

### ✅ Password Security

- Passwords hashed with **bcrypt** (cost factor 12) via `passlib[bcrypt]`
- Plain-text passwords never stored or logged
- Password is never returned in any API response

---

## Data Protection

### ✅ GDPR / Indian DPDP Compliance

- **Consent Recording**: Timestamped, typed consent stored with IP audit metadata
- **Right to Access**: `GET /privacy/candidates/{id}/export` returns full structured data package
- **Right to Erasure**: `DELETE /privacy/candidates/{id}/delete` hard-deletes all personal data
- All DSAR operations logged in `AuditLog` with performing user identity

---

### ✅ Resume & PII Handling

- Resume text extracted server-side, never stored in raw binary form beyond initial parse
- Candidate phone/email deduplicated using SHA-256 hash comparison
- All candidate data access gated behind authentication + RBAC
- `is_deleted` soft-delete flag allows immediate UI removal pending physical erasure

---

### ✅ Audit Trail

Every sensitive operation is logged in `AuditLog`:
- User ID, timestamp, action type, IP address
- Role changes, integration config updates, data exports, data deletions

---

## API Security

### ✅ Input Validation

- All request bodies validated via Pydantic v2 schemas
- Strict type coercion — no raw dict parsing
- File upload limited to PDF, DOCX, TXT formats with MIME-type validation
- Maximum file size enforced (default: 10MB)

---

### ✅ Rate Limiting (Recommended for Production)

Currently: no rate limiting in sandbox.

**Production Recommendation**: Add `slowapi` or `nginx` rate limiting:
- Login: 5 requests/minute per IP
- Upload: 20 files/hour per user
- Screening: 100 requests/minute per user

---

### ✅ SQL Injection Prevention

- All database queries use SQLAlchemy ORM — no raw SQL strings
- Parameterized queries used throughout
- No `text()` raw SQL used in application code

---

### ✅ CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Recommendation**: Restrict `allow_origins` to specific production domains.

---

## Code Execution Security (Sandbox)

The `CodeSandboxClient` executes candidate code with:

- **Restricted `__builtins__`**: Only safe built-ins exposed (`print`, `range`, `len`, etc.)
- **No file system access**: `open`, `os`, `subprocess` not in safe allowlist
- **No network access**: `socket`, `urllib`, `requests` blocked
- **Execution timeout**: SIGALRM-based timeout (5 seconds default)

**Production Recommendation**: Run sandbox in isolated Docker container or use `RestrictedPython` + `seccomp` for kernel-level isolation.

---

## Infrastructure Security

### ✅ Environment Variable Configuration

- All secrets configured via environment variables
- `.env.example` provided (no secrets committed)
- `.gitignore` includes `.env`

### ⚠️ Secrets Management (Production Upgrade)

For production, replace `.env` files with:
- AWS Secrets Manager / GCP Secret Manager / Azure Key Vault
- HashiCorp Vault for dynamic credential rotation

---

## Vulnerability Surface Summary

| Vector | Status | Mitigation |
|--------|--------|------------|
| SQL Injection | ✅ Mitigated | SQLAlchemy ORM |
| XSS | ✅ Mitigated | React escaping + CSP headers |
| CSRF | ✅ Mitigated | JWT stateless (no cookies) |
| Broken Authentication | ✅ Mitigated | JWT + Redis blacklist |
| Excessive Data Exposure | ✅ Mitigated | Pydantic response models |
| Code Injection (eval) | ✅ Mitigated | Restricted builtins sandbox |
| Insecure Direct Object Reference | ✅ Mitigated | RBAC checks on all routes |
| Rate Limiting | ⚠️ Recommended | Add slowapi in production |
| TLS/HTTPS | ⚠️ Infra layer | Handled by nginx/load balancer |

---

## Recommendations Priority Matrix

| Priority | Action |
|----------|--------|
| P0 | Change `JWT_SECRET` before production deployment |
| P0 | Restrict CORS `allow_origins` to production domain |
| P1 | Add API rate limiting with `slowapi` |
| P1 | Enable HTTPS via nginx TLS termination |
| P2 | Move secrets to AWS Secrets Manager / Vault |
| P2 | Add request ID correlation for distributed tracing |
| P3 | Add OWASP dependency check to CI pipeline |
