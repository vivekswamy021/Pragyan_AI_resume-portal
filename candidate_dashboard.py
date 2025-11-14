import streamlit as st
import os
import pdfplumber
import docx
import openpyxl
import json
import tempfile
from groq import Groq
import traceback
import re 
from dotenv import load_dotenv 
from datetime import date 
from streamlit.runtime.uploaded_file_manager import UploadedFile

# --- PDF Generation Mock (required for 'pdf' output format) ---
def generate_pdf_mock(cv_data, cv_name):
    """Mocks the generation of a PDF file and returns its path/bytes."""
    try:
        from fpdf import FPDF
    except ImportError:
        # Fallback if fpdf is not installed (common in restricted environments)
        return f"PDF generation library (e.g., fpdf) not installed. Cannot generate PDF for {cv_name}."

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=cv_data.get('name', cv_name), ln=1, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 5, txt=f"Email: {cv_data.get('email', 'N/A')} | Phone: {cv_data.get('phone', 'N/A')}", ln=1, align="C")
    pdf.ln(5)

    # Summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 5, txt="Summary", ln=1, align="L")
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, txt=cv_data.get('summary', 'N/A'))
    pdf.ln(2)

    # Experience (First Entry)
    if cv_data.get('experience'):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 5, txt="Experience (First Entry)", ln=1, align="L")
        exp = cv_data['experience'][0]
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 5, txt=f"{exp.get('role', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('dates', 'N/A')})", ln=1, align="L")
        pdf.ln(2)
        
    return pdf.output(dest='S').encode('latin-1') # Return bytes

# -------------------------
# CONFIGURATION & API SETUP (Necessary for standalone functions)
# -------------------------

GROQ_MODEL = "llama-3.1-8b-instant"
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Groq Client or Mock Client 
if not GROQ_API_KEY:
    class MockGroqClient:
        def chat(self):
            class Completions:
                def create(self, **kwargs):
                    raise ValueError("GROQ_API_KEY not set. AI functions disabled.")
            return Completions()
    client = MockGroqClient()
else:
    client = Groq(api_key=GROQ_API_KEY)

# --- Utility Functions ---

def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def get_file_type(file_path):
    """Identifies the file type based on its extension."""
    ext = os.path.splitext(file_path)[1].lower().strip('.')
    if ext == 'pdf': return 'pdf'
    elif ext == 'docx': return 'docx'
    elif ext == 'xlsx': return 'xlsx'
    else: return 'txt' 

def extract_content(file_type, file_path):
    """Extracts text content from various file types."""
    text = ''
    try:
        if file_type == 'pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        elif file_type == 'docx':
            doc = docx.Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
        
        if not text.strip():
            return f"Error: {file_type.upper()} content extraction failed or file is empty."
        
        return text
    
    except Exception as e:
        return f"Fatal Extraction Error: Failed to read file content ({file_type}). Error: {e}"


@st.cache_data(show_spinner="Analyzing content with Groq LLM...")
def parse_with_llm(text):
    """Sends resume text to the LLM for structured information extraction."""
    if text.startswith("Error") or not GROQ_API_KEY:
        return {"error": "Parsing error or API key missing.", "raw_output": ""}

    prompt = f"""Extract the following information from the resume in structured JSON.
    - Name, - Email, - Phone, - Skills, - Education (list of degrees/schools), 
    - Experience (list of jobs), - Certifications, 
    - Projects, - Strength, 
    - Personal Details, - Github, - LinkedIn
    
    Also, provide a key called **'summary'** which is a single, brief paragraph (3-4 sentences max) summarizing the candidate's career highlights and most relevant skills.
    
    Resume Text: {text}
    
    Provide the output strictly as a JSON object.
    """
    content = ""
    parsed = {}
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        
        # Robustly isolate JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0).strip()
            json_str = json_str.replace('```json', '').replace('```', '').strip() 
            parsed = json.loads(json_str)
        else:
            raise json.JSONDecodeError("Could not isolate a valid JSON structure.", content, 0)
    except Exception as e:
        parsed = {"error": f"LLM error: {e}", "raw_output": content}

    return parsed

