import streamlit as st
from datetime import date
import json
import base64

# --- Helper Functions (CRITICAL for Streamlit Session State Management) ---

# These functions are called by the button's 'on_click' callback. 
# They update the data and set 'force_rerun_for_add' to True.

def add_education_entry_handler():
    """Adds a new education entry from temporary form inputs."""
    edu_data = {
        "degree": st.session_state.get("temp_edu_degree_key", "").strip(),
        "college": st.session_state.get("temp_edu_college_key", "").strip(),
        "university": st.session_state.get("temp_edu_university_key", "").strip(),
        "from_year": st.session_state.get("temp_edu_from_year_key_sel", str(date.today().year)).strip(),
        "to_year": st.session_state.get("temp_edu_to_year_key_sel", "Present").strip(),
        "score": st.session_state.get("temp_edu_score_key", "").strip(),
        "type": st.session_state.get("temp_edu_type_key_sel", "CGPA").strip(),
    }
    if edu_data['degree'] and edu_data['college']:
        st.session_state.cv_form_data['structured_education'].append(edu_data)
        st.session_state.force_rerun_for_add = True

def remove_education_entry(index):
    """Removes an education entry by index and forces a rerun."""
    if 0 <= index < len(st.session_state.cv_form_data['structured_education']):
        st.session_state.cv_form_data['structured_education'].pop(index)
        st.session_state.force_rerun_for_add = True

def add_experience_entry_handler():
    """Adds a new experience entry from temporary form inputs."""
    exp_data = {
        "company": st.session_state.get("temp_exp_company_key", "").strip(),
        "role": st.session_state.get("temp_exp_role_key", "").strip(),
        "from_year": st.session_state.get("temp_exp_from_year_key_sel", str(date.today().year)).strip(),
        "to_year": st.session_state.get("temp_exp_to_year_key_sel", "Present").strip(),
        "ctc": st.session_state.get("temp_exp_ctc_key", "").strip(),
        "responsibilities": st.session_state.get("temp_exp_responsibilities_key", "").strip()
    }
    if exp_data['company'] and exp_data['role']:
        st.session_state.cv_form_data['structured_experience'].append(exp_data)
        st.session_state.force_rerun_for_add = True

def remove_experience_entry(index):
    """Removes an experience entry by index and forces a rerun."""
    if 0 <= index < len(st.session_state.cv_form_data['structured_experience']):
        st.session_state.cv_form_data['structured_experience'].pop(index)
        st.session_state.force_rerun_for_add = True

def add_certification_entry_handler():
    """Adds a new certification entry from temporary form inputs."""
    cert_data = {
        "title": st.session_state.get("temp_cert_title_key", "").strip(),
        "given_by": st.session_state.get("temp_cert_given_by_name_key", "").strip(),
        "organization_name": st.session_state.get("temp_cert_organization_name_key", "").strip(),
        "issue_date": st.session_state.get("temp_cert_issue_date_key", "").strip()
    }
    if cert_data['title'] and (cert_data['given_by'] or cert_data['organization_name']):
        st.session_state.cv_form_data['structured_certifications'].append(cert_data)
        st.session_state.force_rerun_for_add = True

def remove_certification_entry(index):
    """Removes a certification entry by index and forces a rerun."""
    if 0 <= index < len(st.session_state.cv_form_data['structured_certifications']):
        st.session_state.cv_form_data['structured_certifications'].pop(index)
        st.session_state.force_rerun_for_add = True

def add_project_entry_handler():
    """Adds a new project entry from temporary form inputs."""
    proj_data = {
        "name": st.session_state.get("temp_proj_name_key", "").strip(),
        "link": st.session_state.get("temp_proj_link_key", "").strip(),
        "description": st.session_state.get("temp_proj_description_key", "").strip(),
        "technologies": [t.strip() for t in st.session_state.get("temp_proj_technologies_key", "").split(',') if t.strip()]
    }
    
    if proj_data['name'] and proj_data['description']:
        st.session_state.cv_form_data['structured_projects'].append(proj_data)
        st.session_state.force_rerun_for_add = True

