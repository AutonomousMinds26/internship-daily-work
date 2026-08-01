import streamlit as st
from typing import cast, Any
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

# Main Page Routing
if not st.session_state.token:
    login_ui()
else:
    # Sidebar logged in info
    st.sidebar.success(f"Logged in as: **{st.session_state.username}**")
    st.sidebar.info(f"Role: **{st.session_state.role}**")
    
    if st.session_state.role == "Candidate":
        nav_options = ["My Profile & Status", "Available Jobs"]
    else:
        nav_options = ["Dashboard", "AI Ranking", "Candidates List", "Schedule Interview", "Upload Resume"]
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
        
        with st.spinner("Fetching analytics statistics..."):
            analytics_res = api_request("GET", "/analytics")
            job_res = api_request("GET", "/job")
            
        if analytics_res is not None and analytics_res.status_code == 200:
            analytics = analytics_res.json()
            jobs = job_res.json() if job_res and job_res.status_code == 200 else []
            
            # Metrics Cards Grid
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">👤 Total Candidates</div>
                        <div class="metric-value">{analytics['total_candidates']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">⭐ Shortlisted</div>
                        <div class="metric-value">{analytics['shortlisted_candidates']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">❌ Rejected</div>
                        <div class="metric-value">{analytics['rejected_candidates']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📈 Avg Match %</div>
                        <div class="metric-value">{analytics['average_match_percentage']}%</div>
                    </div>
                """, unsafe_allow_html=True)
            with col5:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📅 Pending Interviews</div>
                        <div class="metric-value">{analytics['pending_interviews']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # Visual Charts Section - Row 1
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.subheader("📊 Match Percentage Distribution")
                match_scores = analytics.get("match_percentages", [])
                if match_scores:
                    df_dist = pd.DataFrame(match_scores, columns=["Match Score"])
                    fig_dist = px.histogram(
                        df_dist,
                        x="Match Score",
                        nbins=10,
                        title="Distribution of Candidate Match Scores",
                        color_discrete_sequence=["#4F46E5"],
                        labels={"Match Score": "Match Percentage (%)"}
                    )
                    fig_dist.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#E5E7EB",
                        yaxis_title="Count of Candidates"
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)
                else:
                    st.info("No compatibility matches recorded yet.")
                    
            with col_chart2:
                st.subheader("💡 Recommendation Count")
                recs_dict = analytics.get("recommendation_counts", {})
                # Remove empty/null keys
                recs_dict = {k: v for k, v in recs_dict.items() if k}
                if recs_dict:
                    df_recs = pd.DataFrame(list(recs_dict.items()), columns=["Recommendation", "Count"])
                    fig_pie = px.pie(
                        df_recs,
                        names="Recommendation",
                        values="Count",
                        title="AI Recommendations Breakdown",
                        hole=0.4,
                        color="Recommendation",
                        color_discrete_map={
                            "Shortlisted": "#10B981",
                            "Maybe": "#F59E0B",
                            "Reject": "#EF4444",
                            "Applied": "#6B7280"
                        }
                    )
                    fig_pie.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#E5E7EB"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No recommendations generated yet.")
            
            # Row 2
            st.markdown("<br>", unsafe_allow_html=True)
            col_chart3, col_chart4 = st.columns(2)
            with col_chart3:
                st.subheader("💪 Skills Distribution")
                skills_dict = analytics.get("skills_distribution", {})
                if skills_dict:
                    df_skills = pd.DataFrame(list(skills_dict.items()), columns=["Skill", "Count"]).sort_values(by="Count", ascending=True)
                    fig_skills = px.bar(
                        df_skills,
                        x="Count",
                        y="Skill",
                        orientation="h",
                        title="Top Candidate Skills (Top 15)",
                        color="Count",
                        color_continuous_scale="Viridis"
                    )
                    fig_skills.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#E5E7EB",
                        xaxis_title="Number of Candidates",
                        yaxis_title="Skill"
                    )
                    st.plotly_chart(fig_skills, use_container_width=True)
                else:
                    st.info("No candidate skills found.")
                    
            with col_chart4:
                st.subheader("🏁 Hiring Funnel")
                funnel_dict = analytics.get("hiring_funnel", {})
                if funnel_dict:
                    df_funnel = pd.DataFrame({
                        "Stage": list(funnel_dict.keys()),
                        "Count": list(funnel_dict.values())
                    })
                    fig_funnel = go.Figure(go.Funnel(
                        y=df_funnel["Stage"],
                        x=df_funnel["Count"],
                        textinfo="value+percent initial",
                        marker={"color": ["#6B7280", "#3B82F6", "#06B6D4", "#F59E0B", "#8B5CF6", "#10B981"]}
                    ))
                    fig_funnel.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#E5E7EB",
                        title="Recruitment Pipeline Funnel"
                    )
                    st.plotly_chart(fig_funnel, use_container_width=True)
                else:
                    st.info("Funnel data unavailable.")
        else:
            st.error("Failed to load dashboard statistics from backend.")

    # CANDIDATES LIST PAGE
    elif choice == "Candidates List":
        st.title("👥 Candidate Pipeline Management")
        st.markdown("---")
        
        # Load Candidates with Details and Jobs
        with st.spinner("Loading candidate pipeline..."):
            cand_res = api_request("GET", "/candidates-with-details")
            job_res = api_request("GET", "/job")
        
        if cand_res is not None and job_res is not None:
            if cand_res.status_code == 200 and job_res.status_code == 200:
                candidates = cand_res.json()
                jobs = job_res.json()
                
                if not candidates:
                    st.info("No candidates found in the database. Head to the Uploader page to add profiles!")
                else:
                    df = cast(Any, pd.DataFrame(candidates))
                    
                    # Search and Filters block
                    with st.container(border=True):
                        st.subheader("🔍 Search and Filter Candidates")
                        col_s1, col_s2 = st.columns([2, 1])
                        with col_s1:
                            search_q = st.text_input("Search Candidate by Name or Skills", "", placeholder="Enter candidate name or specific skill...")
                        with col_s2:
                            # Jobs filter
                            job_titles = ["All"] + [j['title'] for j in jobs]
                            job_filter = st.selectbox("Filter by Job Target", job_titles)
                            
                        col_f1, col_f2, col_f3 = st.columns(3)
                        with col_f1:
                            status_filter = st.selectbox("Filter by Status", ["All", "Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Rejected"])
                        with col_f2:
                            rec_filter = st.selectbox("Filter by AI Recommendation", ["All", "Shortlisted", "Maybe", "Reject", "Applied"])
                        with col_f3:
                            min_exp = st.number_input("Minimum Experience (Years)", min_value=0, max_value=30, value=0)
                            
                    # Sorting block
                    with st.container(border=True):
                        st.subheader("↕️ Sorting Options")
                        col_sort1, col_sort2 = st.columns(2)
                        with col_sort1:
                            sort_by = st.selectbox("Sort By", ["Match Percentage", "Experience", "Upload Date"])
                        with col_sort2:
                            sort_order = st.radio("Sort Order", ["Descending", "Ascending"], horizontal=True)

                    # Apply Search and Filters
                    filtered_df = df
                    
                    # 1. Search Query (Name or Skills)
                    if search_q:
                        q_lower = search_q.lower()
                        filtered_df = filtered_df[
                            filtered_df['name'].str.contains(q_lower, case=False, na=False) |
                            filtered_df['skills'].apply(lambda skills: any(q_lower in s.lower() for s in skills) if isinstance(skills, list) else False)
                        ]
                        
                    # 2. Job Filter
                    if job_filter != "All":
                        filtered_df = filtered_df[filtered_df['primary_job_title'] == job_filter]
                        
                    # 3. Status Filter
                    if status_filter != "All":
                        filtered_df = filtered_df[filtered_df['status'] == status_filter]
                        
                    # 4. Recommendation Filter
                    if rec_filter != "All":
                        filtered_df = filtered_df[filtered_df['recommendation'].str.contains(rec_filter, case=False, na=False)]
                        
                    # 5. Experience Filter
                    filtered_df = filtered_df[filtered_df['experience'] >= min_exp]
                    
                    # Apply Sorting
                    ascending = (sort_order == "Ascending")
                    if sort_by == "Match Percentage":
                        filtered_df = filtered_df.sort_values(by="match_percentage", ascending=ascending)
                    elif sort_by == "Experience":
                        filtered_df = filtered_df.sort_values(by="experience", ascending=ascending)
                    elif sort_by == "Upload Date":
                        filtered_df = filtered_df.sort_values(by="created_at", ascending=ascending, na_position="last")
                        
                    total_results = len(filtered_df)
                    st.write(f"Showing **{total_results}** candidates.")
                    
                    # Pagination block
                    col_page_size, col_page_num = st.columns([1, 2])
                    with col_page_size:
                        page_size = st.selectbox("Candidates per page", [5, 10, 20], index=0)
                        
                    total_pages = max(1, (total_results + page_size - 1) // page_size)
                    
                    if "cand_page" not in st.session_state:
                        st.session_state.cand_page = 1
                        
                    if st.session_state.cand_page > total_pages:
                        st.session_state.cand_page = 1
                        
                    with col_page_num:
                        with st.container(horizontal=True, horizontal_alignment="center"):
                            prev_disabled = st.session_state.cand_page <= 1
                            next_disabled = st.session_state.cand_page >= total_pages
                            
                            if st.button("⬅️ Previous", disabled=prev_disabled):
                                st.session_state.cand_page -= 1
                                st.rerun()
                                
                            st.write(f"Page **{st.session_state.cand_page}** of **{total_pages}**")
                            
                            if st.button("Next ➡️", disabled=next_disabled):
                                st.session_state.cand_page += 1
                                st.rerun()

                    # Slice dataframe for pagination
                    start_idx = (st.session_state.cand_page - 1) * page_size
                    end_idx = start_idx + page_size
                    paginated_df = filtered_df.iloc[start_idx:end_idx]
                    
                    # Render candidates table
                    for index, row in paginated_df.iterrows():
                        cand_id = row['id']
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
                                    <p style="margin: 5px 0; color: #9CA3AF; font-size: 14px;">
                                        💼 <b>Job Target:</b> {row['primary_job_title']} | 🎯 <b>Match Score:</b> {row['match_percentage']}% | 💡 <b>AI Recommendation:</b> {row['recommendation']}
                                    </p>
                                    <div style="margin: 10px 0;">
                                        <b>Skills:</b> {' '.join([f'<span class="badge badge-skill">{s}</span>' for s in row['skills']]) if row['skills'] else 'None'}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Expandable candidate actions
                            with st.expander(f"Inspect profile, journey timeline & communications for {row['name']}", expanded=False):
                                # Journey timeline
                                st.subheader("🎯 Application Journey Tracker")
                                
                                stages = [
                                    "Resume Uploaded",
                                    "Resume Parsed",
                                    "Job Matched",
                                    "Shortlisted",
                                    "Interview Scheduled",
                                    "Selected",
                                    "Offer Released"
                                ]
                                
                                status_mapping = {
                                    "Applied": 0,
                                    "Screening": 0,
                                    "Parsed": 1,
                                    "Matched": 2,
                                    "Shortlisted": 3,
                                    "Interview Scheduled": 4,
                                    "Interview": 4,
                                    "Selected": 5,
                                    "Offer Released": 6
                                }
                                current_status = row['status']
                                current_idx = status_mapping.get(current_status, 0)
                                
                                timeline_html = """
                                <div style="display: flex; justify-content: space-between; align-items: center; margin: 15px 0; padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); overflow-x: auto;">
                                """
                                for idx, stage in enumerate(stages):
                                    is_completed = idx < current_idx
                                    is_current = idx == current_idx
                                    
                                    if current_status == "Rejected" and idx == current_idx:
                                        icon = "❌"
                                        bg = "rgba(239, 68, 68, 0.2)"
                                        text = "#F87171"
                                        border = "rgba(239, 68, 68, 0.4)"
                                        stage_text = "Rejected"
                                    elif is_completed:
                                        icon = "✅"
                                        bg = "rgba(16, 185, 129, 0.15)"
                                        text = "#34D399"
                                        border = "rgba(16, 185, 129, 0.3)"
                                        stage_text = stage
                                    elif is_current:
                                        icon = "🔵"
                                        bg = "rgba(79, 70, 229, 0.2)"
                                        text = "#818CF8"
                                        border = "rgba(79, 70, 229, 0.5)"
                                        stage_text = stage
                                    else:
                                        icon = "⚪"
                                        bg = "rgba(255, 255, 255, 0.02)"
                                        text = "#6B7280"
                                        border = "rgba(255, 255, 255, 0.05)"
                                        stage_text = stage
                                        
                                    timeline_html += f"""
                                    <div style="flex: 1; min-width: 100px; text-align: center; padding: 6px; margin: 0 4px; background: {bg}; border: 1px solid {border}; border-radius: 6px; color: {text}; font-size: 11px; font-weight: 600;">
                                        <div style="font-size: 14px; margin-bottom: 2px;">{icon}</div>
                                        <div>{stage_text}</div>
                                    </div>
                                    """
                                    if idx < len(stages) - 1:
                                        line_color = "rgba(16, 185, 129, 0.5)" if idx < current_idx else "rgba(255, 255, 255, 0.1)"
                                        timeline_html += f"""
                                        <div style="flex: 0.1; height: 2px; min-width: 10px; background-color: {line_color}; margin: 0 -4px;"></div>
                                        """
                                timeline_html += "</div>"
                                st.markdown(timeline_html, unsafe_allow_html=True)
                                
                                st.markdown("---")
                                
                                col_d1, col_d2 = st.columns([1.2, 1])
                                
                                with col_d1:
                                    st.markdown("### Profile Summary")
                                    st.write(f"**Education:** {row['education']}")
                                    st.write(f"**Notice Period:** {row['notice_period'] or 'N/A'}")
                                    st.write(f"**Expected CTC:** {row['expected_ctc'] or 'N/A'}")
                                    
                                    # Status Update block
                                    st.markdown("---")
                                    st.markdown("#### Update Status Manually")
                                    status_options = ["Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Rejected"]
                                    try:
                                        status_idx = status_options.index(current_status)
                                    except ValueError:
                                        status_idx = 0
                                        
                                    new_status = st.selectbox("Assign Status", status_options, index=status_idx, key=f"status_select_{cand_id}")
                                    
                                    if st.button("Update Status", key=f"update_btn_{cand_id}"):
                                        with st.spinner("Updating status..."):
                                            patch_res = api_request("PATCH", f"/candidate/{cand_id}/status", json={"status": new_status})
                                        if patch_res and patch_res.status_code == 200:
                                            st.toast(f"Successfully updated status to {new_status}!", icon="✅")
                                            time.sleep(0.5)
                                            st.rerun()
                                        elif patch_res:
                                            st.error(f"Failed to update status: {patch_res.json().get('detail', 'Unknown error')}")
                                
                                with col_d2:
                                    st.markdown("### 📧 Candidate Communication")
                                    st.caption("Send recruitment updates to the candidate via Email.")
                                    
                                    email_subject = st.text_input("Custom Email Subject (Optional)", key=f"email_sub_{cand_id}")
                                    email_body = st.text_area("Custom Email Message (Optional)", key=f"email_body_{cand_id}")
                                    
                                    comm_col1, comm_col2, comm_col3 = st.columns(3)
                                    with comm_col1:
                                        if st.button("Send Shortlist", key=f"send_shortlist_{cand_id}", use_container_width=True):
                                            payload = {"candidate_id": cand_id}
                                            if email_subject: payload["subject"] = email_subject
                                            if email_body: payload["message"] = email_body
                                            
                                            with st.spinner("Sending shortlist email..."):
                                                mail_res = api_request("POST", "/send-shortlist", json=payload)
                                            if mail_res and mail_res.status_code == 200:
                                                st.success("✉️ Shortlist email sent successfully! Status updated to Shortlisted.")
                                                st.toast("Shortlist email sent!", icon="✉️")
                                                time.sleep(1.0)
                                                st.rerun()
                                            elif mail_res:
                                                st.error(f"Failed to send shortlist email: {mail_res.json().get('detail', 'Unknown error')}")
                                                
                                    with comm_col2:
                                        if st.button("Send Interview", key=f"send_invitation_{cand_id}", use_container_width=True):
                                            payload = {"candidate_id": cand_id}
                                            if email_subject: payload["subject"] = email_subject
                                            if email_body: payload["message"] = email_body
                                            
                                            with st.spinner("Sending interview invitation email..."):
                                                mail_res = api_request("POST", "/send-interview", json=payload)
                                            if mail_res and mail_res.status_code == 200:
                                                st.success("✉️ Interview invitation sent successfully!")
                                                st.toast("Interview email sent!", icon="✉️")
                                            elif mail_res:
                                                st.error(f"Failed to send interview invitation: {mail_res.json().get('detail', 'Unknown error')}")
                                                
                                    with comm_col3:
                                        if st.button("Send Rejection", key=f"send_rejection_{cand_id}", use_container_width=True):
                                            payload = {"candidate_id": cand_id}
                                            if email_subject: payload["subject"] = email_subject
                                            if email_body: payload["message"] = email_body
                                            
                                            with st.spinner("Sending rejection email..."):
                                                mail_res = api_request("POST", "/send-rejection", json=payload)
                                            if mail_res and mail_res.status_code == 200:
                                                st.success("✉️ Rejection email sent successfully! Status updated to Rejected.")
                                                st.toast("Rejection email sent!", icon="✉️")
                                                time.sleep(1.0)
                                                st.rerun()
                                            elif mail_res:
                                                st.error(f"Failed to send rejection email: {mail_res.json().get('detail', 'Unknown error')}")
                                                
                                    st.markdown("---")
                                    st.markdown("### Compatibility Check")
                                    if not jobs:
                                        st.caption("No jobs defined.")
                                    else:
                                        jobs_by_id = {j['id']: j for j in jobs}
                                        job_id = st.selectbox(
                                            "Job Target",
                                            list(jobs_by_id.keys()),
                                            format_func=lambda selected_id: f"{jobs_by_id[selected_id]['title']} (#{selected_id})",
                                            key=f"job_sel_{cand_id}"
                                        )
                                        
                                        if st.button("Run Compatibility Match", key=f"calc_btn_{cand_id}"):
                                            with st.spinner("Calculating compatibility..."):
                                                score_res = api_request("GET", f"/score?candidate_id={cand_id}&job_id={job_id}")
                                            if score_res and score_res.status_code == 200:
                                                score_data = score_res.json()
                                                match_score = score_data["match_score"]
                                                details = score_data["details"]
                                                
                                                fig_gauge = go.Figure(go.Indicator(
                                                    mode = "gauge+number",
                                                    value = match_score,
                                                    domain = {'x': [0, 1], 'y': [0, 1]},
                                                    title = {'text': "Compatibility Score", 'font': {'size': 16}},
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
                                                    height=160, 
                                                    margin=dict(l=10, r=10, t=30, b=10)
                                                )
                                                st.plotly_chart(fig_gauge, use_container_width=True)
                                                
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
                                                        
                                                gap = details["experience_gap"]
                                                if gap > 0:
                                                    st.warning(f"⚠️ Experience gap: Candidate lacks **{gap} years** of experience.")
                                                else:
                                                    st.success("✅ Experience requirements met!")
                                            elif score_res:
                                                st.error("Scoring failed.")
                                                
                                with st.container():
                                    st.markdown("### Raw Resume Text")
                                    st.text_area("Full Extracted text", value=row['resume_text'], height=150, disabled=True, key=f"raw_cv_{cand_id}")
            else:
                st.error("Failed to fetch candidate list.")

    # AI RANKING PAGE
    elif choice == "AI Ranking":
        st.title("AI candidate ranking")
        st.caption("Rank candidates against a selected job requirement.")

        job_res = api_request("GET", "/job")
        cand_res = api_request("GET", "/candidate")
        if job_res is None or cand_res is None:
            st.stop()
        if job_res.status_code != 200 or cand_res.status_code != 200:
            st.error("Failed to load candidates or jobs from the backend.")
            st.stop()

        jobs = job_res.json()
        candidates = cand_res.json()
        if not jobs:
            st.warning("No job roles are available. Create a job role first.")
            st.stop()
        if not candidates:
            st.info("No candidates are available to rank.")
            st.stop()

        def clear_ranking_results():
            st.session_state.pop("ranking_results", None)
            st.session_state.pop("ranking_job_title", None)
            st.session_state.pop("ranking_errors", None)

        jobs_by_id = {job["id"]: job for job in jobs}
        job_id = st.selectbox(
            "Job role",
            list(jobs_by_id),
            format_func=lambda selected_id: f"{jobs_by_id[selected_id]['title']} (#{selected_id})",
            key="ranking_job_select",
            on_change=clear_ranking_results,
        )
        selected_job_title = jobs_by_id[job_id]["title"]

        if st.button("Rank all candidates", type="primary"):
            ranked = []
            ranking_errors = []
            progress = st.progress(0, text="Scoring candidates...")
            for index, candidate in enumerate(candidates, start=1):
                score_res = api_request(
                    "GET", f"/score?candidate_id={candidate['id']}&job_id={job_id}"
                )
                if score_res is not None and score_res.status_code == 200:
                    score_data = score_res.json()
                    ranked.append(
                        {
                            "candidate": candidate,
                            "match_score": score_data["match_score"],
                            "details": score_data["details"],
                        }
                    )
                else:
                    detail = "No response from the scoring service."
                    if score_res is not None:
                        try:
                            detail = score_res.json().get(
                                "detail", f"HTTP {score_res.status_code}"
                            )
                        except ValueError:
                            detail = f"HTTP {score_res.status_code}"
                    ranking_errors.append(f"{candidate['name']}: {detail}")
                progress.progress(index / len(candidates), text=f"Scored {index}/{len(candidates)} candidates")
            progress.empty()
            st.session_state["ranking_results"] = sorted(
                ranked, key=lambda entry: entry["match_score"], reverse=True
            )
            st.session_state["ranking_job_title"] = selected_job_title
            st.session_state["ranking_errors"] = ranking_errors

        ranking_errors = st.session_state.get("ranking_errors", [])
        if ranking_errors:
            st.warning(
                f"{len(ranking_errors)} candidate(s) could not be scored and are excluded from the ranking."
            )
            with st.expander("View scoring errors"):
                st.write("\n".join(f"- {error}" for error in ranking_errors))

        ranked = st.session_state.get("ranking_results")
        if ranked:
            st.subheader(
                f"Rankings for {st.session_state.get('ranking_job_title', selected_job_title)}"
            )
            shortlisted = sum(entry["match_score"] >= 70 for entry in ranked)
            maybe = sum(40 <= entry["match_score"] < 70 for entry in ranked)
            rejected = len(ranked) - shortlisted - maybe
            total_col, shortlist_col, maybe_col, reject_col = st.columns(4)
            total_col.metric("Ranked", len(ranked))
            shortlist_col.metric("Shortlisted", shortlisted)
            maybe_col.metric("Maybe", maybe)
            reject_col.metric("Reject", rejected)

            for rank, entry in enumerate(ranked, start=1):
                candidate = entry["candidate"]
                score = entry["match_score"]
                recommendation = "Shortlisted" if score >= 70 else "Maybe" if score >= 40 else "Reject"
                st.markdown(f"**#{rank} {candidate['name']}** — {score}% · {recommendation}")
                with st.expander(f"View details for {candidate['name']}"):
                    st.write(f"Email: {candidate.get('email', 'N/A')}")
                    st.write(f"Experience: {candidate.get('experience', 'N/A')} years")
                    st.write("Matched skills:", ", ".join(entry["details"].get("matched_skills", [])) or "None")
                    st.write("Missing skills:", ", ".join(entry["details"].get("missing_skills", [])) or "None")
                    gap = entry["details"].get("experience_gap", 0)
                    if gap:
                        st.write(f"Experience gap: {gap} years")

    # UPLOAD RESUME PAGE
    elif choice == "Upload Resume":
        st.title("📤 Resume Intelligence Uploader")
        st.markdown("---")
        
        # Check permissions: Recruiter / Admin only
        if st.session_state.role not in ["Recruiter", "Admin"]:
            st.warning("⛔ Access Restricted: Only Recruiters and Admins can upload resumes.")
        else:
            # Load jobs to choose target job role
            job_res = api_request("GET", "/job")
            jobs = []
            if job_res is not None and job_res.status_code == 200:
                jobs = job_res.json()
            
            if not jobs:
                st.warning("⚠️ No Job Roles Available: Please create a Job Role first before uploading resumes.")
            else:
                st.markdown("""
                    Upload resumes in **PDF** or **TXT** formats. The backend will automatically extract candidate details and match them against the selected Job Role.
                """)
                
                jobs_by_id = {j['id']: j for j in jobs}
                job_id = st.selectbox(
                    "Select Target Job Role",
                    list(jobs_by_id.keys()),
                    format_func=lambda selected_id: f"{jobs_by_id[selected_id]['title']} (#{selected_id})"
                )
                
                uploaded_file = st.file_uploader("Select resume file", type=["pdf", "txt"])
                
                if uploaded_file is not None:
                    st.info(f"Selected file: **{uploaded_file.name}**")
                    
                    # Trigger button
                    if st.button("Extract and Match Resume", use_container_width=True):
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
                        
                        # Premium simulated progress bar during uploading and processing
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Stage 1: Uploading
                        status_text.info("📤 Step 1/4: Uploading resume file to server...")
                        time.sleep(0.3)
                        progress_bar.progress(25)
                        
                        # Stage 2: Extracting Text
                        status_text.info("📄 Step 2/4: Reading document content and extracting text...")
                        time.sleep(0.4)
                        progress_bar.progress(50)
                        
                        # Stage 3: Matching
                        status_text.info("🤖 Step 3/4: Invoking AI Matcher to score candidate compatibility...")
                        time.sleep(0.4)
                        progress_bar.progress(75)
                        
                        # Stage 4: Fetching API
                        status_text.info("💾 Step 4/4: Saving parsed data & generating match recommendation...")
                        
                        res = api_request("POST", f"/upload_resume?job_id={job_id}", files=files)
                        
                        progress_bar.progress(100)
                        if res is not None:
                            if res.status_code == 201:
                                match_result = res.json()
                                st.success("🎉 Resume Uploaded and Matched Successfully!")
                                
                                # Preview profile match
                                with st.container(border=True):
                                    st.subheader(f"👤 Candidate: {match_result['candidate']}")
                                    st.write(f"**Email:** {match_result['email']}")
                                    
                                    rec_val = match_result['recommendation']
                                    rec_color = "green" if "shortlist" in rec_val.lower() else "orange"
                                    st.write(f"**AI Recommendation:** :{rec_color}[{rec_val}]")
                                    
                                    match_pct = match_result['match_percentage']
                                    st.markdown(f"**AI Match Compatibility: {match_pct}%**")
                                    st.progress(match_pct / 100.0)
                                    
                                    col_skills1, col_skills2 = st.columns(2)
                                    with col_skills1:
                                        st.markdown("✅ **Matched Skills**")
                                        if match_result["matched_skills"]:
                                            st.markdown(" ".join([f'<span class="badge badge-matched">{s}</span>' for s in match_result["matched_skills"]]), unsafe_allow_html=True)
                                        else:
                                            st.caption("None matched")
                                    with col_skills2:
                                        st.markdown("❌ **Missing Skills**")
                                        if match_result["missing_skills"]:
                                            st.markdown(" ".join([f'<span class="badge badge-missing">{s}</span>' for s in match_result["missing_skills"]]), unsafe_allow_html=True)
                                        else:
                                            st.caption("None missing")
                                            
                                    st.markdown("---")
                                    col_sw1, col_sw2 = st.columns(2)
                                    with col_sw1:
                                        st.markdown("💪 **AI Identified Strengths**")
                                        if match_result.get("strengths"):
                                            for s in match_result["strengths"]:
                                                st.markdown(f"- {s}")
                                        else:
                                            st.caption("No strengths highlighted")
                                    with col_sw2:
                                        st.markdown("⚠️ **AI Identified Weaknesses / Gaps**")
                                        if match_result.get("weaknesses"):
                                            for w in match_result["weaknesses"]:
                                                st.markdown(f"- {w}")
                                        else:
                                            st.caption("No weaknesses highlighted")
                            
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

    # SCHEDULE INTERVIEW PAGE
    elif choice == "Schedule Interview":
        st.title("📅 Schedule Interview Panel")
        st.markdown("---")
        
        # Load Candidates and Jobs from backend
        with st.spinner("Fetching candidates and jobs..."):
            cand_res = api_request("GET", "/candidates-with-details")
            job_res = api_request("GET", "/job")
            
        if cand_res is not None and job_res is not None:
            if cand_res.status_code == 200 and job_res.status_code == 200:
                candidates = cand_res.json()
                jobs = job_res.json()
                
                # Filter candidates to "Shortlisted" candidates
                shortlisted_cands = [c for c in candidates if c.get("status") == "Shortlisted"]
                
                if not shortlisted_cands:
                    st.warning("⚠️ No Shortlisted Candidates: Currently, there are no candidates with status 'Shortlisted'. Please shortlist candidates first.")
                    st.info("You can shortlist candidates via the 'Candidates List' page using the 'Send Shortlist' button or updating their status manually.")
                    
                    # Fallback option to allow scheduling for other candidates
                    show_all = st.checkbox("Show all candidates as fallback")
                    if show_all:
                        shortlisted_cands = candidates
                    else:
                        st.stop()
                        
                # Create dropdown of candidates
                cand_opts = {c['name']: c for c in shortlisted_cands}
                selected_cand_name = st.selectbox("Candidate Name", list(cand_opts.keys()))
                selected_candidate = cand_opts[selected_cand_name]
                
                st.info(f"Scheduling interview for **{selected_candidate['name']}** (Current Status: **{selected_candidate['status']}**).")
                
                # Fields
                col_field1, col_field2 = st.columns(2)
                with col_field1:
                    interview_date = st.date_input("Interview Date")
                with col_field2:
                    interview_time = st.time_input("Interview Time")
                    
                col_field3, col_field4 = st.columns(2)
                with col_field3:
                    interviewer_name = st.text_input("Interviewer Name", placeholder="Enter interviewer full name...")
                with col_field4:
                    interviewer_email = st.text_input("Interviewer Email", placeholder="Enter interviewer email address...")
                    
                col_field5, col_field6 = st.columns(2)
                with col_field5:
                    platform = st.selectbox("Platform", ["Google Meet", "Microsoft Teams", "Zoom"])
                with col_field6:
                    meeting_link = st.text_input("Meeting Link (Autofilled / Editable)", placeholder="Generated meeting link...")
                    
                # Prefill meeting link based on platform
                # If meeting_link is empty, automatically prefill it when platform changes
                import uuid
                mock_id = str(uuid.uuid4())[:8]
                if not meeting_link:
                    if platform == "Google Meet":
                        meeting_link = f"https://meet.google.com/abc-{mock_id}-xyz"
                    elif platform == "Microsoft Teams":
                        meeting_link = f"https://teams.microsoft.com/l/meetup-join/19%3ameeting_{mock_id}%40thread.v2/0"
                    elif platform == "Zoom":
                        meeting_link = f"https://zoom.us/j/{uuid.uuid4().fields[0]}"
                        
                notes = st.text_area("Notes / Special Instructions (Optional)")
                
                if st.button("Schedule Interview", type="primary", use_container_width=True):
                    if not interviewer_name or not interviewer_email:
                        st.warning("Please fill out both Interviewer Name and Interviewer Email.")
                        st.stop()
                        
                    # Find candidate's matched job ID
                    job_id = selected_candidate.get("primary_job_id")
                    if not job_id:
                        if jobs:
                            job_id = jobs[0]['id']
                            st.caption(f"No specific job match found in Candidate record. Defaulting to job: **{jobs[0]['title']}**")
                        else:
                            st.error("No Job Requirements defined in database. Cannot schedule interview without a job.")
                            st.stop()
                            
                    # Construct datetime ISO string
                    import datetime
                    combined_dt = datetime.datetime.combine(interview_date, interview_time)
                    scheduled_time_str = combined_dt.isoformat()
                    
                    # Call POST /interview
                    payload = {
                        "candidate_id": selected_candidate['id'],
                        "job_id": job_id,
                        "interviewer_name": interviewer_name,
                        "interviewer_email": interviewer_email,
                        "scheduled_time": scheduled_time_str,
                        "duration_minutes": 45,
                        "mode": "Online",
                        "meeting_link": meeting_link,
                        "notes": notes
                    }
                    
                    with st.spinner("Registering interview and updating candidate status..."):
                        sch_res = api_request("POST", "/interview", json=payload)
                        
                    if sch_res is not None:
                        if sch_res.status_code == 201:
                            st.success(f"🎉 Interview successfully scheduled for **{selected_candidate['name']}** on **{interview_date}** at **{interview_time}**!")
                            st.info(f"Platform: **{platform}** | Link: [Join Interview]({meeting_link})")
                            st.toast("Interview scheduled successfully!", icon="🎉")
                            time.sleep(1.0)
                            st.rerun()
                        else:
                            st.error(f"Failed to schedule interview: {sch_res.json().get('detail', 'Unknown error')}")
            else:
                st.error("Failed to load candidates/jobs for scheduling.")

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

    # CANDIDATE PROFILE & STATUS PAGE
    elif choice == "My Profile & Status":
        st.title("👤 My Candidate Portal")
        st.markdown("---")
        
        # Load Candidate record
        cand_res = api_request("GET", "/candidate")
        if cand_res is not None and cand_res.status_code == 200:
            candidates = cand_res.json()
            if not candidates:
                st.warning("⚠️ Profile Not Found: No resume details matching your account have been uploaded yet. Please upload your resume or contact a Recruiter.")
                
                # Let Candidate upload their own resume if it doesn't exist
                st.subheader("📤 Upload Your Resume")
                uploaded_file = st.file_uploader("Select resume file (PDF or TXT)", type=["pdf", "txt"])
                if uploaded_file is not None:
                    st.info(f"Selected file: **{uploaded_file.name}**")
                    if st.button("Extract and Save Resume", use_container_width=True):
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                        with st.spinner("Processing your resume..."):
                            res = api_request("POST", "/upload_resume", files=files)
                            if res and res.status_code == 201:
                                st.success("🎉 Resume uploaded successfully! Rerunning...")
                                time.sleep(0.5)
                                st.rerun()
                            elif res:
                                st.error(f"Upload failed: {res.json().get('detail', 'Unknown error')}")
            else:
                candidate = candidates[0]
                
                # Visual Application Journey Tracker
                st.subheader("🎯 Application Journey Tracker")
                status = candidate.get("status", "Applied")
                
                stages = [
                    "Resume Uploaded",
                    "Resume Parsed",
                    "Job Matched",
                    "Shortlisted",
                    "Interview Scheduled",
                    "Selected",
                    "Offer Released"
                ]
                
                status_mapping = {
                    "Applied": 0,
                    "Screening": 0,
                    "Parsed": 1,
                    "Matched": 2,
                    "Shortlisted": 3,
                    "Interview Scheduled": 4,
                    "Interview": 4,
                    "Selected": 5,
                    "Offer Released": 6
                }
                current_idx = status_mapping.get(status, 0)
                
                # Render visual timeline using html/css
                timeline_html = """
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 15px 0; padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); overflow-x: auto;">
                """
                for idx, stage in enumerate(stages):
                    is_completed = idx < current_idx
                    is_current = idx == current_idx
                    
                    if status == "Rejected" and idx == current_idx:
                        icon = "❌"
                        bg = "rgba(239, 68, 68, 0.2)"
                        text = "#F87171"
                        border = "rgba(239, 68, 68, 0.4)"
                        stage_text = "Rejected"
                    elif is_completed:
                        icon = "✅"
                        bg = "rgba(16, 185, 129, 0.15)"
                        text = "#34D399"
                        border = "rgba(16, 185, 129, 0.3)"
                        stage_text = stage
                    elif is_current:
                        icon = "🔵"
                        bg = "rgba(79, 70, 229, 0.2)"
                        text = "#818CF8"
                        border = "rgba(79, 70, 229, 0.5)"
                        stage_text = stage
                    else:
                        icon = "⚪"
                        bg = "rgba(255, 255, 255, 0.02)"
                        text = "#6B7280"
                        border = "rgba(255, 255, 255, 0.05)"
                        stage_text = stage
                        
                    timeline_html += f"""
                    <div style="flex: 1; min-width: 100px; text-align: center; padding: 6px; margin: 0 4px; background: {bg}; border: 1px solid {border}; border-radius: 6px; color: {text}; font-size: 11px; font-weight: 600;">
                        <div style="font-size: 14px; margin-bottom: 2px;">{icon}</div>
                        <div>{stage_text}</div>
                    </div>
                    """
                    if idx < len(stages) - 1:
                        line_color = "rgba(16, 185, 129, 0.5)" if idx < current_idx else "rgba(255, 255, 255, 0.1)"
                        timeline_html += f"""
                        <div style="flex: 0.1; height: 2px; min-width: 10px; background-color: {line_color}; margin: 0 -4px;"></div>
                        """
                timeline_html += "</div>"
                st.markdown(timeline_html, unsafe_allow_html=True)
                st.progress((current_idx + 1) / len(stages))
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    with st.container(border=True):
                        st.subheader("📝 Profile Details")
                        st.write(f"**Name:** {candidate['name']}")
                        st.write(f"**Email:** {candidate['email']}")
                        st.write(f"**Phone:** {candidate['phone'] or 'N/A'}")
                        st.write(f"**Location:** {candidate['location'] or 'N/A'}")
                        st.write(f"**Experience:** {candidate['experience']} years")
                        st.write(f"**Education:** {candidate['education']}")
                        st.write(f"**Notice Period:** {candidate['notice_period'] or 'N/A'}")
                        st.write(f"**Expected CTC:** {candidate['expected_ctc'] or 'N/A'}")
                        st.markdown("**Skills:**")
                        st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in candidate['skills']]) if candidate['skills'] else 'None', unsafe_allow_html=True)
                
                with col_c2:
                    with st.container(border=True):
                        st.subheader("📊 Compatibility Scoring")
                        job_res = api_request("GET", "/job")
                        if job_res is not None and job_res.status_code == 200:
                            jobs = job_res.json()
                            if not jobs:
                                st.info("No open job requirements available at the moment.")
                            else:
                                jobs_by_id = {j['id']: j for j in jobs}
                                job_id = st.selectbox(
                                    "Select Job Target",
                                    list(jobs_by_id.keys()),
                                    format_func=lambda selected_id: f"{jobs_by_id[selected_id]['title']} (#{selected_id})",
                                    key="candidate_job_target"
                                )
                                
                                if st.button("Check My Compatibility", use_container_width=True):
                                    score_res = api_request("GET", f"/score?candidate_id={candidate['id']}&job_id={job_id}")
                                    if score_res and score_res.status_code == 200:
                                        score_data = score_res.json()
                                        match_score = score_data["match_score"]
                                        details = score_data["details"]
                                        
                                        # Gauge chart
                                        fig_gauge = go.Figure(go.Indicator(
                                            mode = "gauge+number",
                                            value = match_score,
                                            domain = {'x': [0, 1], 'y': [0, 1]},
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
                                            height=160, 
                                            margin=dict(l=10, r=10, t=10, b=10)
                                        )
                                        st.plotly_chart(fig_gauge, use_container_width=True)
                                        
                                        # Matched / Missing skills listing
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
                                                
                                        # Experience gap info
                                        gap = details["experience_gap"]
                                        if gap > 0:
                                            st.warning(f"⚠️ You lack **{gap} years** of experience for this role.")
                                        else:
                                            st.success("✅ You meet the experience requirement!")
                                    elif score_res:
                                        st.error("Failed to check compatibility score.")

    # AVAILABLE JOBS PAGE
    elif choice == "Available Jobs":
        st.title("💼 Open Job Opportunities")
        st.markdown("---")
        
        job_res = api_request("GET", "/job")
        if job_res is not None and job_res.status_code == 200:
            jobs = job_res.json()
            if not jobs:
                st.info("No open job opportunities at the moment. Check back later!")
            else:
                for j in jobs:
                    with st.container(border=True):
                        st.subheader(j['title'])
                        st.write(f"**Experience Required:** {j['experience_required']} years")
                        st.write(f"**Description:** {j['description']}")
                        st.markdown("**Key Requirements:**")
                        st.markdown(" ".join([f'<span class="badge badge-skill">{s}</span>' for s in j['requirements']]) if j['requirements'] else 'None', unsafe_allow_html=True)