# --- Shared Manual Input Logic ---

def save_form_cv():
    """
    Callback function to compile the structured CV data from form states and save it 
    to managed_cvs under the key 'form_cv_key_name'.
    """
    cv_key_name = st.session_state.get('form_cv_key_name', '').strip()
    current_form_name = st.session_state.get('form_name_value', '').strip()
    
    if not cv_key_name:
        st.error("Please provide a name for this new CV to save.")
        return
    elif not current_form_name:
         st.error("Please enter your Full Name to save the CV.") 
         return
    
    # Compile the structured data using session state values
    final_cv_data = {
        "name": current_form_name,
        "email": st.session_state.get('form_email_value', '').strip(),
        "phone": st.session_state.get('form_phone_value', '').strip(),
        "linkedin": st.session_state.get('form_linkedin_value', '').strip(),
        "github": st.session_state.get('form_github_value', '').strip(),
        "summary": st.session_state.get('form_summary_value', '').strip(),
        "skills": [s.strip() for s in st.session_state.get('form_skills_value', '').split('\n') if s.strip()],
        "education": st.session_state.get('form_education', []), 
        "experience": st.session_state.get('form_experience', []), 
        "certifications": st.session_state.get('form_certifications', []), 
        "projects": st.session_state.get('form_projects', []),
        "strength": [s.strip() for s in st.session_state.get('form_strengths_input', '').split('\n') if s.strip()] 
    }
    
    st.session_state.managed_cvs[cv_key_name] = final_cv_data
    st.session_state.current_resume_name = cv_key_name
    st.session_state.show_cv_output = cv_key_name # Set to show the generated CV
    
    st.success(f"🎉 CV **'{cv_key_name}'** created/updated from form and saved!")

def add_education_entry(degree, college, university, date_from, date_to, state_key='form_education'):
    """
    Callback function to add a structured education entry to session state.
    """
    if not degree or not college or not university:
        st.error("Please fill in **Degree**, **College**, and **University**.")
        return
        
    entry = {
        "degree": degree,
        "college": college,
        "university": university,
        "dates": f"{date_from.year} - {date_to.year}"
    }
    
    if state_key not in st.session_state:
        st.session_state[state_key] = []
        
    st.session_state[state_key].append(entry)
    st.toast(f"Added Education: {degree}")

def add_experience_entry(company, role, ctc, project, date_from, date_to, state_key='form_experience'):
    """
    Callback function to add a structured experience entry to session state.
    """
    if not company or not role or not date_from or not date_to:
        st.error("Please fill in **Company Name**, **Role**, and **Dates**.")
        return
        
    entry = {
        "company": company,
        "role": role,
        "ctc": ctc if ctc else "N/A",
        "project": project if project else "General Duties",
        "dates": f"{date_from.year} - {date_to.year}"
    }
    
    if state_key not in st.session_state:
        st.session_state[state_key] = []
        
    st.session_state[state_key].append(entry)
    st.toast(f"Added Experience: {role} at {company}")

def add_certification_entry(name, title, given_by, received_by, course, date_val, state_key='form_certifications'):
    """
    Callback function to add a structured certification entry to session state.
    """
    if not name or not title or not given_by or not course:
        st.error("Please fill in **Name**, **Title**, **Given By**, and **Course**.")
        return
        
    entry = {
        "name": name,
        "title": title,
        "given_by": given_by,
        "received_by_name": received_by if received_by else "N/A",
        "course": course,
        "date_received": date_val.strftime("%Y-%m-%d")
    }
    
    if state_key not in st.session_state:
        st.session_state[state_key] = []
        
    st.session_state[state_key].append(entry)
    st.toast(f"Added Certification: {name} ({title})")