def remove_project_entry(index):
    """Removes a project entry by index and forces a rerun."""
    if 0 <= index < len(st.session_state.cv_form_data['structured_projects']):
        st.session_state.cv_form_data['structured_projects'].pop(index)
        st.session_state.force_rerun_for_add = True

# Utility for formatting for download/preview (simplified)
def format_parsed_json_to_markdown(data):
    """Simple function to format the final data for markdown preview."""
    markdown_text = ""
    for key, value in data.items():
        if key in ["skills", "strength"]:
             markdown_text += f"## {key.title()}\n"
             markdown_text += "\n".join([f"- {item}" for item in value]) + "\n\n"
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            markdown_text += f"## {key.title()}\n"
            for item in value:
                # Determine primary title for the entry
                title = item.get('title') or item.get('role') or item.get('name') or item.get('degree')
                markdown_text += f"### {title}\n"
                for sub_key, sub_value in item.items():
                    if sub_key not in ["title", "role", "name", "degree", "description", "technologies"]:
                        markdown_text += f"- **{sub_key.replace('_', ' ').title()}**: {sub_value}\n"
                
                if item.get('technologies'):
                    markdown_text += f"- **Technologies**: {', '.join(item['technologies'])}\n"

                if item.get('description'):
                     markdown_text += f"**Description/Details**:\n{item['description']}\n"
                markdown_text += "\n"
        elif value:
            markdown_text += f"## {key.replace('_', ' ').title()}\n"
            markdown_text += f"{value}\n\n"
            
    return markdown_text

# Utility for generating HTML (simplified)
def generate_cv_html(data):
    """Generates a basic HTML structure for the CV data."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{data.get('name', 'CV')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
            h1 {{ border-bottom: 2px solid #333; padding-bottom: 5px; }}
            h2 {{ color: #555; margin-top: 20px; }}
            .section-item {{ margin-bottom: 10px; padding-left: 15px; border-left: 3px solid #ccc; }}
        </style>
    </head>
    <body>
        <h1>{data.get('name', 'Candidate')}</h1>
        <p>Email: {data.get('email', '')} | Phone: {data.get('phone', '')} | LinkedIn: {data.get('linkedin', '')}</p>
        
        <h2>Professional Summary</h2>
        <p>{data.get('personal_details', '')}</p>
    """
    
    if data.get('experience'):
        html_content += "<h2>Experience</h2>"
        for exp in data['experience']:
            html_content += f"""
            <div class="section-item">
                <h3>{exp.get('role', 'Role')} at {exp.get('company', 'Company')}</h3>
                <p>{exp.get('from_year', '')} - {exp.get('to_year', '')}</p>
                <p>Responsibilities: {exp.get('responsibilities', '')}</p>
            </div>
            """
    
    if data.get('education'):
        html_content += "<h2>Education</h2>"
        for edu in data['education']:
            html_content += f"""
            <div class="section-item">
                <h3>{edu.get('degree', 'Degree')} from {edu.get('college', 'College')}</h3>
                <p>{edu.get('from_year', '')} - {edu.get('to_year', '')} | Score: {edu.get('score', '')} {edu.get('type', '')}</p>
            </div>
            """

    if data.get('skills'):
        html_content += "<h2>Skills</h2><p>" + ", ".join(data['skills']) + "</p>"
    
    html_content += "</body></html>"
    return html_content

# --- Main Streamlit Function ---

