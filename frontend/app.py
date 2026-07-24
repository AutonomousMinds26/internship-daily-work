import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import time
from datetime import date

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
            background: rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            border-color: rgba(79, 70, 229, 0.4);
            box-shadow: 0 12px 40px 0 rgba(79, 70, 229, 0.2);
        }
        
        .metric-title {
            font-size: 14px;
            color: #8A8F98;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 36px;
            font-weight: 700;
            color: #4F46E5;
        }
        
        /* Profile cards */
        .profile-container {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 15px;
        }
        
        /* Badge styling */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }
        
        .badge-skill {
            background-color: rgba(79, 70, 229, 0.15);
            color: #818CF8;
            border: 1px solid rgba(79, 70, 229, 0.3);
        }
        
        .badge-matched {
            background-color: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .badge-missing {
            background-color: rgba(239, 68, 68, 0.15);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
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
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 12px;
            padding: 14px 20px;
            margin-bottom: 10px;
            transition: all 0.25s ease;
        }
        .rank-row:hover {
            background: rgba(79, 70, 229, 0.08);
            border-color: rgba(79, 70, 229, 0.3);
            transform: translateX(4px);
        }
        .rank-number {
            font-size: 22px;
            font-weight: 700;
            color: #6366F1;
            min-width: 32px;
        }
        .rank-name {
            font-size: 16px;
            font-weight: 600;
            color: #E5E7EB;
            flex: 1;
        }
        .rank-score {
            font-size: 20px;
            font-weight: 700;
        }
        .badge-shortlisted {
            background-color: rgba(16, 185, 129, 0.2);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 600;
        }
        .badge-maybe {
            background-color: rgba(245, 158, 11, 0.2);
            color: #FCD34D;
            border: 1px solid rgba(245, 158, 11, 0.4);
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 600;
        }
        .badge-reject {
            background-color: rgba(239, 68, 68, 0.2);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 600;
        }
        .detail-panel {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 14px;
            padding: 24px;
            margin-top: 8px;
        }
        .job-selector-box {
            background: rgba(79, 70, 229, 0.08);
            border: 1px solid rgba(79, 70, 229, 0.25);
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 24px;
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
            background: rgba(255,255,255,0.1);
            z-index: 0;
        }
        .timeline-step.completed::after {
            background: linear-gradient(90deg, #10B981, #10B981);
        }
        .timeline-step.active::after {
            background: linear-gradient(90deg, #3B82F6, rgba(255,255,255,0.1));
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
            background: rgba(16, 185, 129, 0.2);
            border-color: #10B981;
            color: #10B981;
        }
        .timeline-dot.active {
            background: rgba(59, 130, 246, 0.25);
            border-color: #3B82F6;
            color: #3B82F6;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.5);
        }
        .timeline-dot.pending {
            background: rgba(107, 114, 128, 0.1);
            border-color: rgba(107, 114, 128, 0.3);
            color: #6B7280;
        }
        .timeline-label {
            font-size: 11px;
            text-align: center;
            margin-top: 6px;
            line-height: 1.3;
        }
        .timeline-label.completed { color: #10B981; font-weight: 600; }
        .timeline-label.active { color: #3B82F6; font-weight: 700; }
        .timeline-label.pending { color: #6B7280; }

        /* Communication Buttons */
        .comm-btn-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 12px;
        }

        /* Interview card */
        .interview-card {
            background: rgba(79, 70, 229, 0.07);
            border: 1px solid rgba(79, 70, 229, 0.2);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 10px;
            transition: all 0.25s ease;
        }
        .interview-card:hover {
            border-color: rgba(79, 70, 229, 0.45);
            background: rgba(79, 70, 229, 0.12);
        }

        /* Platform pill */
        .platform-pill {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 600;
            background: rgba(139, 92, 246, 0.15);
            color: #A78BFA;
            border: 1px solid rgba(139, 92, 246, 0.3);
        }

        /* Pagination buttons */
        .pagination-info {
            text-align: center;
            color: #8A8F98;
            font-size: 14px;
            margin: 8px 0;
        }

        /* Funnel chart container */
        .funnel-section {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
            padding: 16px;
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
            if st.button("Log In", use_container_width=True):
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
    nav_options = ["Analytics Dashboard", "AI Ranking", "Candidates List", "Upload Resume", "Schedule Interview"]
    if st.session_state.role == "Admin":
        nav_options.append("Admin Settings")
    if st.session_state.role == "Candidate":
        nav_options = ["My Profile & Status", "Available Jobs"]

    choice = st.sidebar.radio("Navigation", nav_options)

    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYTICS DASHBOARD PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    if choice == "Analytics Dashboard":
        st.title("📊 Recruiter Analytics Dashboard")
        st.markdown("Real-time recruitment insights powered by your candidate pipeline.")
        st.markdown("---")

        with st.spinner("Loading dashboard data..."):
            cand_res = api_request("GET", "/candidate")
            job_res = api_request("GET", "/job")
            interview_res = api_request("GET", "/interview")

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
            st.plotly_chart(fig_bar, use_container_width=True)

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
                st.plotly_chart(fig_rec, use_container_width=True)
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
                    st.plotly_chart(fig_exp, use_container_width=True)

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
                    st.plotly_chart(fig_skills, use_container_width=True)
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
            st.plotly_chart(fig_funnel, use_container_width=True)

        # ── Row 3: Match Score Distribution (if ranking data available) ────────
        if st.session_state.get("ranking_results"):
            st.subheader("📈 Match Percentage Distribution")
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
            st.plotly_chart(fig_hist, use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # CANDIDATES LIST PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "Candidates List":
        st.title("👥 Candidate Pipeline Management")
        st.markdown("---")

        with st.spinner("Fetching candidate pipeline..."):
            cand_res = api_request("GET", "/candidate")
            job_res = api_request("GET", "/job")

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
                                                "PATCH", f"/candidate/{row['id']}/status",
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
                                                st.plotly_chart(fig_gauge, use_container_width=True)

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
                                        if st.button("⭐ Send Shortlist Email", key=f"shortlist_email_{row['id']}", use_container_width=True):
                                            with st.spinner("Sending shortlist email..."):
                                                r = api_request("POST", f"/communicate/shortlist/{row['id']}")
                                            if r and r.status_code == 200:
                                                data = r.json()
                                                st.success(f"✅ {data['message']}")
                                            elif r:
                                                st.error(f"❌ Failed: {r.json().get('detail', 'Unknown error')}")
                                    with comm_c2:
                                        if st.button("📅 Send Interview Invitation", key=f"interview_email_{row['id']}", use_container_width=True):
                                            with st.spinner("Sending interview invitation..."):
                                                r = api_request("POST", f"/communicate/interview/{row['id']}")
                                            if r and r.status_code == 200:
                                                data = r.json()
                                                st.success(f"✅ {data['message']}")
                                            elif r:
                                                st.error(f"❌ Failed: {r.json().get('detail', 'Unknown error')}")
                                    with comm_c3:
                                        if st.button("❌ Send Rejection Email", key=f"reject_email_{row['id']}", use_container_width=True):
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
    # AI RANKING PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "AI Ranking":
        st.title("🏆 AI Candidate Ranking")
        st.markdown("Automatically rank all candidates against a selected job role using AI match scores.")
        st.markdown("---")

        with st.spinner("Loading jobs and candidates..."):
            job_res = api_request("GET", "/job")
            cand_res = api_request("GET", "/candidate")

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

        if st.button("🚀 Rank All Candidates", use_container_width=True, type="primary"):
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
                        st.plotly_chart(fig_gauge, use_container_width=True)

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
        st.title("📅 Interview Scheduling")
        st.markdown("Schedule interviews for shortlisted candidates and track all upcoming sessions.")
        st.markdown("---")

        if st.session_state.role == "Candidate":
            st.warning("⛔ Access Restricted: Only Recruiters and Admins can schedule interviews.")
            st.stop()

        with st.spinner("Loading candidates and interviews..."):
            cand_res = api_request("GET", "/candidate")
            interview_res = api_request("GET", "/interview")

        candidates = cand_res.json() if (cand_res and cand_res.status_code == 200) else []
        interviews = interview_res.json() if (interview_res and interview_res.status_code == 200) else []

        sched_col, list_col = st.columns([1.1, 1])

        # ── Scheduling Form ────────────────────────────────────────────────────
        with sched_col:
            st.subheader("➕ Schedule New Interview")

            if not candidates:
                st.warning("No candidates found. Upload resumes first.")
            else:
                with st.container(border=True):
                    # Candidate dropdown: show shortlisted/interview status candidates first
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
                    platform = st.selectbox(
                        "💻 Platform *",
                        ["Google Meet", "Microsoft Teams", "Zoom"]
                    )
                    notes = st.text_area("📝 Notes (optional)", placeholder="Any special instructions or topics to cover...", height=80)

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📅 Schedule Interview", use_container_width=True, type="primary"):
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
                            with st.spinner("Scheduling interview..."):
                                res = api_request("POST", "/interview", json=payload)

                            if res and res.status_code == 201:
                                data = res.json()
                                st.success(f"🎉 Interview scheduled for **{data['candidate_name']}** on **{data['interview_date']}** at **{data['interview_time']}** via **{data['platform']}**!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            elif res:
                                err = res.json().get("detail", "Unknown error")
                                st.error(f"❌ Failed to schedule interview: {err}")

        # ── Interviews List ────────────────────────────────────────────────────
        with list_col:
            st.subheader(f"📋 All Interviews ({len(interviews)})")
            if not interviews:
                st.info("No interviews scheduled yet. Use the form to schedule one.")
            else:
                status_filter_iv = st.selectbox("Filter by Status", ["All", "Scheduled", "Completed", "Cancelled"], key="iv_status_filter")
                filtered_ivs = interviews if status_filter_iv == "All" else [iv for iv in interviews if iv["status"] == status_filter_iv]

                for iv in filtered_ivs:
                    status_colors_iv = {"Scheduled": "#3B82F6", "Completed": "#10B981", "Cancelled": "#EF4444"}
                    iv_color = status_colors_iv.get(iv["status"], "#6B7280")
                    pf_icon = platform_icon(iv["platform"])

                    st.markdown(f"""
                        <div class="interview-card">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <b style="color:#E5E7EB; font-size:15px;">👤 {iv['candidate_name']}</b>
                                <span style="background:{iv_color}20; color:{iv_color}; border:1px solid {iv_color}60; 
                                      padding:3px 10px; border-radius:50px; font-size:12px; font-weight:600;">
                                    {iv['status']}
                                </span>
                            </div>
                            <div style="color:#9CA3AF; font-size:13px; line-height:1.8;">
                                📆 <b>{iv['interview_date']}</b> at <b>{iv['interview_time']}</b><br>
                                👔 Interviewer: <b>{iv['interviewer_name']}</b><br>
                                {pf_icon} Platform: <span class="platform-pill">{iv['platform']}</span>
                            </div>
                            {f'<div style="color:#6B7280; font-size:12px; margin-top:6px;">📝 {iv["notes"]}</div>' if iv.get("notes") else ""}
                        </div>
                    """, unsafe_allow_html=True)

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
                job_res_up = api_request("GET", "/job")
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

                if st.button("Extract and Save Resume", use_container_width=True):
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
            st.button("Save Configuration", use_container_width=True)

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

            if st.button("Seed Default Jobs List", use_container_width=True):
                jobs_to_seed = [
                    {"title": "Senior FastAPI Developer", "description": "Develop robust FastAPI endpoints.", "requirements": ["Python", "FastAPI", "Docker", "PostgreSQL", "SQL"], "experience_required": 5},
                    {"title": "Machine Learning Engineer", "description": "Build high-throughput ML pipelines.", "requirements": ["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy"], "experience_required": 3},
                    {"title": "React Frontend Architect", "description": "Design modern dashboard templates.", "requirements": ["React", "JavaScript", "Docker", "Git"], "experience_required": 4},
                ]
                success_count = 0
                for job_data in jobs_to_seed:
                    res = api_request("POST", "/job", json=job_data)
                    if res and res.status_code == 201:
                        success_count += 1
                if success_count > 0:
                    st.success(f"Successfully seeded **{success_count}** job requirements!")
                else:
                    st.error("Failed to seed jobs. Check backend connection.")

    # ═══════════════════════════════════════════════════════════════════════════
    # CANDIDATE PROFILE & STATUS PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    elif choice == "My Profile & Status":
        st.title("👤 My Candidate Portal")
        st.markdown("---")

        with st.spinner("Loading your profile..."):
            cand_res = api_request("GET", "/candidate")

        if cand_res is not None and cand_res.status_code == 200:
            candidates = cand_res.json()
            if not candidates:
                st.warning("⚠️ Profile Not Found: No resume has been uploaded for your account yet.")
                st.subheader("📤 Upload Your Resume")
                uploaded_file = st.file_uploader("Select resume file (PDF or TXT)", type=["pdf", "txt"])
                if uploaded_file is not None:
                    st.info(f"Selected file: **{uploaded_file.name}**")
                    if st.button("Extract and Save Resume", use_container_width=True):
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
                            job_res = api_request("GET", "/job")
                        if job_res is not None and job_res.status_code == 200:
                            jobs = job_res.json()
                            if not jobs:
                                st.info("No open job requirements available at the moment.")
                            else:
                                job_opts = {j["title"]: j["id"] for j in jobs}
                                selected_job_title = st.selectbox("Select Job Target", list(job_opts.keys()), key="candidate_job_target")
                                job_id = job_opts[selected_job_title]

                                if st.button("Check My Compatibility", use_container_width=True):
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
                                        st.plotly_chart(fig_gauge, use_container_width=True)

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
            job_res = api_request("GET", "/job")

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