def add_project_entry(name, description, technologies, app_link, state_key='form_projects'):
    """
    Callback function to add a structured project entry to session state.
    """
    if not name or not description or not technologies:
        st.error("Please fill in **Project Name**, **Description**, and **Technologies Used**.")
        return
        
    entry = {
        "name": name,
        "description": description,
        # Split technologies by comma and strip whitespace
        "technologies": [t.strip() for t in technologies.split(',') if t.strip()], 
        "app_link": app_link if app_link else "N/A"
    }
    
    if state_key not in st.session_state:
        st.session_state[state_key] = []
        
    st.session_state[state_key].append(entry)
    st.toast(f"Added Project: {name}")

def remove_entry(index, state_key, entry_type='Item'):
    """
    Generic callback function to remove an entry by index from a specified list in session state.
    The change to session state triggers the re-render automatically.
    """
    if 0 <= index < len(st.session_state.get(state_key, [])):
        entry_data = st.session_state[state_key][index]
        if state_key == 'form_education':
            removed_name = entry_data.get('degree', entry_type)
        elif state_key == 'form_experience':
            removed_name = entry_data.get('role', entry_type)
        elif state_key == 'form_certifications':
            removed_name = entry_data.get('name', entry_type)
        elif state_key == 'form_projects':
            removed_name = entry_data.get('name', entry_type)
        else:
            removed_name = entry_type
            
        del st.session_state[state_key][index]
        st.toast(f"Removed {entry_type}: {removed_name}")

# --- CV Generation/Display Logic ---

def format_cv_to_markdown(cv_data, cv_name):
    """Formats the structured CV data into a viewable Markdown string."""
    md = f"""
# {cv_data.get('name', cv_name)}
### Contact & Links
* **Email:** {cv_data.get('email', 'N/A')}
* **Phone:** {cv_data.get('phone', 'N/A')}
* **LinkedIn:** [{cv_data.get('linkedin', 'N/A')}]({cv_data.get('linkedin', '#')})
* **GitHub:** [{cv_data.get('github', 'N/A')}]({cv_data.get('github', '#')})

---
## Summary
> {cv_data.get('summary', 'N/A')}

---
## Skills
* {', '.join(cv_data.get('skills', ['N/A']))}

---
## Experience
"""
    if cv_data.get('experience'):
        for exp in cv_data['experience']:
            md += f"""
### **{exp.get('role', 'N/A')}**
* **Company:** {exp.get('company', 'N/A')}
* **Dates:** {exp.get('dates', 'N/A')}
* **Key Project/Focus:** {exp.get('project', 'General Duties')}
"""
    else:
        md += "* No experience entries found."

    md += """
---
## Education
"""
    if cv_data.get('education'):
        for edu in cv_data['education']:
            md += f"""
### **{edu.get('degree', 'N/A')}**
* **Institution:** {edu.get('college', 'N/A')} ({edu.get('university', 'N/A')})
* **Dates:** {edu.get('dates', 'N/A')}
"""
    else:
        md += "* No education entries found."
    
    md += """
---
## Certifications
"""
    if cv_data.get('certifications'):
        for cert in cv_data['certifications']:
            md += f"""
* **{cert.get('name', 'N/A')}** - {cert.get('title', 'N/A')}
    * *Issued by:* {cert.get('given_by', 'N/A')}
    * *Date:* {cert.get('date_received', 'N/A')}
"""
    else:
        md += "* No certification entries found."
        
    md += """
---
## Projects
"""
    if cv_data.get('projects'):
        for proj in cv_data['projects']:
            tech_str = ', '.join(proj.get('technologies', []))
            md += f"""
### **{proj.get('name', 'N/A')}**
* *Description:* {proj.get('description', 'N/A')}
* *Technologies:* {tech_str}
"""
    else:
        md += "* No project entries found."
        
    md += """
---
## Strengths
"""
    if cv_data.get('strength'):
        md += "* " + "\n* ".join(cv_data.get('strength', ['N/A']))
    else:
        md += "* No strengths listed."

    return md

