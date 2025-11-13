import streamlit as st
import os
import re
import tempfile
import traceback
import json
from groq import Groq
from io import BytesIO
import pandas as pd

# --- 1. CONFIGURATION AND INITIAL SETUP ---

# Check for API Key (REQUIRED for all AI functions)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 
if not GROQ_API_KEY:
    # Use a dummy key if not set, but warn the user.
    # Deployment in Streamlit Cloud requires setting this as a Secret.
    GROQ_API_KEY = "DUMMY_KEY_FOR_LOCAL_TESTING" 
    st.warning("GROQ_API_KEY is not set in environment variables/secrets. AI functions will use a placeholder or fail.")

# Set page configuration
st.set_page_config(
    page_title="AI Resume Manager & Interview Prep (Candidate)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global variables (replace with real content extraction libraries if available)
question_section_options = ["Personal Details", "Experience", "Education", "Skills", "Projects", "Summary"]

# --- 2. SESSION STATE MANAGEMENT ---

def initialize_session_state():
    """Initializes all necessary session state variables."""
    if 'page' not in st.session_state:
        st.session_state.page = "candidate_dashboard" # Set directly to dashboard for simplicity
    
    # Core Resume Data
    if 'parsed' not in st.session_state: 
        st.session_state.parsed = {} # Parsed JSON output
    if 'full_text' not in st.session_state: 
        st.session_state.full_text = "" # Extracted raw text
    if 'excel_data' not in st.session_state: 
        st.session_state.excel_data = None # Data for Excel/CSV export
    
    # Resume Upload/Input
    if 'candidate_uploaded_resumes' not in st.session_state: 
        st.session_state.candidate_uploaded_resumes = []
    if 'pasted_cv_text' not in st.session_state:
        st.session_state.pasted_cv_text = ""
        
    # JD Management (Candidate)
    if 'candidate_jd_list' not in st.session_state:
         st.session_state.candidate_jd_list = []
    if 'candidate_match_results' not in st.session_state:
        st.session_state.candidate_match_results = []
    if 'filtered_jds_display' not in st.session_state: 
        st.session_state.filtered_jds_display = []
        
    # Interview Prep State
    if 'iq_output' not in st.session_state: st.session_state.iq_output = ""
    if 'interview_qa' not in st.session_state: st.session_state.interview_qa = [] 
    if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = "" 


def go_to(page_name):
    """Simple page navigation helper."""
    st.session_state.page = page_name

def clear_interview_state():
    """Clears interview prep data."""
    st.session_state.iq_output = ""
    st.session_state.interview_qa = []
    st.session_state.evaluation_report = ""

# --- 3. HELPER/PLACEHOLDER FUNCTIONS (MOCKING REAL FUNCTIONALITY) ---

def get_file_type(file_path):
    """Mocks file type detection."""
    return os.path.splitext(file_path)[1].lower().replace('.', '')

def extract_content(file_type, file_input):
    """Mocks content extraction from various file types."""
    if file_type in ["pdf", "docx", "txt", "md", "markdown", "rtf"]:
        # MOCK: In a real app, this would use libraries like 'pdfminer.six' or 'python-docx'
        if isinstance(file_input, str) and os.path.exists(file_input): # File path
            with open(file_input, 'r', encoding='utf-8') as f:
                return f"--- Content extracted from {os.path.basename(file_input)} --- \n" + f.read()
        elif isinstance(file_input, bytes): # Byte content from Streamlit Upload
            return f"--- Content extracted from Bytes (Type: {file_type}) --- \nSample Text..."
        elif isinstance(file_input, str): # Pasted text
            return file_input
        else: # Streamlit UploadedFile object
            return f"--- Content extracted from UploadedFile (Type: {file_type}) --- \nSample Text: {file_input.name}"
            
    elif file_type in ["json", "csv", "xlsx"]:
        return f"[Error] Cannot parse structured data types like {file_type} for text content."
    else:
        return f"[Error] Unsupported file type: {file_type}"


def parse_and_store_resume(file_input, file_name_key, source_type):
    """
    Mocks the AI parsing process.
    In a real app, this would call Groq/OpenAI to structure the text.
    """
    if GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
        st.error("AI functionality is disabled because GROQ_API_KEY is missing. Using mock data.")
        
        # Determine name
        if source_type == 'file':
            name = file_input.name
            full_text = extract_content(get_file_type(name), file_input)
        else:
            name = "Pasted CV Text"
            full_text = file_input
            
        # Mock successful parsing result
        mock_parsed_data = {
            "name": name,
            "contact": {"email": "mock@example.com", "phone": "123-456-7890"},
            "summary": "Mock Candidate with 5 years experience in Streamlit and AI.",
            "experience": [{"title": "AI Developer", "company": "MockTech", "duration": "5 Years"}],
            "skills": ["Python", "Streamlit", "Groq", "LLMs"],
            "education": [{"degree": "M.Sc. AI", "institution": "Mock University"}],
            "projects": ["Project Alpha", "Project Beta"],
            "achievements": ["Mock Award"]
        }
        
        # Mock Excel/CSV data structure
        mock_excel_data = pd.DataFrame([
            {"Section": k, "Content": str(v)} for k, v in mock_parsed_data.items()
        ])
        
        return {
            "parsed": mock_parsed_data,
            "full_text": full_text,
            "excel_data": mock_excel_data,
            "name": name
        }

    # --- Real AI Logic (If key exists) ---
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # 1. Get raw text
        if source_type == 'file':
            file_name = file_input.name
            # Need to save to temp file for file-based extraction libraries
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, file_name)
            with open(temp_path, "wb") as f:
                f.write(file_input.getbuffer())
            
            full_text = extract_content(get_file_type(temp_path), temp_path)
            os.remove(temp_path)
            os.rmdir(temp_dir)
            
        else:
            file_name = "Pasted CV Text"
            full_text = file_input
        
        if full_text.startswith("[Error]"):
            raise ValueError(full_text)

        # 2. Call Groq for structured JSON parsing (MOCK PROMPT)
        system_prompt = f"""You are a world-class resume parser. Analyze the following CV text and extract the information into a single, clean JSON object. 
        The JSON must strictly follow this schema: {{name: str, contact: {{email: str, phone: str}}, summary: str, experience: list[dict], skills: list[str], education: list[dict], projects: list[str]}}. 
        Return ONLY the JSON object. Do not add any extra commentary or Markdown formatting.
        CV Text: {full_text[:3000]}...""" # Truncate for efficiency

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Parse the provided CV text."}
            ],
            temperature=0.0
        )
        
        raw_json_str = completion.choices[0].message.content.strip()
        
        # Attempt to clean and load JSON (often needed for direct LLM output)
        match = re.search(r'\{.*\}', raw_json_str, re.DOTALL)
        if match:
            parsed_data = json.loads(match.group(0))
        else:
            parsed_data = json.loads(raw_json_str) # Last resort
            
        # Create Excel data (MOCK/SIMPLIFIED)
        excel_data = pd.DataFrame([
            {"Section": k, "Content": str(v)} for k, v in parsed_data.items()
        ])

        return {
            "parsed": parsed_data,
            "full_text": full_text,
            "excel_data": excel_data,
            "name": file_name
        }

    except Exception as e:
        return {
            "error": f"AI Parsing Failed. Ensure the text is readable and the GROQ_API_KEY is correct. Details: {e}",
            "full_text": full_text if 'full_text' in locals() else "",
            "name": file_name if 'file_name' in locals() else "Unknown File"
        }

