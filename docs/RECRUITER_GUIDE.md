# Recruiter Guide — RecruiterAI Platform

> Your complete guide to sourcing, screening, interviewing, and hiring top talent with AI.

---

## Getting Started

### Login

Navigate to the RecruiterAI portal and enter your credentials. Your recruiter account gives you full access to:

- Candidate pipeline
- Resume uploads
- AI screening
- Job management
- Interview scheduling
- Analytics

---

## Uploading Resumes

### Single Resume Upload

1. Click **"Resume Ingestion Hub"** in the sidebar
2. Drag and drop a PDF, DOCX, or TXT file
3. Optionally select a **Job Role** to immediately score against
4. Click **Upload**

The platform will:
- Extract candidate information (name, email, phone, skills, experience)
- Run AI scoring against the selected job
- Add the candidate to the pipeline automatically

### Bulk Upload

Upload a ZIP file containing multiple resumes. All resumes are processed in parallel using background workers.

---

## Reviewing Candidates

### Talent Directory

The **Talent Directory** shows all candidates with:

- AI match score (0–100%)
- ATS score
- Status badge (Applied, Screening, Shortlisted, Interview, etc.)
- Skills tags
- Location and experience

**Sorting**: Click any column header to sort.

**Filtering**: Use the search bar or filter dropdowns for status, location, skills, and minimum score.

### Candidate Detail View

Click any candidate to open their deep profile:

- **Overview**: Contact info, education, experience
- **AI Summary**: Auto-generated profile narrative
- **Skill Gap Analysis**: Missing skills vs. job requirements
- **Recommendation**: AI shortlist/reject with reasoning
- **History**: Complete activity timeline

---

## AI Screening

### Running a Screening Session

1. Open **AI Screening Assessment**
2. Select the job role
3. Choose candidates to screen
4. Set threshold score (default: 70%)
5. Click **Run Screening**

Candidates below the threshold are automatically flagged. You can override any AI decision manually.

### Understanding Scores

| Score Range | Interpretation |
|-------------|----------------|
| 85–100% | Excellent match — fast-track for interview |
| 70–84% | Good match — worth scheduling a call |
| 50–69% | Partial match — consider with caveats |
| < 50% | Poor match — likely to reject |

---

## Managing the Pipeline

### Kanban Board

The **Pipeline** view shows candidates in a drag-and-drop Kanban board:

```
Applied → Screening → Shortlisted → Interview → Selected → Hired
                                                     ↓
                                                  Rejected
```

Drag candidates between columns to update their status. All status changes are recorded in the audit trail and trigger real-time notifications to the team.

---

## Interview Scheduling

### Scheduling an Interview

1. Open **Interview Coordinator**
2. Find the candidate (or click "Schedule Interview" from their profile)
3. Select date, time, and interview format (Video / Phone / In-person)
4. Add the job description
5. Click **Schedule**

The system sends calendar invites and generates AI-tailored interview questions automatically.

### Interview Question Generator

From the candidate profile, click **"Generate Questions"** to get role-specific questions covering:
- Technical depth
- Behavioral scenarios
- Cultural fit

---

## Sending Assessments

### Dispatching a Coding Assessment

1. Open a candidate profile
2. Click **"Send Assessment"**
3. Choose provider (HackerRank, Codility, or Internal Sandbox)
4. Select the test type and duration
5. The candidate receives an email with a secure link

Results are automatically imported back into the candidate profile.

---

## Offers

### Extending an Offer

1. Open a candidate profile in **"Selected"** status
2. Click **"Create Offer"**
3. Fill in:
   - Base Salary
   - Bonus
   - Currency
   - Benefits
4. Click **Send Offer**

Track offer status: **Draft → Sent → Accepted / Declined**

---

## Diversity & Analytics

### Diversity Dashboard

The **Analytics** tab shows:

- Gender distribution across pipeline stages
- 4/5ths rule adverse impact calculator
- Stage conversion rates
- Time-to-hire metrics

**Adverse Impact Alert**: If the disparity ratio drops below 0.80, a red alert is shown — indicating potential bias in screening.

---

## Tips for Better AI Results

1. **Upload text-based PDFs** — scanned image PDFs extract less accurately
2. **Create detailed job descriptions** — more skills listed = better ATS matching
3. **Use consistent skill names** — "FastAPI" not "Fast API" or "fast-api"
4. **Score against a job** during upload — this enables full 11-point scoring immediately
5. **Review AI recommendations as suggestions** — always apply human judgment