def generate_and_display_cv(cv_name):
    """Generates the final structured CV data from form states and displays it."""
    
    if cv_name not in st.session_state.managed_cvs:
        st.error(f"Error: CV '{cv_name}' not found in managed CVs.")
        return
        
    cv_data = st.session_state.managed_cvs[cv_name]
    
    st.markdown(f"### 📄 CV View: **{cv_name}**")
    
    tab_md, tab_json, tab_pdf = st.tabs(["Markdown View", "JSON Data", "PDF Download (Mock)"])

    # --- Markdown View ---
    with tab_md:
        md_output = format_cv_to_markdown(cv_data, cv_name)
        st.markdown(md_output)

    # --- JSON View ---
    with tab_json:
        st.code(json.dumps(cv_data, indent=4), language="json")
        st.download_button(
            label="Download JSON",
            data=json.dumps(cv_data, indent=4),
            file_name=f"{cv_name}_data.json",
            mime="application/json",
            key=f"download_json_btn_{cv_name}" 
        )
        
    # --- PDF View ---
    with tab_pdf:
        pdf_bytes = generate_pdf_mock(cv_data, cv_name)
        if isinstance(pdf_bytes, str):
             st.warning(pdf_bytes) # Displays the error message if PDF generation fails
        else:
            st.info("The PDF generation is a simplified mock. In a real app, a professional library would be used here.")
            st.download_button(
                label="Download CV as PDF",
                data=pdf_bytes,
                file_name=f"{cv_name}.pdf",
                mime="application/pdf",
                key=f"download_pdf_btn_{cv_name}"
            )


# -------------------------
# TAB FUNCTIONS
# -------------------------