def cv_management_tab_content():
    st.header("📝 Prepare Your CV")
    st.markdown("### 1. Form Based CV Builder")
    
    st.info("""
    **CV Builder Workflow:** Use the dynamic input fields (e.g., Education, Experience, Projects) to add individual entries by clicking the corresponding **'Add Entry'** button. The current entries are listed below their respective input sections. When finished, click the final **'Generate and Load ALL CV Data'** button at the bottom to finalize all CV sections.
    """)

    # --- Session State Initialization for CV Builder ---
    default_parsed = {
        "name": "", "email": "", "phone": "", "linkedin": "", "github": "",
        "skills": [], "experience": [], "education": [], "certifications": [], 
        "projects": [], "strength": [], "personal_details": "",
        "structured_experience": [],
        "structured_certifications": [],
        "structured_education": [],
        "structured_projects": []
    }
    
    if "cv_form_data" not in st.session_state:
        st.session_state.cv_form_data = default_parsed
        if st.session_state.get('parsed'):
             st.session_state.cv_form_data.update(st.session_state.parsed)
             
    # Ensure lists are initialized correctly
    for key in ['structured_experience', 'structured_certifications', 'structured_education', 'structured_projects', 'skills', 'strength']:
         if not isinstance(st.session_state.cv_form_data.get(key), list):
             st.session_state.cv_form_data[key] = []
         
    if 'force_rerun_for_add' not in st.session_state:
        st.session_state.force_rerun_for_add = False
    
    if 'full_text' not in st.session_state:
        st.session_state.full_text = ""
        
    if 'parsed' not in st.session_state: # Ensure 'parsed' exists for the final download section
        st.session_state.parsed = {}

    # Initialize/reset year options for date pickers
    current_year = date.today().year
    year_options = [str(y) for y in range(current_year, 1950, -1)]
    to_year_options = ["Present"] + year_options
    
    
    # --- CV Builder Form (SINGLE BLOCK) ---
    with st.form("cv_builder_form", clear_on_submit=False):
        
        # --- 1. PERSONAL & CONTACT DETAILS ---
        st.subheader("1. Personal, Contact, and Summary Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.cv_form_data['name'] = st.text_input(
                "Full Name", 
                value=st.session_state.cv_form_data.get('name', ''), 
                key="cv_name_input"
            ).strip() 
        with col2:
            st.session_state.cv_form_data['email'] = st.text_input(
                "Email Address", 
                value=st.session_state.cv_form_data.get('email', ''), 
                key="cv_email_input"
            ).strip() 
        with col3:
            st.session_state.cv_form_data['phone'] = st.text_input(
                "Phone Number", 
                value=st.session_state.cv_form_data.get('phone', ''), 
                key="cv_phone_input"
            ).strip() 
        
        col4, col5 = st.columns(2)
        with col4:
            st.session_state.cv_form_data['linkedin'] = st.text_input(
                "LinkedIn Profile URL", 
                value=st.session_state.cv_form_data.get('linkedin', ''), 
                key="cv_linkedin_input"
            ).strip() 
        with col5:
            st.session_state.cv_form_data['github'] = st.text_input(
                "GitHub Profile URL", 
                value=st.session_state.cv_form_data.get('github', ''), 
                key="cv_github_input"
            ).strip() 
        
        st.session_state.cv_form_data['personal_details'] = st.text_area(
            "Professional Summary (A brief pitch about yourself)", 
            value=st.session_state.cv_form_data.get('personal_details', ''), 
            height=100,
            key="cv_personal_details_input"
        ).strip() 
        
        # --- 2. SKILLS ---
        st.markdown("---")
        st.subheader("2. Key Skills (One Item per Line)")

        skills_text = "\n".join(st.session_state.cv_form_data.get('skills', []))
        new_skills_text = st.text_area(
            "Technical and Soft Skills", 
            value=skills_text,
            height=100,
            key="cv_skills_input_form" 
        )
        st.session_state.cv_form_data['skills'] = [s.strip() for s in new_skills_text.split('\n') if s.strip()]
        
        # --- 3. DYNAMIC EDUCATION INPUT FIELDS & ADD BUTTON ---
        st.markdown("---")
        st.subheader("3. Dynamic Education Management")
        
        col_d, col_c = st.columns(2)
        with col_d:
            st.text_input("Degree/Qualification", key="temp_edu_degree_key", placeholder="e.g., M.Sc. Computer Science")
            
        with col_c:
            st.text_input("College Name", key="temp_edu_college_key", placeholder="e.g., MIT, Chennai")
            
        st.text_input("University Name", key="temp_edu_university_key", placeholder="e.g., Anna University")
        
        col_fy, col_ty = st.columns(2)
        with col_fy:
            st.selectbox("From Year", options=year_options, key="temp_edu_from_year_key_sel")
            
        with col_ty:
            st.selectbox("To Year", options=to_year_options, key="temp_edu_to_year_key_sel")
            
        col_s, col_st = st.columns([2, 1])
        with col_s:
            st.text_input("CGPA or Score Value", key="temp_edu_score_key", placeholder="e.g., 8.5 or 90")
        with col_st:
            st.selectbox("Type", options=["CGPA", "Percentage", "Grade"], key="temp_edu_type_key_sel")
            
        # Add Entry Button
        st.form_submit_button(
            "➕ Add Education Entry", 
            key="add_edu_button_form", 
            type="secondary", 
            use_container_width=True, 
            on_click=add_education_entry_handler,
            help="Adds the entry above and reloads the page to show the current list."
        )
        
        st.markdown("---") 
        
        # --- 4. DYNAMIC EXPERIENCE INPUT FIELDS & ADD BUTTON ---
        st.subheader("4. Dynamic Professional Experience Management")
        
        col_c, col_r = st.columns(2)
        with col_c:
            st.text_input("Company Name", key="temp_exp_company_key", placeholder="e.g., Google")
            
        with col_r:
            st.text_input("Role/Title", key="temp_exp_role_key", placeholder="e.g., Data Scientist")

        col_fy_exp, col_ty_exp, col_c3 = st.columns(3)
        
        with col_fy_exp:
            st.selectbox("From Year", options=year_options, key="temp_exp_from_year_key_sel")
            
        with col_ty_exp:
            st.selectbox("To Year", options=to_year_options, key="temp_exp_to_year_key_sel")
            
        with col_c3:
            st.text_input("CTC (Annual)", key="temp_exp_ctc_key", placeholder="e.g., $150k / 20L INR")

        st.text_area(
            "Key Responsibilities/Achievements (Brief summary)", 
            height=70, 
            key="temp_exp_responsibilities_key"
        )
        
        # Add Entry Button
        st.form_submit_button(
            "➕ Add This Experience", 
            key="add_exp_button_form", 
            type="secondary", 
            use_container_width=True, 
            on_click=add_experience_entry_handler,
            help="Adds the entry above and reloads the page to show the current list."
        )
        
        st.markdown("---") 

        # --- 5. DYNAMIC CERTIFICATION INPUT FIELDS & ADD BUTTON ---
        st.subheader("5. Dynamic Certifications Management")
        
        col_t, col_g, col_o = st.columns(3) 
        with col_t:
            st.text_input("Certification Title", key="temp_cert_title_key", placeholder="e.g., Google Cloud Architect")
            
        with col_g:
            st.text_input(
                "Issue By Name (Sir/Mam)", 
                key="temp_cert_given_by_name_key", 
                placeholder="e.g., Dr. Jane Doe"
            )
            
        with col_o:
            st.text_input(
                "Issuing Organization Name", 
                key="temp_cert_organization_name_key", 
                placeholder="e.g., Coursera, AWS, PMI"
            )

        col_d, _ = st.columns(2)
        with col_d:
            st.text_input("Issue Date (YYYY-MM-DD or Year)", key="temp_cert_issue_date_key", placeholder="e.g., 2024-05-15 or 2023")

        # Add Entry Button
        st.form_submit_button(
            "➕ Add Certificate", 
            key="add_cert_button_form", 
            type="secondary", 
            use_container_width=True, 
            on_click=add_certification_entry_handler,
            help="Adds the entry above and reloads the page to show the current list."
        )

        st.markdown("---")
        
        # --- 6. DYNAMIC PROJECTS INPUT FIELDS & ADD BUTTON ---
        st.subheader("6. Dynamic Projects Management")
        
        st.text_input("Project Name", key="temp_proj_name_key", placeholder="e.g., NLP Sentiment Analysis Model")
        st.text_input("Project Link (Optional)", key="temp_proj_link_key", placeholder="e.g., https://github.com/myuser/myproject")
        
        col_desc, col_tech = st.columns(2)
        with col_desc:
            st.text_area(
                "Project Description (Key goal and achievements)", 
                height=100, 
                key="temp_proj_description_key",
                placeholder="Developed a machine learning model to categorize customer reviews, improving service response time by 15%."
            )
        with col_tech:
             st.text_area(
                "Technologies Used (Comma separated list)", 
                height=100, 
                key="temp_proj_technologies_key",
                placeholder="e.g., Python, TensorFlow, Keras, Flask"
            )

        # Add Entry Button (FIXED: on_click used)
        st.form_submit_button(
            "➕ Add Project", 
            key="add_proj_button_form", 
            type="secondary", 
            use_container_width=True, 
            on_click=add_project_entry_handler,
            help="Adds the project above and reloads the page to show the current list."
        )
            
        st.markdown("---") 

        # --- 7. STRENGTHS ---
        st.subheader("7. Strengths (One Item per Line)")
        strength_text = "\n".join(st.session_state.cv_form_data.get('strength', []))
        new_strength_text = st.text_area(
            "Key Personal Qualities", 
            value=strength_text,
            height=70,
            key="cv_strength_input_form"
        )
        st.session_state.cv_form_data['strength'] = [s.strip() for s in new_strength_text.split('\n') if s.strip()]

        
        st.markdown("---") 

        # --- 8. FINAL SUBMISSION BUTTON (Inside the form) ---
        st.markdown("---")
        st.subheader("8. Generate or Load ALL CV Data")
        st.warning("Click the button below to **finalize** your entire CV data structure using the current form values and the added dynamic entries.")
        submit_form_button = st.form_submit_button("Generate and Load ALL CV Data", type="primary", use_container_width=True)

    
    # --- FORM SUBMISSION LOGIC & RERUN CHECK ---
    if submit_form_button:
        # Final CV Generation
        if not st.session_state.cv_form_data['name'] or not st.session_state.cv_form_data['email']:
            st.error("Please fill in at least your **Full Name** and **Email Address**.")
        else:
            # 1. Synchronize the structured lists into the main keys for AI consumption
            st.session_state.cv_form_data['experience'] = st.session_state.cv_form_data.get('structured_experience', [])
            st.session_state.cv_form_data['certifications'] = st.session_state.cv_form_data.get('structured_certifications', [])
            st.session_state.cv_form_data['education'] = st.session_state.cv_form_data.get('structured_education', [])
            st.session_state.cv_form_data['projects'] = st.session_state.cv_form_data.get('structured_projects', []) 
            
            # 2. Update the main parsed state
            st.session_state.parsed = st.session_state.cv_form_data.copy()
            
            # 3. Create a placeholder full_text 
            compiled_text = ""
            EXCLUDE_KEYS = ["structured_experience", "structured_certifications", "structured_education", "structured_projects"] 
            
            for k, v in st.session_state.cv_form_data.items():
                if k in EXCLUDE_KEYS: continue
                if v and (isinstance(v, str) and v.strip() or isinstance(v, list) and v):
                    compiled_text += f"{k.replace('_', ' ').title()}:\n"
                    if isinstance(v, list):
                        if all(isinstance(item, dict) for item in v):
                             compiled_text += "\n".join([json.dumps(item) for item in v]) + "\n\n"
                        elif all(isinstance(item, str) for item in v):
                            compiled_text += "\n".join([f"- {item}" for item in v]) + "\n\n"
                    else:
                        compiled_text += str(v) + "\n\n"
                        
            st.session_state.full_text = compiled_text
            
            # 4. Reset matching/interview state placeholders (commented out as they likely belong to other tabs)
            # st.session_state.candidate_match_results = []
            # st.session_state.interview_qa = []
            # st.session_state.evaluation_report = ""

            st.success(f"✅ CV data for **{st.session_state.parsed['name']}** successfully generated and loaded!")

    
    # --- Force Rerun for Dynamic Adds (CRITICAL WORKAROUND) ---
    if st.session_state.force_rerun_for_add:
        st.session_state.force_rerun_for_add = False
        st.rerun() # Force rerun to clear inputs and display list update
        
    
    # --- DYNAMIC DISPLAY SECTIONS (OUTSIDE THE FORM, REMOVE BUTTONS HERE) ---
    st.markdown("---") 
    st.markdown("## Current Dynamic Entries")
    
    # Education Display
    st.markdown("### 🎓 Current Education Entries")
    if st.session_state.cv_form_data['structured_education']:
        for i, entry in enumerate(st.session_state.cv_form_data['structured_education']):
            col_disp, col_rem = st.columns([6, 1])
            with col_disp:
                score_display = f"{entry.get('score', 'N/A')} {entry.get('type', '')}".strip()
                st.markdown(f"- **{entry['degree']}** - {entry.get('college', 'N/A')} ({entry['from_year']} - {entry['to_year']}) | Score: {score_display}")
            with col_rem:
                st.button("❌", 
                          key=f"remove_edu_{i}_out", 
                          on_click=remove_education_entry, 
                          args=(i,), 
                          type="primary", 
                          help=f"Remove: {entry['degree']}")
    else:
        st.info("No education entries added yet.")
        
    st.markdown("---")

    # Experience Display
    st.markdown("### 💼 Current Professional Experience Entries")
    if st.session_state.cv_form_data['structured_experience']:
        for i, entry in enumerate(st.session_state.cv_form_data['structured_experience']):
            col_disp, col_rem = st.columns([6, 1])
            with col_disp:
                st.markdown(f"- **{entry['role']}** at {entry['company']} ({entry['from_year']} - {entry['to_year']}) | CTC: {entry['ctc']}")
            with col_rem:
                st.button("❌", 
                          key=f"remove_exp_{i}_out", 
                          on_click=remove_experience_entry, 
                          args=(i,), 
                          type="primary",
                          help=f"Remove: {entry['company']}")
    else:
        st.info("No experience entries added yet.")

    st.markdown("---")
    
    # Certifications Display
    st.markdown("### 🏅 Current Certifications")
    if st.session_state.cv_form_data['structured_certifications']:
        for i, entry in enumerate(st.session_state.cv_form_data['structured_certifications']):
            col_disp, col_rem = st.columns([6, 1])
            with col_disp:
                issuer_info = f"{entry.get('given_by', 'N/A')}"
                if entry.get('organization_name', 'N/A') and entry.get('organization_name', 'N/A') != 'N/A':
                    issuer_info += f" ({entry.get('organization_name', 'N/A')})"
                st.markdown(f"- **{entry['title']}** by {issuer_info} (Issued: {entry['issue_date']})")
            with col_rem:
                st.button("❌", 
                          key=f"remove_cert_{i}_out", 
                          on_click=remove_certification_entry, 
                          args=(i,), 
                          type="primary",
                          help=f"Remove: {entry['title']}")
    else:
        st.info("No certifications added yet.")
        
    st.markdown("---")
    
    # Projects Display
    st.markdown("### 💻 Current Projects")
    if st.session_state.cv_form_data['structured_projects']:
        for i, entry in enumerate(st.session_state.cv_form_data['structured_projects']):
            col_disp, col_rem = st.columns([6, 1])
            with col_disp:
                link_icon = "🔗" if entry.get('link') else ""
                tech_list = ", ".join(entry.get('technologies', []))
                st.markdown(f"- **{entry['name']}** {link_icon} | *Tech: {tech_list}*")
                st.caption(entry.get('description', 'No description.'))
            with col_rem:
                st.button("❌", 
                          key=f"remove_proj_{i}_out", 
                          on_click=remove_project_entry, 
                          args=(i,), 
                          type="primary",
                          help=f"Remove: {entry['name']}")
    else:
        st.info("No projects added yet.")
        
    st.markdown("---")
    
    
    # --- CV Preview and Download ---
    st.markdown("---")
    st.subheader("9. Loaded CV Data Preview and Download")
    
    if st.session_state.get('parsed', {}).get('name') and st.session_state.parsed.get('name') != "":
        
        EXCLUDE_KEYS_PREVIEW = ["structured_experience", "structured_certifications", "structured_education", "structured_projects"]
        filled_data_for_preview = {
            k: v for k, v in st.session_state.parsed.items() 
            if v and k not in EXCLUDE_KEYS_PREVIEW and (isinstance(v, str) and v.strip() or isinstance(v, list) and v)
        }
        
        tab_markdown, tab_json, tab_pdf = st.tabs(["📝 Markdown View", "💾 JSON View", "⬇️ PDF/HTML Download"])

        with tab_markdown:
            cv_markdown_preview = format_parsed_json_to_markdown(filled_data_for_preview)
            st.markdown(cv_markdown_preview)

            st.download_button(
                label="⬇️ Download CV as Markdown (.md)",
                data=cv_markdown_preview,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_CV_Document.md",
                mime="text/markdown",
                key="download_cv_markdown_final"
            )

        with tab_json:
            st.json(filled_data_for_preview)
            st.info("This is the raw, structured data used by the AI tools.")

            json_output = json.dumps(filled_data_for_preview, indent=2)
            st.download_button(
                label="⬇️ Download CV as JSON File",
                data=json_output,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_CV_Data.json",
                mime="application/json",
                key="download_cv_json_final"
            )

        with tab_pdf:
            st.markdown("### Download CV as HTML (Print-to-PDF)")
            st.info("Click the button below to download an HTML file. Open the file in your browser and use the browser's **'Print'** function, selecting **'Save as PDF'** to create your final CV document.")
            
            html_output = generate_cv_html(filled_data_for_preview)

            st.download_button(
                label="⬇️ Download CV as Print-Ready HTML File (for PDF conversion)",
                data=html_output,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_CV_Document.html",
                mime="text/html",
                key="download_cv_html"
            )
            
            st.markdown("---")
            st.markdown("### Raw Text Data Download (for utility)")
            st.download_button(
                label="⬇️ Download All CV Data as Raw Text (.txt)",
                data=st.session_state.full_text,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_Raw_Data.txt",
                mime="text/plain",
                key="download_cv_txt_final"
            )
            
    else:
        st.info("Please fill out the form above and click 'Generate and Load ALL CV Data' or parse a resume in the 'Resume Parsing' tab to see the preview and download options.")

# --- Main App Structure (Run the App) ---
if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="AI Candidate Dashboard")
    st.title("🤖 AI-Powered Candidate Dashboard")
    st.caption("Manage, Review, and Optimize your CV data.")

    # Call the main function
    cv_management_tab_content()

    st.sidebar.markdown("---")
    st.sidebar.markdown("## Current Session State")
    if st.sidebar.checkbox("Show Raw Session State"):
        st.sidebar.json({k: v for k, v in st.session_state.items() if k not in ['cv_form_data', 'parsed']})
        st.sidebar.markdown("---")
        st.sidebar.json(st.session_state.get('cv_form_data', {}))
                label="⬇️ Download All CV Data as Raw Text (.txt)",
                data=st.session_state.full_text,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_Raw_Data.txt",
                mime="text/plain",
                key="download_cv_txt_final"
            )
            
    else:
        st.info("Please fill out the form above and click 'Generate and Load ALL CV Data' or parse a resume in the 'Resume Parsing' tab to see the preview and download options.")
