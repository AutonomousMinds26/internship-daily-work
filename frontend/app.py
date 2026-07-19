import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import time

# Page Configuration
st.set_page_config(
    page_title="RecruiterAI Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism theme)
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
    </style>
""", unsafe_allow_html=True)

# Environment and Session State Initialization
BACKEND_DEFAULT = os.getenv("BACKEND_API_URL", "http://localhost:8000")

if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Sidebar configuration
st.sidebar.title("💼 RecruiterAI")
api_url = st.sidebar.text_input("Backend API URL", value=BACKEND_DEFAULT, help="Change URL if backend runs elsewhere")

# Helper: Show unified backend API error message
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

# Helper: Make authenticated calls
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
    except Exception as e:
        handle_api_error(e, f"{method.upper()} to {endpoint}")
        return None

# AUTHENTICATION LOGIC
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
                
                # Call backend auth
                login_data = {"username": username, "password": password}
                try:
                    url = f"{api_url.rstrip('/')}/auth/token"
                    res = requests.post(url, data=login_data, timeout=5)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.username = username
                        
                        # Fetch current user role by decoding token payload or matching standard user names
                        # Standard roles based on username
                        if "admin" in username.lower():
                            st.session_state.role = "Admin"
                        elif "manager" in username.lower():
                            st.session_state.role = "Hiring Manager"
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

# Main Page Routing
if not st.session_state.token:
    login_ui()
else:
    # Sidebar logged in info
    st.sidebar.success(f"Logged in as: **{st.session_state.username}**")
    st.sidebar.info(f"Role: **{st.session_state.role}**")
    
    # Navigation list depending on role
    nav_options = ["Dashboard", "AI Ranking", "Candidates List", "Upload Resume"]
    if st.session_state.role == "Admin":
        nav_options.append("Admin Settings")
        
    choice = st.sidebar.radio("Navigation", nav_options)
    
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    # DASHBOARD PAGE
    if choice == "Dashboard":
        st.title("📊 Recruiter Insights Dashboard")
        st.markdown("---")
        
        # Load Candidates and Jobs from backend
        cand_res = api_request("GET", "/candidate")
        job_res = api_request("GET", "/job")
        
        if cand_res is not None and job_res is not None:
            if cand_res.status_code == 200 and job_res.status_code == 200:
                candidates = cand_res.json()
                jobs = job_res.json()
                
                df_candidates = pd.DataFrame(candidates)
                df_jobs = pd.DataFrame(jobs)
                
                # Compute Dashboard Stats
                total_cand = len(candidates)
                open_jobs = len(jobs)
                
                # Check status column exists
                if not df_candidates.empty and 'status' in df_candidates.columns:
                    shortlisted_cand = len(df_candidates[df_candidates['status'] == 'Shortlisted'])
                    interviews_scheduled = len(df_candidates[df_candidates['status'] == 'Interview'])
                    status_counts = df_candidates['status'].value_counts().to_dict()
                else:
                    shortlisted_cand = 0
                    interviews_scheduled = 0
                    status_counts = {}
                
                # Metrics Cards Grid
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">👤 Total Candidates</div>
                            <div class="metric-value">{total_cand}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">💼 Open Jobs</div>
                            <div class="metric-value">{open_jobs}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">⭐️ Shortlisted</div>
                            <div class="metric-value">{shortlisted_cand}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">📅 Interviews</div>
                            <div class="metric-value">{interviews_scheduled}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br><br>", unsafe_allow_html=True)
                
                # Visual Charts Section
                col_chart1, col_chart2 = st.columns([1.2, 1])
                with col_chart1:
                    st.subheader("📋 Candidate Status Distribution")
                    all_statuses = ["Applied", "Screening", "Shortlisted", "Interview", "Selected"]
                    status_data = {status: status_counts.get(status, 0) for status in all_statuses}
                    
                    df_status = pd.DataFrame(list(status_data.items()), columns=["Status", "Count"])
                    
                    # Create Plotly Bar Chart
                    fig_bar = px.bar(
                        df_status, 
                        x="Status", 
                        y="Count", 
                        color="Status",
                        color_discrete_map={
                            "Applied": "#6B7280",
                            "Screening": "#3B82F6",
                            "Shortlisted": "#F59E0B",
                            "Interview": "#8B5CF6",
                            "Selected": "#10B981"
                        },
                        text="Count"
                    )
                    fig_bar.update_layout(
                        showlegend=False, 
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#E5E7EB",
                        yaxis_title="Candidates Count"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with col_chart2:
                    st.subheader("💡 Experience Distribution")
                    if not df_candidates.empty:
                        fig_pie = px.pie(
                            df_candidates,
                            names="experience",
                            title="Candidates by Years of Experience",
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        fig_pie.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", 
                            font_color="#E5E7EB",
                            legend_title="Years"
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("No candidates uploaded yet to show experience stats.")
            else:
                st.error("Failed to load dashboard statistics from backend.")

    # CANDIDATES LIST PAGE
    elif choice == "Candidates List":
        st.title("👥 Candidate Pipeline Management")
        st.markdown("---")
        
        # Load Candidates and Jobs from backend
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
                    
                    # Filters bar
                    st.subheader("🔍 Filters")
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        search_q = st.text_input("Search Candidate by Name/Skills", "")
                    with col_f2:
                        status_filter = st.selectbox("Status Filter", ["All", "Applied", "Screening", "Shortlisted", "Interview", "Selected"])
                    with col_f3:
                        min_exp = st.number_input("Minimum Experience (Years)", min_value=0, max_value=30, value=0)
                    
                    # Apply filters
                    filtered_df = df
                    if search_q:
                        filtered_df = filtered_df[
                            filtered_df['name'].str.contains(search_q, case=False, na=False) |
                            filtered_df['skills'].apply(lambda skills: any(search_q.lower() in s.lower() for s in skills))
                        ]
                    if status_filter != "All":
                        filtered_df = filtered_df[filtered_df['status'] == status_filter]
                    filtered_df = filtered_df[filtered_df['experience'] >= min_exp]
                    
                    st.markdown(f"Showing **{len(filtered_df)}** candidates.")
                    
                    # Render candidates table
                    for index, row in filtered_df.iterrows():
                        with st.container():
                            st.markdown(f"""
                                <div class="profile-container">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <h4 style="margin: 0; color: #E5E7EB;">👤 {row['name']}</h4>
                                        <span class="badge" style="background-color: rgba(79, 70, 229, 0.2); color: #818CF8; border: 1px solid rgba(79, 70, 229, 0.4);">
                                            📍 {row['location'] or 'Not Specified'}
                                        </span>
                                    </div>
                                    <p style="margin: 5px 0; color: #9CA3AF; font-size: 14px;">
                                        📧 <b>Email:</b> {row['email']} | 📞 <b>Phone:</b> {row['phone'] or 'N/A'} | ⏳ <b>Exp:</b> {row['experience']} years
                                    </p>
                                    <div style="margin: 10px 0;">
                                        <b>Skills:</b> {' '.join([f'<span class="badge badge-skill">{s}</span>' for s in row['skills']]) if row['skills'] else 'None'}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Expandable candidate actions
                            with st.expander(f"Inspect profile & compatibility for {row['name']}", expanded=False):
                                col_d1, col_d2 = st.columns([1.2, 1])
                                
                                with col_d1:
                                    st.markdown("### Profile Summary")
                                    st.write(f"**Education:** {row['education']}")
                                    st.write(f"**Notice Period:** {row['notice_period'] or 'N/A'}")
                                    st.write(f"**Expected CTC:** {row['expected_ctc'] or 'N/A'}")
                                    
                                    # Status Update block
                                    st.markdown("---")
                                    st.markdown("#### Update Status")
                                    current_status = row['status']
                                    status_options = ["Applied", "Screening", "Shortlisted", "Interview", "Selected"]
                                    try:
                                        status_idx = status_options.index(current_status)
                                    except ValueError:
                                        status_idx = 0
                                        
                                    new_status = st.selectbox("Assign Status", status_options, index=status_idx, key=f"status_select_{row['id']}")
                                    
                                    if st.button("Update Status", key=f"update_btn_{row['id']}"):
                                        # Call API
                                        patch_res = api_request("PATCH", f"/candidate/{row['id']}/status", json={"status": new_status})
                                        if patch_res and patch_res.status_code == 200:
                                            st.toast(f"Successfully updated {row['name']} status to {new_status}!", icon="✅")
                                            time.sleep(0.5)
                                            st.rerun()
                                        elif patch_res:
                                            st.error(f"Failed to update status: {patch_res.json().get('detail', 'Unknown error')}")
                                
                                with col_d2:
                                    st.markdown("### Compatibility Scoring")
                                    if not jobs:
                                        st.warning("No jobs defined yet. Create a job first to test score calculation.")
                                    else:
                                        # Select Job
                                        job_opts = {j['title']: j['id'] for j in jobs}
                                        selected_job_title = st.selectbox("Select Job Target", list(job_opts.keys()), key=f"job_sel_{row['id']}")
                                        job_id = job_opts[selected_job_title]
                                        
                                        if st.button("Calculate Compatibility", key=f"calc_btn_{row['id']}"):
                                            # Call Score endpoint
                                            score_res = api_request("GET", f"/score?candidate_id={row['id']}&job_id={job_id}")
                                            if score_res and score_res.status_code == 200:
                                                score_data = score_res.json()
                                                match_score = score_data["match_score"]
                                                details = score_data["details"]
                                                
                                                # Gauge chart
                                                fig_gauge = go.Figure(go.Indicator(
                                                    mode = "gauge+number",
                                                    value = match_score,
                                                    domain = {'x': [0, 1], 'y': [0, 1]},
                                                    title = {'text': "Compatibility Score", 'font': {'size': 18}},
                                                    gauge = {
                                                        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                                                        'bar': {'color': "#4F46E5"},
                                                        'bgcolor': "rgba(0,0,0,0)",
                                                        'borderwidth': 2,
                                                        'bordercolor': "gray",
                                                        'steps': [
                                                            {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.15)'},
                                                            {'range': [40, 70], 'color': 'rgba(245, 158, 11, 0.15)'},
                                                            {'range': [70, 100], 'color': 'rgba(16, 185, 129, 0.15)'}
                                                        ]
                                                    }
                                                ))
                                                fig_gauge.update_layout(
                                                    paper_bgcolor="rgba(0,0,0,0)", 
                                                    font_color="#E5E7EB", 
                                                    height=180, 
                                                    margin=dict(l=10, r=10, t=40, b=10)
                                                )
                                                st.plotly_chart(fig_gauge, use_container_width=True)
                                                
                                                # Matched / Missing skills listing
                                                col_skills1, col_skills2 = st.columns(2)
                                                with col_skills1:
                                                    st.markdown("✅ **Matched Skills**")
                                                    if details["matched_skills"]:
                                                        st.markdown(" ".join([f'<span class="badge badge-matched">{s}</span>' for s in details["matched_skills"]]), unsafe_allow_html=True)
                                                    else:
                                                        st.caption("None matched")
                                                with col_skills2:
                                                    st.markdown("❌ **Missing Skills**")
                                                    if details["missing_skills"]:
                                                        st.markdown(" ".join([f'<span class="badge badge-missing">{s}</span>' for s in details["missing_skills"]]), unsafe_allow_html=True)
                                                    else:
                                                        st.caption("None missing")
                                                        
                                                # Experience gap info
                                                gap = details["experience_gap"]
                                                if gap > 0:
                                                    st.warning(f"⚠️ Experience gap detected: Candidate lacks **{gap} years** of experience for this role.")
                                                else:
                                                    st.success("✅ Experience requirements fully met!")
                                                    
                                            elif score_res:
                                                st.error(f"Scoring failed: {score_res.json().get('detail', 'Unknown error')}")
                                
                                # Full CV drawer
                                with st.container():
                                    st.markdown("### Raw Resume Text")
                                    st.text_area("Full Extracted text", value=row['resume_text'], height=200, disabled=True, key=f"raw_cv_{row['id']}")

    # AI RANKING PAGE
    elif choice == "AI Ranking":
        st.title("🏆 AI Candidate Ranking")
        st.markdown("Automatically rank all candidates against a selected job role using AI match scores.")
        st.markdown("---")

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

        # ── Job Role Selector ──────────────────────────────────────────────
        st.markdown('<div class="job-selector-box">', unsafe_allow_html=True)
        col_js1, col_js2 = st.columns([2, 1])
        with col_js1:
            st.markdown("### 🎯 Select Job Role")
            job_opts = {j["title"]: j["id"] for j in jobs}
            selected_job_title = st.selectbox(
                "Choose the job to rank candidates against:",
                list(job_opts.keys()),
                key="ranking_job_select"
            )
            job_id = job_opts[selected_job_title]
        with col_js2:
            st.markdown("<br>", unsafe_allow_html=True)
            selected_job_obj = next((j for j in jobs if j["id"] == job_id), None)
            if selected_job_obj:
                st.caption(f"**Required Experience:** {selected_job_obj.get('experience_required', 'N/A')} years")
                reqs = selected_job_obj.get('requirements', [])
                if reqs:
                    st.caption("**Required Skills:**")
                    st.markdown(" ".join([f'<span class="badge badge-skill">{r}</span>' for r in reqs]), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Rank All Candidates ────────────────────────────────────────────
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

        # ── Display Rankings ───────────────────────────────────────────────
        if st.session_state.get("ranking_results"):
            ranked = st.session_state["ranking_results"]
            job_title_display = st.session_state.get("ranking_job_title", selected_job_title)

            st.markdown(f"### 📋 Rankings for: **{job_title_display}**")

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
                else:
                    return "#F87171"

            # Summary stats row
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

            # Table header
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

                # Expandable detail panel
                with st.expander(f"View details for {cand['name']}", expanded=False):
                    st.markdown('<div class="detail-panel">', unsafe_allow_html=True)

                    d_col1, d_col2 = st.columns([1.3, 1])

                    with d_col1:
                        st.markdown(f"## 👤 {cand['name']}")
                        st.markdown(f"📧 **Email:** {cand['email']}")
                        if cand.get('phone'):
                            st.markdown(f"📞 **Phone:** {cand['phone']}")
                        if cand.get('location'):
                            st.markdown(f"📍 **Location:** {cand['location']}")
                        st.markdown(f"⏳ **Experience:** {cand['experience']} years")

                        st.markdown("---")
                        st.markdown("#### 🛠️ Skills")
                        if cand.get('skills'):
                            st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in cand['skills']]), unsafe_allow_html=True)
                        else:
                            st.caption("No skills extracted.")

                    with d_col2:
                        # Match gauge
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=score,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Match Score", 'font': {'size': 16}},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': color},
                                'bgcolor': "rgba(0,0,0,0)",
                                'steps': [
                                    {'range': [0, 40], 'color': 'rgba(239,68,68,0.1)'},
                                    {'range': [40, 70], 'color': 'rgba(245,158,11,0.1)'},
                                    {'range': [70, 100], 'color': 'rgba(16,185,129,0.1)'}
                                ]
                            }
                        ))
                        fig_gauge.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="#E5E7EB",
                            height=180,
                            margin=dict(l=10, r=10, t=40, b=10)
                        )
                        st.plotly_chart(fig_gauge, use_container_width=True)

                    st.markdown("---")
                    str_col, weak_col, rec_col = st.columns(3)

                    with str_col:
                        st.markdown("#### 💪 Strengths")
                        matched = details.get('matched_skills', [])
                        if matched:
                            for sk in matched:
                                st.markdown(f'<span class="badge badge-matched">✅ {sk}</span>', unsafe_allow_html=True)
                        else:
                            st.caption("No matching skills found.")

                    with weak_col:
                        st.markdown("#### ⚠️ Weaknesses")
                        missing = details.get('missing_skills', [])
                        if missing:
                            for sk in missing:
                                st.markdown(f'<span class="badge badge-missing">❌ {sk}</span>', unsafe_allow_html=True)
                        else:
                            st.caption("All required skills matched! 🎉")
                        gap = details.get('experience_gap', 0)
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

                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<hr style='margin: 4px 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    # UPLOAD RESUME PAGE
    elif choice == "Upload Resume":
        st.title("📤 Resume Intelligence Uploader")
        st.markdown("---")
        
        # Check permissions: Recruiter / Admin only
        if st.session_state.role not in ["Recruiter", "Admin"]:
            st.warning("⛔ Access Restricted: Only Recruiters and Admins can upload resumes.")
        else:
            # ── Job Role Selection ─────────────────────────────────────────
            job_res_up = api_request("GET", "/job")
            jobs_for_upload = []
            if job_res_up and job_res_up.status_code == 200:
                jobs_for_upload = job_res_up.json()

            st.markdown('<div class="job-selector-box">', unsafe_allow_html=True)
            st.markdown("### 🎯 Select Job Role")
            if not jobs_for_upload:
                st.warning("No job roles available. Ask an Admin to seed jobs first.")
                selected_upload_job = None
            else:
                upload_job_opts = {j["title"]: j["id"] for j in jobs_for_upload}
                selected_upload_job_title = st.selectbox(
                    "Which job are you hiring for?",
                    list(upload_job_opts.keys()),
                    key="upload_job_select"
                )
                selected_upload_job = upload_job_opts[selected_upload_job_title]
                st.caption(f"📌 Resumes will be matched against: **{selected_upload_job_title}**")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("""
                Upload resumes in **PDF** or **TXT** formats. The backend will automatically extract:
                - Basic profiles (Name, Email, Phone, Location)
                - Technical skills and educational details
                - Notice period and compensation expectations
            """)
            
            uploaded_file = st.file_uploader("Choose Files", type=["pdf", "txt"])
            
            if uploaded_file is not None:
                st.info(f"Selected file: **{uploaded_file.name}**")
                
                # Trigger button
                if st.button("Extract and Save Resume", use_container_width=True):
                    # Frontend validation: Invalid Resume type check
                    filename = uploaded_file.name.lower()
                    if not (filename.endswith(".pdf") or filename.endswith(".txt")):
                        st.markdown("""
                            <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                                <div class="error-header">❌ Invalid Resume format</div>
                                <p style="margin: 0; color: #F87171; font-size: 14px;">
                                    The selected file format is not supported. Please upload a valid document in <b>PDF</b> or <b>TXT</b> format.
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.stop()
                    
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                    
                    with st.spinner("Processing resume, performing entity extraction..."):
                        # Send to backend
                        res = api_request("POST", "/upload_resume", files=files)
                        
                        if res is not None:
                            if res.status_code == 201:
                                candidate = res.json()
                                st.success("🎉 Resume Uploaded and Processed Successfully!")
                                
                                # Preview profile
                                with st.container(border=True):
                                    st.subheader(f"👤 Candidate Extracted Profile: {candidate['name']}")
                                    col_p1, col_p2 = st.columns(2)
                                    with col_p1:
                                        st.write(f"**Email:** {candidate['email']}")
                                        st.write(f"**Phone:** {candidate['phone'] or 'N/A'}")
                                        st.write(f"**Location:** {candidate['location'] or 'N/A'}")
                                        st.write(f"**Experience:** {candidate['experience']} years")
                                    with col_p2:
                                        st.write(f"**Education:** {candidate['education']}")
                                        st.write(f"**Notice Period:** {candidate['notice_period'] or 'N/A'}")
                                        st.write(f"**Expected CTC:** {candidate['expected_ctc'] or 'N/A'}")
                                        st.write(f"**Initial Status:** :blue[{candidate['status']}]")
                                        
                                    st.markdown("**Extracted Skills:**")
                                    st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in candidate['skills']]) if candidate['skills'] else 'None', unsafe_allow_html=True)

                                # Auto-score against selected job if one is chosen
                                if selected_upload_job:
                                    st.markdown("---")
                                    with st.spinner("Calculating AI match score against selected job..."):
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
                                            sc2.metric("Matched Skills", len(auto_details.get('matched_skills', [])))
                                            sc3.metric("Missing Skills", len(auto_details.get('missing_skills', [])))
                                            rec_fn(f"**Recommendation:** {rec}")
                            
                            # Invalid Resume parsing error (HTTP 400)
                            elif res.status_code == 400:
                                detail = res.json().get("detail", "Failed parsing resume structure.")
                                st.markdown(f"""
                                    <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                                        <div class="error-header">❌ Invalid Resume</div>
                                        <p style="margin: 0; color: #F87171; font-size: 14px;">
                                            We were unable to extract details from the resume document.<br>
                                            <b>Detail:</b> {detail}
                                        </p>
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            # Server / API upload errors
                            else:
                                detail = res.json().get("detail", "Server returned unexpected error.")
                                st.markdown(f"""
                                    <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                                        <div class="error-header">🚨 Upload Failed</div>
                                        <p style="margin: 0; color: #F87171; font-size: 14px;">
                                            The backend server failed to process the upload request.<br>
                                            <b>HTTP Status:</b> {res.status_code}<br>
                                            <b>Detail:</b> {detail}
                                        </p>
                                    </div>
                                """, unsafe_allow_html=True)

    # ADMIN PAGE (UI MOCK ONLY FOR NOW)
    elif choice == "Admin Settings":
        st.title("⚙️ System Administration Settings")
        st.caption("UI Demonstration Panel (Actions Simulated)")
        st.markdown("---")
        
        # Grid layout
        col_ad1, col_ad2 = st.columns(2)
        
        with col_ad1:
            st.subheader("🤖 LLM Model Extraction Configuration")
            extraction_mode = st.radio("Resume Extraction Engine", ["Fast Hybrid (Regex + Local parser)", "Accurate LLM (OpenAI GPT-4o Mock)", "Semantic Embeddings (Mock)"])
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
            
            # Show list of seeded accounts
            accounts_data = [
                {"Username": "admin_user", "Role": "Admin", "Status": "Active"},
                {"Username": "recruiter_user", "Role": "Recruiter", "Status": "Active"},
                {"Username": "manager_user", "Role": "Hiring Manager", "Status": "Active"},
            ]
            st.table(accounts_data)
            
            if st.button("Seed Default Jobs List", use_container_width=True):
                # Call POST /job endpoints mock or real API calls to populate jobs
                jobs_to_seed = [
                    {
                        "title": "Senior FastAPI Developer",
                        "description": "Develop and maintain robust and secure FastAPI web endpoints.",
                        "requirements": ["Python", "FastAPI", "Docker", "PostgreSQL", "SQL"],
                        "experience_required": 5
                    },
                    {
                        "title": "Machine Learning Engineer",
                        "description": "Build high-throughput ML pipelines and models.",
                        "requirements": ["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy"],
                        "experience_required": 3
                    },
                    {
                        "title": "React Frontend Architect",
                        "description": "Design and build reactive, modern dashboard templates.",
                        "requirements": ["React", "JavaScript", "Docker", "Git"],
                        "experience_required": 4
                    }
                ]
                
                success_count = 0
                for job_data in jobs_to_seed:
                    res = api_request("POST", "/job", json=job_data)
                    if res and res.status_code == 201:
                        success_count += 1
                
                if success_count > 0:
                    st.success(f"Successfully seeded **{success_count}** jobs requirements!")
                else:
                    st.error("Failed to seed jobs. Check backend connection.")