def tab_cv_management():
    st.header("📊 CV Management")
    
    # Initialization for list-based state (done here for tab scope)
    if "form_education" not in st.session_state:
        st.session_state.form_education = []
    if "form_experience" not in st.session_state: 
        st.session_state.form_experience = []
    if "form_certifications" not in st.session_state:
        st.session_state.form_certifications = []
    if "form_projects" not in st.session_state: 
        st.session_state.form_projects = []

    tab_upload, tab_form, tab_view = st.tabs(["Upload & Parse Resume", "Prepare your CV (Form-Based)", "View Saved CVs"])

    with tab_upload:
        st.markdown("### Upload & Parse New CV")
        st.caption("Upload a document, and the AI will extract structured data for management.")
        
        new_cv_file = st.file_uploader(
            "Upload a PDF or DOCX Resume",
            type=["pdf", "docx"],
            key="new_cv_upload"
        )

        if new_cv_file:
            cv_name = st.text_input("Name this CV version (e.g., 'Tech Resume')", 
                                    value=new_cv_file.name.split('.')[0], key="upload_cv_name_input")
            
            if st.button(f"Save & Parse '{cv_name}'", type="primary", key="save_parsed_cv"):
                if not GROQ_API_KEY:
                    st.error("❌ AI Analysis is disabled. Cannot parse CV for storage.")
                    return

                with st.spinner(f"Parsing CV: {new_cv_file.name}..."):
                    try:
                        temp_dir = tempfile.mkdtemp()
                        temp_path = os.path.join(temp_dir, new_cv_file.name)
                        with open(temp_path, "wb") as f:
                            f.write(new_cv_file.getbuffer())
                        
                        file_type = get_file_type(temp_path)
                        text = extract_content(file_type, temp_path)
                            
                        parsed_data = parse_with_llm(text)

                        if "error" in parsed_data:
                            st.error(f"Parsing failed: {parsed_data.get('error', 'Unknown error')}")
                        else:
                            st.session_state.managed_cvs[cv_name] = parsed_data
                            st.success(f"✅ CV **'{cv_name}'** successfully parsed and saved!")
                            st.session_state.current_resume_name = cv_name
                            st.rerun() 
                            
                    except Exception as e:
                        st.error(f"An unexpected error occurred during parsing: {e}")
                        st.code(traceback.format_exc())

    with tab_form:
        st.markdown("### Prepare your CV (Form-Based)")
        st.caption("Manually enter your CV details. This will be saved as a structured JSON CV.")
        
        # Renamed CV name input
        st.text_input(
            "**Name this new CV (e.g., 'Manual 2025 CV'):**", 
            key="form_cv_key_name", 
            on_change=save_form_cv, # Auto-save on changing CV Name
            help="Changing this name will save the current form data under the new name."
        )

        # --- 1. Personal Details Form ---
        st.markdown("#### 1. Personal & Summary Details")
        
        col_name, col_email = st.columns(2)
        with col_name:
            st.text_input("Full Name", key="form_name_value")
        with col_email:
            st.text_input("Email", key="form_email_value")
            
        col_phone, col_linkedin, col_github = st.columns(3)
        with col_phone:
            st.text_input("Phone Number", key="form_phone_value")
        with col_linkedin:
            st.text_input("LinkedIn Link", key="form_linkedin_value")
        with col_github:
            st.text_input("GitHub Link", key="form_github_value")
            
        st.text_area("Career Summary / Objective (3-4 sentences)", height=100, key="form_summary_value")
        
        # --- Simplified Save Button for changes in Personal/Summary ---
        st.button("💾 Save Details", type="primary", use_container_width=True, help="Save the current form data to the CV name specified above.", on_click=save_form_cv)
        
        st.markdown("---")

        # --- 2. Skills ---
        st.markdown("#### 2. Skills")
        st.text_area("Skills (Enter one skill per line)", height=100, key="form_skills_value")
        
        # --- 3. Experience ---
        st.markdown("#### 3. Experience")
        
        with st.form("form_experience_entry", clear_on_submit=True):
            col_comp, col_role = st.columns(2)
            with col_comp:
                new_company = st.text_input("Company Name", key="form_new_company")
            with col_role:
                new_role = st.text_input("Role / Designation", key="form_new_role")
            
            col_ctc, col_proj = st.columns(2)
            with col_ctc:
                new_ctc = st.text_input("CTC (Optional)", key="form_new_ctc")
            with col_proj:
                new_project = st.text_input("Key Project / Main Focus", key="form_new_project")

            col_from, col_to = st.columns(2)
            with col_from:
                new_exp_date_from = st.date_input("Date From (Start)", value=date(2020, 1, 1), key="form_new_exp_date_from")
            with col_to:
                new_exp_date_to = st.date_input("Date To (End/Present)", value=date.today(), key="form_new_exp_date_to")

            if st.form_submit_button("Add Experience and Save CV"):
                add_experience_entry(
                    new_company.strip(), 
                    new_role.strip(), 
                    new_ctc.strip(),
                    new_project.strip(),
                    new_exp_date_from, 
                    new_exp_date_to,
                    state_key='form_experience'
                )
                save_form_cv() # Save CV after adding entry

        if st.session_state.form_experience:
            st.markdown("##### Current Experience Entries:")
            experience_list = st.session_state.form_experience
            for i, entry in enumerate(experience_list):
                col_exp, col_rem = st.columns([0.8, 0.2])
                with col_exp:
                    st.code(f"{entry['role']} at {entry['company']} ({entry['dates']})", language="text")
                with col_rem:
                    # Rerun will automatically update the view after removal
                    st.button(
                        "Remove", 
                        key=f"remove_exp_{i}", 
                        on_click=remove_entry, 
                        args=(i, 'form_experience', 'Experience'),
                        type="secondary", 
                        use_container_width=True
                    )
        
        # --- 4. Education ---
        st.markdown("#### 4. Education")

        with st.form("form_education_entry", clear_on_submit=True):
            col_degree, col_college = st.columns(2)
            with col_degree:
                new_degree = st.text_input("Degree/Qualification", key="form_new_degree")
            with col_college:
                new_college = st.text_input("College/Institution Name", key="form_new_college")
            
            new_university = st.text_input("Affiliating University Name", key="form_new_university")

            col_from, col_to = st.columns(2)
            with col_from:
                new_date_from = st.date_input("Date From (Start)", value=date(2018, 1, 1), key="form_new_date_from")
            with col_to:
                new_date_to = st.date_input("Date To (End/Expected)", value=date.today(), key="form_new_date_to")

            if st.form_submit_button("Add Education and Save CV"):
                add_education_entry(
                    new_degree.strip(), 
                    new_college.strip(), 
                    new_university.strip(), 
                    new_date_from, 
                    new_date_to,
                    state_key='form_education'
                )
                save_form_cv() # Save CV after adding entry

        if st.session_state.form_education:
            st.markdown("##### Current Education Entries:")
            for i, entry in enumerate(st.session_state.form_education):
                col_edu, col_rem = st.columns([0.8, 0.2])
                with col_edu:
                    st.code(f"{entry['degree']} at {entry['college']} ({entry['dates']})", language="text")
                with col_rem:
                    st.button(
                        "Remove", 
                        key=f"remove_edu_{i}", 
                        on_click=remove_entry, 
                        args=(i, 'form_education', 'Education'),
                        type="secondary",
                        use_container_width=True
                    )
        
        # -----------------------------
        # 5. CERTIFICATIONS SECTION
        # -----------------------------
        st.markdown("#### 5. Certifications")
        
        with st.form("form_certification_entry", clear_on_submit=True):
            col_cert_name, col_cert_title = st.columns(2)
            with col_cert_name:
                new_cert_name = st.text_input("Certification Name (e.g., AWS Certified)", key="form_new_cert_name")
            with col_cert_title:
                new_cert_title = st.text_input("Title (e.g., Solutions Architect - Associate)", key="form_new_cert_title")
                
            col_given, col_received = st.columns(2)
            with col_given:
                new_given_by = st.text_input("Given By (Issuing Authority)", key="form_new_given_by")
            with col_received:
                new_received_by = st.text_input("Received By Name (Optional)", key="form_new_received_by")
                
            new_course = st.text_input("Related Course/Training (Optional)", key="form_new_course")

            new_date_received = st.date_input("Date Received", value=date.today(), key="form_new_date_received")

            if st.form_submit_button("Add Certification and Save CV"):
                add_certification_entry(
                    new_cert_name.strip(), 
                    new_cert_title.strip(), 
                    new_given_by.strip(), 
                    new_received_by.strip(),
                    new_course.strip(),
                    new_date_received,
                    state_key='form_certifications'
                )
                save_form_cv() # Save CV after adding entry

        if st.session_state.form_certifications:
            st.markdown("##### Current Certification Entries:")
            for i, entry in enumerate(st.session_state.form_certifications):
                col_cert, col_rem = st.columns([0.8, 0.2])
                with col_cert:
                    st.code(f"{entry['name']} - {entry['title']} (Issued: {entry['date_received']})", language="text")
                with col_rem:
                    st.button(
                        "Remove", 
                        key=f"remove_cert_{i}", 
                        on_click=remove_entry, 
                        args=(i, 'form_certifications', 'Certification'),
                        type="secondary",
                        use_container_width=True
                    )
        
        # -----------------------------
        # 6. PROJECTS SECTION 
        # -----------------------------
        st.markdown("#### 6. Projects")
        
        with st.form("form_project_entry", clear_on_submit=True):
            new_project_name = st.text_input("Project Name", key="form_new_project_name")
            new_project_description = st.text_area("Description of Project", height=100, key="form_new_project_description")
                
            col_tech, col_link = st.columns(2)
            with col_tech:
                new_technologies = st.text_input("Technologies Used (Comma separated list, e.g., Python, SQL, Streamlit)", key="form_new_technologies")
            with col_link:
                new_app_link = st.text_input("App Link / Repository URL (Optional)", key="form_new_app_link")

            if st.form_submit_button("Add Project and Save CV"):
                add_project_entry(
                    new_project_name.strip(), 
                    new_project_description.strip(), 
                    new_technologies.strip(), 
                    new_app_link.strip(),
                    state_key='form_projects'
                )
                save_form_cv() # Save CV after adding entry

        if st.session_state.form_projects:
            st.markdown("##### Current Project Entries:")
            
            for i, entry in enumerate(st.session_state.form_projects):
                with st.container(border=True):
                    st.markdown(f"**{i+1}. {entry['name']}**")
                    st.caption(f"Technologies: {', '.join(entry['technologies'])}")
                    st.markdown(f"Description: *{entry['description']}*")
                    if entry['app_link'] != "N/A":
                        st.markdown(f"Link: [{entry['app_link']}]({entry['app_link']})")
                    
                    st.button(
                        "Remove Project", 
                        key=f"remove_project_{i}", 
                        on_click=remove_entry, 
                        args=(i, 'form_projects', 'Project'),
                        type="secondary"
                    )
        
        # -----------------------------
        # 7. STRENGTHS SECTION
        # -----------------------------
        st.markdown("#### 7. Strengths")
        st.text_area(
            "Your Key Strengths (Enter one strength or attribute per line)", 
            height=100, 
            key="form_strengths_input",
            help="E.g., Problem-Solving, Team Leadership, Adaptability, Communication"
        )
        
        # --- Final Save Button ---
        st.markdown("---")
        st.button("💾 **Save Final CV Details**", key="final_save_button", type="primary", use_container_width=True, on_click=save_form_cv)
        
        st.markdown("---")
        
        # --- CV Output Display Section ---
        if st.session_state.show_cv_output:
            generate_and_display_cv(st.session_state.show_cv_output)
            st.markdown("---")


    with tab_view:
        st.markdown("### View Saved CVs")
        if not st.session_state.managed_cvs:
            st.info("No CVs saved yet. Upload or create one in the other tabs.")
        else:
            cv_names = list(st.session_state.managed_cvs.keys())
            
            default_index = cv_names.index(st.session_state.current_resume_name) if st.session_state.get('current_resume_name') in cv_names else 0

            selected_cv = st.selectbox("Select a CV to view details:", cv_names, index=default_index, key="cv_select_view")
            
            if selected_cv:
                data = st.session_state.managed_cvs[selected_cv]
                st.markdown(f"**Current Active CV:** `{st.session_state.get('current_resume_name', 'None')}`")
                st.markdown(f"**Name:** {data.get('name', 'N/A')}")
                st.markdown(f"**Summary:** *{data.get('summary', 'N/A')}*")
                
                col_actions_1, col_actions_2 = st.columns(2)
                with col_actions_1:
                    if st.button("View/Download", key="view_cv_from_list", use_container_width=True):
                        st.session_state.show_cv_output = selected_cv
                        st.rerun()
                with col_actions_2:
                    if st.button("Delete CV", key="delete_cv", use_container_width=True):
                        del st.session_state.managed_cvs[selected_cv]
                        if 'current_resume_name' in st.session_state and st.session_state.current_resume_name == selected_cv:
                            del st.session_state.current_resume_name
                        if 'show_cv_output' in st.session_state and st.session_state.show_cv_output == selected_cv:
                            del st.session_state.show_cv_output
                        st.warning(f"CV **'{selected_cv}'** deleted.")
                        st.rerun()
                
                st.markdown("---")
                
                # Dynamic View when clicking 'View/Download' from this tab
                if st.session_state.show_cv_output == selected_cv:
                    generate_and_display_cv(selected_cv)
                else:
                    with st.expander(f"View Raw JSON Data for '{selected_cv}'"):
                        st.json(data)


