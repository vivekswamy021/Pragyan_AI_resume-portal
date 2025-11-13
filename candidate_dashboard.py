import streamlit as st
import os
import pdfplumber
import docx
import openpyxl
import json
import tempfile
from groq import Groq
from gtts import gTTS 
import traceback
import re 
from dotenv import load_dotenv 
from datetime import date 
import csv 

# --- CRITICAL DEPENDENCIES: FUNCTIONS AND GLOBALS ---
# NOTE: These functions must be defined or imported for the candidate_dashboard to run.
# Since the full context is not provided here, assume these globals/functions exist 
# in the environment where this code is run. 
# Placeholder variables for setup:

GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_API_KEY = os.getenv('GROQ_API_KEY') # Assume this is loaded/mocked
question_section_options = ["skills","experience", "certifications", "projects", "education"] 
DEFAULT_JOB_TYPES = ["Full-time", "Contract", "Internship", "Remote", "Part-time"]
DEFAULT_ROLES = ["Software Engineer", "Data Scientist", "Product Manager", "HR Manager", "Marketing Specialist", "Operations Analyst"]

# Mock/Minimal implementation for required functions (Replace with actual implementations if needed)
def go_to(page_name): 
    st.session_state.page = page_name
def clear_interview_state():
    st.session_state.interview_qa = []
    st.session_state.iq_output = ""
    st.session_state.evaluation_report = ""
    st.toast("Practice answers cleared.")
def parse_and_store_resume(*args, **kwargs):
    # This function is complex and assumed to be defined externally,
    # it needs access to LLM and file I/O.
    # Placeholder implementation:
    return {"parsed": {}, "full_text": "Mock text", "excel_data": None, "name": "Mock Candidate"}
def extract_jd_metadata(*args, **kwargs):
    return {"role": "Mock Role", "job_type": "Mock Type", "key_skills": ["Mock Skill"]}
def extract_jd_from_linkedin_url(*args, **kwargs):
    return "Mock JD Content"
def extract_content(*args, **kwargs):
    return "Mock File Content"
def get_file_type(*args, **kwargs):
    return "txt"
def qa_on_jd(*args, **kwargs):
    return "Mock Answer about JD."
def qa_on_resume(*args, **kwargs):
    return "Mock Answer about Resume."
def evaluate_jd_fit(*args, **kwargs):
    return "Overall Fit Score: 7/10\n\n--- Section Match Analysis ---\nSkills Match: 70%\nExperience Match: 60%\nEducation Match: 80%\n\nStrengths/Matches:\n- Mock strength.\n\nGaps/Areas for Improvement:\n- Mock gap.\n\nOverall Summary: Good fit."
def generate_interview_questions(*args, **kwargs):
    return "[Generic]\nQ1: Tell me about yourself.\n[Basic]\nQ1: Why this job?"
def evaluate_interview_answers(*args, **kwargs):
    return "## Evaluation Results\n### Question 1: (Generic) Tell me about yourself.\nScore: 8/10\nFeedback:\n- Clarity & Accuracy: Good.\n- Gaps & Improvements: Add more quantifiable metrics.\n\n## Final Assessment\nTotal Score: 8/10\nOverall Summary: Good."
def generate_cv_html(parsed_data):
    # Simple mock for brevity
    return f"<html><body><h1>{parsed_data.get('name', 'CV')}</h1></body></html>"
# Assume client (Groq) is initialized or mocked
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# -------------------------
# UI Components (called by candidate_dashboard)
# -------------------------

def cv_management_tab_content():
    st.header("📝 Prepare Your CV")
    st.info("Form-based CV builder and parsed data preview/download.")

    # Simplified form logic for brevity in this excerpt
    if "cv_form_data" not in st.session_state:
        st.session_state.cv_form_data = {k: "" for k in ["name", "email", "phone", "linkedin", "github"]}
        st.session_state.cv_form_data.update({k: [] for k in ["skills", "experience", "education"]})
        st.session_state.cv_form_data['personal_details'] = ""
    
    with st.form("cv_builder_form_mock"):
        st.text_input("Full Name", key="cv_name_mock", value=st.session_state.cv_form_data['name'])
        st.text_area("Experience (One per Line)", key="cv_exp_mock", value="\n".join(st.session_state.cv_form_data.get('experience', [])))
        if st.form_submit_button("Generate and Load CV Data (Mock)"):
            st.session_state.parsed = {"name": st.session_state.cv_form_data['name'], "experience": st.session_state.cv_form_data.get('experience', [])}
            st.session_state.full_text = "Mock CV text."
            st.success("CV data loaded (Mock).")
            st.rerun()

    if st.session_state.get('parsed', {}).get('name'):
        st.subheader("Loaded CV Data Preview")
        st.json({"name": st.session_state.parsed.get('name'), "skills_count": len(st.session_state.parsed.get('skills', []))})
        st.download_button(
            label="⬇️ Download CV as HTML (Mock)",
            data=generate_cv_html(st.session_state.parsed),
            file_name="Mock_CV.html",
            mime="text/html",
            key="download_cv_html_mock"
        )
    else:
        st.info("No CV data loaded yet.")

