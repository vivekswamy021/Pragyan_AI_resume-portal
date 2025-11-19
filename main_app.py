# app.py

import streamlit as st
from admin_dashboard import admin_dashboard
from candidate_dashboard import candidate_dashboard
from hiring_dashboard import hiring_dashboard

# --- Utility Functions for Navigation and State Management ---

def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def initialize_session_state():
    """Initializes all necessary session state variables for the entire application."""
    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'user_type' not in st.session_state: st.session_state.user_type = None

    # Admin/Global Data
    if 'admin_jd_list' not in st.session_state: st.session_state.admin_jd_list = []
    if 'resumes_to_analyze' not in st.session_state: st.session_state.resumes_to_analyze = []
    if 'admin_match_results' not in st.session_state: st.session_state.admin_match_results = []
    if 'resume_statuses' not in st.session_state: st.session_state.resume_statuses = {}
    if 'vendors' not in st.session_state: st.session_state.vendors = []
    if 'vendor_statuses' not in st.session_state: st.session_state.vendor_statuses = {}
    
    # Candidate Data
    if "parsed" not in st.session_state: st.session_state.parsed = {} 
    if "full_text" not in st.session_state: st.session_state.full_text = ""
    if "excel_data" not in st.session_state: st.session_state.excel_data = None
    if "candidate_uploaded_resumes" not in st.session_state: st.session_state.candidate_uploaded_resumes = []
    if "pasted_cv_text" not in st.session_state: st.session_state.pasted_cv_text = ""
    if "current_parsing_source_name" not in st.session_state: st.session_state.current_parsing_source_name = None 
    
    if "candidate_jd_list" not in st.session_state: st.session_state.candidate_jd_list = []
    if "candidate_match_results" not in st.session_state: st.session_state.candidate_match_results = []
    if 'filtered_jds_display' not in st.session_state: st.session_state.filtered_jds_display = []
    if 'last_selected_skills' not in st.session_state: st.session_state.last_selected_skills = []
    if 'generated_cover_letter' not in st.session_state: st.session_state.generated_cover_letter = "" 
    if 'cl_jd_name' not in st.session_state: st.session_state.cl_jd_name = "" 

    # Hiring Manager Data (Placeholder)
    if 'hiring_jds' not in st.session_state: st.session_state.hiring_jds = []
    
def login_page():
    """Handles the user login and redirects to the appropriate dashboard."""
    st.title("Welcome to PragyanAI - Login")
    
    st.header("Login")
    st.info("Use **admin**, **candidate**, or **hiring** as username to test.")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password (Any value)", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            user = username.lower()
            if user == "candidate":
                st.session_state.logged_in = True
                st.session_state.user_type = "candidate"
                go_to("candidate_dashboard")
                st.success("Logged in as Candidate!")
                st.rerun()
            elif user == "admin":
                st.session_state.logged_in = True
                st.session_state.user_type = "admin"
                go_to("admin_dashboard")
                st.success("Logged in as Admin!")
                st.rerun()
            elif user == "hiring":
                st.session_state.logged_in = True
                st.session_state.user_type = "hiring"
                go_to("hiring_dashboard")
                st.success("Logged in as Hiring Manager!")
                st.rerun()
            else:
                st.error("Invalid username. Please use 'candidate', 'admin', or 'hiring'.")

# -------------------------
# MAIN EXECUTION BLOCK 
# -------------------------

if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="PragyanAI Multi-Dashboard")
    
    initialize_session_state()

    if st.session_state.logged_in:
        # Pass the go_to function to the dashboard for navigation
        if st.session_state.user_type == "admin":
            admin_dashboard(go_to)
        elif st.session_state.user_type == "candidate":
            candidate_dashboard(go_to)
        elif st.session_state.user_type == "hiring":
            hiring_dashboard(go_to)
        else:
            login_page()
    else:
        # Fallback to login if not logged in
        login_page()