# -------------------------
# CANDIDATE DASHBOARD FUNCTION
# -------------------------

def candidate_dashboard():
    st.title("🧑‍💻 Candidate Dashboard")
    st.caption("Manage your CVs using Structured Form Data and Parsing.")
    
    col_header, col_logout = st.columns([4, 1])
    with col_logout:
        if st.button("🚪 Log Out", use_container_width=True):
            # Keys to delete to fully reset the candidate session
            keys_to_delete = ['candidate_results', 'current_resume', 'manual_education', 'managed_cvs', 'current_resume_name', 'form_education', 'form_experience', 'form_certifications', 'form_projects', 'show_cv_output', 'form_name_value', 'form_email_value', 'form_phone_value', 'form_linkedin_value', 'form_github_value', 'form_summary_value', 'form_skills_value', 'form_strengths_input', 'form_cv_key_name']
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            go_to("login")
            st.rerun() 
            
    st.markdown("---")

    # --- Session State Initialization for Candidate ---
    if "managed_cvs" not in st.session_state: st.session_state.managed_cvs = {} 
    if "current_resume_name" not in st.session_state: st.session_state.current_resume_name = None 
    if "show_cv_output" not in st.session_state: st.session_state.show_cv_output = None 
    
    # Initialize keys for personal details to ensure stability
    if "form_cv_key_name" not in st.session_state: st.session_state.form_cv_key_name = ""
    if "form_name_value" not in st.session_state: st.session_state.form_name_value = ""
    if "form_email_value" not in st.session_state: st.session_state.form_email_value = ""
    if "form_phone_value" not in st.session_state: st.session_state.form_phone_value = ""
    if "form_linkedin_value" not in st.session_state: st.session_state.form_linkedin_value = ""
    if "form_github_value" not in st.session_state: st.session_state.form_github_value = ""
    if "form_summary_value" not in st.session_state: st.session_state.form_summary_value = ""
    if "form_skills_value" not in st.session_state: st.session_state.form_skills_value = ""
    if "form_strengths_input" not in st.session_state: st.session_state.form_strengths_input = ""


    # --- Main Tabs ---
    # Only the CV Management tab remains
    tab_cv_management()