def filter_jd_tab_content():
    st.header("🔍 Filter Job Descriptions by Criteria")
    st.info("Filter your saved JDs based on role, type, or skills.")
    if not st.session_state.get('candidate_jd_list'):
        st.info("No Job Descriptions are currently loaded. Please add JDs in the 'JD Management' tab.")
        return
    
    # Mock filtering logic
    unique_roles = sorted(list(set(
        [item.get('role', 'General Analyst') for item in st.session_state.candidate_jd_list] + DEFAULT_ROLES
    )))
    selected_role = st.selectbox("Role Title", options=["All Roles"] + unique_roles)
    
    if st.button("Apply Filters (Mock)"):
        st.session_state.filtered_jds_display = [
            jd for jd in st.session_state.candidate_jd_list 
            if selected_role == "All Roles" or selected_role == jd.get('role')
        ]
        st.success(f"Found {len(st.session_state.filtered_jds_display)} matching JDs (Mock).")
    
    if st.session_state.get('filtered_jds_display'):
        st.dataframe([
            {"Title": jd['name'], "Role": jd.get('role')} 
            for jd in st.session_state.filtered_jds_display
        ])
    else:
        st.info("Click 'Apply Filters' to see results.")

# -------------------------
# CORE FUNCTION: candidate_dashboard
# -------------------------

