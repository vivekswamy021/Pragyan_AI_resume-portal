import streamlit as st
from admin_dashboard import admin_dashboard
from candidate_dashboard import candidate_dashboard
from hiring_dashboard import hiring_dashboard

# 🔥 SET YOUR LOGO HERE
LOGO_URL = "https://raw.githubusercontent.com/vivekswamy021/Pragyan_AI_resume/main/pragyan_ai_school_cover.jpg"

def show_logo(width=510):
    st.image(LOGO_URL, width=width)

def go_to(page_name):
    st.session_state.page = page_name

def initialize_session_state():
    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'user_type' not in st.session_state: st.session_state.user_type = None
    if 'user_email' not in st.session_state: st.session_state.user_email = "" 
    if 'user_name' not in st.session_state: st.session_state.user_name = ""
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {"profile_pic": None, "github_link": "", "linkedin_link": "", "password": "password123"}
    
    # Initialize all other data keys if they don't exist...
    # (Keeping your existing initialization logic here)

# --------------------------------------------------
# 🚪 LOGOUT HEADER COMPONENT
# --------------------------------------------------
def render_logout_header():
    """Renders the 'Logged in as' text and Log Out button as seen in your image."""
    st.write(f"Logged in as: **{st.session_state.user_type.capitalize()}**")
    if st.button("🚪 Log Out"):
        # Clear session and refresh
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.divider()

def render_profile_sidebar():
    with st.sidebar:
        st.header(f"👤 {st.session_state.user_name}")
        st.markdown(f"**Role:** {st.session_state.user_type.capitalize()}")
        st.divider()
        # ... (Your existing profile editing code) ...

# --------------------------------------------------
# LOGIN & SIGNUP PAGES (Standard)
# --------------------------------------------------
def login_page():
    show_logo()
    st.markdown("<h1>PragyanAI Job Portal</h1>", unsafe_allow_html=True)
    st.subheader("Login")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            role = st.selectbox("Select Role", ["Select Role", "Candidate", "Admin", "Hiring Manager"])
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if role != "Select Role" and email and password:
                    user_role = {"Candidate": "candidate", "Admin": "admin", "Hiring Manager": "hiring"}.get(role)
                    st.session_state.logged_in = True
                    st.session_state.user_type = user_role
                    st.session_state.user_email = email
                    st.session_state.user_name = email.split("@")[0].capitalize()
                    go_to(f"{user_role}_dashboard")
                    st.rerun()

def signup_page():
    show_logo()
    st.markdown("<h1>Create an Account</h1>", unsafe_allow_html=True)
    if st.button("Back to Login"):
        go_to("login")
        st.rerun()

# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------
if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="PragyanAI App")
    initialize_session_state()

    if st.session_state.logged_in:
        # 1. Show Profile Sidebar
        render_profile_sidebar()
        
        # 2. Show Logo
        show_logo()
        
        # 3. Show the Logout Button and "Logged in as" text (Matches your Image)
        render_logout_header()

        # 4. Route to the correct Dashboard
        if st.session_state.user_type == "admin":
            admin_dashboard(go_to)
        elif st.session_state.user_type == "candidate":
            candidate_dashboard(go_to)
        elif st.session_state.user_type == "hiring":
            hiring_dashboard(go_to)
    else:
        if st.session_state.page == "signup":
            signup_page()
        else:
            login_page()