def extract_jd_from_linkedin_url(url):
    """Mocks LinkedIn JD extraction."""
    if GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
        return f"--- Simulated JD for: {url} ---\nThis is a mock JD for a Senior AI Developer. Key skills include Python, Streamlit, Groq, and 5+ years of relevant experience. Please set your GROQ_API_KEY for real extraction."
    try:
        # In a real app, this would use a web scraper/proxy.
        # Here, we use Groq to simulate/generate a JD based on the URL context.
        client = Groq(api_key=GROQ_API_KEY)
        
        prompt = f"Analyze this job URL: {url} and write a realistic job description (JD) including role, requirements, skills, and company summary. Start the JD with a clear title."

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        
        return f"--- Simulated JD for: {url} ---\n" + completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error] JD Extraction from URL failed: {e}"

def extract_jd_metadata(jd_text):
    """Uses AI to extract key metadata from the JD text."""
    if GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
        return {"role": "Mock Developer", "job_type": "Full-Time", "key_skills": ["Mock", "Data"]}
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        system_prompt = """Analyze the following Job Description (JD) and extract key metadata into a JSON object. 
        The JSON must strictly follow this schema: {"role": str, "job_type": str, "key_skills": list[str]}. 
        - Role: The main job title.
        - Job Type: Full-Time, Part-Time, Contract, etc.
        - Key Skills: Top 5-10 technical skills mentioned.
        Return ONLY the JSON object. Do not add any extra commentary or Markdown formatting.
        """
        
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"JD Text: {jd_text[:2000]}..."}
            ],
            temperature=0.0
        )
        
        raw_json_str = completion.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', raw_json_str, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return json.loads(raw_json_str) 

    except Exception as e:
        return {"role": "N/A (Error)", "job_type": "N/A", "key_skills": ["Error", str(e)]}

def evaluate_jd_fit(jd_content, parsed_json):
    """Uses AI to evaluate the resume fit against a JD."""
    if GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
        return f"Overall Fit Score: 7/10\n\n--- Section Match Analysis ---\nSkills Match: 75%\nExperience Match: 70%\nEducation Match: 80%\n\nStrengths/Matches:\n- Matches mock skills like Python and Streamlit.\n\nWeaknesses/Gaps:\n- Lacks real-world experience details.\n\nRecommendation:\n- Add more specific metrics to experience descriptions. (Mock Analysis)"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        system_prompt = """You are an expert resume analyst. Your task is to compare a candidate's structured resume data against a Job Description (JD) and provide a detailed fit analysis.
        
        Output format MUST be strictly adhered to:
        
        1. **Overall Fit Score:** Provide a single score out of 10. Start on a new line: `Overall Fit Score: X/10`.
        2. **Section Match Analysis:** Analyze fit for Skills, Experience, and Education (as a percentage, e.g., 85%).
        3. **Strengths/Matches:** List bullet points of key areas where the resume strongly aligns with the JD.
        4. **Weaknesses/Gaps:** List bullet points of key areas where the resume is weak or missing requirements.
        5. **Recommendation:** A short paragraph on how the candidate can improve their resume for this specific JD.
        
        JD Content: {jd_content}
        
        Candidate Structured Resume Data: {parsed_json}
        """

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt.format(jd_content=jd_content, parsed_json=parsed_json)},
                {"role": "user", "content": "Provide the detailed fit analysis."}
            ],
            temperature=0.2
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error] JD Fit Evaluation Failed: {e}"

def qa_on_resume(question):
    """Uses AI to answer questions about the candidate's resume."""
    if GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
        return f"Mock Answer: Based on the mock data, the candidate's core expertise is in Streamlit and AI, as per your question: '{question}'."
    try:
        client = Groq(api_key=GROQ_API_KEY)
        resume_data = st.session_state.parsed
        
        system_prompt = f"""You are a helpful Q&A bot for a recruiter. Based on the candidate's structured resume data provided below, answer the user's question directly and concisely. 
        Candidate Structured Resume Data: {resume_data}
        """

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error] Resume Q&A Failed: {e}"

def qa_on_jd(question, jd_name):
    """Uses AI to answer questions about a specific JD."""
    if GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
        return f"Mock Answer: Based on the mock JD '{jd_name}', the key requirement is 5+ years of experience, as per your question: '{question}'."
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        jd_item = next(item for item in st.session_state.candidate_jd_list if item['name'] == jd_name)
        jd_content = jd_item['content']
        
        system_prompt = f"""You are a helpful Q&A bot for a job seeker. Based on the Job Description (JD) provided below, answer the user's question directly and concisely.
        Job Description: {jd_content}
        """

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error] JD Q&A Failed: {e}"