def candidate_dashboard():
    st.header("👩‍🎓 Candidate Dashboard")
    st.markdown("Welcome! Use the tabs below to manage your CV and access AI preparation tools.")

    # --- Navigation Block ---
    nav_col, _ = st.columns([1, 1]) 
    with nav_col:
        if st.button("🚪 Log Out", key="candidate_logout_btn", use_container_width=True):
            go_to("login") 
    
    # --- Sidebar for Status Only ---
    with st.sidebar:
        st.header("Resume/CV Status")
        if st.session_state.get('parsed', {}).get("name"):
            st.success(f"Currently loaded: **{st.session_state.parsed['name']}**")
        else:
            st.info("Please upload a file or use the CV builder to begin.")

    # 🚨🚨🚨 KEY EDITING AREA: TAB DEFINITIONS 🚨🚨🚨
    # If you want to add or remove a tab, edit this list.
    # The order below is: CV Mgmt, Parsing, JD Mgmt, Batch Match, Filter JD, Chatbot, Interview Prep
    tab_cv_mgmt, tab_parsing, tab_jd_mgmt, tab_batch_match, tab_filter_jd, tab_chatbot, tab_interview_prep = st.tabs([
        "✍️ CV Management", 
        "📄 Resume Parsing", 
        "📚 JD Management", 
        "🎯 Batch JD Match",
        "🔍 Filter JD",
        "💬 Resume/JD Chatbot (Q&A)", 
        "❓ Interview Prep"            
    ])
    # 🚨🚨🚨 END KEY EDITING AREA 🚨🚨🚨
    
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name')) or bool(st.session_state.get('full_text'))
    
    # --- TAB 1: CV Management (Calls separate function) ---
    with tab_cv_mgmt:
        cv_management_tab_content()

    # --- TAB 2: Resume Parsing (Input and LLM Parsing) ---
    with tab_parsing:
        st.header("Resume Upload and Parsing")
        
        input_method = st.radio("Select Input Method", ["Upload File", "Paste Text"], key="parsing_input_method")
        st.markdown("---")

        if input_method == "Upload File":
            uploaded_file = st.file_uploader( 
                "Choose PDF, DOCX, TXT, JSON, MD, CSV, XLSX file", 
                type=["pdf", "docx", "txt", "json", "md", "csv", "xlsx", "markdown", "rtf"], 
                key='candidate_file_upload_main'
            )
            if uploaded_file and st.button(f"Parse and Load: **{uploaded_file.name}**"):
                # Mock call: Replace with actual `parse_and_store_resume`
                result = parse_and_store_resume(uploaded_file, file_name_key='single_resume_candidate', source_type='file')
                if "error" not in result:
                    st.session_state.parsed = result['parsed']
                    st.session_state.full_text = result['full_text']
                    st.session_state.parsed['name'] = result['name'] 
                    clear_interview_state()
                    st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                else:
                    st.error(f"Parsing failed: {result['error']}")

        else: # Paste Text
            pasted_text = st.text_area(
                "Copy and paste your entire CV or resume text here.",
                height=300,
                key='pasted_cv_text_input'
            )
            if pasted_text.strip() and st.button("Parse and Load Pasted Text"):
                # Mock call: Replace with actual `parse_and_store_resume`
                result = parse_and_store_resume(pasted_text, file_name_key='single_resume_candidate', source_type='text')
                if "error" not in result:
                    st.session_state.parsed = result['parsed']
                    st.session_state.full_text = result['full_text']
                    st.session_state.parsed['name'] = result['name'] 
                    clear_interview_state()
                    st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                else:
                    st.error(f"Parsing failed: {result['error']}")

    # --- TAB 3: JD Management (Candidate) ---
    with tab_jd_mgmt:
        st.header("📚 Manage Job Descriptions for Matching")
        if "candidate_jd_list" not in st.session_state:
             st.session_state.candidate_jd_list = []
        
        # Simplified JD input for this excerpt
        jd_input = st.text_area("Paste a JD here to add it to the list.", key="jd_text_input_mock")
        if st.button("Add JD (Mock)"):
            if jd_input.strip():
                jd_name = jd_input.splitlines()[0][:30].strip() or f"JD {len(st.session_state.candidate_jd_list) + 1}"
                metadata = extract_jd_metadata(jd_input) # Mock call
                st.session_state.candidate_jd_list.append({"name": jd_name, "content": jd_input, **metadata})
                st.success(f"JD '{jd_name}' added (Mock).")
            st.rerun()

        if st.session_state.candidate_jd_list:
            st.markdown("### Current JDs Added:")
            st.dataframe([{"Name": jd['name'], "Role": jd.get('role')} for jd in st.session_state.candidate_jd_list])

    # --- TAB 4: Batch JD Match (Comparison) ---
    with tab_batch_match:
        st.header("🎯 Batch JD Match: Best Matches")
        if not is_resume_parsed:
            st.warning("Please load your resume first.")
        elif not st.session_state.get('candidate_jd_list'):
            st.error("Please add Job Descriptions first.")
        else:
            if st.button("Run Match Analysis (Mock)"):
                # Mock analysis logic
                st.session_state.candidate_match_results = []
                for jd_item in st.session_state.candidate_jd_list:
                    fit_output = evaluate_jd_fit(jd_item['content'], st.session_state.parsed) # Mock call
                    score_match = re.search(r'Overall Fit Score:\s*[^\d]*(\d+)\s*/10', fit_output)
                    score = score_match.group(1) if score_match else 'N/A'
                    st.session_state.candidate_match_results.append({
                        "jd_name": jd_item['name'],
                        "overall_score": score,
                        "rank": 1, # Mock rank
                        "full_analysis": fit_output
                    })
                st.session_state.candidate_match_results.sort(key=lambda x: x['overall_score'], reverse=True)
                st.success("Analysis complete (Mock).")
            
            if st.session_state.get('candidate_match_results'):
                st.dataframe([
                    {"Rank": item['rank'], "JD": item['jd_name'], "Score": item['overall_score']}
                    for item in st.session_state.candidate_match_results
                ])

    # --- TAB 5: Filter JD (Calls separate function) ---
    with tab_filter_jd:
        filter_jd_tab_content()

    # --- TAB 6: Resume/JD Chatbot (Q&A) (MOVED) ---
    with tab_chatbot:
        st.header("Resume/JD Chatbot (Q&A) 💬")
        
        sub_tab_resume, sub_tab_jd = st.tabs(["👤 Chat about Your Resume", "📄 Chat about Saved JDs"])
        
        with sub_tab_resume:
            if is_resume_parsed:
                question = st.text_input("Your Question (about Resume)", key="resume_qa_question_mock")
                if st.button("Get Answer (Resume)", key="qa_btn_resume_mock"):
                    answer = qa_on_resume(question) # Mock call
                    st.session_state.qa_answer_resume = answer
                if st.session_state.get('qa_answer_resume'):
                    st.text_area("Answer (Resume)", st.session_state.qa_answer_resume, height=100)
            else: st.warning("Load resume first.")
        
        with sub_tab_jd:
            if st.session_state.get('candidate_jd_list'):
                selected_jd_name = st.selectbox("Select JD", [jd['name'] for jd in st.session_state.candidate_jd_list])
                question = st.text_input("Your Question (about JD)", key="jd_qa_question_mock")
                if st.button("Get Answer (JD)", key="qa_btn_jd_mock"):
                    answer = qa_on_jd(question, selected_jd_name) # Mock call
                    st.session_state.qa_answer_jd = answer
                if st.session_state.get('qa_answer_jd'):
                    st.text_area("Answer (JD)", st.session_state.qa_answer_jd, height=100)
            else: st.warning("Add JDs first.")

    # --- TAB 7: Interview Prep (MOVED) ---
    with tab_interview_prep:
        st.header("❓ Interview Preparation Tools")
        if not is_resume_parsed:
            st.warning("Please load your resume first.")
        else:
            if 'interview_qa' not in st.session_state: st.session_state.interview_qa = []
            
            st.subheader("1. Generate Interview Questions")
            section_choice = st.selectbox("Select Section", question_section_options, key='iq_section_c_mock')
            
            if st.button("Generate Interview Questions (Mock)"):
                raw_questions_response = generate_interview_questions(st.session_state.parsed, section_choice) # Mock call
                q_list = [{"question": q.strip(), "answer": ""} for q in raw_questions_response.splitlines() if q.startswith('Q')]
                st.session_state.interview_qa = q_list
                st.success(f"Generated {len(q_list)} questions (Mock).")

            if st.session_state.get('interview_qa'):
                st.subheader("2. Practice and Record Answers")
                with st.form("interview_practice_form_mock"):
                    for i, qa_item in enumerate(st.session_state.interview_qa):
                        st.text_area(f"Q{i+1}: {qa_item['question']}", key=f'answer_q_{i}_mock', value=qa_item['answer'])
                    
                    if st.form_submit_button("Submit & Evaluate Answers (Mock)"):
                        report = evaluate_interview_answers(st.session_state.interview_qa, st.session_state.parsed) # Mock call
                        st.session_state.evaluation_report = report
                        st.success("Evaluation complete (Mock).")
                
                if st.session_state.get('evaluation_report'):
                    st.subheader("3. AI Evaluation Report")
                    st.markdown(st.session_state.evaluation_report)

