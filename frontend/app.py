import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re
import time
import calendar as cal_module
from datetime import date, datetime, timedelta
from collections import Counter

# Page Configuration
st.set_page_config(
    page_title="RecruiterAI Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom Styling (Glassmorphism + extended component styles) ───────────────
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        * {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Metric Card styling */
        .metric-card {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid #334155;
            box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
            text-align: center;
            color: #F8FAFC;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: #6366F1;
            box-shadow: 0 12px 32px 0 rgba(99, 102, 241, 0.25);
        }
        
        .metric-title {
            font-size: 13px;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 36px;
            font-weight: 800;
            color: #818CF8;
        }
        
        /* Profile cards */
        .profile-container {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #334155;
            margin-bottom: 15px;
            color: #F8FAFC;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        
        /* Badge styling */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 700;
            margin: 2px;
        }
        
        .badge-skill {
            background-color: #1E1B4B;
            color: #A5B4FC;
            border: 1px solid #4338CA;
        }
        
        .badge-matched {
            background-color: #064E3B;
            color: #6EE7B7;
            border: 1px solid #059669;
        }
        
        .badge-missing {
            background-color: #7F1D1D;
            color: #FCA5A5;
            border: 1px solid #DC2626;
        }

        /* Error alerts overrides */
        .error-header {
            font-weight: 700;
            color: #EF4444;
            margin-bottom: 8px;
        }

        /* Ranking table row */
        .rank-row {
            display: flex;
            align-items: center;
            gap: 16px;
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 14px 20px;
            margin-bottom: 10px;
            transition: all 0.25s ease;
            color: #F8FAFC;
        }
        .rank-row:hover {
            background: #2D3748;
            border-color: #6366F1;
            transform: translateX(4px);
        }
        .rank-number {
            font-size: 22px;
            font-weight: 700;
            color: #818CF8;
            min-width: 32px;
        }
        .rank-name {
            font-size: 16px;
            font-weight: 600;
            color: #F8FAFC;
            flex: 1;
        }
        .rank-score {
            font-size: 20px;
            font-weight: 700;
        }
        .badge-shortlisted {
            background-color: #064E3B;
            color: #6EE7B7;
            border: 1px solid #059669;
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 700;
        }
        .badge-maybe {
            background-color: #78350F;
            color: #FDE68A;
            border: 1px solid #D97706;
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 700;
        }
        .badge-reject {
            background-color: #7F1D1D;
            color: #FCA5A5;
            border: 1px solid #DC2626;
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 700;
        }
        .detail-panel {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 24px;
            margin-top: 8px;
            color: #F8FAFC;
        }
        .job-selector-box {
            background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
            border: 1px solid #4338CA;
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 24px;
            color: #F8FAFC;
        }

        /* Journey Timeline */
        .timeline-container {
            display: flex;
            align-items: flex-start;
            gap: 0;
            margin: 16px 0;
            overflow-x: auto;
            padding-bottom: 8px;
        }
        .timeline-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            min-width: 90px;
            position: relative;
        }
        .timeline-step:not(:last-child)::after {
            content: '';
            position: absolute;
            top: 18px;
            left: 50%;
            width: 100%;
            height: 2px;
            background: #334155;
            z-index: 0;
        }
        .timeline-step.completed::after {
            background: linear-gradient(90deg, #10B981, #10B981);
        }
        .timeline-step.active::after {
            background: linear-gradient(90deg, #3B82F6, #334155);
        }
        .timeline-dot {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            z-index: 1;
            border: 2px solid;
            transition: all 0.3s ease;
        }
        .timeline-dot.completed {
            background: #064E3B;
            border-color: #10B981;
            color: #6EE7B7;
        }
        .timeline-dot.active {
            background: #1E3A8A;
            border-color: #3B82F6;
            color: #93C5FD;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.5);
        }
        .timeline-dot.pending {
            background: #1E293B;
            border-color: #475569;
            color: #94A3B8;
        }
        .timeline-label {
            font-size: 11px;
            text-align: center;
            margin-top: 6px;
            line-height: 1.3;
        }
        .timeline-label.completed { color: #10B981; font-weight: 700; }
        .timeline-label.active { color: #3B82F6; font-weight: 700; }
        .timeline-label.pending { color: #64748B; font-weight: 600; }

        /* Communication Buttons */
        .comm-btn-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 12px;
        }

        /* Interview card */
        .interview-card {
            background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
            border: 1px solid #4338CA;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 10px;
            transition: all 0.25s ease;
            color: #F8FAFC;
        }
        .interview-card:hover {
            border-color: #6366F1;
        }

        /* Platform pill */
        .platform-pill {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 600;
            background: #312E81;
            color: #C7D2FE;
            border: 1px solid #4338CA;
        }

        /* Pagination buttons */
        .pagination-info {
            text-align: center;
            color: #64748B;
            font-size: 14px;
            margin: 8px 0;
        }

        /* AI Insight Card */
        .ai-insight-card {
            background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
            border: 1px solid #4338CA;
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 14px;
            color: #F8FAFC;
            transition: all 0.3s ease;
        }
        .ai-insight-card:hover {
            border-color: #6366F1;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
        }

        /* Question Card */
        .question-card {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 10px;
            color: #F8FAFC;
            transition: all 0.25s ease;
        }
        .question-card:hover {
            border-color: #6366F1;
        }

        /* Comparison Grid */
        .comparison-col {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 20px;
            min-height: 200px;
            color: #F8FAFC;
        }
        .comparison-col:hover {
            border-color: #6366F1;
        }
        .comparison-winner {
            border: 2px solid #10B981 !important;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.25);
        }

        /* Calendar cell */
        .cal-cell {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 8px;
            min-height: 80px;
            font-size: 12px;
            color: #F8FAFC;
        }
        .cal-cell-today {
            border-color: #6366F1;
            background: #1E1B4B;
        }
        .cal-event {
            background: #312E81;
            border-left: 3px solid #6366F1;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 11px;
            margin-top: 4px;
            color: #C7D2FE;
        }

        /* Diversity metric */
        .diversity-metric {
            background: linear-gradient(135deg, #0891B2 0%, #0F172A 100%);
            border: 1px solid #06B6D4;
            border-radius: 12px;
            padding: 16px 20px;
            text-align: center;
            color: #F8FAFC;
        }

        /* Section header */
        .section-header {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #6366F1;
            font-weight: 700;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #334155;
        }

        /* ── Assessment Card ── */
        .assessment-card {
            background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
            border: 1px solid #4338CA;
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 14px;
            transition: all 0.3s ease;
            color: #F8FAFC;
        }
        .assessment-card:hover {
            border-color: #6366F1;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.25);
        }

        /* ── Vertical Activity Timeline ── */
        .timeline-v-container {
            position: relative;
            padding-left: 32px;
            margin: 16px 0;
        }
        .timeline-v-container::before {
            content: '';
            position: absolute;
            left: 12px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(180deg, #6366F1, #10B981, #F59E0B);
        }
        .timeline-v-item {
            position: relative;
            padding: 14px 18px;
            margin-bottom: 12px;
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 10px;
            transition: all 0.25s ease;
            color: #F8FAFC;
        }
        .timeline-v-item:hover {
            background: #2D3748;
            border-color: #6366F1;
            transform: translateX(4px);
        }
        .timeline-v-item::before {
            content: '';
            position: absolute;
            left: -26px;
            top: 18px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #6366F1;
            border: 2px solid #818CF8;
            box-shadow: 0 0 8px rgba(99, 102, 241, 0.6);
        }
        .timeline-v-time {
            font-size: 12px;
            color: #94A3B8;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .timeline-v-text {
            font-size: 14px;
            color: #F8FAFC;
            font-weight: 600;
        }

        /* ── Verification Row ── */
        .verification-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 10px;
            transition: all 0.25s ease;
            color: #F8FAFC;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        .verification-row:hover {
            border-color: #6366F1;
            transform: translateY(-2px);
        }
        .verification-label {
            font-size: 16px;
            font-weight: 700;
            color: #F8FAFC;
        }
        .verification-status {
            padding: 6px 16px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 700;
        }

        /* ── Prediction Card (Glassmorphism) ── */
        .prediction-card {
            background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
            border-radius: 18px;
            padding: 28px;
            border: 1px solid #4C1D95;
            box-shadow: 0 10px 32px 0 rgba(0, 0, 0, 0.25);
            transition: all 0.35s ease;
            color: #F8FAFC;
        }
        .prediction-card:hover {
            transform: translateY(-4px);
            border-color: #8B5CF6;
            box-shadow: 0 16px 48px rgba(139, 92, 246, 0.25);
        }
        .prediction-header {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #C4B5FD;
            font-weight: 700;
            margin-bottom: 16px;
        }
        .prediction-value {
            font-size: 42px;
            font-weight: 800;
            color: #34D399;
        }
        .prediction-value-warn {
            font-size: 42px;
            font-weight: 800;
            color: #FBBF24;
        }

        /* ── Source Badge ── */
        .source-badge {
            display: inline-block;
            padding: 5px 14px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 700;
        }
        .source-linkedin { background: #1E3A8A; color: #93C5FD; border: 1px solid #3B82F6; }
        .source-indeed { background: #1E293B; color: #60A5FA; border: 1px solid #3B82F6; }
        .source-referral { background: #064E3B; color: #6EE7B7; border: 1px solid #10B981; }
        .source-portal { background: #78350F; color: #FDE68A; border: 1px solid #F59E0B; }
        .source-direct { background: #4C1D95; color: #C4B5FD; border: 1px solid #8B5CF6; }

        /* ── Comment Bubble ── */
        .comment-bubble {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 10px;
            border-left: 4px solid #6366F1;
            transition: all 0.2s ease;
            color: #F8FAFC;
        }
        .comment-bubble:hover {
            border-left-color: #818CF8;
            background: #2D3748;
        }
        .comment-author {
            font-size: 13px;
            font-weight: 700;
            color: #A5B4FC;
        }
        .comment-time {
            font-size: 11px;
            color: #94A3B8;
            margin-left: 8px;
        }
        .comment-text {
            font-size: 14px;
            color: #F1F5F9;
            margin-top: 6px;
            line-height: 1.5;
        }

        /* ── Factor Check ── */
        .factor-check {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 10px;
            margin-bottom: 10px;
            font-size: 14px;
            color: #F8FAFC;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .factor-check:hover {
            background: #2D3748;
            border-color: #10B981;
            transform: translateX(4px);
        }
        .factor-icon {
            color: #34D399;
            font-weight: 800;
            font-size: 18px;
        }

        /* ── Risk Level Badge ── */
        .risk-low { background: #064E3B; color: #6EE7B7; border: 1px solid #10B981; padding: 6px 18px; border-radius: 50px; font-weight: 700; font-size: 14px; }
        .risk-medium { background: #78350F; color: #FDE68A; border: 1px solid #F59E0B; padding: 6px 18px; border-radius: 50px; font-weight: 700; font-size: 14px; }
        .risk-high { background: #7F1D1D; color: #FCA5A5; border: 1px solid #EF4444; padding: 6px 18px; border-radius: 50px; font-weight: 700; font-size: 14px; }

        /* ── AI Recommendation Card ── */
        .ai-rec-card {
            background: linear-gradient(135deg, #064E3B 0%, #0F172A 100%);
            border: 1px solid #059669;
            border-radius: 14px;
            padding: 20px 24px;
            margin-top: 12px;
            color: #F8FAFC;
            box-shadow: 0 6px 20px rgba(5, 150, 105, 0.15);
        }
    </style>
""", unsafe_allow_html=True)

# ─── Environment & Session State ──────────────────────────────────────────────
BACKEND_DEFAULT = os.getenv("BACKEND_API_URL", "http://localhost:8000")

if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "candidate_page" not in st.session_state:
    st.session_state.candidate_page = 0

# ── Assessment Integration state ──
if "assessment_data" not in st.session_state:
    st.session_state.assessment_data = [
        {"id": 1, "candidate_name": "Rahul Sharma", "candidate_email": "rahul@example.com", "type": "Technical", "status": "Completed", "score": 87, "assigned_date": "2026-08-10", "deadline": "2026-08-14", "time_taken": "42 min", "sections": {"Data Structures": 90, "Algorithms": 85, "System Design": 82, "SQL": 92}, "strengths": ["Strong algorithmic thinking", "Excellent SQL proficiency"], "recommendations": ["Practice system design patterns", "Review distributed systems concepts"]},
        {"id": 2, "candidate_name": "Priya Desai", "candidate_email": "priya@example.com", "type": "Coding Challenge", "status": "In Progress", "score": None, "assigned_date": "2026-08-14", "deadline": "2026-08-18", "time_taken": None, "sections": {}, "strengths": [], "recommendations": []},
        {"id": 3, "candidate_name": "Ayush Patel", "candidate_email": "ayush@example.com", "type": "Aptitude", "status": "Pending", "score": None, "assigned_date": "2026-08-15", "deadline": "2026-08-20", "time_taken": None, "sections": {}, "strengths": [], "recommendations": []},
        {"id": 4, "candidate_name": "Sneha Kulkarni", "candidate_email": "sneha@example.com", "type": "Personality", "status": "Completed", "score": 74, "assigned_date": "2026-08-08", "deadline": "2026-08-12", "time_taken": "28 min", "sections": {"Communication": 80, "Teamwork": 78, "Leadership": 65, "Adaptability": 72}, "strengths": ["Excellent communicator", "Team-oriented mindset"], "recommendations": ["Develop leadership initiatives", "Seek cross-functional project exposure"]},
    ]

# ── Candidate Sourcing state ──
if "sourced_candidates" not in st.session_state:
    st.session_state.sourced_candidates = [
        {"id": 1, "source": "LinkedIn", "name": "Amit Verma", "email": "amit.v@email.com", "phone": "+91-9876543210", "skills": "Python, Django, AWS", "experience": 5, "date_imported": "2026-08-12", "status": "Contacted"},
        {"id": 2, "source": "Indeed", "name": "Kavita Nair", "email": "kavita.n@email.com", "phone": "+91-9123456789", "skills": "React, Node.js, MongoDB", "experience": 3, "date_imported": "2026-08-13", "status": "New"},
        {"id": 3, "source": "Referral", "name": "Ravi Kumar", "email": "ravi.k@email.com", "phone": "+91-9988776655", "skills": "Java, Spring Boot, Kafka", "experience": 7, "date_imported": "2026-08-10", "status": "In Review"},
        {"id": 4, "source": "Job Portal", "name": "Deepa Menon", "email": "deepa.m@email.com", "phone": "+91-9012345678", "skills": "ML, Python, TensorFlow", "experience": 4, "date_imported": "2026-08-14", "status": "Converted"},
        {"id": 5, "source": "Direct Apply", "name": "Sanjay Gupta", "email": "sanjay.g@email.com", "phone": "+91-9567890123", "skills": "Go, Docker, Kubernetes", "experience": 6, "date_imported": "2026-08-15", "status": "New"},
    ]

# ── Collaboration state ──
if "team_notes" not in st.session_state:
    st.session_state.team_notes = {}
if "recruiter_comments" not in st.session_state:
    st.session_state.recruiter_comments = {}
if "candidate_activity" not in st.session_state:
    st.session_state.candidate_activity = {}
if "assigned_recruiters" not in st.session_state:
    st.session_state.assigned_recruiters = {}

# Sidebar
st.sidebar.title("💼 RecruiterAI")
api_url = st.sidebar.text_input("Backend API URL", value=BACKEND_DEFAULT, help="Change URL if backend runs elsewhere")

# ─── Helpers ──────────────────────────────────────────────────────────────────
def handle_api_error(e, context="API Request Failed"):
    st.sidebar.error("🔌 Connection Error")
    st.error(f"""
        ### 🚨 API Error
        **Context:** {context}
        
        Failed to connect to the backend API at **{api_url}**.
        
        **Possible Reasons:**
        - The backend server is not running.
        - The API URL provided is incorrect.
        - There is a network or firewall block.
        
        *Technical details:* `{str(e)}`
    """)

def api_request(method, endpoint, json=None, data=None, files=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    url = f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        if method.lower() == "post":
            return requests.post(url, headers=headers, json=json, data=data, files=files, timeout=10)
        elif method.lower() == "patch":
            return requests.patch(url, headers=headers, json=json, timeout=10)
        elif method.lower() == "get":
            return requests.get(url, headers=headers, params=json, timeout=10)
        elif method.lower() == "delete":
            return requests.delete(url, headers=headers, timeout=10)
    except Exception as e:
        handle_api_error(e, f"{method.upper()} to {endpoint}")
        return None

def get_recommendation(score):
    if score >= 70:
        return "Shortlisted", "badge-shortlisted", "✅"
    elif score >= 40:
        return "Maybe", "badge-maybe", "🤔"
    else:
        return "Reject", "badge-reject", "❌"

def score_color(score):
    if score >= 70:
        return "#34D399"
    elif score >= 40:
        return "#FCD34D"
    return "#F87171"

def platform_icon(platform):
    icons = {"Google Meet": "🟢", "Microsoft Teams": "🔵", "Zoom": "🟣"}
    return icons.get(platform, "📹")

# ─── AI Helper Functions ──────────────────────────────────────────────────────
def generate_ai_summary(candidate, match_score=None, matched_skills=None, missing_skills=None, experience_gap=None):
    """Generate a simulated AI summary for a candidate."""
    name = candidate.get("name", "Candidate") if isinstance(candidate, dict) else str(candidate)
    skills = candidate.get("skills", []) if isinstance(candidate, dict) else []
    exp = candidate.get("experience", 0) if isinstance(candidate, dict) else 0
    education = candidate.get("education", "N/A") if isinstance(candidate, dict) else "N/A"

    top_skills = ", ".join(skills[:5]) if skills else "no specific skills listed"
    parts = [
        f"**{name}** is a candidate with **{exp} years** of professional experience",
        f"and expertise in {top_skills}.",
    ]
    if education and education != "N/A":
        parts.append(f"Educational background: {education}.")
    if match_score is not None:
        if match_score >= 70:
            parts.append(f"With a **{match_score}%** match score, this candidate is a **strong fit** for the role.")
        elif match_score >= 40:
            parts.append(f"At **{match_score}%** match, this candidate shows **moderate alignment** and may benefit from upskilling.")
        else:
            parts.append(f"The **{match_score}%** match score indicates **significant gaps** in required qualifications.")
    if matched_skills:
        parts.append(f"Key strengths include: {', '.join(matched_skills[:4])}.")
    if missing_skills:
        parts.append(f"Areas for development: {', '.join(missing_skills[:4])}.")
    if experience_gap and experience_gap > 0:
        parts.append(f"Note: {experience_gap} year(s) below the experience requirement.")
    return " ".join(parts)


def generate_interview_questions(skills, job_requirements=None, missing_skills=None, experience=0):
    """Generate interview questions based on candidate profile."""
    questions = {"technical": [], "behavioral": [], "skill_gap": []}

    tech_templates = [
        "Describe a complex project where you used {skill}. What challenges did you face?",
        "How do you stay current with best practices in {skill}?",
        "Can you explain the architecture decisions you've made involving {skill}?",
        "What testing strategies do you employ when working with {skill}?",
        "Walk us through how you would debug a performance issue in a {skill}-based system.",
    ]
    for i, skill in enumerate(skills[:5]):
        template = tech_templates[i % len(tech_templates)]
        questions["technical"].append(template.format(skill=skill))

    behavioral = [
        "Tell me about a time you had to learn a new technology quickly to meet a project deadline.",
        "Describe a situation where you disagreed with a team member on a technical approach. How did you resolve it?",
        "How do you prioritize tasks when working on multiple projects simultaneously?",
        "Give an example of how you mentored a junior team member or contributed to knowledge sharing.",
        "Describe a time when a project requirement changed significantly. How did you adapt?",
    ]
    if experience >= 5:
        behavioral.append("Tell me about your experience leading a team through a challenging project.")
        behavioral.append("How do you approach setting technical direction for your team?")
    questions["behavioral"] = behavioral

    if missing_skills:
        gap_templates = [
            "While your background is strong, this role requires {skill}. What's your familiarity with it?",
            "How would you approach learning {skill} in the context of this role?",
            "Have you worked alongside teams that used {skill}? What did you observe?",
        ]
        for i, skill in enumerate(missing_skills[:3]):
            template = gap_templates[i % len(gap_templates)]
            questions["skill_gap"].append(template.format(skill=skill))

    return questions


def extract_certifications_from_text(resume_text):
    """Extract certifications from resume text using regex patterns."""
    if not resume_text:
        return []
    cert_patterns = [
        r'(?:certified|certification|certificate)\s*(?:in|:)?\s*([A-Za-z\s\-\+\.]{4,40})',
        r'(AWS\s+(?:Certified\s+)?(?:Solutions?\s*Architect|Developer|SysOps|DevOps|Cloud\s*Practitioner)[^\n]{0,30})',
        r'(Google\s+(?:Cloud\s+)?(?:Certified|Professional)[^\n]{0,30})',
        r'(Azure\s+(?:Certified|Administrator|Developer|Solutions?\s*Architect)[^\n]{0,30})',
        r'(PMP|SCRUM|CSM|CISSP|CCNA|CCNP|CKA|CKAD)',
        r'((?:Oracle|Microsoft|Salesforce)\s+Certified[^\n]{0,30})',
    ]
    certs = []
    for pattern in cert_patterns:
        matches = re.findall(pattern, resume_text, re.IGNORECASE)
        for match in matches:
            cleaned = match.strip().strip('.,;:')
            if len(cleaned) > 3 and cleaned not in certs:
                certs.append(cleaned)
    return certs[:10]


def parse_education_level(education_text):
    """Parse education level from text."""
    if not education_text:
        return "Unknown"
    text = education_text.lower()
    if any(t in text for t in ["phd", "ph.d", "doctorate", "doctoral"]):
        return "PhD/Doctorate"
    elif any(t in text for t in ["master", "m.s.", "m.sc", "mba", "m.tech", "m.e."]):
        return "Master's"
    elif any(t in text for t in ["bachelor", "b.s.", "b.sc", "b.tech", "b.e.", "bba", "b.a."]):
        return "Bachelor's"
    elif any(t in text for t in ["diploma", "associate"]):
        return "Diploma/Associate"
    elif any(t in text for t in ["high school", "12th", "hsc"]):
        return "High School"
    return "Other"

# ─── Journey Timeline component ───────────────────────────────────────────────
JOURNEY_STAGES = [
    ("📄", "Resume\nUploaded"),
    ("🔍", "Resume\nParsed"),
    ("🎯", "Job\nMatched"),
    ("⭐", "Shortlisted"),
    ("📅", "Interview\nScheduled"),
    ("✅", "Selected"),
    ("🎁", "Offer\nReleased"),
]

STATUS_TO_STAGE_IDX = {
    "Applied": 2,       # Resume Uploaded + Parsed + Job Matched
    "Screening": 2,
    "Shortlisted": 3,
    "Interview": 4,
    "Selected": 5,
    "Offer Released": 6,
}

def render_journey_timeline(candidate_status: str):
    current_idx = STATUS_TO_STAGE_IDX.get(candidate_status, 0)
    steps_html = ""
    for i, (icon, label) in enumerate(JOURNEY_STAGES):
        if i < current_idx:
            dot_cls = "completed"
            lbl_cls = "completed"
        elif i == current_idx:
            dot_cls = "active"
            lbl_cls = "active"
        else:
            dot_cls = "pending"
            lbl_cls = "pending"

        connector_cls = ""
        if i < current_idx:
            connector_cls = "completed"
        elif i == current_idx:
            connector_cls = "active"

        step_cls = f"timeline-step {connector_cls}"
        steps_html += f"""
        <div class="{step_cls}">
            <div class="timeline-dot {dot_cls}">{icon}</div>
            <div class="timeline-label {lbl_cls}">{label}</div>
        </div>"""

    st.markdown(
        f'<div class="timeline-container">{steps_html}</div>',
        unsafe_allow_html=True,
    )

# ─── Authentication ────────────────────────────────────────────────────────────
def login_ui():
    st.markdown("<h2 style='text-align: center;'>🔐 Sign In to RecruiterAI</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.info("💡 **Test Users (seeded):**\n- `recruiter_user` / `password123` (Recruiter)\n- `manager_user` / `password123` (Hiring Manager)\n- `admin_user` / `password123` (Admin)")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Log In", width="stretch"):
                if not username or not password:
                    st.warning("Please enter both username and password.")
                    return
                login_data = {"username": username, "password": password}
                try:
                    url = f"{api_url.rstrip('/')}/auth/token"
                    res = requests.post(url, data=login_data, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.username = username
                        if "admin" in username.lower():
                            st.session_state.role = "Admin"
                        elif "manager" in username.lower():
                            st.session_state.role = "Hiring Manager"
                        elif "candidate" in username.lower() or "@" in username:
                            st.session_state.role = "Candidate"
                        else:
                            st.session_state.role = "Recruiter"
                        st.toast(f"Welcome back, {username}! Role: {st.session_state.role}", icon="🎉")
                        time.sleep(0.5)
                        st.rerun()
                    elif res.status_code == 401:
                        st.error("❌ Invalid Username or Password. Please try again.")
                    else:
                        st.error(f"❌ Login Failed: {res.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    handle_api_error(e, "User Authentication")

# ─── Main Routing ──────────────────────────────────────────────────────────────
if not st.session_state.token:
    login_ui()
else:
    st.sidebar.success(f"Logged in as: **{st.session_state.username}**")
    st.sidebar.info(f"Role: **{st.session_state.role}**")

    # Build nav options by role
    nav_options = [
        "Recruiter Dashboard",
        "Candidate Pipeline / Kanban",
        "Candidate Details Page",
        "Recruitment Reports",
        "AI Dashboard",
        "Analytics Dashboard",
        "AI Ranking",
        "Candidates List",
        "Upload Resume",
        "Schedule Interview",
        "Compare Candidates",
        "Assessment Integration",
        "Candidate Sourcing",
        "Reference & Verification",
        "Predictive Analytics",
    ]
    if st.session_state.role == "Admin":
        nav_options.append("Admin Settings")
    if st.session_state.role == "Candidate":
        nav_options = ["My Profile & Status", "Available Jobs"]

    choice = st.sidebar.radio("Navigation", nav_options)

    if st.sidebar.button("Log Out", width="stretch"):
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # A2-9. RECRUITER DASHBOARD PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    if choice == "Recruiter Dashboard":
        st.title("💼 Recruiter Candidate Dashboard")
        st.markdown("Overview of candidate metrics and recruitment pipeline distribution.")
        st.markdown("---")

        with st.spinner("Loading candidate statistics..."):
            cand_res = api_request("GET", "/candidates")

        candidates = cand_res.json() if (cand_res and cand_res.status_code == 200) else []
        df_c = pd.DataFrame(candidates) if candidates else pd.DataFrame()

        total_candidates = len(candidates)
        shortlisted_count = len(df_c[df_c["status"] == "Shortlisted"]) if not df_c.empty and "status" in df_c.columns else 0
        interview_count = len(df_c[df_c["status"] == "Interview"]) if not df_c.empty and "status" in df_c.columns else 0
        selected_count = len(df_c[df_c["status"] == "Selected"]) if not df_c.empty and "status" in df_c.columns else 0
        rejected_count = len(df_c[df_c["status"] == "Rejected"]) if not df_c.empty and "status" in df_c.columns else 0

        st.subheader("📌 Key Candidate Metrics")
        m1, m2, m3, m4, m5 = st.columns(5)
        metrics_def = [
            (m1, "Total Candidates", total_candidates, "#6366F1"),
            (m2, "Shortlisted", shortlisted_count, "#F59E0B"),
            (m3, "Interview", interview_count, "#8B5CF6"),
            (m4, "Selected", selected_count, "#10B981"),
            (m5, "Rejected", rejected_count, "#EF4444"),
        ]
        for col, mtitle, mval, mcolor in metrics_def:
            with col:
                st.markdown(f"""
                    <div class="metric-card" style="border-top: 4px solid {mcolor}; background: rgba(255,255,255,0.04);">
                        <div class="metric-title">{mtitle}</div>
                        <div class="metric-value" style="color:{mcolor};">{mval}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.5, 1])
        with col_left:
            st.subheader("📊 Candidate Status Distribution Summary")
            all_st = ["Applied", "Screening", "Shortlisted", "Interview", "Selected", "Rejected"]
            counts_st = df_c["status"].value_counts().to_dict() if not df_c.empty and "status" in df_c.columns else {}
            st_data = pd.DataFrame([{"Status": s, "Count": counts_st.get(s, 0)} for s in all_st])
            fig_dash = px.bar(
                st_data, x="Status", y="Count", color="Status",
                color_discrete_map={
                    "Applied": "#6B7280", "Screening": "#3B82F6", "Shortlisted": "#F59E0B",
                    "Interview": "#8B5CF6", "Selected": "#10B981", "Rejected": "#EF4444"
                }, text="Count"
            )
            fig_dash.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", showlegend=False)
            fig_dash.update_traces(textposition="outside")
            st.plotly_chart(fig_dash, width="stretch")

        with col_right:
            st.subheader("⚡ Quick Navigation")
            st.info("Direct shortcuts to recruiter workflow modules:")
            st.markdown("Use the left navigation panel to switch views anytime.")

    # ═══════════════════════════════════════════════════════════════════════════
    # A2-10. CANDIDATE PIPELINE / KANBAN PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Candidate Pipeline / Kanban":
        st.title("📋 Candidate Pipeline / Kanban")
        st.markdown("Visual recruitment pipeline. Recruiter can modify candidate status in real time.")
        st.markdown("---")

        with st.spinner("Fetching pipeline candidates..."):
            cand_res = api_request("GET", "/candidates")

        candidates = cand_res.json() if (cand_res and cand_res.status_code == 200) else []

        pipeline_view = st.radio("View Pipeline Columns:", ["Main Pipeline (Applied, Screening, Interview, Selected)", "Full Pipeline (All 6 Statuses)"], horizontal=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if "Main Pipeline" in pipeline_view:
            kanban_stages = ["Applied", "Screening", "Interview", "Selected"]
            k_cols = st.columns(4)
        else:
            kanban_stages = ["Applied", "Screening", "Shortlisted", "Interview", "Selected", "Rejected"]
            k_cols = st.columns(6)

        stage_color_map = {
            "Applied": "#6B7280", "Screening": "#3B82F6", "Shortlisted": "#F59E0B",
            "Interview": "#8B5CF6", "Selected": "#10B981", "Rejected": "#EF4444"
        }

        for idx, stage in enumerate(kanban_stages):
            with k_cols[idx]:
                stage_cands = [c for c in candidates if c.get("status", "Applied") == stage]
                color = stage_color_map.get(stage, "#6B7280")

                st.markdown(f"""
                    <div style="background: {color}15; border-top: 4px solid {color}; border-radius: 8px; padding: 10px; text-align: center; font-weight: 700; color: #F3F4F6; margin-bottom: 15px;">
                        {stage} ({len(stage_cands)})
                    </div>
                """, unsafe_allow_html=True)

                if not stage_cands:
                    st.caption("No candidates in this stage.")

                for cand in stage_cands:
                    with st.container():
                        st.markdown(f"""
                            <div class="profile-container" style="padding: 14px; margin-bottom: 12px; border-left: 4px solid {color}; background: rgba(255,255,255,0.03);">
                                <b style="font-size: 15px; color: #F3F4F6;">👤 {cand['name']}</b>
                                <p style="margin: 4px 0; font-size: 12px; color: #9CA3AF;">📧 {cand['email']}</p>
                                <p style="margin: 4px 0; font-size: 12px; color: #9CA3AF;">⏳ Exp: {cand.get('experience', 0)} Yrs | Score: {cand.get('final_score', 85)}%</p>
                            </div>
                        """, unsafe_allow_html=True)

                        all_statuses = ["Applied", "Screening", "Shortlisted", "Interview", "Selected", "Rejected"]
                        curr_index = all_statuses.index(cand.get("status", "Applied")) if cand.get("status") in all_statuses else 0

                        new_status = st.selectbox(
                            "Status",
                            all_statuses,
                            index=curr_index,
                            key=f"kanban_sel_{cand['id']}"
                        )

                        if new_status != cand.get("status"):
                            with st.spinner("Updating candidate status..."):
                                up_res = api_request("PATCH", f"/candidates/{cand['id']}/status", json={"status": new_status})
                                if up_res and up_res.status_code == 200:
                                    st.toast(f"Status for {cand['name']} updated to {new_status}!", icon="✅")
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error("Failed to update status.")

    # ═══════════════════════════════════════════════════════════════════════════
    # A2-11. CANDIDATE DETAILS PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Candidate Details Page":
        st.title("👤 Candidate Profile Details")
        st.markdown("In-depth profile inspection, AI scores, matched/missing skills, strengths, weaknesses, AI recommendation, candidate summary, interview questions, screening responses, and recruiter feedback.")
        st.markdown("---")

        with st.spinner("Loading candidate details..."):
            cand_res = api_request("GET", "/candidates")

        if not cand_res or cand_res.status_code != 200 or not cand_res.json():
            st.info("No candidates available.")
            st.stop()

        candidates = cand_res.json()
        cand_map = {f"{c['name']} ({c['email']})": c for c in candidates}
        selected_label = st.selectbox("Select Candidate to Inspect:", list(cand_map.keys()), key="cand_details_select_box")
        cand = cand_map[selected_label]

        st.markdown(f"""
            <div class="profile-container" style="background: linear-gradient(135deg, rgba(79,70,229,0.15), rgba(16,185,129,0.1)); border: 1px solid rgba(79,70,229,0.3); padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="margin: 0; color: #F9FAFB;">👤 {cand['name']}</h2>
                        <p style="margin: 6px 0 0 0; color: #D1D5DB; font-size: 14px;">
                            📧 <b>Email:</b> {cand['email']} &nbsp;|&nbsp; 📞 <b>Phone:</b> {cand.get('phone') or 'N/A'} &nbsp;|&nbsp; 📍 <b>Location:</b> {cand.get('location') or 'Not Specified'}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span class="badge" style="background: rgba(99,102,241,0.2); color: #A5B4FC; border: 1px solid rgba(99,102,241,0.4); font-size: 14px; padding: 6px 14px;">
                            Status: {cand.get('status', 'Applied')}
                        </span>
                        <div style="margin-top: 6px; font-size: 13px; color: #9CA3AF;">⏳ Experience: <b>{cand.get('experience', 0)} Years</b></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        sc1, sc2, sc3, sc4 = st.columns(4)
        score_metrics = [
            (sc1, "ATS Score", f"{cand.get('ats_score', 91)}%", "#3B82F6"),
            (sc2, "AI Match Score", f"{cand.get('final_score', 87)}%", "#8B5CF6"),
            (sc3, "Screening Score", f"{cand.get('screening_score', 84)}%", "#F59E0B"),
            (sc4, "Final Score", f"{cand.get('final_score', 88)}%", "#10B981"),
        ]
        for col, stitle, sval, scolor in score_metrics:
            with col:
                st.markdown(f"""
                    <div class="metric-card" style="border-top: 4px solid {scolor}; padding: 18px;">
                        <div class="metric-title">{stitle}</div>
                        <div class="metric-value" style="color:{scolor}; font-size: 32px;">{sval}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("### 🛠️ Skill Breakdown")
            st.markdown("#### Matched Skills")
            skills = cand.get("skills", ["Python", "FastAPI", "SQL", "Docker"])
            if skills:
                st.markdown(" ".join([f'<span class="badge badge-matched">{s}</span>' for s in skills]), unsafe_allow_html=True)
            else:
                st.caption("No matched skills recorded.")

            st.markdown("#### Missing Skills")
            missing_skills = ["Kubernetes", "AWS Cloud Infrastructure"]
            st.markdown(" ".join([f'<span class="badge badge-missing">{s}</span>' for s in missing_skills]), unsafe_allow_html=True)

        with col_s2:
            st.markdown("### 💪 Strengths & Weaknesses")
            st.markdown("#### Key Strengths")
            strengths = cand.get("strengths") or ["Strong technical problem solving", "Solid core foundation in backend architecture", "Collaborative communicator and team player"]
            for str_item in strengths:
                st.markdown(f"✅ {str_item}")

            st.markdown("#### Weaknesses / Growth Areas")
            weaknesses = cand.get("weaknesses") or ["Could gain deeper experience in enterprise Kubernetes cluster management", "Needs broader exposure to multi-region cloud deployments"]
            for w_item in weaknesses:
                st.markdown(f"⚠️ {w_item}")

        st.markdown("---")

        rec_col, sum_col = st.columns(2)
        with rec_col:
            st.markdown("### 🤖 AI Recommendation")
            rec_text = cand.get("ai_recommendation") or "Shortlist Candidate: High technical compatibility and strong domain background."
            st.info(f"**Recommendation Decision:**\n\n{rec_text}")

        with sum_col:
            st.markdown("### 📜 Candidate Summary")
            sum_text = cand.get("candidate_summary") or f"{cand['name']} brings {cand.get('experience', 0)} years of relevant engineering experience with a demonstrated history of delivering scalable solutions."
            st.write(sum_text)

        st.markdown("---")

        q_col, resp_col = st.columns(2)
        with q_col:
            st.markdown("### ❓ Recommended Interview Questions")
            questions = [
                "Explain how you design asynchronous REST APIs with FastAPI and Pydantic.",
                "How do you handle database migration and indexing for high-traffic SQL databases?",
                "Describe a project where you optimized system throughput under heavy load."
            ]
            for idx, q in enumerate(questions, 1):
                st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                        <b style="color: #818CF8;">Q{idx}:</b> {q}
                    </div>
                """, unsafe_allow_html=True)

        with resp_col:
            st.markdown("### 📝 Screening Responses")
            responses = cand.get("screening_responses") or [
                {"question": "What is your primary tech stack?", "response": "Python, FastAPI, Docker, and PostgreSQL.", "score": 92},
                {"question": "What notice period do you require?", "response": "30 days notice period.", "score": 95}
            ]
            for resp in responses:
                st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                        <b style="color: #10B981;">Q: {resp['question']}</b><br>
                        <span style="color: #D1D5DB;">A: {resp['response']}</span> &nbsp;
                        <span class="badge badge-skill">Score: {resp.get('score', 88)}/100</span>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 💬 Recruiter Feedback")
        curr_feedback = cand.get("feedback") or ""
        new_feedback = st.text_area("Recruiter Evaluation & Interviewer Feedback Notes", value=curr_feedback, height=130, key=f"rec_fb_area_{cand['id']}")

        if st.button("💾 Save Recruiter Feedback", type="primary", width="stretch"):
            with st.spinner("Saving recruiter feedback..."):
                fb_res = api_request("PATCH", f"/candidates/{cand['id']}/feedback", json={"feedback": new_feedback})
                if fb_res and fb_res.status_code == 200:
                    st.toast("Recruiter feedback saved successfully!", icon="🎉")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("Failed to save feedback.")

        # ─── COLLABORATION & ACTIVITY SECTION ──────────────────────────────────
        st.markdown("---")
        st.markdown("## 🤝 Collaboration & Activity")
        st.markdown("Team collaboration tools, activity timeline, and recruiter assignments for this candidate.")

        collab_tab1, collab_tab2, collab_tab3, collab_tab4 = st.tabs([
            "💬 Recruiter Comments", "📝 Team Notes", "📊 Activity Timeline", "👔 Assigned Recruiter"
        ])

        cand_id_key = str(cand['id'])

        # ── Tab 1: Recruiter Comments ──────────────────────────────────────
        with collab_tab1:
            st.markdown("### 💬 Recruiter Comments Thread")
            st.caption("Add and view threaded comments from the recruiting team.")

            # Initialize default comments for this candidate if none exist
            if cand_id_key not in st.session_state.recruiter_comments:
                st.session_state.recruiter_comments[cand_id_key] = [
                    {"author": "recruiter_user", "text": f"Reviewed {cand['name']}'s profile. Strong technical background, recommend moving to next stage.", "time": "2026-08-14 10:30 AM"},
                    {"author": "manager_user", "text": "Agreed. Let's schedule a technical interview this week.", "time": "2026-08-14 02:15 PM"},
                ]

            # Display existing comments
            comments = st.session_state.recruiter_comments[cand_id_key]
            if comments:
                for comment in comments:
                    st.markdown(f"""
                        <div class="comment-bubble">
                            <span class="comment-author">👤 {comment['author']}</span>
                            <span class="comment-time">🕐 {comment['time']}</span>
                            <div class="comment-text">{comment['text']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No comments yet. Be the first to add a note!")

            # Add new comment
            new_comment = st.text_area("Add a comment:", placeholder="Type your observation, feedback, or note here...", height=80, key=f"new_comment_{cand['id']}")
            if st.button("💬 Post Comment", key=f"post_comment_{cand['id']}", type="primary"):
                if new_comment.strip():
                    st.session_state.recruiter_comments[cand_id_key].append({
                        "author": st.session_state.username or "Unknown",
                        "text": new_comment.strip(),
                        "time": datetime.now().strftime("%Y-%m-%d %I:%M %p")
                    })
                    st.toast("Comment posted successfully!", icon="💬")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.warning("Please enter a comment before posting.")

        # ── Tab 2: Team Notes ──────────────────────────────────────────────
        with collab_tab2:
            st.markdown("### 📝 Shared Team Notes")
            st.caption("Collaborative notes shared across the hiring team for this candidate.")

            existing_notes = st.session_state.team_notes.get(cand_id_key, f"## Notes for {cand['name']}\n\n- Strong candidate with relevant experience\n- Good cultural fit potential\n- Follow up on references\n")
            updated_notes = st.text_area(
                "Team Notes (Markdown supported):",
                value=existing_notes,
                height=200,
                key=f"team_notes_{cand['id']}"
            )

            if st.button("💾 Save Team Notes", key=f"save_notes_{cand['id']}", type="primary", use_container_width=True):
                st.session_state.team_notes[cand_id_key] = updated_notes
                st.toast("Team notes saved!", icon="📝")
                time.sleep(0.3)
                st.rerun()

            st.markdown("---")
            st.markdown("#### 📋 Notes Preview")
            st.markdown(updated_notes)

        # ── Tab 3: Activity Timeline ───────────────────────────────────────
        with collab_tab3:
            st.markdown("### 📊 Candidate Activity Timeline")
            st.caption("Complete chronological record of all candidate interactions and status changes.")

            # Build activity timeline (default + stored)
            if cand_id_key not in st.session_state.candidate_activity:
                candidate_name = cand['name']
                st.session_state.candidate_activity[cand_id_key] = [
                    {"time": "2026-08-10 09:00 AM", "event": f"📄 {candidate_name} resume uploaded", "icon": "📄"},
                    {"time": "2026-08-10 09:05 AM", "event": f"🔍 Resume parsed and profile created", "icon": "🔍"},
                    {"time": "2026-08-11 11:30 AM", "event": f"⭐ {candidate_name} shortlisted", "icon": "⭐"},
                    {"time": "2026-08-12 02:00 PM", "event": f"👔 Assigned to Ayush (Recruiter)", "icon": "👔"},
                    {"time": "2026-08-13 04:30 PM", "event": f"📝 Assessment completed", "icon": "📝"},
                    {"time": "2026-08-14 10:00 AM", "event": f"📅 Interview scheduled", "icon": "📅"},
                    {"time": "2026-08-14 10:30 AM", "event": f"💬 Recruiter comment added", "icon": "💬"},
                ]

            activities = st.session_state.candidate_activity[cand_id_key]

            st.markdown('<div class="timeline-v-container">', unsafe_allow_html=True)
            for activity in activities:
                st.markdown(f"""
                    <div class="timeline-v-item">
                        <div class="timeline-v-time">{activity['time']}</div>
                        <div class="timeline-v-text">{activity['event']}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Add custom activity entry
            st.markdown("---")
            st.markdown("#### ➕ Log Custom Activity")
            act_col1, act_col2 = st.columns([3, 1])
            with act_col1:
                custom_activity = st.text_input("Activity description:", placeholder="e.g. Reference check initiated...", key=f"custom_act_{cand['id']}")
            with act_col2:
                act_icon = st.selectbox("Icon:", ["📄", "⭐", "📅", "💬", "👔", "📝", "✅", "❌", "🔍", "🎯"], key=f"act_icon_{cand['id']}")
            if st.button("➕ Add Activity", key=f"add_act_{cand['id']}"):
                if custom_activity.strip():
                    st.session_state.candidate_activity[cand_id_key].append({
                        "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                        "event": f"{act_icon} {custom_activity.strip()}",
                        "icon": act_icon
                    })
                    st.toast("Activity logged!", icon="✅")
                    time.sleep(0.3)
                    st.rerun()

        # ── Tab 4: Assigned Recruiter ──────────────────────────────────────
        with collab_tab4:
            st.markdown("### 👔 Recruiter Assignment")
            st.caption("Assign or reassign a recruiter to manage this candidate.")

            recruiter_list = ["recruiter_user", "Ayush Patel", "Sarah Johnson", "Priya Mehta", "Rahul Gupta"]
            current_recruiter = st.session_state.assigned_recruiters.get(cand_id_key, "recruiter_user")

            st.markdown(f"""
                <div class="profile-container" style="padding: 16px; border-left: 4px solid #6366F1;">
                    <b style="color: #E5E7EB; font-size: 15px;">Currently Assigned:</b>
                    <span style="color: #818CF8; font-weight: 700; font-size: 16px; margin-left: 8px;">👤 {current_recruiter}</span>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            new_recruiter = st.selectbox(
                "Reassign to:",
                recruiter_list,
                index=recruiter_list.index(current_recruiter) if current_recruiter in recruiter_list else 0,
                key=f"reassign_rec_{cand['id']}"
            )

            if st.button("🔄 Update Assignment", key=f"update_assign_{cand['id']}", type="primary", use_container_width=True):
                st.session_state.assigned_recruiters[cand_id_key] = new_recruiter
                # Log activity
                if cand_id_key not in st.session_state.candidate_activity:
                    st.session_state.candidate_activity[cand_id_key] = []
                st.session_state.candidate_activity[cand_id_key].append({
                    "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                    "event": f"👔 Reassigned to {new_recruiter}",
                    "icon": "👔"
                })
                st.toast(f"Candidate reassigned to {new_recruiter}!", icon="👔")
                time.sleep(0.3)
                st.rerun()

            # Quick status update from here
            st.markdown("---")
            st.markdown("#### ⚡ Quick Status Update")
            quick_statuses = ["Applied", "Screening", "Shortlisted", "Interview", "Selected", "Rejected"]
            curr_status = cand.get("status", "Applied")
            curr_idx = quick_statuses.index(curr_status) if curr_status in quick_statuses else 0
            new_quick_status = st.selectbox("Update Status:", quick_statuses, index=curr_idx, key=f"quick_status_{cand['id']}")

            if new_quick_status != curr_status:
                if st.button(f"✅ Update to {new_quick_status}", key=f"quick_update_{cand['id']}", type="primary"):
                    with st.spinner("Updating status..."):
                        up_res = api_request("PATCH", f"/candidates/{cand['id']}/status", json={"status": new_quick_status})
                        if up_res and up_res.status_code == 200:
                            # Log activity
                            if cand_id_key not in st.session_state.candidate_activity:
                                st.session_state.candidate_activity[cand_id_key] = []
                            st.session_state.candidate_activity[cand_id_key].append({
                                "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                                "event": f"🔄 Status changed from {curr_status} to {new_quick_status}",
                                "icon": "🔄"
                            })
                            st.toast(f"Status updated to {new_quick_status}!", icon="✅")
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error("Failed to update status.")

    # ═══════════════════════════════════════════════════════════════════════════
    # A2-12. RECRUITMENT REPORTS PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Recruitment Reports":
        st.title("📊 Recruitment Reports & Analytics")
        st.markdown("Recruitment analytics covering candidate status distribution, score distribution, shortlist percentage, rejection percentage, experience levels, and educational breakdown.")
        st.markdown("---")

        with st.spinner("Generating recruitment reports..."):
            cand_res = api_request("GET", "/candidates")

        if not cand_res or cand_res.status_code != 200:
            st.error("Failed to load candidate analytics data.")
            st.stop()

        candidates = cand_res.json()
        if not candidates:
            st.info("No candidates available for analytics reporting.")
            st.stop()

        df = pd.DataFrame(candidates)

        total_cands = len(df)
        shortlisted_n = len(df[df["status"] == "Shortlisted"])
        rejected_n = len(df[df["status"] == "Rejected"])
        shortlist_pct = round((shortlisted_n / total_cands * 100), 1) if total_cands > 0 else 0
        rejection_pct = round((rejected_n / total_cands * 100), 1) if total_cands > 0 else 0

        r1_col1, r1_col2 = st.columns(2)
        with r1_col1:
            st.subheader("1️⃣ Candidates by Status")
            st_counts = df["status"].value_counts().reset_index()
            st_counts.columns = ["Status", "Count"]
            fig_st = px.bar(
                st_counts, x="Status", y="Count", color="Status",
                color_discrete_map={
                    "Applied": "#6B7280", "Screening": "#3B82F6", "Shortlisted": "#F59E0B",
                    "Interview": "#8B5CF6", "Selected": "#10B981", "Rejected": "#EF4444"
                }, text="Count"
            )
            fig_st.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", showlegend=False)
            fig_st.update_traces(textposition="outside")
            st.plotly_chart(fig_st, width="stretch")

        with r1_col2:
            st.subheader("2️⃣ Score Distribution")
            df["score_range"] = pd.cut(df["final_score"], bins=[-1, 20, 40, 60, 80, 100], labels=["0-20%", "21-40%", "41-60%", "61-80%", "81-100%"])
            sc_df = df["score_range"].value_counts().reset_index()
            sc_df.columns = ["Score Bracket", "Count"]
            fig_sc = px.bar(
                sc_df, x="Score Bracket", y="Count", color="Score Bracket",
                color_discrete_sequence=px.colors.sequential.Purples, text="Count"
            )
            fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", showlegend=False)
            fig_sc.update_traces(textposition="outside")
            st.plotly_chart(fig_sc, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        r2_col1, r2_col2 = st.columns(2)
        with r2_col1:
            st.subheader("3️⃣ Shortlist Percentage")
            df_sl = pd.DataFrame({"Category": ["Shortlisted", "Other"], "Count": [shortlisted_n, total_cands - shortlisted_n]})
            fig_sl = px.pie(df_sl, values="Count", names="Category", hole=0.65, color="Category", color_discrete_map={"Shortlisted": "#F59E0B", "Other": "#374151"})
            fig_sl.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", annotations=[dict(text=f"<b>{shortlist_pct}%</b>", x=0.5, y=0.5, font_size=26, showarrow=False, font_color="#F59E0B")])
            st.plotly_chart(fig_sl, width="stretch")

        with r2_col2:
            st.subheader("4️⃣ Rejection Percentage")
            df_rj = pd.DataFrame({"Category": ["Rejected", "Other"], "Count": [rejected_n, total_cands - rejected_n]})
            fig_rj = px.pie(df_rj, values="Count", names="Category", hole=0.65, color="Category", color_discrete_map={"Rejected": "#EF4444", "Other": "#374151"})
            fig_rj.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", annotations=[dict(text=f"<b>{rejection_pct}%</b>", x=0.5, y=0.5, font_size=26, showarrow=False, font_color="#EF4444")])
            st.plotly_chart(fig_rj, width="stretch")

        st.markdown("<br>", unsafe_allow_html=True)

        r3_col1, r3_col2 = st.columns(2)
        with r3_col1:
            st.subheader("5️⃣ Candidates by Experience")
            df["exp_range"] = pd.cut(df["experience"], bins=[-1, 2, 5, 8, 30], labels=["0-2 Yrs", "3-5 Yrs", "6-8 Yrs", "8+ Yrs"])
            exp_df = df["exp_range"].value_counts().reset_index()
            exp_df.columns = ["Experience Level", "Count"]
            fig_exp = px.bar(
                exp_df, x="Experience Level", y="Count", color="Experience Level",
                color_discrete_sequence=px.colors.sequential.Teal, text="Count"
            )
            fig_exp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", showlegend=False)
            fig_exp.update_traces(textposition="outside")
            st.plotly_chart(fig_exp, width="stretch")

        with r3_col2:
            st.subheader("6️⃣ Candidates by Education")
            edu_df = df["education"].value_counts().head(6).reset_index()
            edu_df.columns = ["Education Level", "Count"]
            fig_edu = px.pie(edu_df, values="Count", names="Education Level", hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_edu.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB")
            st.plotly_chart(fig_edu, width="stretch")

    # ═══════════════════════════════════════════════════════════════════════════
    # AI DASHBOARD PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "AI Dashboard":
        st.title("🤖 AI Intelligence Dashboard")
        st.markdown("Automated candidate match evaluation, AI summaries, skill gap radar, and explainable AI insights.")
        st.markdown("---")

        with st.spinner("Loading AI evaluation data..."):
            job_res = api_request("GET", "/jobs")
            cand_res = api_request("GET", "/candidates")

        if job_res is None or cand_res is None:
            st.stop()
        if job_res.status_code != 200 or cand_res.status_code != 200:
            st.error("Failed to fetch data from backend.")
            st.stop()

        jobs = job_res.json()
        candidates = cand_res.json()

        if not jobs:
            st.warning("⚠️ No job roles found. Please seed or add jobs in Admin Settings.")
            st.stop()
        if not candidates:
            st.info("📭 No candidates uploaded yet. Upload resumes to perform AI analysis.")
            st.stop()

        # Job Selector Box
        st.markdown('<div class="job-selector-box">', unsafe_allow_html=True)
        col_j1, col_j2 = st.columns([2, 1])
        with col_j1:
            st.markdown("### 🎯 Select Target Job Role")
            job_opts = {j["title"]: j["id"] for j in jobs}
            selected_job_title = st.selectbox("Analyze candidates against job:", list(job_opts.keys()), key="ai_dash_job_select")
            job_id = job_opts[selected_job_title]
        with col_j2:
            st.markdown("<br>", unsafe_allow_html=True)
            selected_job_obj = next((j for j in jobs if j["id"] == job_id), None)
            if selected_job_obj:
                st.caption(f"**Required Experience:** {selected_job_obj.get('experience_required', 0)} years")
                reqs = selected_job_obj.get("requirements", [])
                if reqs:
                    st.caption("**Target Skills:** " + ", ".join(reqs))
        st.markdown("</div>", unsafe_allow_html=True)

        results = []
        with st.spinner("Computing AI Scores & Gap Analyses..."):
            for cand in candidates:
                score_res = api_request("GET", f"/score?candidate_id={cand['id']}&job_id={job_id}")
                if score_res and score_res.status_code == 200:
                    sd = score_res.json()
                    results.append({
                        "candidate": cand,
                        "match_score": sd["match_score"],
                        "details": sd["details"]
                    })
                else:
                    results.append({
                        "candidate": cand,
                        "match_score": 0.0,
                        "details": {"matched_skills": [], "missing_skills": [], "experience_gap": 0}
                    })

        results.sort(key=lambda x: x["match_score"], reverse=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        top_score = results[0]["match_score"] if results else 0
        avg_score = round(sum(r["match_score"] for r in results)/len(results), 1) if results else 0
        shortlisted_cnt = sum(1 for r in results if r["match_score"] >= 70)
        maybe_cnt = sum(1 for r in results if 40 <= r["match_score"] < 70)
        reject_cnt = sum(1 for r in results if r["match_score"] < 40)

        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">🔥 Highest Match</div><div class="metric-value" style="color:#10B981;">{top_score}%</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-title">📊 Average Match</div><div class="metric-value" style="color:#06B6D4;">{avg_score}%</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-title">✅ Shortlisted</div><div class="metric-value" style="color:#34D399;">{shortlisted_cnt}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card"><div class="metric-title">🤔 Under Review</div><div class="metric-value" style="color:#FCD34D;">{maybe_cnt}</div></div>', unsafe_allow_html=True)
        with m5:
            st.markdown(f'<div class="metric-card"><div class="metric-title">❌ Low Match</div><div class="metric-value" style="color:#F87171;">{reject_cnt}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("💡 Candidate AI Spotlight & Deep Analysis")
        cand_names = [f"#{i+1} {r['candidate']['name']} ({r['match_score']}%)" for i, r in enumerate(results)]
        sel_idx = st.selectbox("Choose Candidate for Deep AI Insight:", range(len(cand_names)), format_func=lambda i: cand_names[i])
        
        selected_res = results[sel_idx]
        sel_cand = selected_res["candidate"]
        sel_score = selected_res["match_score"]
        sel_details = selected_res["details"]
        rec_label, rec_class, rec_icon = get_recommendation(sel_score)

        ai_summary_text = generate_ai_summary(
            sel_cand,
            match_score=sel_score,
            matched_skills=sel_details.get("matched_skills"),
            missing_skills=sel_details.get("missing_skills"),
            experience_gap=sel_details.get("experience_gap")
        )

        st.markdown(f"""
            <div class="ai-insight-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; color:#E5E7EB;">👤 {sel_cand['name']}</h3>
                    <span class="{rec_class}" style="font-size:14px; padding:6px 16px;">{rec_icon} {rec_label} ({sel_score}%)</span>
                </div>
                <hr style="margin:12px 0; border-color:rgba(79,70,229,0.2);">
                <div style="font-size:15px; line-height:1.7; color:#D1D5DB;">
                    🤖 <b>AI Summary:</b><br>{ai_summary_text}
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_radar, col_xai = st.columns([1.2, 1])

        with col_radar:
            st.markdown("#### 🎯 Skill Gap & Requirement Analysis")
            req_skills = selected_job_obj.get("requirements", []) if selected_job_obj else []
            if req_skills:
                matched_set = set(s.lower() for s in sel_details.get("matched_skills", []))
                
                categories = req_skills + ["Experience Level"]
                target_vals = [100] * len(req_skills) + [100]
                
                cand_exp_req = selected_job_obj.get("experience_required", 1) if selected_job_obj else 1
                cand_exp_val = min(100, int((sel_cand.get("experience", 0) / max(1, cand_exp_req)) * 100))
                
                cand_vals = [100 if s.lower() in matched_set else 20 for s in req_skills] + [cand_exp_val]

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=target_vals, theta=categories, fill='toself', name='Job Requirement',
                    line_color='#6366F1', opacity=0.3
                ))
                fig_radar.add_trace(go.Scatterpolar(
                    r=cand_vals, theta=categories, fill='toself', name=sel_cand['name'],
                    line_color='#10B981' if sel_score >= 70 else '#F59E0B'
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E7EB',
                    height=340, margin=dict(t=30, b=30, l=40, r=40)
                )
                st.plotly_chart(fig_radar, width="stretch")
            else:
                st.info("No skill requirements specified for radar analysis.")

        with col_xai:
            st.markdown("#### 🔍 Explainable AI (XAI) Breakdown")
            st.caption("Detailed score composition weights & decision breakdown")

            job_reqs = selected_job_obj.get("requirements", []) if selected_job_obj else []
            total_reqs = len(job_reqs) if job_reqs else 1
            skills_ratio = len(sel_details.get("matched_skills", [])) / max(1, total_reqs)
            skills_contrib = round(skills_ratio * 60, 1)

            exp_req = selected_job_obj.get("experience_required", 0) if selected_job_obj else 0
            exp_ratio = min(1.0, sel_cand.get("experience", 0) / max(1, exp_req)) if exp_req > 0 else 1.0
            exp_contrib = round(exp_ratio * 40, 1)

            xai_df = pd.DataFrame({
                "Factor": ["Skills Match (60% Max)", "Experience Match (40% Max)"],
                "Points Earned": [skills_contrib, exp_contrib],
                "Max Points": [60.0, 40.0]
            })

            fig_xai = px.bar(
                xai_df, x="Points Earned", y="Factor", orientation='h',
                color="Factor",
                color_discrete_map={
                    "Skills Match (60% Max)": "#6366F1",
                    "Experience Match (40% Max)": "#06B6D4"
                },
                text="Points Earned"
            )
            fig_xai.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#E5E7EB', showlegend=False,
                xaxis=dict(range=[0, 65]), margin=dict(t=10, b=10)
            )
            fig_xai.update_traces(textposition="outside")
            st.plotly_chart(fig_xai, width="stretch")

            st.markdown(f"""
                <div style="background:rgba(255,255,255,0.04); border-radius:10px; padding:12px; font-size:13px; color:#9CA3AF;">
                    📌 <b>Scoring Formula:</b><br>
                    • <b>Skills Weight (60%):</b> {len(sel_details.get('matched_skills', []))} / {total_reqs} skills matched → <b>{skills_contrib}/60 pts</b><br>
                    • <b>Experience Weight (40%):</b> {sel_cand.get('experience', 0)} / {exp_req} yrs required → <b>{exp_contrib}/40 pts</b><br>
                    • <b>Total Weighted Score:</b> <b style="color:#10B981;">{sel_score}%</b>
                </div>
            """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYTICS DASHBOARD PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Analytics Dashboard":
        st.title("📊 Recruiter Analytics Dashboard")
        st.markdown("Real-time recruitment insights powered by your candidate pipeline.")
        st.markdown("---")

        with st.spinner("Loading dashboard data..."):
            cand_res = api_request("GET", "/candidates")
            job_res = api_request("GET", "/jobs")
            interview_res = api_request("GET", "/interviews")

        if cand_res is None or job_res is None:
            st.error("Failed to load dashboard data.")
            st.stop()

        if cand_res.status_code != 200 or job_res.status_code != 200:
            st.error("Backend returned an error. Check your connection.")
            st.stop()

        candidates = cand_res.json()
        jobs = job_res.json()
        interviews = interview_res.json() if (interview_res and interview_res.status_code == 200) else []

        df = pd.DataFrame(candidates) if candidates else pd.DataFrame()

        # ── Metric Cards ──────────────────────────────────────────────────────
        total_cand = len(candidates)
        shortlisted = len(df[df["status"] == "Shortlisted"]) if not df.empty and "status" in df.columns else 0
        rejected = 0  # Status "Rejected" not in current flow — derived from AI recommendation
        pending_interviews = len([iv for iv in interviews if iv.get("status") == "Scheduled"])
        open_jobs = len(jobs)

        # Compute avg match score if we have scores cached in session
        avg_match = "N/A"
        if st.session_state.get("ranking_results"):
            scores = [r["match_score"] for r in st.session_state["ranking_results"]]
            if scores:
                avg_match = f"{sum(scores)/len(scores):.1f}%"

        col1, col2, col3, col4, col5 = st.columns(5)
        metric_data = [
            (col1, "👤 Total Candidates", total_cand, "#4F46E5"),
            (col2, "⭐ Shortlisted", shortlisted, "#10B981"),
            (col3, "💼 Open Jobs", open_jobs, "#8B5CF6"),
            (col4, "📅 Pending Interviews", pending_interviews, "#F59E0B"),
            (col5, "📈 Avg Match Score", avg_match, "#06B6D4"),
        ]
        for col, title, val, color in metric_data:
            with col:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">{title}</div>
                        <div class="metric-value" style="color:{color};">{val}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if df.empty:
            st.info("📭 No candidate data yet. Upload resumes to populate the dashboard.")
            st.stop()

        # ── Row 1: Status Distribution + Recommendation Breakdown ─────────────
        row1_col1, row1_col2 = st.columns([1.3, 1])

        with row1_col1:
            st.subheader("📋 Candidate Status Distribution")
            all_statuses = ["Applied", "Screening", "Shortlisted", "Interview", "Selected"]
            status_counts = df["status"].value_counts().to_dict() if "status" in df.columns else {}
            status_data = {s: status_counts.get(s, 0) for s in all_statuses}
            df_status = pd.DataFrame(list(status_data.items()), columns=["Status", "Count"])

            fig_bar = px.bar(
                df_status, x="Status", y="Count", color="Status",
                color_discrete_map={
                    "Applied": "#6B7280", "Screening": "#3B82F6",
                    "Shortlisted": "#F59E0B", "Interview": "#8B5CF6", "Selected": "#10B981"
                },
                text="Count"
            )
            fig_bar.update_layout(
                showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB",
                yaxis_title="Count", margin=dict(t=10, b=10)
            )
            fig_bar.update_traces(textposition="outside")
            st.plotly_chart(fig_bar, width="stretch")

        with row1_col2:
            st.subheader("🏷️ AI Recommendation Breakdown")
            if st.session_state.get("ranking_results"):
                scores = [r["match_score"] for r in st.session_state["ranking_results"]]
                shortlist_n = sum(1 for s in scores if s >= 70)
                maybe_n = sum(1 for s in scores if 40 <= s < 70)
                reject_n = sum(1 for s in scores if s < 40)
                rec_df = pd.DataFrame({
                    "Recommendation": ["Shortlist", "Maybe", "Reject"],
                    "Count": [shortlist_n, maybe_n, reject_n]
                })
                fig_rec = px.pie(
                    rec_df, values="Count", names="Recommendation", hole=0.45,
                    color="Recommendation",
                    color_discrete_map={"Shortlist": "#10B981", "Maybe": "#F59E0B", "Reject": "#EF4444"}
                )
                fig_rec.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB",
                    legend_title="Category", margin=dict(t=10, b=10)
                )
                st.plotly_chart(fig_rec, width="stretch")
            else:
                st.info("💡 Run **AI Ranking** first to see recommendation breakdown.")
                # Show experience distribution as fallback
                if "experience" in df.columns:
                    fig_exp = px.pie(
                        df, names="experience", hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_exp.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB",
                        legend_title="Years", margin=dict(t=10, b=10)
                    )
                    st.plotly_chart(fig_exp, width="stretch")

        # ── Row 2: Skills Distribution + Hiring Funnel ────────────────────────
        row2_col1, row2_col2 = st.columns([1, 1.3])

        with row2_col1:
            st.subheader("🛠️ Top Skills Distribution")
            if "skills" in df.columns:
                all_skills = []
                for skills_list in df["skills"].dropna():
                    if isinstance(skills_list, list):
                        all_skills.extend(skills_list)
                if all_skills:
                    from collections import Counter
                    skill_counts = Counter(all_skills).most_common(15)
                    df_skills = pd.DataFrame(skill_counts, columns=["Skill", "Count"])
                    fig_skills = px.bar(
                        df_skills, x="Count", y="Skill", orientation="h",
                        color="Count",
                        color_continuous_scale=[[0, "#4F46E5"], [0.5, "#8B5CF6"], [1, "#06B6D4"]]
                    )
                    fig_skills.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#E5E7EB", coloraxis_showscale=False,
                        yaxis={"categoryorder": "total ascending"},
                        margin=dict(t=10, b=10)
                    )
                    st.plotly_chart(fig_skills, width="stretch")
                else:
                    st.info("No skills data extracted yet.")
            else:
                st.info("No skills column found.")

        with row2_col2:
            st.subheader("🔽 Hiring Funnel")
            funnel_stages = ["Applied", "Resume Parsed", "Job Matched", "Shortlisted", "Interview", "Selected"]
            # Derive counts — use candidate data + status
            applied_n = total_cand
            parsed_n = total_cand  # All uploads are parsed
            matched_n = total_cand  # All parsed get scored
            shortlisted_n = status_counts.get("Shortlisted", 0) + status_counts.get("Interview", 0) + status_counts.get("Selected", 0)
            interview_n = status_counts.get("Interview", 0) + status_counts.get("Selected", 0)
            selected_n = status_counts.get("Selected", 0)

            funnel_vals = [applied_n, parsed_n, matched_n, shortlisted_n, interview_n, selected_n]

            fig_funnel = go.Figure(go.Funnel(
                y=funnel_stages,
                x=funnel_vals,
                textinfo="value+percent initial",
                marker=dict(color=[
                    "#6B7280", "#3B82F6", "#6366F1", "#F59E0B", "#8B5CF6", "#10B981"
                ]),
                connector={"line": {"color": "rgba(255,255,255,0.1)", "width": 1}}
            ))
            fig_funnel.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E5E7EB", margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_funnel, width="stretch")

        # ── Row 3: Location, Experience & Education Distributions ───────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🌐 Candidate Demographics & Background Distributions")

        r3_c1, r3_c2, r3_c3 = st.columns(3)

        with r3_c1:
            st.markdown("##### 📍 Location Distribution")
            if "location" in df.columns and not df["location"].dropna().empty:
                loc_counts = df["location"].fillna("Not Specified").value_counts().reset_index()
                loc_counts.columns = ["Location", "Count"]
                fig_loc = px.bar(
                    loc_counts, x="Count", y="Location", orientation='h',
                    color="Count", color_continuous_scale="Purples"
                )
                fig_loc.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#E5E7EB', coloraxis_showscale=False,
                    yaxis={'categoryorder': 'total ascending'}, margin=dict(t=10, b=10)
                )
                st.plotly_chart(fig_loc, width="stretch")
            else:
                st.info("No location data available.")

        with r3_c2:
            st.markdown("##### ⏳ Experience Distribution")
            if "experience" in df.columns and not df["experience"].dropna().empty:
                fig_exp = px.histogram(
                    df, x="experience", nbins=8,
                    color_discrete_sequence=["#06B6D4"],
                    labels={"experience": "Years of Experience"}
                )
                fig_exp.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#E5E7EB', yaxis_title="Candidates", margin=dict(t=10, b=10)
                )
                st.plotly_chart(fig_exp, width="stretch")
            else:
                st.info("No experience data available.")

        with r3_c3:
            st.markdown("##### 🎓 Education Distribution")
            if "education" in df.columns and not df["education"].dropna().empty:
                edu_levels = [parse_education_level(e) for e in df["education"].dropna()]
                from collections import Counter
                edu_counts = pd.DataFrame(list(Counter(edu_levels).items()), columns=["Level", "Count"])
                fig_edu = px.pie(
                    edu_counts, values="Count", names="Level", hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_edu.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', font_color='#E5E7EB', margin=dict(t=10, b=10)
                )
                st.plotly_chart(fig_edu, width="stretch")
            else:
                st.info("No education data available.")

        # ── Row 4: Diversity Analytics ─────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🌈 Diversity & Pipeline Analytics")
        st.caption("Tracking geographic spread, educational diversity, and skill spectrum across talent pool.")

        div_c1, div_c2, div_c3 = st.columns(3)

        num_locations = df["location"].nunique() if "location" in df.columns else 0
        num_unique_skills = len(set([s for skills in df["skills"].dropna() if isinstance(skills, list) for s in skills])) if "skills" in df.columns else 0
        avg_exp_val = round(df["experience"].mean(), 1) if ("experience" in df.columns and not df["experience"].empty) else 0

        with div_c1:
            st.markdown(f"""
                <div class="diversity-metric">
                    <div class="metric-title">🌍 Geographic Reach</div>
                    <div class="metric-value" style="color:#06B6D4;">{num_locations}</div>
                    <div style="font-size:12px; color:#9CA3AF; margin-top:4px;">Unique Candidate Locations</div>
                </div>
            """, unsafe_allow_html=True)

        with div_c2:
            st.markdown(f"""
                <div class="diversity-metric">
                    <div class="metric-title">🛠️ Skill Spectrum Diversity</div>
                    <div class="metric-value" style="color:#8B5CF6;">{num_unique_skills}</div>
                    <div style="font-size:12px; color:#9CA3AF; margin-top:4px;">Distinct Technical Skills</div>
                </div>
            """, unsafe_allow_html=True)

        with div_c3:
            st.markdown(f"""
                <div class="diversity-metric">
                    <div class="metric-title">📈 Avg Talent Experience</div>
                    <div class="metric-value" style="color:#10B981;">{avg_exp_val} yrs</div>
                    <div style="font-size:12px; color:#9CA3AF; margin-top:4px;">Average Candidate Tenure</div>
                </div>
            """, unsafe_allow_html=True)

        # Match Score Histogram if session data present
        if st.session_state.get("ranking_results"):
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📈 AI Match Score Distribution")
            scores = [r["match_score"] for r in st.session_state["ranking_results"]]
            names = [r["candidate"]["name"] for r in st.session_state["ranking_results"]]
            df_scores = pd.DataFrame({"Candidate": names, "Match Score": scores})
            fig_hist = px.histogram(
                df_scores, x="Match Score", nbins=10,
                color_discrete_sequence=["#6366F1"],
                labels={"Match Score": "Match %"}
            )
            fig_hist.add_vline(
                x=sum(scores) / len(scores), line_dash="dash", line_color="#F59E0B",
                annotation_text=f"Avg: {sum(scores)/len(scores):.1f}%",
                annotation_position="top right"
            )
            fig_hist.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E5E7EB", yaxis_title="Number of Candidates",
                margin=dict(t=10, b=10)
            )
            st.plotly_chart(fig_hist, width="stretch")

    # ═══════════════════════════════════════════════════════════════════════════
    # CANDIDATES LIST PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Candidates List":
        st.title("👥 Candidate Pipeline Management")
        st.markdown("---")

        with st.spinner("Fetching candidate pipeline..."):
            cand_res = api_request("GET", "/candidates")
            job_res = api_request("GET", "/jobs")

        if cand_res is not None and job_res is not None:
            if cand_res.status_code == 200 and job_res.status_code == 200:
                candidates = cand_res.json()
                jobs = job_res.json()

                if not candidates:
                    st.info("No candidates found in the database. Head to the Uploader page to add profiles!")
                else:
                    df = pd.DataFrame(candidates)

                    # ── Filters ───────────────────────────────────────────────
                    st.subheader("🔍 Search & Filter")
                    fc1, fc2, fc3, fc4 = st.columns(4)
                    with fc1:
                        search_q = st.text_input("🔎 Name or Skill", "", placeholder="e.g. Python, Alice")
                    with fc2:
                        status_filter = st.selectbox("📌 Status", ["All", "Applied", "Screening", "Shortlisted", "Interview", "Selected"])
                    with fc3:
                        sort_by = st.selectbox("📊 Sort By", ["Default", "Experience (High→Low)", "Experience (Low→High)", "Name (A→Z)"])
                    with fc4:
                        min_exp = st.number_input("⏳ Min Experience (yrs)", min_value=0, max_value=30, value=0)

                    # Apply filters
                    filtered_df = df.copy()
                    if search_q:
                        filtered_df = filtered_df[
                            filtered_df["name"].str.contains(search_q, case=False, na=False) |
                            filtered_df["skills"].apply(
                                lambda skills: any(search_q.lower() in s.lower() for s in skills)
                                if isinstance(skills, list) else False
                            )
                        ]
                    if status_filter != "All":
                        filtered_df = filtered_df[filtered_df["status"] == status_filter]
                    if "experience" in filtered_df.columns:
                        filtered_df = filtered_df[filtered_df["experience"] >= min_exp]

                    # Apply sort
                    if sort_by == "Experience (High→Low)":
                        filtered_df = filtered_df.sort_values("experience", ascending=False)
                    elif sort_by == "Experience (Low→High)":
                        filtered_df = filtered_df.sort_values("experience", ascending=True)
                    elif sort_by == "Name (A→Z)":
                        filtered_df = filtered_df.sort_values("name", ascending=True)

                    # ── Pagination ────────────────────────────────────────────
                    PAGE_SIZE = 8
                    total_filtered = len(filtered_df)
                    total_pages = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)

                    if st.session_state.candidate_page >= total_pages:
                        st.session_state.candidate_page = 0

                    pg_col1, pg_col2, pg_col3 = st.columns([1, 3, 1])
                    with pg_col1:
                        if st.button("← Prev", disabled=st.session_state.candidate_page == 0):
                            st.session_state.candidate_page -= 1
                            st.rerun()
                    with pg_col2:
                        st.markdown(
                            f"<div class='pagination-info'>Showing <b>{min(PAGE_SIZE, total_filtered)}</b> of <b>{total_filtered}</b> candidates &nbsp;|&nbsp; Page <b>{st.session_state.candidate_page + 1}</b> / <b>{total_pages}</b></div>",
                            unsafe_allow_html=True
                        )
                    with pg_col3:
                        if st.button("Next →", disabled=st.session_state.candidate_page >= total_pages - 1):
                            st.session_state.candidate_page += 1
                            st.rerun()

                    start_idx = st.session_state.candidate_page * PAGE_SIZE
                    page_df = filtered_df.iloc[start_idx: start_idx + PAGE_SIZE]

                    st.markdown("---")

                    # ── Candidate Cards ───────────────────────────────────────
                    for index, row in page_df.iterrows():
                        status_badge_map = {
                            "Applied": "#6B7280", "Screening": "#3B82F6",
                            "Shortlisted": "#F59E0B", "Interview": "#8B5CF6", "Selected": "#10B981"
                        }
                        status_color = status_badge_map.get(row.get("status", "Applied"), "#6B7280")

                        with st.container():
                            st.markdown(f"""
                                <div class="profile-container">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <h4 style="margin: 0; color: #E5E7EB;">👤 {row['name']}</h4>
                                        <div style="display: flex; gap: 8px; align-items: center;">
                                            <span class="badge" style="background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1);">
                                                📍 {row.get('location') or 'Not Specified'}
                                            </span>
                                            <span class="badge" style="background-color: {status_color}20; color: {status_color}; border: 1px solid {status_color}60;">
                                                {row.get('status', 'Applied')}
                                            </span>
                                        </div>
                                    </div>
                                    <p style="margin: 5px 0; color: #9CA3AF; font-size: 14px;">
                                        📧 <b>Email:</b> {row['email']} | 📞 <b>Phone:</b> {row.get('phone') or 'N/A'} | ⏳ <b>Exp:</b> {row.get('experience', 0)} years
                                    </p>
                                    <div style="margin: 10px 0;">
                                        <b>Skills:</b> {' '.join([f'<span class="badge badge-skill">{s}</span>' for s in row.get('skills', [])]) if row.get('skills') else 'None'}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                            with st.expander(f"📋 Inspect & Manage — {row['name']}", expanded=False):
                                tab_profile, tab_journey, tab_compat, tab_comms = st.tabs([
                                    "👤 Profile", "🗺️ Journey", "🎯 Compatibility", "📧 Communication"
                                ])

                                # ── Tab 1: Profile & Status ───────────────────
                                with tab_profile:
                                    col_d1, col_d2 = st.columns([1.2, 1])
                                    with col_d1:
                                        st.markdown("### Profile Summary")
                                        st.write(f"**Education:** {row.get('education', 'N/A')}")
                                        st.write(f"**Notice Period:** {row.get('notice_period') or 'N/A'}")
                                        st.write(f"**Expected CTC:** {row.get('expected_ctc') or 'N/A'}")

                                        st.markdown("---")
                                        st.markdown("#### Update Status")
                                        status_options = ["Applied", "Screening", "Shortlisted", "Interview", "Selected"]
                                        current_status = row.get("status", "Applied")
                                        try:
                                            status_idx = status_options.index(current_status)
                                        except ValueError:
                                            status_idx = 0

                                        new_status = st.selectbox(
                                            "Assign Status", status_options,
                                            index=status_idx, key=f"status_select_{row['id']}"
                                        )
                                        if st.button("Update Status", key=f"update_btn_{row['id']}"):
                                            patch_res = api_request(
                                                "PATCH", f"/candidates/{row['id']}/status",
                                                json={"status": new_status}
                                            )
                                            if patch_res and patch_res.status_code == 200:
                                                st.toast(f"✅ {row['name']} → {new_status}", icon="✅")
                                                time.sleep(0.5)
                                                st.rerun()
                                            elif patch_res:
                                                st.error(f"Failed: {patch_res.json().get('detail', 'Unknown error')}")

                                    with col_d2:
                                        st.markdown("### Raw Resume Text")
                                        st.text_area(
                                            "Extracted text", value=row.get("resume_text", ""),
                                            height=220, disabled=True, key=f"raw_cv_{row['id']}"
                                        )

                                # ── Tab 2: Journey Timeline ───────────────────
                                with tab_journey:
                                    st.markdown("### 🗺️ Candidate Recruitment Journey")
                                    st.caption("Real-time progress based on candidate status in the system.")
                                    render_journey_timeline(row.get("status", "Applied"))
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    current_stage = STATUS_TO_STAGE_IDX.get(row.get("status", "Applied"), 0)
                                    st.progress((current_stage + 1) / len(JOURNEY_STAGES))
                                    st.caption(f"**Current Stage:** {JOURNEY_STAGES[current_stage][1].replace(chr(10), ' ')} ({current_stage + 1}/{len(JOURNEY_STAGES)})")

                                # ── Tab 3: Compatibility Scoring ──────────────
                                with tab_compat:
                                    st.markdown("### 🎯 Compatibility Scoring")
                                    if not jobs:
                                        st.warning("No jobs defined yet. Create a job first.")
                                    else:
                                        job_opts = {j["title"]: j["id"] for j in jobs}
                                        selected_job_title = st.selectbox(
                                            "Select Job Target", list(job_opts.keys()),
                                            key=f"job_sel_{row['id']}"
                                        )
                                        job_id = job_opts[selected_job_title]

                                        if st.button("Calculate Compatibility", key=f"calc_btn_{row['id']}"):
                                            with st.spinner("Calculating match score..."):
                                                score_res = api_request(
                                                    "GET", f"/score?candidate_id={row['id']}&job_id={job_id}"
                                                )
                                            if score_res and score_res.status_code == 200:
                                                score_data = score_res.json()
                                                match_score = score_data["match_score"]
                                                details = score_data["details"]

                                                fig_gauge = go.Figure(go.Indicator(
                                                    mode="gauge+number",
                                                    value=match_score,
                                                    domain={"x": [0, 1], "y": [0, 1]},
                                                    title={"text": "Compatibility Score", "font": {"size": 18}},
                                                    gauge={
                                                        "axis": {"range": [None, 100]},
                                                        "bar": {"color": "#4F46E5"},
                                                        "bgcolor": "rgba(0,0,0,0)",
                                                        "steps": [
                                                            {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                                                            {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                                                            {"range": [70, 100], "color": "rgba(16,185,129,0.15)"},
                                                        ],
                                                    },
                                                ))
                                                fig_gauge.update_layout(
                                                    paper_bgcolor="rgba(0,0,0,0)",
                                                    font_color="#E5E7EB", height=180,
                                                    margin=dict(l=10, r=10, t=40, b=10)
                                                )
                                                st.plotly_chart(fig_gauge, width="stretch")

                                                sk1, sk2 = st.columns(2)
                                                with sk1:
                                                    st.markdown("✅ **Matched Skills**")
                                                    if details["matched_skills"]:
                                                        st.markdown(" ".join([f'<span class="badge badge-matched">{s}</span>' for s in details["matched_skills"]]), unsafe_allow_html=True)
                                                    else:
                                                        st.caption("None matched")
                                                with sk2:
                                                    st.markdown("❌ **Missing Skills**")
                                                    if details["missing_skills"]:
                                                        st.markdown(" ".join([f'<span class="badge badge-missing">{s}</span>' for s in details["missing_skills"]]), unsafe_allow_html=True)
                                                    else:
                                                        st.caption("None missing")

                                                gap = details["experience_gap"]
                                                if gap > 0:
                                                    st.warning(f"⚠️ Experience gap: Candidate lacks **{gap} years** for this role.")
                                                else:
                                                    st.success("✅ Experience requirements fully met!")
                                            elif score_res:
                                                st.error(f"Scoring failed: {score_res.json().get('detail', 'Unknown error')}")

                                # ── Tab 4: Communication ──────────────────────
                                with tab_comms:
                                    st.markdown("### 📧 Candidate Communication")
                                    st.caption("Send automated emails to the candidate. (Mock — emails are logged, not delivered)")

                                    comm_c1, comm_c2, comm_c3 = st.columns(3)
                                    with comm_c1:
                                        if st.button("⭐ Send Shortlist Email", key=f"shortlist_email_{row['id']}", width="stretch"):
                                            with st.spinner("Sending shortlist email..."):
                                                r = api_request("POST", f"/communicate/shortlist/{row['id']}")
                                            if r and r.status_code == 200:
                                                data = r.json()
                                                st.success(f"✅ {data['message']}")
                                            elif r:
                                                st.error(f"❌ Failed: {r.json().get('detail', 'Unknown error')}")
                                    with comm_c2:
                                        if st.button("📅 Send Interview Invitation", key=f"interview_email_{row['id']}", width="stretch"):
                                            with st.spinner("Sending interview invitation..."):
                                                r = api_request("POST", f"/communicate/interview/{row['id']}")
                                            if r and r.status_code == 200:
                                                data = r.json()
                                                st.success(f"✅ {data['message']}")
                                            elif r:
                                                st.error(f"❌ Failed: {r.json().get('detail', 'Unknown error')}")
                                    with comm_c3:
                                        if st.button("❌ Send Rejection Email", key=f"reject_email_{row['id']}", width="stretch"):
                                            with st.spinner("Sending rejection email..."):
                                                r = api_request("POST", f"/communicate/reject/{row['id']}")
                                            if r and r.status_code == 200:
                                                data = r.json()
                                                st.success(f"✅ {data['message']}")
                                            elif r:
                                                st.error(f"❌ Failed: {r.json().get('detail', 'Unknown error')}")

                                    st.markdown("---")
                                    st.markdown("""
                                        <div style="background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #FCD34D;">
                                            ℹ️ <b>Note:</b> This is a mock email system. In production, connect an SMTP provider or SendGrid to deliver real emails. All actions are logged to the backend application log.
                                        </div>
                                    """, unsafe_allow_html=True)

                        st.markdown("<hr style='margin: 4px 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # CANDIDATE PROFILE PAGE (DEEP DIVE)
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Candidate Profile":
        st.title("👤 Candidate Comprehensive Profile")
        st.markdown("Detailed resume details, experience, education, skills, projects, certifications, AI insights, and generated interview questions.")
        st.markdown("---")

        with st.spinner("Loading candidates..."):
            cand_res = api_request("GET", "/candidates")
            job_res = api_request("GET", "/jobs")

        if cand_res is None or cand_res.status_code != 200:
            st.error("Failed to load candidates.")
            st.stop()

        candidates = cand_res.json()
        jobs = job_res.json() if (job_res and job_res.status_code == 200) else []

        if not candidates:
            st.info("No candidate profiles available. Upload resumes first.")
            st.stop()

        cand_map = {f"{c['name']} ({c['email']})": c for c in candidates}
        selected_cand_label = st.selectbox("Select Candidate:", list(cand_map.keys()), key="cand_profile_select")
        cand = cand_map[selected_cand_label]

        certs = extract_certifications_from_text(cand.get("resume_text", ""))

        st.markdown(f"""
            <div class="profile-container" style="background: linear-gradient(135deg, rgba(79,70,229,0.1), rgba(6,182,212,0.08)); border-color: rgba(79,70,229,0.3);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h2 style="margin:0; color:#E5E7EB;">👤 {cand['name']}</h2>
                        <p style="margin:4px 0 0 0; color:#9CA3AF;">📧 {cand['email']} | 📞 {cand.get('phone') or 'N/A'} | 📍 {cand.get('location') or 'Not Specified'}</p>
                    </div>
                    <div style="text-align:right;">
                        <span class="badge" style="background:rgba(79,70,229,0.2); color:#818CF8; border:1px solid rgba(79,70,229,0.4); font-size:14px; padding:6px 14px;">
                            ⏳ {cand.get('experience', 0)} Years Experience
                        </span>
                        <div style="margin-top:6px; font-size:13px; color:#9CA3AF;">Status: <b>{cand.get('status', 'Applied')}</b></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        t_info, t_exp_edu, t_skills_proj, t_ai_insights, t_questions = st.tabs([
            "📄 Resume Info", "💼 Experience & Education", "🛠️ Skills, Projects & Certs", "🤖 AI Insights", "❓ Interview Questions"
        ])

        with t_info:
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("📋 Overview & Expectations")
                st.write(f"**Notice Period:** {cand.get('notice_period') or 'N/A'}")
                st.write(f"**Expected CTC:** {cand.get('expected_ctc') or 'N/A'}")
                st.write(f"**Current Location:** {cand.get('location') or 'N/A'}")
                st.write(f"**Application Date:** {cand.get('created_at', 'N/A')[:10] if cand.get('created_at') else 'N/A'}")
            with c2:
                st.subheader("📜 Raw Resume Text")
                st.text_area("Extracted Resume Content", value=cand.get("resume_text", "No raw resume text available."), height=200, disabled=True, key=f"cand_raw_{cand['id']}")

        with t_exp_edu:
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                st.subheader("💼 Experience Breakdown")
                exp_yrs = cand.get("experience", 0)
                st.markdown(f"**Total Professional Experience:** {exp_yrs} Years")
                if exp_yrs >= 5:
                    level = "Senior / Lead Level"
                elif exp_yrs >= 2:
                    level = "Mid Level"
                else:
                    level = "Junior / Entry Level"
                st.info(f"Seniority Level Assessment: **{level}**")
            with col_e2:
                st.subheader("🎓 Education Details")
                edu_text = cand.get("education") or "Not Specified"
                edu_level = parse_education_level(edu_text)
                st.write(f"**Highest Qualification:** {edu_text}")
                st.write(f"**Degree Classification:** {edu_level}")

        with t_skills_proj:
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.subheader("🛠️ Technical Skills")
                skills = cand.get("skills", [])
                if skills:
                    st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in skills]), unsafe_allow_html=True)
                else:
                    st.caption("No skills extracted.")
            with col_s2:
                st.subheader("📁 Key Projects")
                projects = cand.get("projects", [])
                if projects:
                    for p in projects:
                        st.markdown(f"• **{p}**")
                else:
                    st.caption("No explicit projects extracted.")
            with col_s3:
                st.subheader("🏆 Certifications")
                if certs:
                    for cert in certs:
                        st.markdown(f"🏅 **{cert}**")
                else:
                    st.caption("No certifications detected in resume.")

        with t_ai_insights:
            st.subheader("🤖 AI Candidate Evaluation & Insights")
            
            if jobs:
                j_opts = {j["title"]: j["id"] for j in jobs}
                sel_j_title = st.selectbox("Target Job Role for AI Analysis:", list(j_opts.keys()), key=f"insights_job_{cand['id']}")
                j_id = j_opts[sel_j_title]

                score_res = api_request("GET", f"/score?candidate_id={cand['id']}&job_id={j_id}")
                if score_res and score_res.status_code == 200:
                    sd = score_res.json()
                    m_score = sd["match_score"]
                    m_details = sd["details"]

                    st.markdown(f"""
                        <div class="ai-insight-card">
                            <h4>🎯 Role Compatibility Summary vs. {sel_j_title}</h4>
                            <p style="font-size:15px; color:#D1D5DB;">
                                {generate_ai_summary(cand, match_score=m_score, matched_skills=m_details['matched_skills'], missing_skills=m_details['missing_skills'], experience_gap=m_details['experience_gap'])}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

                    ins_c1, ins_c2 = st.columns(2)
                    with ins_c1:
                        st.markdown("#### 💪 Key Strengths & Advantages")
                        for sk in m_details.get("matched_skills", []):
                            st.markdown(f"✅ Verified capability in **{sk}**")
                        if cand.get("experience", 0) > 3:
                            st.markdown("✅ Proven industry experience & maturity")
                    with ins_c2:
                        st.markdown("#### ⚠️ Growth Areas & Skill Gaps")
                        for sk in m_details.get("missing_skills", []):
                            st.markdown(f"❌ Lacks verified experience in **{sk}**")
                        if m_details.get("experience_gap", 0) > 0:
                            st.markdown(f"⏳ **{m_details['experience_gap']} year(s)** below required experience threshold")
            else:
                st.info("No jobs available for targeted AI insights.")

        with t_questions:
            st.subheader("❓ AI-Generated Candidate Interview Questions")
            st.caption("Tailored technical, behavioral, and skill-gap questions based on candidate profile.")

            candidate_skills = cand.get("skills", [])
            questions_data = generate_interview_questions(
                candidate_skills,
                experience=cand.get("experience", 0)
            )

            q_tab1, q_tab2 = st.tabs(["💻 Technical Questions", "🤝 Behavioral Questions"])

            with q_tab1:
                for idx, q in enumerate(questions_data["technical"], 1):
                    st.markdown(f"""
                        <div class="question-card">
                            <b style="color:#6366F1;">Question {idx}:</b> {q}
                        </div>
                    """, unsafe_allow_html=True)

            with q_tab2:
                for idx, q in enumerate(questions_data["behavioral"], 1):
                    st.markdown(f"""
                        <div class="question-card">
                            <b style="color:#10B981;">Question {idx}:</b> {q}
                        </div>
                    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # AI RANKING PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "AI Ranking":
        st.title("🏆 AI Candidate Ranking")
        st.markdown("Automatically rank all candidates against a selected job role using AI match scores.")
        st.markdown("---")

        with st.spinner("Loading jobs and candidates..."):
            job_res = api_request("GET", "/jobs")
            cand_res = api_request("GET", "/candidates")

        if job_res is None or cand_res is None:
            st.stop()
        if job_res.status_code != 200 or cand_res.status_code != 200:
            st.error("Failed to load data from backend.")
            st.stop()

        jobs = job_res.json()
        candidates = cand_res.json()

        if not jobs:
            st.warning("⚠️ No job roles found. Please create or seed jobs first (Admin Settings → Seed Default Jobs).")
            st.stop()
        if not candidates:
            st.info("No candidates uploaded yet. Head to **Upload Resume** to get started.")
            st.stop()

        st.markdown('<div class="job-selector-box">', unsafe_allow_html=True)
        col_js1, col_js2 = st.columns([2, 1])
        with col_js1:
            st.markdown("### 🎯 Select Job Role")
            job_opts = {j["title"]: j["id"] for j in jobs}
            selected_job_title = st.selectbox(
                "Choose the job to rank candidates against:",
                list(job_opts.keys()), key="ranking_job_select"
            )
            job_id = job_opts[selected_job_title]
        with col_js2:
            st.markdown("<br>", unsafe_allow_html=True)
            selected_job_obj = next((j for j in jobs if j["id"] == job_id), None)
            if selected_job_obj:
                st.caption(f"**Required Experience:** {selected_job_obj.get('experience_required', 'N/A')} years")
                reqs = selected_job_obj.get("requirements", [])
                if reqs:
                    st.caption("**Required Skills:**")
                    st.markdown(" ".join([f'<span class="badge badge-skill">{r}</span>' for r in reqs]), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🚀 Rank All Candidates", width="stretch", type="primary"):
            st.session_state["ranking_results"] = None
            ranked = []
            progress = st.progress(0, text="Scoring candidates...")
            for i, cand in enumerate(candidates):
                score_res = api_request("GET", f"/score?candidate_id={cand['id']}&job_id={job_id}")
                if score_res and score_res.status_code == 200:
                    sd = score_res.json()
                    ranked.append({
                        "candidate": cand,
                        "match_score": sd["match_score"],
                        "details": sd["details"]
                    })
                else:
                    ranked.append({
                        "candidate": cand,
                        "match_score": 0,
                        "details": {"matched_skills": [], "missing_skills": [], "experience_gap": 0}
                    })
                progress.progress((i + 1) / len(candidates), text=f"Scored {i+1}/{len(candidates)} candidates")
            progress.empty()
            ranked.sort(key=lambda x: x["match_score"], reverse=True)
            st.session_state["ranking_results"] = ranked
            st.session_state["ranking_job_title"] = selected_job_title

        if st.session_state.get("ranking_results"):
            ranked = st.session_state["ranking_results"]
            job_title_display = st.session_state.get("ranking_job_title", selected_job_title)
            st.markdown(f"### 📋 Rankings for: **{job_title_display}**")

            shortlisted_count = sum(1 for r in ranked if r["match_score"] >= 70)
            maybe_count = sum(1 for r in ranked if 40 <= r["match_score"] < 70)
            reject_count = sum(1 for r in ranked if r["match_score"] < 40)

            stat_c1, stat_c2, stat_c3, stat_c4 = st.columns(4)
            with stat_c1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">👥 Total Ranked</div><div class="metric-value">{len(ranked)}</div></div>', unsafe_allow_html=True)
            with stat_c2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">✅ Shortlisted</div><div class="metric-value" style="color:#34D399">{shortlisted_count}</div></div>', unsafe_allow_html=True)
            with stat_c3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">🤔 Maybe</div><div class="metric-value" style="color:#FCD34D">{maybe_count}</div></div>', unsafe_allow_html=True)
            with stat_c4:
                st.markdown(f'<div class="metric-card"><div class="metric-title">❌ Reject</div><div class="metric-value" style="color:#F87171">{reject_count}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            hdr1, hdr2, hdr3, hdr4 = st.columns([0.5, 3, 2, 2])
            hdr1.markdown("**#**")
            hdr2.markdown("**Candidate**")
            hdr3.markdown("**Match %**")
            hdr4.markdown("**Recommendation**")
            st.markdown("<hr style='margin: 4px 0 12px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

            for rank_idx, entry in enumerate(ranked):
                cand = entry["candidate"]
                score = entry["match_score"]
                details = entry["details"]
                rec_label, rec_class, rec_icon = get_recommendation(score)
                color = score_color(score)

                row_c1, row_c2, row_c3, row_c4 = st.columns([0.5, 3, 2, 2])
                with row_c1:
                    st.markdown(f"<div style='padding-top:8px; font-size:18px; font-weight:700; color:#6366F1;'>#{rank_idx+1}</div>", unsafe_allow_html=True)
                with row_c2:
                    st.markdown(f"<div style='padding-top:8px; font-size:15px; font-weight:600; color:#E5E7EB;'>👤 {cand['name']}</div>", unsafe_allow_html=True)
                with row_c3:
                    st.markdown(f"<div style='padding-top:8px; font-size:18px; font-weight:700; color:{color};'>{score}%</div>", unsafe_allow_html=True)
                with row_c4:
                    st.markdown(f"<div style='padding-top:6px;'><span class='{rec_class}'>{rec_icon} {rec_label}</span></div>", unsafe_allow_html=True)

                with st.expander(f"View details for {cand['name']}", expanded=False):
                    st.markdown('<div class="detail-panel">', unsafe_allow_html=True)
                    d_col1, d_col2 = st.columns([1.3, 1])
                    with d_col1:
                        st.markdown(f"## 👤 {cand['name']}")
                        st.markdown(f"📧 **Email:** {cand['email']}")
                        if cand.get("phone"):
                            st.markdown(f"📞 **Phone:** {cand['phone']}")
                        if cand.get("location"):
                            st.markdown(f"📍 **Location:** {cand['location']}")
                        st.markdown(f"⏳ **Experience:** {cand['experience']} years")
                        st.markdown("---")
                        st.markdown("#### 🛠️ Skills")
                        if cand.get("skills"):
                            st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in cand["skills"]]), unsafe_allow_html=True)
                        else:
                            st.caption("No skills extracted.")

                    with d_col2:
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number", value=score,
                            domain={"x": [0, 1], "y": [0, 1]},
                            title={"text": "Match Score", "font": {"size": 16}},
                            gauge={
                                "axis": {"range": [0, 100]},
                                "bar": {"color": color},
                                "bgcolor": "rgba(0,0,0,0)",
                                "steps": [
                                    {"range": [0, 40], "color": "rgba(239,68,68,0.1)"},
                                    {"range": [40, 70], "color": "rgba(245,158,11,0.1)"},
                                    {"range": [70, 100], "color": "rgba(16,185,129,0.1)"},
                                ],
                            },
                        ))
                        fig_gauge.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB",
                            height=180, margin=dict(l=10, r=10, t=40, b=10)
                        )
                        st.plotly_chart(fig_gauge, width="stretch")

                    st.markdown("---")
                    str_col, weak_col, rec_col = st.columns(3)
                    with str_col:
                        st.markdown("#### 💪 Strengths")
                        matched = details.get("matched_skills", [])
                        if matched:
                            for sk in matched:
                                st.markdown(f'<span class="badge badge-matched">✅ {sk}</span>', unsafe_allow_html=True)
                        else:
                            st.caption("No matching skills found.")
                    with weak_col:
                        st.markdown("#### ⚠️ Weaknesses")
                        missing = details.get("missing_skills", [])
                        if missing:
                            for sk in missing:
                                st.markdown(f'<span class="badge badge-missing">❌ {sk}</span>', unsafe_allow_html=True)
                        else:
                            st.caption("All required skills matched! 🎉")
                        gap = details.get("experience_gap", 0)
                        if gap and gap > 0:
                            st.markdown(f'<span class="badge badge-missing">⏳ {gap} yrs experience gap</span>', unsafe_allow_html=True)
                    with rec_col:
                        st.markdown("#### 🏷️ Recommendation")
                        st.markdown(f'<span class="{rec_class}" style="font-size:15px; padding: 8px 18px;">{rec_icon} {rec_label}</span>', unsafe_allow_html=True)
                        if rec_label == "Shortlisted":
                            st.success("Strong match — recommend proceeding to interview.")
                        elif rec_label == "Maybe":
                            st.warning("Partial match — review manually before deciding.")
                        else:
                            st.error("Low match — does not meet key requirements.")

                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<hr style='margin: 4px 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SCHEDULE INTERVIEW PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Schedule Interview":
        st.title("📅 Interview Scheduling & Management")
        st.markdown("Schedule interviews for candidates, view calendar schedules, track session statuses, and generate tailored interview questions.")
        st.markdown("---")

        if st.session_state.role == "Candidate":
            st.warning("⛔ Access Restricted: Only Recruiters and Admins can schedule interviews.")
            st.stop()

        with st.spinner("Loading candidates and interviews..."):
            cand_res = api_request("GET", "/candidates")
            interview_res = api_request("GET", "/interviews")

        candidates = cand_res.json() if (cand_res and cand_res.status_code == 200) else []
        interviews = interview_res.json() if (interview_res and interview_res.status_code == 200) else []

        tab_sched, tab_cal, tab_status, tab_qgen = st.tabs([
            "➕ Schedule Interview", "📅 Calendar View", "📋 Interview Status", "❓ Generated Interview Questions"
        ])

        # ── Tab 1: Schedule Form ──────────────────────────────────────────────
        with tab_sched:
            sched_col, info_col = st.columns([1.2, 1])
            with sched_col:
                st.subheader("Schedule New Session")
                if not candidates:
                    st.warning("No candidates found. Upload resumes first.")
                else:
                    with st.container(border=True):
                        priority_statuses = ["Shortlisted", "Applied", "Screening", "Interview", "Selected"]
                        sorted_cands = sorted(
                            candidates,
                            key=lambda c: priority_statuses.index(c.get("status", "Applied"))
                            if c.get("status") in priority_statuses else 99
                        )
                        cand_options = {f"{c['name']} ({c.get('status', 'Applied')}) — {c['email']}": c["id"] for c in sorted_cands}

                        selected_cand_label = st.selectbox(
                            "👤 Candidate Name *",
                            list(cand_options.keys()),
                            help="Shortlisted candidates appear first"
                        )
                        selected_cand_id = cand_options[selected_cand_label]

                        int_date = st.date_input(
                            "📆 Interview Date *",
                            min_value=date.today(),
                            value=date.today()
                        )
                        int_time = st.time_input("🕐 Interview Time *")
                        interviewer = st.text_input("👔 Interviewer Name *", placeholder="e.g. Sarah Johnson")
                        platform = st.selectbox("💻 Platform *", ["Google Meet", "Microsoft Teams", "Zoom"])
                        notes = st.text_area("📝 Notes (optional)", placeholder="Topics, focus areas...", height=80)

                        if st.button("📅 Confirm & Schedule Interview", width="stretch", type="primary"):
                            if not interviewer.strip():
                                st.error("❌ Please enter the interviewer's name.")
                            else:
                                payload = {
                                    "candidate_id": selected_cand_id,
                                    "interview_date": str(int_date),
                                    "interview_time": str(int_time)[:5],
                                    "interviewer_name": interviewer.strip(),
                                    "platform": platform,
                                    "notes": notes.strip() if notes.strip() else None,
                                }
                                with st.spinner("Scheduling..."):
                                    res = api_request("POST", "/interviews", json=payload)

                                if res and res.status_code == 201:
                                    data = res.json()
                                    st.success(f"🎉 Interview scheduled for **{data['candidate_name']}** on **{data['interview_date']}** at **{data['interview_time']}** via **{data['platform']}**!")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                elif res:
                                    err = res.json().get("detail", "Unknown error")
                                    st.error(f"❌ Failed to schedule: {err}")

            with info_col:
                st.subheader("💡 Tips for Scheduling")
                st.markdown("""
                    - **Candidate Status:** Scheduling an interview automatically updates the candidate's status to **Interview**.
                    - **Automated Invite:** Use the *Candidates List → Communication* tab to send formal calendar invites.
                    - **Platform:** Support for Google Meet, Microsoft Teams, and Zoom.
                """)

        # ── Tab 2: Calendar View ──────────────────────────────────────────────
        with tab_cal:
            st.subheader("📅 Monthly Interview Calendar")
            today = date.today()
            
            # Month/Year selection
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                sel_month = st.selectbox("Select Month", range(1, 13), index=today.month - 1, format_func=lambda m: cal_module.month_name[m])
            with col_m2:
                sel_year = st.number_input("Select Year", min_value=2024, max_value=2030, value=today.year)

            month_cal = cal_module.monthcalendar(sel_year, sel_month)
            days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            
            # Render Calendar Table
            cal_cols = st.columns(7)
            for idx, d_name in enumerate(days_header):
                cal_cols[idx].markdown(f"**{d_name}**")

            # Map interviews by date string YYYY-MM-DD
            iv_by_date = {}
            for iv in interviews:
                d_str = iv.get("interview_date")
                if d_str:
                    iv_by_date.setdefault(d_str, []).append(iv)

            for week in month_cal:
                w_cols = st.columns(7)
                for day_idx, day_num in enumerate(week):
                    with w_cols[day_idx]:
                        if day_num == 0:
                            st.markdown('<div class="cal-cell" style="opacity:0.3;"></div>', unsafe_allow_html=True)
                        else:
                            date_key = f"{sel_year}-{sel_month:02d}-{day_num:02d}"
                            is_today = (date_key == today.strftime("%Y-%m-%d"))
                            cell_cls = "cal-cell cal-cell-today" if is_today else "cal-cell"

                            day_events = iv_by_date.get(date_key, [])
                            events_html = ""
                            for ev in day_events:
                                events_html += f'<div class="cal-event">👤 {ev["candidate_name"]}<br>🕒 {ev["interview_time"]}</div>'

                            st.markdown(f"""
                                <div class="{cell_cls}">
                                    <b>{day_num}</b> {'📌 Today' if is_today else ''}
                                    {events_html}
                                </div>
                            """, unsafe_allow_html=True)

        # ── Tab 3: Interview Status ───────────────────────────────────────────
        with tab_status:
            st.subheader(f"📋 Scheduled Sessions & Status ({len(interviews)})")
            if not interviews:
                st.info("No interviews scheduled yet.")
            else:
                sf = st.selectbox("Filter by Status", ["All", "Scheduled", "Completed", "Cancelled"], key="iv_status_filter_tab")
                filtered_ivs = interviews if sf == "All" else [iv for iv in interviews if iv["status"] == sf]

                for iv in filtered_ivs:
                    status_colors_iv = {"Scheduled": "#3B82F6", "Completed": "#10B981", "Cancelled": "#EF4444"}
                    iv_color = status_colors_iv.get(iv["status"], "#6B7280")
                    pf_icon = platform_icon(iv["platform"])

                    ic1, ic2 = st.columns([3, 1])
                    with ic1:
                        st.markdown(f"""
                            <div class="interview-card">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <b style="color:#E5E7EB; font-size:15px;">👤 {iv['candidate_name']} ({iv['candidate_email']})</b>
                                    <span style="background:{iv_color}20; color:{iv_color}; border:1px solid {iv_color}60; padding:3px 10px; border-radius:50px; font-size:12px; font-weight:600;">
                                        {iv['status']}
                                    </span>
                                </div>
                                <div style="color:#9CA3AF; font-size:13px; line-height:1.8;">
                                    📆 <b>{iv['interview_date']}</b> at <b>{iv['interview_time']}</b> | 👔 Interviewer: <b>{iv['interviewer_name']}</b><br>
                                    {pf_icon} Platform: <span class="platform-pill">{iv['platform']}</span>
                                </div>
                                {f'<div style="color:#6B7280; font-size:12px; margin-top:6px;">📝 {iv["notes"]}</div>' if iv.get("notes") else ""}
                            </div>
                        """, unsafe_allow_html=True)
                    with ic2:
                        new_st = st.selectbox("Update Status", ["Scheduled", "Completed", "Cancelled"], index=["Scheduled", "Completed", "Cancelled"].index(iv["status"]), key=f"status_sel_{iv['id']}")
                        if st.button("Update", key=f"btn_update_iv_{iv['id']}"):
                            patch_r = api_request("PATCH", f"/interviews/{iv['id']}/status?new_status={new_st}")
                            if patch_r and patch_r.status_code == 200:
                                st.toast("✅ Status updated!")
                                time.sleep(0.4)
                                st.rerun()

        # ── Tab 4: Generated Interview Questions ─────────────────────────────
        with tab_qgen:
            st.subheader("❓ Interview Question Generator")
            st.caption("Generate role-tailored technical and behavioral questions for upcoming interviews.")

            if not candidates:
                st.info("No candidates available to generate questions.")
            else:
                q_cand_opts = {f"{c['name']} ({c['email']})": c for c in candidates}
                sel_q_cand_label = st.selectbox("Select Candidate for Interview Questions:", list(q_cand_opts.keys()), key="qgen_cand_select")
                q_cand = q_cand_opts[sel_q_cand_label]

                q_skills = q_cand.get("skills", [])
                gen_questions = generate_interview_questions(q_skills, experience=q_cand.get("experience", 0))

                col_q1, col_q2 = st.columns(2)
                with col_q1:
                    st.markdown("#### 💻 Technical Questions")
                    for idx, q in enumerate(gen_questions["technical"], 1):
                        st.markdown(f'<div class="question-card"><b style="color:#6366F1;">Q{idx}:</b> {q}</div>', unsafe_allow_html=True)
                with col_q2:
                    st.markdown("#### 🤝 Behavioral & Leadership Questions")
                    for idx, q in enumerate(gen_questions["behavioral"], 1):
                        st.markdown(f'<div class="question-card"><b style="color:#10B981;">Q{idx}:</b> {q}</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # UPLOAD RESUME PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Upload Resume":
        st.title("📤 Resume Intelligence Uploader")
        st.markdown("---")

        if st.session_state.role not in ["Recruiter", "Admin"]:
            st.warning("⛔ Access Restricted: Only Recruiters and Admins can upload resumes.")
        else:
            with st.spinner("Loading available job roles..."):
                job_res_up = api_request("GET", "/jobs")
            jobs_for_upload = []
            if job_res_up and job_res_up.status_code == 200:
                jobs_for_upload = job_res_up.json()

            st.markdown('<div class="job-selector-box">', unsafe_allow_html=True)
            st.markdown("### 🎯 Select Job Role")
            if not jobs_for_upload:
                st.warning("No job roles available. Ask an Admin to seed jobs first.")
                selected_upload_job = None
                selected_upload_job_title = None
            else:
                upload_job_opts = {j["title"]: j["id"] for j in jobs_for_upload}
                selected_upload_job_title = st.selectbox(
                    "Which job are you hiring for?",
                    list(upload_job_opts.keys()), key="upload_job_select"
                )
                selected_upload_job = upload_job_opts[selected_upload_job_title]
                st.caption(f"📌 Resumes will be matched against: **{selected_upload_job_title}**")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("""
                Upload resumes in **PDF** or **TXT** formats. The backend will automatically extract:
                - Basic profiles (Name, Email, Phone, Location)
                - Technical skills and educational details
                - Notice period and compensation expectations
            """)

            uploaded_file = st.file_uploader("Choose File", type=["pdf", "txt"])

            if uploaded_file is not None:
                file_size_kb = len(uploaded_file.getvalue()) / 1024
                st.info(f"📄 Selected: **{uploaded_file.name}** ({file_size_kb:.1f} KB)")

                # Progress bar preview
                prog_placeholder = st.empty()
                prog_placeholder.progress(0, text="Ready to upload...")

                if st.button("Extract and Save Resume", width="stretch"):
                    filename = uploaded_file.name.lower()
                    if not (filename.endswith(".pdf") or filename.endswith(".txt")):
                        st.markdown("""
                            <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                                <div class="error-header">❌ Invalid Resume format</div>
                                <p style="margin: 0; color: #F87171; font-size: 14px;">
                                    Only <b>PDF</b> or <b>TXT</b> formats are supported.
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.stop()

                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}

                    # Animated upload progress
                    prog_placeholder.progress(20, text="Uploading file...")
                    with st.spinner("Processing resume — performing entity extraction..."):
                        prog_placeholder.progress(50, text="Parsing resume content...")
                        res = api_request("POST", "/upload_resume", files=files)
                        prog_placeholder.progress(90, text="Finalizing...")
                        time.sleep(0.3)
                        prog_placeholder.progress(100, text="Done!")

                    if res is not None:
                        if res.status_code == 201:
                            candidate = res.json()
                            st.success("🎉 Resume Uploaded and Processed Successfully!")

                            with st.container(border=True):
                                st.subheader(f"👤 Candidate Extracted Profile: {candidate['name']}")
                                col_p1, col_p2 = st.columns(2)
                                with col_p1:
                                    st.write(f"**Email:** {candidate['email']}")
                                    st.write(f"**Phone:** {candidate.get('phone') or 'N/A'}")
                                    st.write(f"**Location:** {candidate.get('location') or 'N/A'}")
                                    st.write(f"**Experience:** {candidate['experience']} years")
                                with col_p2:
                                    st.write(f"**Education:** {candidate.get('education', 'N/A')}")
                                    st.write(f"**Notice Period:** {candidate.get('notice_period') or 'N/A'}")
                                    st.write(f"**Expected CTC:** {candidate.get('expected_ctc') or 'N/A'}")
                                    st.write(f"**Initial Status:** :blue[{candidate['status']}]")
                                st.markdown("**Extracted Skills:**")
                                st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in candidate["skills"]]) if candidate["skills"] else "None", unsafe_allow_html=True)

                            if selected_upload_job:
                                st.markdown("---")
                                with st.spinner(f"Calculating AI match score against **{selected_upload_job_title}**..."):
                                    auto_score_res = api_request("GET", f"/score?candidate_id={candidate['id']}&job_id={selected_upload_job}")
                                    if auto_score_res and auto_score_res.status_code == 200:
                                        auto_sd = auto_score_res.json()
                                        auto_score = auto_sd["match_score"]
                                        auto_details = auto_sd["details"]
                                        if auto_score >= 70:
                                            rec = "✅ Shortlisted"
                                            rec_fn = st.success
                                        elif auto_score >= 40:
                                            rec = "🤔 Maybe"
                                            rec_fn = st.warning
                                        else:
                                            rec = "❌ Reject"
                                            rec_fn = st.error
                                        st.subheader(f"🤖 AI Match Score vs. {selected_upload_job_title}")
                                        sc1, sc2, sc3 = st.columns(3)
                                        sc1.metric("Match Score", f"{auto_score}%")
                                        sc2.metric("Matched Skills", len(auto_details.get("matched_skills", [])))
                                        sc3.metric("Missing Skills", len(auto_details.get("missing_skills", [])))
                                        rec_fn(f"**Recommendation:** {rec}")

                        elif res.status_code == 400:
                            detail = res.json().get("detail", "Failed parsing resume structure.")
                            st.markdown(f"""
                                <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                                    <div class="error-header">❌ Invalid Resume</div>
                                    <p style="margin: 0; color: #F87171; font-size: 14px;">
                                        We were unable to extract details from the resume.<br>
                                        <b>Detail:</b> {detail}
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            detail = res.json().get("detail", "Server returned unexpected error.")
                            st.markdown(f"""
                                <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                                    <div class="error-header">🚨 Upload Failed</div>
                                    <p style="margin: 0; color: #F87171; font-size: 14px;">
                                        <b>HTTP Status:</b> {res.status_code}<br>
                                        <b>Detail:</b> {detail}
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                else:
                    prog_placeholder.empty()

    # ═══════════════════════════════════════════════════════════════════════════
    # CANDIDATE COMPARISON PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Compare Candidates":
        st.title("⚔️ Side-by-Side Candidate Comparison")
        st.markdown("Compare 2 to 4 candidates side-by-side on match score, skills, experience, education, certifications, and projects.")
        st.markdown("---")

        with st.spinner("Loading comparison data..."):
            cand_res = api_request("GET", "/candidates")
            job_res = api_request("GET", "/jobs")

        if cand_res is None or job_res is None or cand_res.status_code != 200 or job_res.status_code != 200:
            st.error("Failed to load candidates or jobs for comparison.")
            st.stop()

        candidates = cand_res.json()
        jobs = job_res.json()

        if len(candidates) < 2:
            st.warning("⚠️ At least 2 candidates are required to perform comparison. Upload more resumes first.")
            st.stop()

        st.markdown('<div class="job-selector-box">', unsafe_allow_html=True)
        col_cj1, col_cj2 = st.columns([2, 1])
        with col_cj1:
            job_opts = {j["title"]: j["id"] for j in jobs}
            selected_job_title = st.selectbox("Select Target Job for Comparison:", list(job_opts.keys()), key="comp_job_select")
            job_id = job_opts[selected_job_title]
        with col_cj2:
            st.markdown("<br>", unsafe_allow_html=True)
            sel_job_obj = next((j for j in jobs if j["id"] == job_id), None)
            if sel_job_obj:
                st.caption(f"**Required Exp:** {sel_job_obj.get('experience_required', 0)} yrs | **Req Skills:** {len(sel_job_obj.get('requirements', []))}")
        st.markdown("</div>", unsafe_allow_html=True)

        cand_opts = {f"{c['name']} ({c['email']})": c for c in candidates}
        default_selected = list(cand_opts.keys())[:min(3, len(candidates))]
        selected_cand_keys = st.multiselect("Select 2 to 4 Candidates to Compare:", list(cand_opts.keys()), default=default_selected, max_selections=4)

        if len(selected_cand_keys) < 2:
            st.warning("Please select at least 2 candidates to compare.")
            st.stop()

        comp_candidates = [cand_opts[k] for k in selected_cand_keys]

        comp_data = []
        for c in comp_candidates:
            score_res = api_request("GET", f"/score?candidate_id={c['id']}&job_id={job_id}")
            if score_res and score_res.status_code == 200:
                sd = score_res.json()
                m_score = sd["match_score"]
                m_details = sd["details"]
            else:
                m_score = 0.0
                m_details = {"matched_skills": [], "missing_skills": [], "experience_gap": 0}
            
            certs = extract_certifications_from_text(c.get("resume_text", ""))
            comp_data.append({
                "candidate": c,
                "score": m_score,
                "details": m_details,
                "certs": certs
            })

        best_cand_id = max(comp_data, key=lambda x: x["score"])["candidate"]["id"]

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📊 Side-by-Side Comparison Overview")

        cols = st.columns(len(comp_data))

        for idx, item in enumerate(comp_data):
            c = item["candidate"]
            sc = item["score"]
            dt = item["details"]
            cr = item["certs"]
            is_best = (c["id"] == best_cand_id)

            rec_lbl, rec_cls, rec_ic = get_recommendation(sc)
            border_style = "comparison-col comparison-winner" if is_best else "comparison-col"

            with cols[idx]:
                st.markdown(f"""
                    <div class="{border_style}">
                        {'<div style="background:#10B981; color:#000; font-weight:700; font-size:11px; padding:2px 8px; border-radius:4px; display:inline-block; margin-bottom:8px;">🏆 TOP MATCH</div>' if is_best else ''}
                        <h3 style="margin:0; color:#E5E7EB;">{c['name']}</h3>
                        <p style="color:#9CA3AF; font-size:12px; margin:4px 0 12px 0;">{c['email']}</p>
                        
                        <div style="text-align:center; margin:16px 0;">
                            <div style="font-size:32px; font-weight:700; color:{score_color(sc)};">{sc}%</div>
                            <span class="{rec_cls}" style="font-size:12px; margin-top:4px;">{rec_ic} {rec_lbl}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        st.subheader("🔍 Attribute-by-Attribute Comparison")

        st.markdown("#### 1. Match Score Comparison")
        score_df = pd.DataFrame({
            "Candidate": [d["candidate"]["name"] for d in comp_data],
            "Match Score (%)": [d["score"] for d in comp_data]
        })
        fig_comp_scores = px.bar(
            score_df, x="Candidate", y="Match Score (%)", color="Candidate",
            color_discrete_sequence=["#10B981", "#6366F1", "#06B6D4", "#F59E0B"],
            text="Match Score (%)"
        )
        fig_comp_scores.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#E5E7EB', showlegend=False, margin=dict(t=10, b=10))
        fig_comp_scores.update_traces(textposition="outside")
        st.plotly_chart(fig_comp_scores, width="stretch")

        st.markdown("#### 2. Experience & Education")
        c_exp_cols = st.columns(len(comp_data))
        for idx, item in enumerate(comp_data):
            c = item["candidate"]
            with c_exp_cols[idx]:
                st.markdown(f"**{c['name']}**")
                st.write(f"⏳ **Experience:** {c.get('experience', 0)} years")
                st.write(f"🎓 **Education:** {c.get('education', 'N/A')}")
                st.write(f"📍 **Location:** {c.get('location', 'N/A')}")

        st.markdown("---")

        st.markdown("#### 3. Skills Matrix")
        c_sk_cols = st.columns(len(comp_data))
        for idx, item in enumerate(comp_data):
            c = item["candidate"]
            dt = item["details"]
            with c_sk_cols[idx]:
                st.markdown(f"**{c['name']}**")
                st.markdown("**Matched Required Skills:**")
                if dt.get("matched_skills"):
                    st.markdown(" ".join([f'<span class="badge badge-matched">{s}</span>' for s in dt["matched_skills"]]), unsafe_allow_html=True)
                else:
                    st.caption("None matched")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Missing Required Skills:**")
                if dt.get("missing_skills"):
                    st.markdown(" ".join([f'<span class="badge badge-missing">{s}</span>' for s in dt["missing_skills"]]), unsafe_allow_html=True)
                else:
                    st.caption("None missing")

        st.markdown("---")

        st.markdown("#### 4. Certifications & Key Projects")
        c_cp_cols = st.columns(len(comp_data))
        for idx, item in enumerate(comp_data):
            c = item["candidate"]
            cr = item["certs"]
            projs = c.get("projects", [])
            with c_cp_cols[idx]:
                st.markdown(f"**{c['name']}**")
                st.markdown("🏅 **Certifications:**")
                if cr:
                    for cert in cr:
                        st.markdown(f"• {cert}")
                else:
                    st.caption("None detected")
                
                st.markdown("📁 **Projects:**")
                if projs:
                    for p in projs:
                        st.markdown(f"• {p}")
                else:
                    st.caption("None specified")

    # ═══════════════════════════════════════════════════════════════════════════
    # ADMIN SETTINGS PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Admin Settings":
        st.title("⚙️ System Administration Settings")
        st.caption("UI Demonstration Panel (Actions Simulated)")
        st.markdown("---")

        col_ad1, col_ad2 = st.columns(2)
        with col_ad1:
            st.subheader("🤖 LLM Model Extraction Configuration")
            extraction_mode = st.radio("Resume Extraction Engine", [
                "Fast Hybrid (Regex + Local parser)",
                "Accurate LLM (OpenAI GPT-4o Mock)",
                "Semantic Embeddings (Mock)"
            ])
            st.slider("Model Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
            st.checkbox("Enable Automatic Schema Validation", value=True)
            st.button("Save Configuration", width="stretch")

        with col_ad2:
            st.subheader("🖥️ Server Stats & Infrastructure Status")
            st.markdown("""
                - **Database Engine:** SQLite (Local)
                - **Cache Driver:** Redis Cache (Resilient Fallback Mode Active)
                - **API Latency:** 4.2ms average
                - **System Health:** 🟢 All Systems Operational
            """)
            st.divider()
            st.subheader("👤 User Account Management")
            accounts_data = [
                {"Username": "admin_user", "Role": "Admin", "Status": "Active"},
                {"Username": "recruiter_user", "Role": "Recruiter", "Status": "Active"},
                {"Username": "manager_user", "Role": "Hiring Manager", "Status": "Active"},
            ]
            st.table(accounts_data)

            if st.button("Seed Default Jobs List", width="stretch"):
                jobs_to_seed = [
                    {"title": "Senior FastAPI Developer", "description": "Develop robust FastAPI endpoints.", "requirements": ["Python", "FastAPI", "Docker", "PostgreSQL", "SQL"], "experience_required": 5},
                    {"title": "Machine Learning Engineer", "description": "Build high-throughput ML pipelines.", "requirements": ["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy"], "experience_required": 3},
                    {"title": "React Frontend Architect", "description": "Design modern dashboard templates.", "requirements": ["React", "JavaScript", "Docker", "Git"], "experience_required": 4},
                ]
                success_count = 0
                for job_data in jobs_to_seed:
                    res = api_request("POST", "/jobs", json=job_data)
                    if res and res.status_code == 201:
                        success_count += 1
                if success_count > 0:
                    st.success(f"Successfully seeded **{success_count}** job requirements!")
                else:
                    st.error("Failed to seed jobs. Check backend connection.")

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. ASSESSMENT INTEGRATION UI
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Assessment Integration":
        st.title("📝 Assessment Integration & Evaluation")
        st.markdown("Assign assessments, track completion statuses, inspect scores, and review detailed evaluation results.")
        st.markdown("---")

        with st.spinner("Loading candidate list..."):
            cand_res = api_request("GET", "/candidates")
        candidates = cand_res.json() if (cand_res and cand_res.status_code == 200) else []

        tab_assign, tab_status, tab_results = st.tabs([
            "➕ Assign Assessment", "📋 Assessment Status", "📊 Scores & Results"
        ])

        # ── Tab 1: Assign Assessment ──────────────────────────────────────────
        with tab_assign:
            st.subheader("Assign New Assessment")
            col_a1, col_a2 = st.columns([1.2, 1])

            with col_a1:
                with st.container(border=True):
                    cand_names = [f"{c['name']} ({c['email']})" for c in candidates] if candidates else ["Rahul Sharma (rahul@example.com)", "Priya Desai (priya@example.com)", "Ayush Patel (ayush@example.com)"]
                    sel_cand_assign = st.selectbox("Select Candidate *", cand_names, key="assign_cand_select")

                    ass_type = st.selectbox("Assessment Type *", [
                        "Technical Assessment", "Coding Challenge", "Aptitude Test", "Personality & Culture Fit", "System Design Challenge"
                    ])

                    deadline_date = st.date_input("Submission Deadline *", value=date.today() + timedelta(days=5))
                    notes_assign = st.text_area("Instructions / Notes for Candidate", placeholder="e.g. Complete within 60 minutes once started...")

                    if st.button("🚀 Assign Assessment Now", type="primary", use_container_width=True):
                        c_name = sel_cand_assign.split(" (")[0]
                        c_email = sel_cand_assign.split("(")[1].rstrip(")") if "(" in sel_cand_assign else "candidate@example.com"
                        new_item = {
                            "id": len(st.session_state.assessment_data) + 1,
                            "candidate_name": c_name,
                            "candidate_email": c_email,
                            "type": ass_type.replace(" Assessment", "").replace(" Test", "").replace(" Challenge", ""),
                            "status": "Pending",
                            "score": None,
                            "assigned_date": date.today().strftime("%Y-%m-%d"),
                            "deadline": str(deadline_date),
                            "time_taken": None,
                            "sections": {},
                            "strengths": [],
                            "recommendations": []
                        }
                        st.session_state.assessment_data.append(new_item)
                        st.toast(f"Assessment assigned to {c_name}!", icon="🎯")
                        time.sleep(0.4)
                        st.rerun()

            with col_a2:
                st.info("💡 **Assessment Guidelines:**\n- Candidates will receive an automated invitation link.\n- Results automatically sync back to candidate scorecards.\n- Minimum passing score threshold: **70%**.")
                st.markdown("""
                    #### Available Test Suites
                    - 💻 **Technical Assessment:** Algorithms, Data Structures, SQL
                    - ⚡ **Coding Challenge:** Live sandboxed programming
                    - 🧠 **Aptitude Test:** Numerical & Logical reasoning
                    - 🤝 **Personality & Culture Fit:** Behavioral matrix
                """)

        # ── Tab 2: Assessment Status ──────────────────────────────────────────
        with tab_status:
            st.subheader("📋 Candidate Assessment Tracker")
            
            assessments = st.session_state.assessment_data
            
            # Metric row
            total_ass = len(assessments)
            comp_ass = sum(1 for a in assessments if a["status"] == "Completed")
            prog_ass = sum(1 for a in assessments if a["status"] == "In Progress")
            pend_ass = sum(1 for a in assessments if a["status"] == "Pending")

            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.markdown(f'<div class="metric-card"><div class="metric-title">Total Assigned</div><div class="metric-value">{total_ass}</div></div>', unsafe_allow_html=True)
            sm2.markdown(f'<div class="metric-card"><div class="metric-title">Completed</div><div class="metric-value" style="color:#10B981;">{comp_ass}</div></div>', unsafe_allow_html=True)
            sm3.markdown(f'<div class="metric-card"><div class="metric-title">In Progress</div><div class="metric-value" style="color:#3B82F6;">{prog_ass}</div></div>', unsafe_allow_html=True)
            sm4.markdown(f'<div class="metric-card"><div class="metric-title">Pending</div><div class="metric-value" style="color:#F59E0B;">{pend_ass}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Table view
            df_ass = pd.DataFrame(assessments)
            if not df_ass.empty:
                display_df = df_ass[["candidate_name", "candidate_email", "type", "assigned_date", "deadline", "status", "score"]].copy()
                display_df.columns = ["Candidate", "Email", "Type", "Assigned Date", "Deadline", "Status", "Score %"]
                display_df["Score %"] = display_df["Score %"].apply(lambda v: f"{v}%" if pd.notnull(v) and v is not None else "N/A")
                st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("⚡ Update Assessment Status")
            up_col1, up_col2, up_col3 = st.columns([2, 1.5, 1])
            with up_col1:
                ass_opts = {f"{a['candidate_name']} — {a['type']} ({a['status']})": a["id"] for a in assessments}
                sel_ass_label = st.selectbox("Select Assessment:", list(ass_opts.keys()), key="status_ass_sel")
                sel_ass_id = ass_opts[sel_ass_label]
            with up_col2:
                new_ass_st = st.selectbox("New Status:", ["Pending", "In Progress", "Completed", "Expired"], key="new_ass_st_sel")
            with up_col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Update Status", key="btn_update_ass_st"):
                    for a in st.session_state.assessment_data:
                        if a["id"] == sel_ass_id:
                            a["status"] = new_ass_st
                            if new_ass_st == "Completed" and a["score"] is None:
                                a["score"] = 82
                                a["time_taken"] = "35 min"
                                a["sections"] = {"Core Skills": 85, "Problem Solving": 80}
                                a["strengths"] = ["Good execution speed"]
                                a["recommendations"] = ["Continue practicing complex scenarios"]
                    st.toast("Assessment status updated!", icon="✅")
                    time.sleep(0.3)
                    st.rerun()

        # ── Tab 3: Scores & Results ────────────────────────────────────────────
        with tab_results:
            st.subheader("📊 Assessment Scorecards & Deep Dive")

            completed_items = [a for a in st.session_state.assessment_data if a["status"] == "Completed"]

            if not completed_items:
                st.info("No completed assessments available yet.")
            else:
                comp_opts = {f"{a['candidate_name']} ({a['type']}) — Score: {a['score']}%": a for a in completed_items}
                sel_comp_label = st.selectbox("Select Assessment Result to Inspect:", list(comp_opts.keys()), key="comp_inspect_sel")
                ass_res = comp_opts[sel_comp_label]

                col_res1, col_res2 = st.columns([1.2, 1])

                with col_res1:
                    st.markdown(f"""
                        <div class="assessment-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <h3 style="margin:0; color:#E5E7EB;">👤 {ass_res['candidate_name']}</h3>
                                    <p style="color:#9CA3AF; margin:4px 0 0 0; font-size:13px;">Assessment Type: <b>{ass_res['type']}</b> | Time Taken: <b>{ass_res.get('time_taken', 'N/A')}</b></p>
                                </div>
                                <div style="text-align:right;">
                                    <span class="badge badge-shortlisted" style="font-size:16px; padding:6px 16px;">Score: {ass_res['score']}%</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown("#### 🎯 Section-wise Breakdown")
                    sections = ass_res.get("sections", {})
                    if sections:
                        sec_df = pd.DataFrame(list(sections.items()), columns=["Section", "Score %"])
                        fig_sec = px.bar(
                            sec_df, x="Score %", y="Section", orientation="h", text="Score %",
                            color="Score %", color_continuous_scale="Viridis"
                        )
                        fig_sec.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", coloraxis_showscale=False, height=220, margin=dict(t=10, b=10))
                        fig_sec.update_traces(textposition="outside")
                        st.plotly_chart(fig_sec, use_container_width=True)
                    else:
                        st.caption("No section details provided.")

                with col_res2:
                    st.markdown("#### 💪 Key Strengths")
                    for s in ass_res.get("strengths", ["Strong analytical approach"]):
                        st.markdown(f"✅ {s}")

                    st.markdown("#### 💡 AI Recommendations & Next Steps")
                    for r in ass_res.get("recommendations", ["Proceed to technical interview stage"]):
                        st.markdown(f"📌 {r}")

                    st.markdown("---")
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number", value=ass_res['score'],
                        title={"text": "Overall Score"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#10B981" if ass_res['score'] >= 70 else "#F59E0B"},
                            "steps": [
                                {"range": [0, 50], "color": "rgba(239,68,68,0.1)"},
                                {"range": [50, 70], "color": "rgba(245,158,11,0.1)"},
                                {"range": [70, 100], "color": "rgba(16,185,129,0.1)"}
                            ]
                        }
                    ))
                    fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", height=180, margin=dict(t=30, b=10))
                    st.plotly_chart(fig_gauge, use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. CANDIDATE SOURCING UI
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Candidate Sourcing":
        st.title("🎯 Candidate Sourcing & Acquisition")
        st.markdown("Track multi-channel candidate sources, manage imported leads, and import new candidate profiles.")
        st.markdown("---")

        sourced = st.session_state.sourced_candidates

        # Metric summary
        src_counts = Counter(s["source"] for s in sourced)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.markdown(f'<div class="metric-card"><div class="metric-title">LinkedIn</div><div class="metric-value" style="color:#60A5FA;">{src_counts.get("LinkedIn", 0)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="metric-title">Indeed</div><div class="metric-value" style="color:#93C5FD;">{src_counts.get("Indeed", 0)}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="metric-title">Referrals</div><div class="metric-value" style="color:#34D399;">{src_counts.get("Referral", 0)}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card"><div class="metric-title">Job Portals</div><div class="metric-value" style="color:#FCD34D;">{src_counts.get("Job Portal", 0)}</div></div>', unsafe_allow_html=True)
        m5.markdown(f'<div class="metric-card"><div class="metric-title">Direct Apply</div><div class="metric-value" style="color:#A78BFA;">{src_counts.get("Direct Apply", 0)}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tab_sources, tab_import = st.tabs(["📋 Candidate Sources Table", "📥 Import Candidate"])

        # ── Tab 1: Candidate Sources Table ─────────────────────────────────────
        with tab_sources:
            st.subheader("Candidate Sources")

            filter_c1, filter_c2 = st.columns(2)
            with filter_c1:
                sel_src_filter = st.selectbox("Filter by Source:", ["All", "LinkedIn", "Indeed", "Referral", "Job Portal", "Direct Apply"])
            with filter_c2:
                sel_st_filter = st.selectbox("Filter by Status:", ["All", "New", "Contacted", "In Review", "Converted"])

            filtered_sourced = sourced
            if sel_src_filter != "All":
                filtered_sourced = [s for s in filtered_sourced if s["source"] == sel_src_filter]
            if sel_st_filter != "All":
                filtered_sourced = [s for s in filtered_sourced if s["status"] == sel_st_filter]

            # Render Table
            hdr1, hdr2, hdr3, hdr4, hdr5 = st.columns([1.5, 2.5, 1.5, 1.5, 1])
            hdr1.markdown("**Source**")
            hdr2.markdown("**Candidate**")
            hdr3.markdown("**Date Imported**")
            hdr4.markdown("**Status**")
            hdr5.markdown("**Action**")
            st.markdown("<hr style='margin: 4px 0 12px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

            source_css_map = {
                "LinkedIn": "source-linkedin", "Indeed": "source-indeed",
                "Referral": "source-referral", "Job Portal": "source-portal",
                "Direct Apply": "source-direct"
            }

            for idx, cand in enumerate(filtered_sourced):
                row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns([1.5, 2.5, 1.5, 1.5, 1])

                css_cls = source_css_map.get(cand["source"], "badge badge-skill")
                with row_c1:
                    st.markdown(f'<span class="source-badge {css_cls}">{cand["source"]}</span>', unsafe_allow_html=True)
                with row_c2:
                    st.markdown(f"**{cand['name']}**<br><span style='font-size:12px; color:#9CA3AF;'>{cand['email']}</span>", unsafe_allow_html=True)
                with row_c3:
                    st.markdown(f"<span style='color:#9CA3AF;'>{cand['date_imported']}</span>", unsafe_allow_html=True)
                with row_c4:
                    st.markdown(f"<span class='badge badge-skill'>{cand['status']}</span>", unsafe_allow_html=True)
                with row_c5:
                    if st.button("View", key=f"view_src_{cand['id']}"):
                        st.info(f"**Candidate:** {cand['name']}\n**Skills:** {cand['skills']}\n**Experience:** {cand['experience']} yrs\n**Phone:** {cand['phone']}")

                st.markdown("<hr style='margin: 4px 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

        # ── Tab 2: Import Candidate Form ───────────────────────────────────────
        with tab_import:
            st.subheader("📥 Import New Sourced Candidate")
            st.markdown("Manually add a candidate lead from external sources.")

            with st.container(border=True):
                imp_c1, imp_c2 = st.columns(2)
                with imp_c1:
                    imp_name = st.text_input("Candidate Full Name *", placeholder="e.g. Vikramaditya Singh")
                    imp_email = st.text_input("Email Address *", placeholder="e.g. vikram@email.com")
                    imp_source = st.selectbox("Sourcing Channel *", ["LinkedIn", "Indeed", "Referral", "Job Portal", "Direct Apply"])
                with imp_c2:
                    imp_phone = st.text_input("Phone Number", placeholder="e.g. +91-9876543210")
                    imp_exp = st.number_input("Years of Experience", min_value=0, max_value=30, value=3)
                    imp_skills = st.text_input("Skills (comma-separated)", placeholder="e.g. Python, React, SQL")

                if st.button("📥 Import Candidate Now", type="primary", use_container_width=True):
                    if not imp_name.strip() or not imp_email.strip():
                        st.error("Please fill in candidate name and email.")
                    else:
                        new_sourced = {
                            "id": len(st.session_state.sourced_candidates) + 1,
                            "source": imp_source,
                            "name": imp_name.strip(),
                            "email": imp_email.strip(),
                            "phone": imp_phone.strip() if imp_phone.strip() else "N/A",
                            "skills": imp_skills.strip() if imp_skills.strip() else "General",
                            "experience": imp_exp,
                            "date_imported": date.today().strftime("%Y-%m-%d"),
                            "status": "New"
                        }
                        st.session_state.sourced_candidates.append(new_sourced)
                        st.toast(f"Candidate {imp_name} imported from {imp_source}!", icon="🎉")
                        time.sleep(0.4)
                        st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. REFERENCE & VERIFICATION UI
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Reference & Verification":
        st.title("🛡️ Candidate Reference & Verification")
        st.markdown("Verify reference checks, background credentials, and assess candidate risk profiles.")
        st.markdown("---")

        with st.spinner("Loading candidate profiles..."):
            cand_res = api_request("GET", "/candidates")
        candidates = cand_res.json() if (cand_res and cand_res.status_code == 200) else []

        if not candidates:
            candidates = [
                {"id": 1, "name": "Rahul Sharma", "email": "rahul@example.com"},
                {"id": 2, "name": "Priya Desai", "email": "priya@example.com"},
            ]

        cand_map = {f"{c['name']} ({c['email']})": c for c in candidates}
        selected_v_label = st.selectbox("Select Candidate to View Verification:", list(cand_map.keys()), key="verif_cand_sel")
        selected_v_cand = cand_map[selected_v_label]

        st.markdown(f"### Candidate Details → Verification: **{selected_v_cand['name']}**")
        st.markdown("<br>", unsafe_allow_html=True)

        # Verification Overview Cards
        v_col1, v_col2, v_col3 = st.columns(3)

        with v_col1:
            st.markdown("""
                <div class="verification-row">
                    <div>
                        <div class="verification-label">Reference Check</div>
                        <div style="font-size:12px; color:#CBD5E1; font-weight:600; margin-top:4px;">2/2 References Verified</div>
                    </div>
                    <span class="verification-status" style="background:#064E3B; color:#6EE7B7; border:1px solid #10B981;">Completed</span>
                </div>
            """, unsafe_allow_html=True)

        with v_col2:
            st.markdown("""
                <div class="verification-row">
                    <div>
                        <div class="verification-label">Background Check</div>
                        <div style="font-size:12px; color:#CBD5E1; font-weight:600; margin-top:4px;">Identity & Employment</div>
                    </div>
                    <span class="verification-status" style="background:#78350F; color:#FDE68A; border:1px solid #F59E0B;">In Progress</span>
                </div>
            """, unsafe_allow_html=True)

        with v_col3:
            st.markdown("""
                <div class="verification-row">
                    <div>
                        <div class="verification-label">Verification Risk</div>
                        <div style="font-size:12px; color:#CBD5E1; font-weight:600; margin-top:4px;">Overall Risk Rating</div>
                    </div>
                    <span class="risk-low">Low Risk</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabs for detailed verification results
        v_tab1, v_tab2, v_tab3 = st.tabs(["📞 Reference Check Details", "🔎 Background Check Report", "⚠️ Risk Factors & Analysis"])

        with v_tab1:
            st.subheader("📞 Professional Reference Checks")

            ref1, ref2 = st.columns(2)
            with ref1:
                with st.container(border=True):
                    st.markdown("#### Reference #1: Previous Manager")
                    st.write("**Name:** Rajesh Malhotra")
                    st.write("**Title:** VP of Engineering, TechCorp Solutions")
                    st.write("**Relationship:** Direct Manager (2022 - 2025)")
                    st.write("**Feedback:** *' Rahul was an outstanding software engineer. Consistently delivered complex projects on time and mentored junior team members. Highly recommend.'*")
                    st.success("✅ Rating: 5/5 Stars — Verified")

            with ref2:
                with st.container(border=True):
                    st.markdown("#### Reference #2: Peer / Lead")
                    st.write("**Name:** Ananya Sharma")
                    st.write("**Title:** Tech Lead, CloudStack Systems")
                    st.write("**Relationship:** Senior Teammate")
                    st.write("**Feedback:** *' Exceptional technical skills, great problem solver, and very easy to collaborate with.'*")
                    st.success("✅ Rating: 4.8/5 Stars — Verified")

        with v_tab2:
            st.subheader("🔎 Background Verification Report")
            st.caption("Verification performed via Checkr / InstantID Service Provider")

            bg_data = [
                {"Verification Check": "Identity & SSN/Aadhaar Trace", "Status": "Passed ✅", "Provider": "Checkr ID", "Timestamp": "2026-08-11"},
                {"Verification Check": "Highest Degree & Education", "Status": "Passed ✅", "Provider": "National Clearinghouse", "Timestamp": "2026-08-12"},
                {"Verification Check": "Past Employment (Last 5 Yrs)", "Status": "Passed ✅", "Provider": "WorkNumber API", "Timestamp": "2026-08-13"},
                {"Verification Check": "Criminal Background Check", "Status": "In Progress ⏳", "Provider": "Global Security Audit", "Timestamp": "2026-08-14"},
            ]
            st.table(bg_data)

        with v_tab3:
            st.subheader("⚠️ AI Verification Risk Matrix")

            rc1, rc2 = st.columns([1.2, 1])
            with rc1:
                st.markdown("""
                    <div class="factor-check">
                        <span class="factor-icon">✓</span>
                        <span><b>Identity Authenticity:</b> 100% Match on Government Identification</span>
                    </div>
                    <div class="factor-check">
                        <span class="factor-icon">✓</span>
                        <span><b>Employment History:</b> Dates match resume claims within 1 month accuracy</span>
                    </div>
                    <div class="factor-check">
                        <span class="factor-icon">✓</span>
                        <span><b>Degree Validation:</b> Accredited University degree confirmed</span>
                    </div>
                    <div class="factor-check">
                        <span class="factor-icon">✓</span>
                        <span><b>Reference Feedback Consistency:</b> Highly aligned with interview evaluation</span>
                    </div>
                """, unsafe_allow_html=True)

            with rc2:
                st.markdown("""
                    <div class="prediction-card">
                        <div class="prediction-header">Overall Risk Score</div>
                        <div class="prediction-value">4.2%</div>
                        <div style="font-size:13px; color:#9CA3AF; margin-top:8px;">
                            Very low risk profile. High confidence for offer issuance.
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. PREDICTIVE ANALYTICS DASHBOARD ⭐
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Predictive Analytics":
        st.title("⭐ Predictive Analytics & AI Hiring Predictions")
        st.markdown("AI-driven predictive hiring insights, retention probability modeling, and risk factors analysis.")
        st.markdown("---")

        with st.spinner("Loading predictive models..."):
            cand_res = api_request("GET", "/candidates")
        candidates = cand_res.json() if (cand_res and cand_res.status_code == 200) else []

        # Candidate Selector for prediction
        cand_map = {f"{c['name']} ({c['email']})": c for c in candidates} if candidates else {
            "Rahul Sharma (rahul@example.com)": {"name": "Rahul Sharma", "email": "rahul@example.com", "final_score": 87, "experience": 5},
            "Priya Desai (priya@example.com)": {"name": "Priya Desai", "email": "priya@example.com", "final_score": 76, "experience": 3},
        }

        col_ps1, col_ps2 = st.columns([2, 1])
        with col_ps1:
            sel_p_label = st.selectbox("🎯 Select Candidate for AI Hiring Prediction:", list(cand_map.keys()), key="predict_cand_sel")
            sel_p_cand = cand_map[sel_p_label]
        with col_ps2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption(f"Predictive Model: **HR-AI-v4.2** | Confidence: **94.8%**")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Section 1: AI Hiring Prediction Panel ─────────────────────────────
        st.subheader("🤖 AI Hiring Prediction")

        pred_c1, pred_c2, pred_c3 = st.columns(3)

        cand_score = sel_p_cand.get("final_score", 87)
        hiring_success = min(98, max(50, int(cand_score * 0.95 + 4)))
        retention_prob = min(95, max(45, int(cand_score * 0.88 + 8)))

        with pred_c1:
            st.markdown(f"""
                <div class="prediction-card">
                    <div class="prediction-header">Hiring Success</div>
                    <div class="prediction-value">{hiring_success}%</div>
                    <div style="font-size:13px; color:#9CA3AF; margin-top:8px;">Predicted performance success rate</div>
                </div>
            """, unsafe_allow_html=True)

        with pred_c2:
            st.markdown(f"""
                <div class="prediction-card">
                    <div class="prediction-header">Retention Probability</div>
                    <div class="prediction-value">{retention_prob}%</div>
                    <div style="font-size:13px; color:#9CA3AF; margin-top:8px;">Predicted 2-year retention likelihood</div>
                </div>
            """, unsafe_allow_html=True)

        with pred_c3:
            st.markdown(f"""
                <div class="prediction-card">
                    <div class="prediction-header">Risk Level</div>
                    <div style="margin: 12px 0;">
                        <span class="risk-low">LOW</span>
                    </div>
                    <div style="font-size:13px; color:#9CA3AF; margin-top:16px;">Minimal attrition & flight risk</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Section 2: Key Factors & AI Recommendation ────────────────────────
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            st.subheader("🔑 Key Factors")
            st.markdown("""
                <div class="factor-check">
                    <span class="factor-icon">✓</span>
                    <span><b>Strong skill match:</b> Exceeds core technical requirements by 15%</span>
                </div>
                <div class="factor-check">
                    <span class="factor-icon">✓</span>
                    <span><b>Relevant experience:</b> 5+ years in domain-aligned engineering roles</span>
                </div>
                <div class="factor-check">
                    <span class="factor-icon">✓</span>
                    <span><b>Good screening score:</b> Ranked top 10% in initial screening</span>
                </div>
                <div class="factor-check">
                    <span class="factor-icon">✓</span>
                    <span><b>High career stability:</b> Average tenure of 2.5 years per organization</span>
                </div>
            """, unsafe_allow_html=True)

        with col_f2:
            st.subheader("💡 AI Recommendation")
            st.markdown("""
                <div class="ai-rec-card">
                    <h3 style="margin:0; color:#34D399;">🌟 High Potential Candidate</h3>
                    <p style="color:#D1D5DB; margin-top:10px; font-size:15px; line-height:1.6;">
                        This candidate demonstrates <b>high potential for fast onboarding</b> and <b>long-term success</b> in the organization. Recommended for immediate offer release with senior mentoring track.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br><hr>", unsafe_allow_html=True)

        # ── Section 3: Hiring Predictions Report & Charts ─────────────────────
        st.subheader("📊 Hiring Predictions Report & Analytics")

        rep_c1, rep_c2 = st.columns(2)

        with rep_c1:
            st.markdown("#### 📈 Predicted Hiring Success Trend (6-Month Forecast)")
            months = ["Sep 2026", "Oct 2026", "Nov 2026", "Dec 2026", "Jan 2027", "Feb 2027"]
            trend_df = pd.DataFrame({
                "Month": months,
                "Success Rate (%)": [82, 85, 84, 88, 87, 91],
                "Benchmark (%)": [75, 75, 75, 75, 75, 75]
            })
            fig_trend = px.line(
                trend_df, x="Month", y=["Success Rate (%)", "Benchmark (%)"],
                markers=True, color_discrete_sequence=["#10B981", "#6B7280"]
            )
            fig_trend.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", height=280, margin=dict(t=10, b=10))
            st.plotly_chart(fig_trend, use_container_width=True)

        with rep_c2:
            st.markdown("#### 🎯 Score vs. Predicted Retention Probability")
            scatter_data = pd.DataFrame({
                "Match Score (%)": [87, 76, 92, 65, 84, 95, 58],
                "Retention Prob (%)": [81, 74, 90, 60, 83, 94, 52],
                "Candidate": ["Rahul", "Priya", "Amit", "Kavita", "Ravi", "Deepa", "Sanjay"]
            })
            fig_scat = px.scatter(
                scatter_data, x="Match Score (%)", y="Retention Prob (%)",
                text="Candidate", size="Match Score (%)", color="Retention Prob (%)",
                color_continuous_scale="Teal"
            )
            fig_scat.update_traces(textposition="top center")
            fig_scat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB", coloraxis_showscale=False, height=280, margin=dict(t=10, b=10))
            st.plotly_chart(fig_scat, use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # CANDIDATE PROFILE & STATUS PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "My Profile & Status":
        st.title("👤 My Candidate Portal")
        st.markdown("---")

        with st.spinner("Loading your profile..."):
            cand_res = api_request("GET", "/candidates")

        if cand_res is not None and cand_res.status_code == 200:
            candidates = cand_res.json()
            if not candidates:
                st.warning("⚠️ Profile Not Found: No resume has been uploaded for your account yet.")
                st.subheader("📤 Upload Your Resume")
                uploaded_file = st.file_uploader("Select resume file (PDF or TXT)", type=["pdf", "txt"])
                if uploaded_file is not None:
                    st.info(f"Selected file: **{uploaded_file.name}**")
                    if st.button("Extract and Save Resume", width="stretch"):
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                        with st.spinner("Processing your resume..."):
                            res = api_request("POST", "/upload_resume", files=files)
                            if res and res.status_code == 201:
                                st.success("🎉 Resume uploaded successfully!")
                                time.sleep(0.5)
                                st.rerun()
                            elif res:
                                st.error(f"Upload failed: {res.json().get('detail', 'Unknown error')}")
            else:
                candidate = candidates[0]

                # ── Journey Timeline ──────────────────────────────────────────
                st.subheader("🗺️ Your Recruitment Journey")
                render_journey_timeline(candidate.get("status", "Applied"))
                current_idx = STATUS_TO_STAGE_IDX.get(candidate.get("status", "Applied"), 0)
                st.progress((current_idx + 1) / len(JOURNEY_STAGES))
                st.caption(f"**Current Stage:** {JOURNEY_STAGES[current_idx][1].replace(chr(10), ' ')} — Status: **{candidate.get('status', 'Applied')}**")

                st.markdown("<br>", unsafe_allow_html=True)

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    with st.container(border=True):
                        st.subheader("📝 Profile Details")
                        st.write(f"**Name:** {candidate['name']}")
                        st.write(f"**Email:** {candidate['email']}")
                        st.write(f"**Phone:** {candidate.get('phone') or 'N/A'}")
                        st.write(f"**Location:** {candidate.get('location') or 'N/A'}")
                        st.write(f"**Experience:** {candidate['experience']} years")
                        st.write(f"**Education:** {candidate.get('education', 'N/A')}")
                        st.write(f"**Notice Period:** {candidate.get('notice_period') or 'N/A'}")
                        st.write(f"**Expected CTC:** {candidate.get('expected_ctc') or 'N/A'}")
                        st.markdown("**Skills:**")
                        st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in candidate.get("skills", [])]) or "None", unsafe_allow_html=True)

                with col_c2:
                    with st.container(border=True):
                        st.subheader("📊 Compatibility Scoring")
                        with st.spinner("Loading jobs..."):
                            job_res = api_request("GET", "/jobs")
                        if job_res is not None and job_res.status_code == 200:
                            jobs = job_res.json()
                            if not jobs:
                                st.info("No open job requirements available at the moment.")
                            else:
                                job_opts = {j["title"]: j["id"] for j in jobs}
                                selected_job_title = st.selectbox("Select Job Target", list(job_opts.keys()), key="candidate_job_target")
                                job_id = job_opts[selected_job_title]

                                if st.button("Check My Compatibility", width="stretch"):
                                    with st.spinner("Calculating..."):
                                        score_res = api_request("GET", f"/score?candidate_id={candidate['id']}&job_id={job_id}")
                                    if score_res and score_res.status_code == 200:
                                        score_data = score_res.json()
                                        match_score = score_data["match_score"]
                                        details = score_data["details"]

                                        fig_gauge = go.Figure(go.Indicator(
                                            mode="gauge+number", value=match_score,
                                            domain={"x": [0, 1], "y": [0, 1]},
                                            gauge={
                                                "axis": {"range": [None, 100]},
                                                "bar": {"color": "#4F46E5"},
                                                "bgcolor": "rgba(0,0,0,0)",
                                                "steps": [
                                                    {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                                                    {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                                                    {"range": [70, 100], "color": "rgba(16,185,129,0.15)"},
                                                ],
                                            },
                                        ))
                                        fig_gauge.update_layout(
                                            paper_bgcolor="rgba(0,0,0,0)", font_color="#E5E7EB",
                                            height=160, margin=dict(l=10, r=10, t=10, b=10)
                                        )
                                        st.plotly_chart(fig_gauge, width="stretch")

                                        col_s1, col_s2 = st.columns(2)
                                        with col_s1:
                                            st.markdown("✅ **Matched Skills**")
                                            if details["matched_skills"]:
                                                st.markdown(" ".join([f'<span class="badge badge-matched">{s}</span>' for s in details["matched_skills"]]), unsafe_allow_html=True)
                                            else:
                                                st.caption("None matched")
                                        with col_s2:
                                            st.markdown("❌ **Missing Skills**")
                                            if details["missing_skills"]:
                                                st.markdown(" ".join([f'<span class="badge badge-missing">{s}</span>' for s in details["missing_skills"]]), unsafe_allow_html=True)
                                            else:
                                                st.caption("None missing")

                                        gap = details["experience_gap"]
                                        if gap > 0:
                                            st.warning(f"⚠️ You lack **{gap} years** of experience for this role.")
                                        else:
                                            st.success("✅ You meet the experience requirement!")
                                    elif score_res:
                                        st.error("Failed to check compatibility score.")

    # ═══════════════════════════════════════════════════════════════════════════
    # AVAILABLE JOBS PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Available Jobs":
        st.title("💼 Open Job Opportunities")
        st.markdown("---")

        with st.spinner("Loading open positions..."):
            job_res = api_request("GET", "/jobs")

        if job_res is not None and job_res.status_code == 200:
            jobs = job_res.json()
            if not jobs:
                st.info("No open job opportunities at the moment. Check back later!")
            else:
                for j in jobs:
                    with st.container(border=True):
                        st.subheader(j["title"])
                        st.write(f"**Experience Required:** {j['experience_required']} years")
                        st.write(f"**Description:** {j['description']}")
                        st.markdown("**Key Requirements:**")
                        st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in j["requirements"]]) if j["requirements"] else "None", unsafe_allow_html=True)