def generate_interview_questions(parsed_json, section_choice):
    """Generates interview questions based on a resume section."""
    if GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
        return f"[Easy] Q1: Tell me about your {section_choice} background.\n[Medium] Q2: How did your {section_choice} prepare you for a real-world project?\n[Hard] Q3: Describe a challenging scenario related to your {section_choice} and how you overcame it."
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # Get the relevant section content
        content = parsed_json.get(section_choice.lower(), "Content not found.")
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)
        elif not isinstance(content, str):
            content = str(content)
            
        system_prompt = f"""You are an expert interviewer. Generate 3-5 challenging behavioral and technical interview questions based *only* on the candidate's **{section_choice}** section from their resume.
        The questions must be categorized by difficulty: [Easy], [Medium], and [Hard].
        
        Format your response strictly as:
        [Easy] Q1: ...
        [Medium] Q2: ...
        [Hard] Q3: ...
        ...
        
        Relevant Resume Content for {section_choice}: {content}
        """

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate interview questions for the {section_choice} section."}
            ],
            temperature=0.7
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error] Question Generation Failed: {e}"

def evaluate_interview_answers(qa_list, parsed_json):
    """Evaluates the candidate's answers against their own resume."""
    if GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
        return "Mock Evaluation Report:\n\n- **Overall Score:** 8/10\n- **Consistency:** Answers were generally consistent with the mock resume data.\n- **Improvement:** Need more detail in technical responses. (Mock Analysis)"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        answers_text = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in qa_list])
        
        system_prompt = f"""You are an expert interviewer evaluator. Assess the candidate's answers based on two criteria:
        1. **Clarity and Quality:** How well-structured and insightful are the answers? (Score 1-10).
        2. **Resume Consistency:** Do the answers align with and elaborate on the content of the candidate's actual resume data? (Score 1-10).
        
        Generate a comprehensive report with:
        - An Overall Score (out of 10).
        - A section on **Strengths** (Where the candidate excelled).
        - A section on **Areas for Improvement** (Where the answers were weak or inconsistent with the resume).
        - A list of feedback for each question answered.
        
        Candidate's Resume Data: {parsed_json}
        
        Candidate's Q&A Session:
        {answers_text}
        """

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Provide the detailed interview evaluation report."}
            ],
            temperature=0.3
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error] Answer Evaluation Failed: {e}"

# --- 4. TAB CONTENT FUNCTIONS (To keep main function clean) ---