# -------------------------
# EXAMPLE USAGE (for testing the function)
# -------------------------
if __name__ == '__main__':
    # Initialize necessary session state variables for standalone testing
    if 'page' not in st.session_state: st.session_state.page = "candidate_dashboard"
    if 'parsed' not in st.session_state: 
        st.session_state.parsed = {"name": "Test Candidate", "skills": ["Python", "SQL", "Streamlit"]}
    if 'full_text' not in st.session_state: st.session_state.full_text = "Full Resume Content."
    if 'candidate_jd_list' not in st.session_state: 
        st.session_state.candidate_jd_list = [
            {"name": "JD 1: Software Engineer", "content": "Need Python and Cloud.", "role": "Software Engineer"},
            {"name": "JD 2: Data Scientist", "content": "Need ML and SQL.", "role": "Data Scientist"}
        ]
    if 'candidate_match_results' not in st.session_state: st.session_state.candidate_match_results = []
    if 'filtered_jds_display' not in st.session_state: st.session_state.filtered_jds_display = []
    if 'cv_form_data' not in st.session_state: st.session_state.cv_form_data = {"name": "Test Candidate", "experience": ["3 years"], "skills": ["Python"]}
    if 'qa_answer_resume' not in st.session_state: st.session_state.qa_answer_resume = ""
    if 'qa_answer_jd' not in st.session_state: st.session_state.qa_answer_jd = ""

    # Call the dashboard function
    st.title("Standalone Candidate Dashboard Test")
    candidate_dashboard()