# -------------------------
# MOCK LOGIN AND MAIN APP LOGIC (For full execution)
# -------------------------

def admin_dashboard():
    st.title("Admin Dashboard (Mock)")
    st.info("This is a placeholder for the Admin Dashboard. Use the Log Out button to switch.")
    if st.button("🚪 Log Out (Switch to Candidate)"):
        go_to("candidate_dashboard")
        st.session_state.user_type = "candidate"
        st.rerun()

def login_page():
    st.title("Welcome to PragyanAI")
    st.header("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username (Enter 'candidate' or 'admin')")
        password = st.text_input("Password (Any value)", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username.lower() == "candidate":
                st.session_state.logged_in = True
                st.session_state.user_type = "candidate"
                go_to("candidate_dashboard")
                st.success("Logged in as Candidate!")
                st.rerun()
            elif username.lower() == "admin":
                st.session_state.logged_in = True
                st.session_state.user_type = "admin"
                go_to("admin_dashboard")
                st.success("Logged in as Admin!")
                st.rerun()
            else:
                st.error("Invalid username. Please use 'candidate' or 'admin'.")

# --- Main App Execution ---

if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="PragyanAI Candidate Dashboard")

    # Initialize state for navigation and authentication
    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'user_type' not in st.session_state: st.session_state.user_type = None
    
    if st.session_state.logged_in:
        if st.session_state.user_type == "candidate":
            candidate_dashboard()
        elif st.session_state.user_type == "admin":
            admin_dashboard() 
    else:
        login_page()