def cv_management_tab_content():
    st.header("✍️ CV Management: View, Edit, & Export")
    
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name'))

    if not is_resume_parsed:
        st.warning("Please upload and parse a resume in the 'Resume Parsing' tab first.")
        return

    st.subheader(f"Data for: **{st.session_state.parsed.get('name', 'N/A')}**")
    
    parsed_data = st.session_state.parsed
    
    # --- Edit Feature (Using st.data_editor) ---
    st.markdown("### Editable Parsed Data")
    st.info("The AI-parsed data is shown below. You can edit the content directly before exporting.")

    # Convert complex dict to a simple list of dicts for data_editor
    editable_data = [{"Section": k, "Content": str(v)} for k, v in parsed_data.items()]
    
    # Ensure all list items (like experience, education) are properly formatted for display
    def format_content(content):
        if isinstance(content, list):
            return "\n---\n".join([str(item) for item in content])
        return str(content)

    display_data = []
    for k, v in parsed_data.items():
        # Exclude 'name' since it's displayed in the header
        if k != 'name':
            display_data.append({"Section": k, "Content": format_content(v)})

    # Use a DataFrame for a better structured editable view
    df_editable = pd.DataFrame(display_data)

    edited_df = st.data_editor(
        df_editable,
        column_config={
            "Section": st.column_config.TextColumn("Section", disabled=True),
            "Content": st.column_config.TextColumn("Content", help="Edit the extracted resume data here", width="large"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Save edited data back to session state
    if st.button("Save Edited Data"):
        new_parsed = st.session_state.parsed.copy()
        for index, row in edited_df.iterrows():
            section = row['Section']
            content = row['Content']
            
            # Attempt basic re-parsing for lists/dicts 
            try:
                # If the original was a list/dict, try to re-evaluate the string as a Python object
                if isinstance(st.session_state.parsed.get(section), (list, dict)):
                    # Simple case: try to load as JSON
                    new_parsed[section] = json.loads(content.replace("'", '"')) 
                else:
                    new_parsed[section] = content
            except Exception:
                # If re-evaluation fails, store as a multi-line string
                new_parsed[section] = content 

        st.session_state.parsed = new_parsed
        st.session_state.excel_data = edited_df # Update the simplified excel data
        st.success("Data saved successfully! Changes are reflected in all subsequent analysis tabs.")
    
    st.markdown("---")
    
    # --- Export Features ---
    st.markdown("### Export Options")
    
    col_json, col_excel, col_raw = st.columns(3)
    
    # 1. Export JSON
    with col_json:
        json_string = json.dumps(st.session_state.parsed, indent=4)
        st.download_button(
            label="Download Parsed JSON",
            data=json_string,
            file_name=f"{st.session_state.parsed.get('name', 'resume')}_parsed.json",
            mime="application/json",
            use_container_width=True
        )

    # 2. Export Excel/CSV
    with col_excel:
        if st.session_state.excel_data is not None:
            # Use the EDITED data for export
            excel_data = BytesIO()
            edited_df.to_excel(excel_data, index=False, sheet_name='Parsed Data')
            excel_data.seek(0)
            
            st.download_button(
                label="Download Parsed Excel/CSV",
                data=excel_data,
                file_name=f"{st.session_state.parsed.get('name', 'resume')}_parsed.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.download_button(
                label="Download Parsed Excel/CSV",
                data="No data to export.",
                file_name="no_data.xlsx",
                disabled=True,
                use_container_width=True
            )
            
    # 3. Export Raw Text
    with col_raw:
        st.download_button(
            label="Download Raw Extracted Text",
            data=st.session_state.full_text,
            file_name=f"{st.session_state.parsed.get('name', 'resume')}_raw_text.txt",
            mime="text/plain",
            use_container_width=True
        )

def filter_jd_tab_content():
    st.header("🔍 Filter & Select Job Descriptions")
    st.markdown("Filter your saved JDs based on metadata (Role, Job Type, Skills).")
    
    if not st.session_state.candidate_jd_list:
        st.warning("Please **add Job Descriptions** in the 'JD Management' tab first.")
        return

    jds = st.session_state.candidate_jd_list
    
    # Collect unique filter values
    all_roles = sorted(list(set(jd.get('role') for jd in jds if jd.get('role'))))
    all_job_types = sorted(list(set(jd.get('job_type') for jd in jds if jd.get('job_type'))))
    all_key_skills = sorted(list(set(skill for jd in jds for skill in jd.get('key_skills', []) if skill)))

    # --- Filter Controls ---
    st.subheader("Filter Criteria")
    col_role, col_type = st.columns(2)
    
    with col_role:
        selected_roles = st.multiselect(
            "Filter by Role/Title",
            options=all_roles,
            default=all_roles if all_roles else None,
            key='filter_role_c'
        )
        
    with col_type:
        selected_types = st.multiselect(
            "Filter by Job Type",
            options=all_job_types,
            default=all_job_types if all_job_types else None,
            key='filter_type_c'
        )

    st.markdown("---")
    
    selected_skills = st.multiselect(
        "Filter by Key Skills (Match ANY selected skill)",
        options=all_key_skills,
        default=[],
        key='filter_skill_c'
    )
    
    # --- Filtering Logic ---
    filtered_jds = []
    
    for jd in jds:
        # Check Role
        role_match = not selected_roles or (jd.get('role') in selected_roles)
        
        # Check Job Type
        type_match = not selected_types or (jd.get('job_type') in selected_types)
        
        # Check Skills (Match ANY)
        skill_match = True
        if selected_skills:
            jd_skills = jd.get('key_skills', [])
            skill_match = any(skill in jd_skills for skill in selected_skills)
            
        if role_match and type_match and skill_match:
            filtered_jds.append(jd)

    st.markdown("### Filtered Job Descriptions")
    
    if filtered_jds:
        st.success(f"Showing **{len(filtered_jds)}** of **{len(jds)}** total JDs.")
        
        # Store filtered results for display
        st.session_state.filtered_jds_display = filtered_jds
        
        # Convert to DataFrame for better viewing
        display_df_data = []
        for jd in filtered_jds:
            display_df_data.append({
                "JD Name": jd['name'].replace("--- Simulated JD for: ", ""),
                "Role": jd.get('role', 'N/A'),
                "Job Type": jd.get('job_type', 'N/A'),
                "Key Skills": ", ".join(jd.get('key_skills', []))
            })
            
        st.dataframe(display_df_data, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("##### Detailed View of Filtered JDs")
        for idx, jd_item in enumerate(filtered_jds, 1):
            title = jd_item['name']
            display_title = title.replace("--- Simulated JD for: ", "")
            with st.expander(f"JD {idx}: {display_title} | Role: {jd_item.get('role', 'N/A')}"):
                st.markdown(f"**Job Type:** {jd_item.get('job_type', 'N/A')} | **Key Skills:** {', '.join(jd_item.get('key_skills', ['N/A']))}") 
                st.markdown("---")
                st.text(jd_item['content'])
        
    else:
        st.info("No Job Descriptions match the current filter criteria.")

# --- 5. MAIN DASHBOARD FUNCTION (THE CORE) ---

def candidate_dashboard():
    st.header("👩‍🎓 Candidate Dashboard")
    st.markdown("Welcome! Use the tabs below to manage your CV and access AI preparation tools.")

    # --- LOG OUT BLOCK (MOCK NAVIGATION) ---
    nav_col, _ = st.columns([1, 1]) 

    with nav_col:
        # NOTE: 'go_to("login")' is mocked here. In a real app, this would change the session state page to 'login'.
        if st.button("🚪 Log Out", key="candidate_logout_btn", use_container_width=True):
            st.session_state.page = "login"
            st.rerun() 
    # --- END LOG OUT BLOCK ---
    
    # Sidebar for Status Only
    with st.sidebar:
        st.header("Resume/CV Status")
        
        # Check if a resume is currently loaded into the main parsing variables
        if st.session_state.parsed.get("name"):
            st.success(f"Currently loaded: **{st.session_state.parsed['name']}**")
        elif st.session_state.full_text:
            st.warning("Resume content is loaded, but parsing may have errors.")
        else:
            st.info("Please upload a file or use the CV builder in 'CV Management' to begin.")

    # Main Content Tabs (REARRANGED TABS HERE - Chatbot and Interview Prep are now at the end)
    
    # *** INSERT NEW TABS HERE ***
    # To add a new tab, insert it here and assign it a variable (e.g., tab_new)
    tab_cv_mgmt, tab_parsing, tab_jd_mgmt, tab_batch_match, tab_filter_jd, tab_chatbot, tab_interview_prep, tab_new_feature = st.tabs([
        "✍️ CV Management", 
        "📄 Resume Parsing", 
        "📚 JD Management", 
        "🎯 Batch JD Match",
        "🔍 Filter JD",
        "💬 Resume/JD Chatbot (Q&A)", 
        "❓ Interview Prep",
        "✨ New Feature Tab" # <--- ADDED NEW TAB
    ])
    
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name')) or bool(st.session_state.get('full_text'))
    
    # --- TAB 0: CV Management ---
    with tab_cv_mgmt:
        cv_management_tab_content()

    # --- TAB 1 (Now tab_parsing): Resume Parsing ---
    with tab_parsing:
        st.header("Resume Upload and Parsing")
        
        # 1. Input Method Selection
        input_method = st.radio(
            "Select Input Method",
            ["Upload File", "Paste Text"],
            key="parsing_input_method"
        )
        
        st.markdown("---")

        # --- A. Upload File Method ---
        if input_method == "Upload File":
            st.markdown("### 1. Upload Resume File") 
            
            # 🚨 File types expanded here
            uploaded_file = st.file_uploader( 
                "Choose PDF, DOCX, TXT, JSON, MD, CSV, XLSX file", 
                type=["pdf", "docx", "txt", "json", "md", "csv", "xlsx", "markdown", "rtf"], 
                accept_multiple_files=False, 
                key='candidate_file_upload_main'
            )
            
            st.markdown(
                """
                <div style='font-size: 10px; color: grey;'>
                Supported File Types: PDF, DOCX, TXT, JSON, MARKDOWN, CSV, XLSX, RTF
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.markdown("---")

            # --- File Management Logic ---
            if uploaded_file is not None:
                # Only store the single uploaded file if it's new
                if not st.session_state.candidate_uploaded_resumes or st.session_state.candidate_uploaded_resumes[0].name != uploaded_file.name:
                    st.session_state.candidate_uploaded_resumes = [uploaded_file] 
                    st.session_state.pasted_cv_text = "" # Clear pasted text
                    st.toast("Resume file uploaded successfully.")
            elif st.session_state.candidate_uploaded_resumes and uploaded_file is None:
                # Case where the file is removed from the uploader
                st.session_state.candidate_uploaded_resumes = []
                st.session_state.parsed = {}
                st.session_state.full_text = ""
                st.toast("Upload cleared.")
            
            file_to_parse = st.session_state.candidate_uploaded_resumes[0] if st.session_state.candidate_uploaded_resumes else None
            
            st.markdown("### 2. Parse Uploaded File")
            
            if file_to_parse:
                if st.button(f"Parse and Load: **{file_to_parse.name}**", use_container_width=True):
                    with st.spinner(f"Parsing {file_to_parse.name}..."):
                        result = parse_and_store_resume(file_to_parse, file_name_key='single_resume_candidate', source_type='file')
                        
                        if "error" not in result:
                            st.session_state.parsed = result['parsed']
                            st.session_state.full_text = result['full_text']
                            st.session_state.excel_data = result['excel_data'] 
                            st.session_state.parsed['name'] = result['name'] 
                            clear_interview_state()
                            st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                            st.info("View, edit, and download the parsed data in the **CV Management** tab.") 
                        else:
                            st.error(f"Parsing failed for {file_to_parse.name}: {result['error']}")
                            st.session_state.parsed = {"error": result['error'], "name": result['name']}
                            st.session_state.full_text = result['full_text'] or ""
            else:
                st.info("No resume file is currently uploaded. Please upload a file above.")

        # --- B. Paste Text Method ---
        else: # input_method == "Paste Text"
            st.markdown("### 1. Paste Your CV Text")
            
            pasted_text = st.text_area(
                "Copy and paste your entire CV or resume text here.",
                value=st.session_state.get('pasted_cv_text', ''),
                height=300,
                key='pasted_cv_text_input'
            )
            st.session_state.pasted_cv_text = pasted_text # Update session state immediately
            
            st.markdown("---")
            st.markdown("### 2. Parse Pasted Text")
            
            if pasted_text.strip():
                if st.button("Parse and Load Pasted Text", use_container_width=True):
                    with st.spinner("Parsing pasted text..."):
                        # Clear file upload state
                        st.session_state.candidate_uploaded_resumes = []
                        
                        result = parse_and_store_resume(pasted_text, file_name_key='single_resume_candidate', source_type='text')
                        
                        if "error" not in result:
                            st.session_state.parsed = result['parsed']
                            st.session_state.full_text = result['full_text']
                            st.session_state.excel_data = result['excel_data'] 
                            st.session_state.parsed['name'] = result['name'] 
                            clear_interview_state()
                            st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                            st.info("View, edit, and download the parsed data in the **CV Management** tab.") 
                        else:
                            st.error(f"Parsing failed: {result['error']}")
                            st.session_state.parsed = {"error": result['error'], "name": result['name']}
                            st.session_state.full_text = result['full_text'] or ""
            else:
                st.info("Please paste your CV text into the box above.")

    # --- TAB 2 (Now tab_jd_mgmt): JD Management (Candidate) ---
    with tab_jd_mgmt:
        st.header("📚 Manage Job Descriptions for Matching")
        st.markdown("Add multiple JDs here to compare your resume against them in the next tabs.")
        
        if "candidate_jd_list" not in st.session_state:
             st.session_state.candidate_jd_list = []
        
        jd_type = st.radio("Select JD Type", ["Single JD", "Multiple JD"], key="jd_type_candidate")
        st.markdown("### Add JD by:")
        
        method = st.radio("Choose Method", ["Upload File", "Paste Text", "LinkedIn URL"], key="jd_add_method_candidate") 

        # URL
        if method == "LinkedIn URL":
            url_list = st.text_area(
                "Enter one or more URLs (comma separated)" if jd_type == "Multiple JD" else "Enter URL", key="url_list_candidate"
            )
            if st.button("Add JD(s) from URL", key="add_jd_url_btn_candidate"):
                if url_list:
                    urls = [u.strip() for u in url_list.split(",")] if jd_type == "Multiple JD" else [url_list.strip()]
                    
                    count = 0
                    for url in urls:
                        if not url: continue
                        
                        with st.spinner(f"Attempting JD extraction and metadata analysis for: {url}"):
                            jd_text = extract_jd_from_linkedin_url(url)
                            metadata = extract_jd_metadata(jd_text) # NEW METADATA EXTRACTION
                        
                        name_base = url.split('/jobs/view/')[-1].split('/')[0] if '/jobs/view/' in url else f"URL {count+1}"
                        # CRITICAL: Added explicit JD naming convention for LinkedIn URLs in Candidate JD list
                        name = f"JD from URL: {name_base}" 
                        if name in [item['name'] for item in st.session_state.candidate_jd_list]:
                            name = f"JD from URL: {name_base} ({len(st.session_state.candidate_jd_list) + 1})" 

                        st.session_state.candidate_jd_list.append({"name": name, "content": jd_text, **metadata}) # ADD METADATA
                        
                        if not jd_text.startswith("[Error"):
                            count += 1
                                
                    if count > 0:
                        st.success(f"✅ {count} JD(s) added successfully! Check the display below for the extracted content.")
                    else:
                        st.error("No JDs were added successfully.")


        # Paste Text
        elif method == "Paste Text":
            text_list = st.text_area(
                "Paste one or more JD texts (separate by '---')" if jd_type == "Multiple JD" else "Paste JD text here", key="text_list_candidate"
            )
            if st.button("Add JD(s) from Text", key="add_jd_text_btn_candidate"):
                if text_list:
                    texts = [t.strip() for t in text_list.split("---")] if jd_type == "Multiple JD" else [text_list.strip()]
                    for i, text in enumerate(texts):
                         if text:
                            name_base = text.splitlines()[0].strip()
                            if len(name_base) > 30: name_base = f"{name_base[:27]}..."
                            if not name_base: name_base = f"Pasted JD {len(st.session_state.candidate_jd_list) + i + 1}"
                            
                            metadata = extract_jd_metadata(text) # NEW METADATA EXTRACTION
                            st.session_state.candidate_jd_list.append({"name": name_base, "content": text, **metadata}) # ADD METADATA
                    st.success(f"✅ {len(texts)} JD(s) added successfully!")

        # Upload File
        elif method == "Upload File":
            uploaded_files = st.file_uploader(
                "Upload JD file(s)",
                type=["pdf", "txt", "docx"],
                accept_multiple_files=(jd_type == "Multiple JD"), # Dynamically set
                key="jd_file_uploader_candidate"
            )
            if st.button("Add JD(s) from File", key="add_jd_file_btn_candidate"):
                # CRITICAL FIX: Ensure 'files_to_process' is always a list of single UploadedFile objects
                if uploaded_files is None:
                    st.warning("Please upload file(s).")
                    
                files_to_process = uploaded_files if isinstance(uploaded_files, list) else ([uploaded_files] if uploaded_files else [])
                
                count = 0
                for file in files_to_process:
                    if file:
                        # Streamlit UploaderFile needs to be written to a temp file for `extract_content` mock
                        temp_dir = tempfile.mkdtemp()
                        temp_path = os.path.join(temp_dir, file.name)
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                            
                        file_type = get_file_type(temp_path)
                        jd_text = extract_content(file_type, temp_path)
                        
                        os.remove(temp_path)
                        os.rmdir(temp_dir)
                        
                        if not jd_text.startswith("Error"):
                            metadata = extract_jd_metadata(jd_text) # NEW METADATA EXTRACTION
                            st.session_state.candidate_jd_list.append({"name": file.name, "content": jd_text, **metadata}) # ADD METADATA
                            count += 1
                        else:
                            st.error(f"Error extracting content from {file.name}: {jd_text}")
                            
                if count > 0:
                    st.success(f"✅ {count} JD(s) added successfully!")
                elif uploaded_files:
                    st.error("No valid JD files were uploaded or content extraction failed.")


        # Display Added JDs
        if st.session_state.candidate_jd_list:
            
            col_display_header, col_clear_button = st.columns([3, 1])
            
            with col_display_header:
                st.markdown("### ✅ Current JDs Added:")
                
            with col_clear_button:
                if st.button("🗑️ Clear All JDs", key="clear_jds_candidate", use_container_width=True, help="Removes all currently loaded JDs."):
                    st.session_state.candidate_jd_list = []
                    st.session_state.candidate_match_results = [] 
                    # Also clear filter display
                    st.session_state.filtered_jds_display = [] 
                    st.success("All JDs and associated match results have been cleared.")
                    st.rerun() 

            for idx, jd_item in enumerate(st.session_state.candidate_jd_list, 1):
                title = jd_item['name']
                display_title = title.replace("--- Simulated JD for: ", "")
                with st.expander(f"JD {idx}: {display_title} | Role: {jd_item.get('role', 'N/A')}"):
                    st.markdown(f"**Job Type:** {jd_item.get('job_type', 'N/A')} | **Key Skills:** {', '.join(jd_item.get('key_skills', ['N/A']))}") # ADDED METADATA DISPLAY
                    st.markdown("---")
                    st.text(jd_item['content'])
        else:
            st.info("No Job Descriptions added yet.")

    # --- TAB 3 (Now tab_batch_match): Batch JD Match (Candidate) ---
    with tab_batch_match:
        st.header("🎯 Batch JD Match: Best Matches")
        st.markdown("Compare your current resume against all saved job descriptions.")

        if not is_resume_parsed:
            st.warning("Please **upload and parse your resume** in the 'Resume Parsing' tab or **build your CV** in the 'CV Management' tab first.")
        
        elif not st.session_state.candidate_jd_list:
            st.error("Please **add Job Descriptions** in the 'JD Management' tab (Tab 4) before running batch analysis.")
            
        elif GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
             st.error("Cannot use JD Match: GROQ_API_KEY is not configured. Please set the secret to enable AI functionality.")
             
        else:
            if "candidate_match_results" not in st.session_state:
                st.session_state.candidate_match_results = []

            # 1. Get all available JD names
            all_jd_names = [item['name'] for item in st.session_state.candidate_jd_list]
            
            # 2. Add multiselect widget
            selected_jd_names = st.multiselect(
                "Select Job Descriptions to Match Against",
                options=all_jd_names,
                default=all_jd_names, # Default to selecting all JDs
                key='candidate_batch_jd_select'
            )
            
            # 3. Filter the list of JDs based on selection
            jds_to_match = [
                jd_item for jd_item in st.session_state.candidate_jd_list 
                if jd_item['name'] in selected_jd_names
            ]
            
            if st.button(f"Run Match Analysis on {len(jds_to_match)} Selected JD(s)"):
                st.session_state.candidate_match_results = []
                
                if not jds_to_match:
                    st.warning("Please select at least one Job Description to run the analysis.")
                    
                else:
                    resume_name = st.session_state.parsed.get('name', 'Uploaded Resume')
                    parsed_json = st.session_state.parsed
                    results_with_score = []

                    with st.spinner(f"Matching {resume_name}'s resume against {len(jds_to_match)} selected JD(s)..."):
                        
                        # Loop over jds_to_match
                        for jd_item in jds_to_match:
                            
                            jd_name = jd_item['name']
                            jd_content = jd_item['content']

                            try:
                                fit_output = evaluate_jd_fit(jd_content, parsed_json)
                                
                                # Use regex to reliably extract score and section percentages
                                overall_score_match = re.search(r'Overall Fit Score:\s*[^\d]*(\d+)\s*/10', fit_output, re.IGNORECASE)
                                section_analysis_match = re.search(
                                    r'--- Section Match Analysis ---\s*(.*?)\s*Strengths/Matches:', 
                                    fit_output, re.DOTALL
                                ) or re.search( # Fallback pattern
                                    r'Skills Match:\s*(\d+)%', fit_output, re.DOTALL
                                )

                                skills_percent, experience_percent, education_percent = 'N/A', 'N/A', 'N/A'
                                
                                if section_analysis_match:
                                    section_text = section_analysis_match.group(0) # Use group(0) for the whole match
                                    skills_match = re.search(r'Skills Match:\s*\[?(\d+)%\]?', section_text, re.IGNORECASE)
                                    experience_match = re.search(r'Experience Match:\s*\[?(\d+)%\]?', section_text, re.IGNORECASE)
                                    education_match = re.search(r'Education Match:\s*\[?(\d+)%\]?', section_text, re.IGNORECASE)
                                    
                                    if skills_match: skills_percent = skills_match.group(1)
                                    if experience_match: experience_percent = experience_match.group(1)
                                    if education_match: education_percent = education_match.group(1)
                                
                                overall_score = overall_score_match.group(1) if overall_score_match else 'N/A'

                                results_with_score.append({
                                    "jd_name": jd_name,
                                    "overall_score": overall_score,
                                    "numeric_score": int(overall_score) if overall_score.isdigit() else -1, # Added for sorting/ranking
                                    "skills_percent": skills_percent,
                                    "experience_percent": experience_percent, 
                                    "education_percent": education_percent,   
                                    "full_analysis": fit_output
                                })
                            except Exception as e:
                                results_with_score.append({
                                    "jd_name": jd_name,
                                    "overall_score": "Error",
                                    "numeric_score": -1, # Set a low score for errors
                                    "skills_percent": "Error",
                                    "experience_percent": "Error", 
                                    "education_percent": "Error",   
                                    "full_analysis": f"Error running analysis for {jd_name}: {e}\n{traceback.format_exc()}"
                                })
                                
                        # --- NEW RANKING LOGIC ---
                        # 1. Sort by numeric_score (highest first)
                        results_with_score.sort(key=lambda x: x['numeric_score'], reverse=True)
                        
                        # 2. Assign Rank (handle ties)
                        current_rank = 1
                        current_score = -1 
                        
                        for i, item in enumerate(results_with_score):
                            if item['numeric_score'] > current_score:
                                current_rank = i + 1
                                current_score = item['numeric_score']
                            
                            item['rank'] = current_rank
                            # Remove the temporary numeric_score field
                            del item['numeric_score'] 
                            
                        st.session_state.candidate_match_results = results_with_score
                        # --- END NEW RANKING LOGIC ---
                        
                        st.success("Batch analysis complete!")


            # 3. Display Results (UPDATED TO INCLUDE RANK)
            if st.session_state.get('candidate_match_results'):
                st.markdown("#### Match Results for Your Resume")
                results_df = st.session_state.candidate_match_results
                
                display_data = []
                for item in results_df:
                    # Also include extracted JD metadata for a richer view
                    
                    # Find the full JD item to get the metadata
                    full_jd_item = next((jd for jd in st.session_state.candidate_jd_list if jd['name'] == item['jd_name']), {})
                    
                    display_data.append({
                        # 🚨 ADDED RANK COLUMN
                        "Rank": item.get("rank", "N/A"),
                        "Job Description (Ranked)": item["jd_name"].replace("--- Simulated JD for: ", ""),
                        "Role": full_jd_item.get('role', 'N/A'), # Added Role
                        "Job Type": full_jd_item.get('job_type', 'N/A'), # Added Job Type
                        "Fit Score (out of 10)": item["overall_score"],
                        "Skills (%)": item.get("skills_percent", "N/A"),
                        "Experience (%)": item.get("experience_percent", "N/A"), 
                        "Education (%)": item.get("education_percent", "N/A"),   
                    })

                st.dataframe(display_data, use_container_width=True)

                st.markdown("##### Detailed Reports")
                for item in results_df:
                    # UPDATED HEADER TO INCLUDE RANK
                    rank_display = f"Rank {item.get('rank', 'N/A')} | "
                    header_text = f"{rank_display}Report for **{item['jd_name'].replace('--- Simulated JD for: ', '')}** (Score: **{item['overall_score']}/10** | S: **{item.get('skills_percent', 'N/A')}%** | E: **{item.get('experience_percent', 'N/A')}%** | Edu: **{item.get('education_percent', 'N/A')}%**)"
                    with st.expander(header_text):
                        st.markdown(item['full_analysis'])

    # --- TAB 4 (Now tab_filter_jd): Filter JD ---
    with tab_filter_jd:
        filter_jd_tab_content()

    # --- TAB 5 (Now tab_chatbot): Resume Chatbot (Q&A) ---
    with tab_chatbot:
        st.header("Resume/JD Chatbot (Q&A) 💬")
        
        # --- NESTED TABS ---
        sub_tab_resume, sub_tab_jd = st.tabs([
            "👤 Chat about Your Resume",
            "📄 Chat about Saved JDs"
        ])
        
        # --- 5A. RESUME CHATBOT CONTENT ---
        with sub_tab_resume:
            st.markdown("### Ask any question about the currently loaded resume.")
            if not is_resume_parsed:
                st.warning("Please upload and parse a resume in the 'Resume Parsing' tab or use the 'CV Management' tab first.")
            elif "error" in st.session_state.parsed:
                 st.error("Cannot use Resume Chatbot: Resume data has parsing errors.")
            elif GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
                 st.error("Cannot use Chatbot: GROQ_API_KEY is not configured. Please set the secret to enable AI functionality.")
            else:
                if 'qa_answer_resume' not in st.session_state: st.session_state.qa_answer_resume = ""
                
                question = st.text_input(
                    "Your Question (about Resume)", 
                    placeholder="e.g., What are the candidate's key skills?",
                    key="resume_qa_question"
                )
                
                if st.button("Get Answer (Resume)", key="qa_btn_resume"):
                    with st.spinner("Generating answer..."):
                        try:
                            answer = qa_on_resume(question)
                            st.session_state.qa_answer_resume = answer
                        except Exception as e:
                            st.error(f"Error during Resume Q&A: {e}")
                            st.session_state.qa_answer_resume = "Could not generate an answer."

                if st.session_state.get('qa_answer_resume'):
                    st.text_area("Answer (Resume)", st.session_state.qa_answer_resume, height=150)
        
        # --- 5B. JD CHATBOT CONTENT ---
        with sub_tab_jd:
            st.markdown("### Ask any question about a saved Job Description.")
            
            if not st.session_state.candidate_jd_list:
                st.warning("Please add Job Descriptions in the 'JD Management' tab (Tab 4) first.")
            elif GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
                 st.error("Cannot use JD Chatbot: GROQ_API_KEY is not configured. Please set the secret to enable AI functionality.")
            else:
                if 'qa_answer_jd' not in st.session_state: st.session_state.qa_answer_jd = ""

                # 1. JD Selection
                jd_names = [jd['name'] for jd in st.session_state.candidate_jd_list]
                selected_jd_name = st.selectbox(
                    "Select Job Description to Query",
                    options=jd_names,
                    key="jd_qa_select"
                )
                
                # 2. Question Input
                question = st.text_input(
                    "Your Question (about JD)", 
                    placeholder="e.g., What is the minimum experience required for this role?",
                    key="jd_qa_question"
                )
                
                # 3. Get Answer Button
                if st.button("Get Answer (JD)", key="qa_btn_jd"):
                    if selected_jd_name and question.strip():
                        with st.spinner(f"Generating answer for {selected_jd_name}..."):
                            try:
                                answer = qa_on_jd(question, selected_jd_name)
                                st.session_state.qa_answer_jd = answer
                            except Exception as e:
                                st.error(f"Error during JD Q&A: {e}")
                                st.session_state.qa_answer_jd = "Could not generate an answer."
                    else:
                        st.error("Please select a JD and enter a question.")

                # 4. Answer Output
                if st.session_state.get('qa_answer_jd'):
                    st.text_area("Answer (JD)", st.session_state.qa_answer_jd, height=150)


    # --- TAB 6 (Now tab_interview_prep): Interview Prep ---
    with tab_interview_prep:
        st.header("❓ Interview Preparation Tools")
        if not is_resume_parsed or "error" in st.session_state.parsed:
            st.warning("Please upload and successfully parse a resume first.")
        elif GROQ_API_KEY == "DUMMY_KEY_FOR_LOCAL_TESTING":
             st.error("Cannot use Interview Prep: GROQ_API_KEY is not configured. Please set the secret to enable AI functionality.")
        else:
            if 'iq_output' not in st.session_state: st.session_state.iq_output = ""
            if 'interview_qa' not in st.session_state: st.session_state.interview_qa = [] 
            if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = "" 
            
            st.subheader("1. Generate Interview Questions")
            
            section_choice = st.selectbox(
                "Select Section", 
                question_section_options, 
                key='iq_section_c',
                on_change=clear_interview_state 
            )
            
            if st.button("Generate Interview Questions", key='iq_btn_c'):
                with st.spinner("Generating questions..."):
                    try:
                        raw_questions_response = generate_interview_questions(st.session_state.parsed, section_choice)
                        st.session_state.iq_output = raw_questions_response
                        
                        st.session_state.interview_qa = [] 
                        st.session_state.evaluation_report = "" 
                        
                        q_list = []
                        current_level = ""
                        for line in raw_questions_response.splitlines():
                            line = line.strip()
                            if line.startswith('[') and line.endswith(']'):
                                current_level = line.strip('[]')
                            elif line.lower().startswith('q') and ':' in line:
                                question_text = line[line.find(':') + 1:].strip()
                                q_list.append({
                                    "question": f"({current_level}) {question_text}",
                                    "answer": "", 
                                    "level": current_level
                                })
                                
                        st.session_state.interview_qa = q_list
                        
                        st.success(f"Generated {len(q_list)} questions based on your **{section_choice}** section.")
                        
                    except Exception as e:
                        st.error(f"Error generating questions: {e}")
                        st.session_state.iq_output = "Error generating questions."
                        st.session_state.interview_qa = []

            if st.session_state.get('interview_qa'):
                st.markdown("---")
                st.subheader("2. Practice and Record Answers")
                
                with st.form("interview_practice_form"):
                    
                    for i, qa_item in enumerate(st.session_state.interview_qa):
                        st.markdown(f"**Question {i+1}:** {qa_item['question']}")
                        
                        answer = st.text_area(
                            f"Your Answer for Q{i+1}", 
                            value=st.session_state.interview_qa[i]['answer'], 
                            height=100,
                            key=f'answer_q_{i}',
                            label_visibility='collapsed'
                        )
                        st.session_state.interview_qa[i]['answer'] = answer 
                        st.markdown("---") 
                        
                    submit_button = st.form_submit_button("Submit & Evaluate Answers", use_container_width=True)

                    if submit_button:
                        
                        if all(item['answer'].strip() for item in st.session_state.interview_qa):
                            with st.spinner("Sending answers to AI Evaluator..."):
                                try:
                                    report = evaluate_interview_answers(
                                        st.session_state.interview_qa,
                                        st.session_state.parsed
                                    )
                                    st.session_state.evaluation_report = report
                                    st.success("Evaluation complete! See the report below.")
                                except Exception as e:
                                    st.error(f"Evaluation failed: {e}")
                                    st.session_state.evaluation_report = f"Evaluation failed: {e}\n{traceback.format_exc()}"
                        else:
                            st.error("Please answer all generated questions before submitting.")
                
                if st.session_state.get('evaluation_report'):
                    st.markdown("---")
                    st.subheader("3. AI Evaluation Report")
                    st.markdown(st.session_state.evaluation_report)
                    
    # --- TAB 7 (NEW FEATURE TAB) ---
    with tab_new_feature:
        st.header("✨ My Awesome New Feature")
        st.info("This is the new tab you requested. You can start adding your custom logic and Streamlit components here.")
        st.markdown("#### Example Content")
        st.code("""
        # Add your custom code here, e.g.:
        # st.selectbox("Select Model", ["Groq", "GPT-4"])
        # st.button("Run Analysis")
        """)


# --- 6. MAIN APPLICATION ENTRY POINT ---

if __name__ == "__main__":
    initialize_session_state()
    
    # Simple mock routing logic
    if st.session_state.page == "candidate_dashboard":
        candidate_dashboard()
    elif st.session_state.page == "login":
        # In a real app, this would be your login screen
        st.title("👤 Login (Mock Page)")
        st.info("Log in successful! Redirecting to dashboard...")
        st.session_state.page = "candidate_dashboard"
        st.rerun()
    else:
        st.error("Unknown page state.")
