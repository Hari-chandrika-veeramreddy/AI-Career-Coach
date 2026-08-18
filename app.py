import os
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="AI Career Coach – Adaptive Interview & Presentation Coach",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database Schema
from database.database import (
    init_db, create_user, authenticate_user,
    get_user_profile, get_user_latest_career_result
)
init_db()

# Load Custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Import Page Modules
from pages.resume import render_resume_page
from pages.interview import render_interview_page
from pages.presentation import render_presentation_page
from pages.dashboard import render_dashboard_page

# Navigation Page Names
PAGES = [
    "🏠 Home",
    "📄 Resume & Career Analysis",
    "🎯 Interview Coach",
    "🎤 Presentation Coach",
    "📊 Dashboard",
    "👤 Profile"
]

# Session State Initialization
if "user" not in st.session_state:
    st.session_state["user"] = None
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "🏠 Home"

def on_nav_change():
    """Callback when sidebar radio option is selected."""
    st.session_state["current_page"] = st.session_state["nav_radio_key"]

def rehydrate_user_state(user_id):
    """Re-hydrate user session state directly from SQLite upon login."""
    profile = get_user_profile(user_id)
    if profile:
        st.session_state["resume_skills"] = profile.get("extracted_skills", [])
        st.session_state["resume_text"] = profile.get("resume_text", "")

    latest_career = get_user_latest_career_result(user_id)
    if latest_career:
        st.session_state["job_match_result"] = {
            "match_percentage": latest_career["match_percentage"],
            "matched_skills": latest_career["matched_skills"],
            "missing_skills": latest_career["missing_skills"],
            "has_required_skills": True
        }
        st.session_state["career_recommendations"] = latest_career["recommended_careers"]

# Sidebar Navigation & Authentication
def render_sidebar():
    st.sidebar.markdown("# 🎓 AI Career Coach")
    st.sidebar.markdown("*Adaptive Career Readiness Platform*")
    st.sidebar.markdown("---")

    user = st.session_state.get("user")
    if user:
        st.sidebar.success(f"Logged in as **{user['name']}**\n\n({user['college']} - {user['branch']})")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            # Clear authentication session state without touching database
            st.session_state["user"] = None
            st.session_state["current_page"] = "🏠 Home"
            st.session_state.pop("resume_skills", None)
            st.session_state.pop("resume_text", None)
            st.session_state.pop("job_match_result", None)
            st.session_state.pop("career_recommendations", None)
            st.rerun()
    else:
        st.sidebar.info("Account Authentication")
        auth_mode = st.sidebar.radio("Account Action", ["🔐 Login", "📝 Register"], key="auth_action_radio")

        if auth_mode == "🔐 Login":
            with st.sidebar.form("login_form"):
                email = st.text_input("Email", placeholder="student@college.edu")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Login")
                
                if submit_login:
                    if not email or not password:
                        st.sidebar.error("Please enter email and password.")
                    else:
                        success, user_data, msg = authenticate_user(email, password)
                        if success:
                            st.session_state["user"] = user_data
                            rehydrate_user_state(user_data["id"])
                            st.session_state["current_page"] = "📊 Dashboard"
                            st.sidebar.success(msg)
                            st.rerun()
                        else:
                            st.sidebar.error(msg)

        elif auth_mode == "📝 Register":
            with st.sidebar.form("register_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                college = st.text_input("College / University")
                branch = st.text_input("Branch (e.g. CSE)")
                submit_reg = st.form_submit_button("Register")
                
                if submit_reg:
                    if not (name and email and password and college and branch):
                        st.sidebar.error("Please fill in all registration fields.")
                    else:
                        success, uid, msg = create_user(name, email, password, college, branch)
                        if success:
                            st.sidebar.success(msg + " You can now log in.")
                        else:
                            st.sidebar.error(msg)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Navigation")
    
    current_idx = PAGES.index(st.session_state["current_page"]) if st.session_state["current_page"] in PAGES else 0
    st.sidebar.radio(
        "Go to Page:",
        PAGES,
        index=current_idx,
        key="nav_radio_key",
        on_change=on_nav_change
    )

render_sidebar()

# Main Page Routing
curr_page = st.session_state.get("current_page", "🏠 Home")

if curr_page == "🏠 Home":
    st.markdown("""
    <div class="banner-card">
        <h1>🎓 AI Career Coach</h1>
        <p>Adaptive AI Platform for Student Placement Interviews, Resume Alignment, & Presentation Readiness</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🚀 Launch Platform Modules")
    st.write("Click any card below to launch an assessment module:")

    # 2x2 Responsive Grid to prevent squeezed text on mobile devices
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.markdown("""
        <div class="coach-card">
            <h3>📄 Resume & Career Analysis</h3>
            <p>Parses PDF/DOCX resumes, extracts technical skills using spaCy, and calculates job match & career paths.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Resume Analysis ➔", key="btn_goto_resume", use_container_width=True):
            st.session_state["current_page"] = "📄 Resume & Career Analysis"
            st.rerun()

    with row1_col2:
        st.markdown("""
        <div class="coach-card">
            <h3>🎯 Interview Coach</h3>
            <p>Dynamically adapts question difficulty based on NLP answer evaluation and acoustic speech feedback.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Mock Interview ➔", key="btn_goto_interview", use_container_width=True):
            st.session_state["current_page"] = "🎯 Interview Coach"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.markdown("""
        <div class="coach-card">
            <h3>🎤 Presentation Coach</h3>
            <p>Evaluates PPT slide density with python-pptx and speech delivery metrics using Faster-Whisper & Librosa.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Evaluate Presentation ➔", key="btn_goto_presentation", use_container_width=True):
            st.session_state["current_page"] = "🎤 Presentation Coach"
            st.rerun()

    with row2_col2:
        st.markdown("""
        <div class="coach-card">
            <h3>📊 Dashboard & History</h3>
            <p>Visualizes personal Career Readiness, performance trends, and isolated user history from SQLite.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View My Dashboard ➔", key="btn_goto_dashboard", use_container_width=True):
            st.session_state["current_page"] = "📊 Dashboard"
            st.rerun()

elif curr_page == "📄 Resume & Career Analysis":
    render_resume_page()

elif curr_page == "🎯 Interview Coach":
    render_interview_page()

elif curr_page == "🎤 Presentation Coach":
    render_presentation_page()

elif curr_page == "📊 Dashboard":
    render_dashboard_page()

elif curr_page == "👤 Profile":
    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in to view your profile details.")
    else:
        st.markdown(f"""
        <div class="banner-card">
            <h1>👤 Student Account Profile</h1>
            <p>Account details and registered credentials</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="coach-card">
            <h3>Account Details</h3>
            <p><b>Full Name:</b> {user['name']}</p>
            <p><b>Email:</b> {user['email']}</p>
            <p><b>College / University:</b> {user['college']}</p>
            <p><b>Branch:</b> {user['branch']}</p>
            <p><b>Member Since:</b> {user.get('created_at', 'Active')}</p>
        </div>
        """, unsafe_allow_html=True)