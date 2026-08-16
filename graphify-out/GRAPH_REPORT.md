# Graph Report - internship-daily-work  (2026-08-16)

## Corpus Check
- Corpus is ~46,827 words - fits in a single context window. You may not need a graph.

## Summary
- 658 nodes · 1841 edges · 27 communities (22 shown, 5 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 212 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Analytics & Statistics Dashboard
- Legacy Route Schema Definitions
- Enhancement Candidate Scoring Logic
- ATS Match Resume Analysis
- Assessment API Integrations
- Interviews Routing and Scheduling
- Resume Processing Document Readers
- SQLAlchemy Application Database Models
- Candidates Route Handlers
- JWT Auth & DB Configurations
- Candidate DB Routing Handlers
- Jobs Route Endpoint Handlers
- Streamlit Frontend Dashboard Logic
- Core Backend Integration Tests
- AI Endpoint Enhancement Tests
- Redis Caching Verification Mocks
- Token Authentication Routes
- System Logger Implementations
- HTTP Middleware Request Logger
- User DB Authentication Guards
- System Settings Configurations
- Backend Root API Endpoints
- Candidate Email Rejection System

## God Nodes (most connected - your core abstractions)
1. `Candidate` - 89 edges
2. `User` - 68 edges
3. `Job` - 45 edges
4. `Interview` - 22 edges
5. `upload_resume()` - 22 edges
6. `import_candidate_from_source()` - 18 edges
7. `CandidateScore` - 16 edges
8. `get_score()` - 16 edges
9. `calculate_enhanced_score()` - 15 edges
10. `CandidateHistory` - 15 edges

## Surprising Connections (you probably didn't know these)
- `job_extraction_node()` --uses--> `Job`  [INFERRED]
  backend/AI/workflow.py → backend/app/models.py
- `recommendation_generation_node()` --uses--> `Candidate`  [INFERRED]
  backend/AI/workflow.py → backend/app/models.py
- `recommendation_generation_node()` --uses--> `Job`  [INFERRED]
  backend/AI/workflow.py → backend/app/models.py
- `store_results_node()` --uses--> `Candidate`  [INFERRED]
  backend/AI/workflow.py → backend/app/models.py
- `store_results_node()` --uses--> `CandidateScore`  [INFERRED]
  backend/AI/workflow.py → backend/app/models.py

## Import Cycles
- None detected.

## Communities (27 total, 5 thin omitted)

### Community 0 - "Analytics & Statistics Dashboard"
Cohesion: 0.05
Nodes (79): get_diversity_analytics(), get_education_distribution(), get_experience_distribution(), get_hiring_funnel_distribution(), get_location_distribution(), get, post, Session (+71 more)

### Community 1 - "Legacy Route Schema Definitions"
Cohesion: 0.07
Nodes (60): CandidateCreate, CandidateResponse, CandidateStatusUpdate, CandidateUpdate, Config, create_candidate(), create_job(), delete_candidate() (+52 more)

### Community 2 - "Enhancement Candidate Scoring Logic"
Cohesion: 0.07
Nodes (53): calculate_enhanced_score(), extract_years(), normalize(), Enhanced Candidate Scoring Algorithm (11 criteria): 1. Skills Match (30 pts) 2.…, CandidateScore, InterviewQuestion, Recommendation, Resume (+45 more)

### Community 3 - "ATS Match Resume Analysis"
Cohesion: 0.06
Nodes (51): analyze_ats(), analyze_ats_fallback(), clean_json_response(), extract_years_numeric(), Any, Scans and scores a candidate resume/profile against job details for ATS…, analyze_feedback(), analyze_feedback_fallback() (+43 more)

### Community 4 - "Assessment API Integrations"
Cohesion: 0.07
Nodes (37): APIAuthenticationError, APIIntegrationError, APIResponseError, APITimeoutError, APIUnavailableError, AssessmentIntegrationManager, BaseExternalClient, CodilityClient (+29 more)

### Community 5 - "Interviews Routing and Scheduling"
Cohesion: 0.08
Nodes (53): CandidateHistory, Interview, InterviewSlot, Job, book_interview_slot(), cancel_interview(), create_interview_slot(), download_calendar_invite() (+45 more)

### Community 6 - "Resume Processing Document Readers"
Cohesion: 0.09
Nodes (41): ai_match_candidate(), extract_resume_text(), read_docx(), read_pdf(), extract_job_info(), rank_candidates(), extract_candidate_info(), calculate_score() (+33 more)

### Community 7 - "SQLAlchemy Application Database Models"
Cohesion: 0.11
Nodes (46): Assessment, Candidate, CandidateActivity, CandidateSource, Prediction, Base, RecruiterComment, ReferenceCheck (+38 more)

### Community 8 - "Candidates Route Handlers"
Cohesion: 0.10
Nodes (37): create_candidate(), get_candidate(), get_candidate_by_id(), get_candidate_history(), get_score(), list_all_candidates(), list_candidates_with_details(), log_candidate_history() (+29 more)

### Community 9 - "JWT Auth & DB Configurations"
Cohesion: 0.19
Nodes (15): create_access_token(), get_password_hash(), RoleChecker, verify_password(), get_db(), run_db_migrations(), lifespan(), Seed default test users if they don't already exist. (+7 more)

### Community 10 - "Candidate DB Routing Handlers"
Cohesion: 0.17
Nodes (20): _get_candidate_or_404(), Candidate, post, Session, Shared helper to fetch candidate or raise 404., Send a shortlist congratulations email to the candidate. Mock implementation —…, Send an interview invitation email to the candidate. Mock implementation — logs…, send_interview_invitation() (+12 more)

### Community 11 - "Jobs Route Endpoint Handlers"
Cohesion: 0.20
Nodes (14): create_job(), get_job_by_id(), get_jobs(), get, Job, post, Session, Create a new job requirement. Access is restricted to Recruiters and Admins. (+6 more)

### Community 12 - "Streamlit Frontend Dashboard Logic"
Cohesion: 0.14
Nodes (11): api_request(), extract_certifications_from_text(), generate_ai_summary(), generate_interview_questions(), handle_api_error(), login_ui(), parse_education_level(), Generate a simulated AI summary for a candidate. (+3 more)

### Community 13 - "Core Backend Integration Tests"
Cohesion: 0.25
Nodes (11): get_token(), test_candidate_crud(), test_create_job_rbac(), test_email_communication(), test_get_candidate_caching(), test_get_jobs_list(), test_get_score_calculation(), test_interview_management() (+3 more)

### Community 14 - "AI Endpoint Enhancement Tests"
Cohesion: 0.40
Nodes (12): get_token(), setup_candidate_and_job(), test_ai_interview_questions_endpoint(), test_ai_recommendation_endpoint(), test_ai_score_endpoint(), test_ai_semantic_match_endpoint(), test_ai_skill_gap_endpoint(), test_ai_summary_endpoint() (+4 more)

### Community 15 - "Redis Caching Verification Mocks"
Cohesion: 0.20
Nodes (6): client(), mock_redis(), MockRedis, Create a FastAPI TestClient that overrides the get_db dependency., Automatically mock the Redis client for all tests., fixture

### Community 16 - "Token Authentication Routes"
Cohesion: 0.50
Nodes (4): login_for_access_token(), post, Session, OAuth2PasswordRequestForm

### Community 18 - "HTTP Middleware Request Logger"
Cohesion: 0.67
Nodes (3): log_requests_and_handle_errors(), middleware, Request

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Candidate` connect `SQLAlchemy Application Database Models` to `Analytics & Statistics Dashboard`, `Legacy Route Schema Definitions`, `Enhancement Candidate Scoring Logic`, `ATS Match Resume Analysis`, `Assessment API Integrations`, `Interviews Routing and Scheduling`, `Resume Processing Document Readers`, `Candidates Route Handlers`, `JWT Auth & DB Configurations`, `Candidate DB Routing Handlers`, `AI Endpoint Enhancement Tests`?**
  _High betweenness centrality (0.294) - this node is a cross-community bridge._
- **Why does `Job` connect `Interviews Routing and Scheduling` to `Analytics & Statistics Dashboard`, `Enhancement Candidate Scoring Logic`, `ATS Match Resume Analysis`, `Assessment API Integrations`, `Resume Processing Document Readers`, `SQLAlchemy Application Database Models`, `Candidates Route Handlers`, `JWT Auth & DB Configurations`, `Jobs Route Endpoint Handlers`, `AI Endpoint Enhancement Tests`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `User` connect `SQLAlchemy Application Database Models` to `Analytics & Statistics Dashboard`, `Enhancement Candidate Scoring Logic`, `ATS Match Resume Analysis`, `Interviews Routing and Scheduling`, `Candidates Route Handlers`, `JWT Auth & DB Configurations`, `Candidate DB Routing Handlers`, `Token Authentication Routes`, `User DB Authentication Guards`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Are the 69 inferred relationships involving `Candidate` (e.g. with `recommendation_generation_node()` and `store_results_node()`) actually correct?**
  _`Candidate` has 69 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `User` (e.g. with `get_current_user()` and `RoleChecker`) actually correct?**
  _`User` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `Job` (e.g. with `job_extraction_node()` and `recommendation_generation_node()`) actually correct?**
  _`Job` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Interview` (e.g. with `run_feedback_analysis()` and `book_interview_slot()`) actually correct?**
  _`Interview` has 14 INFERRED edges - model-reasoned connections that need verification._