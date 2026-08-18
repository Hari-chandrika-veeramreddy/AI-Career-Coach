import streamlit as st
from utils.resume_parser import extract_resume_text
from utils.skill_extractor import extract_skills
from utils.job_analyzer import analyze_job_match
from utils.career_recommender import recommend_careers
from database.database import (
    save_profile, save_career_result, save_progress_snapshot,
    get_user_profile, get_user_latest_career_result
)

def render_resume_page():
    st.markdown("""
    <div class="banner-card">
        <h1>📄 Resume & Job Analyzer</h1>
        <p>Extract technical skills, evaluate job description alignment, and discover your top career paths.</p>
    </div>
    """, unsafe_allow_html=True)

    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in to upload your resume and run career analysis.")
        return

    # Load existing profile from SQLite if available
    profile = get_user_profile(user["id"])
    if profile and "resume_skills" not in st.session_state:
        st.session_state["resume_skills"] = profile.get("extracted_skills", [])
        st.session_state["resume_text"] = profile.get("resume_text", "")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Upload Resume")
        uploaded_resume = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])
        
        if uploaded_resume is not None:
            with st.spinner("Extracting resume text & skills..."):
                text = extract_resume_text(uploaded_resume)
                if text:
                    skills = extract_skills(text)
                    st.session_state["resume_text"] = text
                    st.session_state["resume_skills"] = skills
                    
                    # Persist profile to SQLite bound to user_id
                    save_profile(
                        user_id=user["id"],
                        resume_filename=uploaded_resume.name,
                        resume_text=text,
                        extracted_skills=skills,
                        target_role=""
                    )
                    st.success(f"Successfully extracted {len(skills)} tech skills and saved to your profile!")
                else:
                    st.error("Could not extract readable text from the uploaded file. Please try another PDF/DOCX.")

        # Display extracted skills if stored in session state
        resume_skills = st.session_state.get("resume_skills", [])
        if resume_skills:
            st.markdown("### Extracted Skills")
            skill_html = "".join([f'<span class="skill-tag">{s}</span>' for s in resume_skills])
            st.markdown(skill_html, unsafe_allow_html=True)

    with col2:
        st.subheader("2. Target Job Description")
        job_desc = st.text_area("Paste target job description here...", height=180, placeholder="e.g. Seeking a Web Developer with experience in HTML, CSS, JavaScript, React, and Git...")
        
        if st.button("Analyze Resume & Job", key="analyze_resume_job_btn", use_container_width=True):
            if not resume_skills:
                st.warning("Please upload a resume first to extract your skills.")
            elif not job_desc.strip():
                st.warning("Please paste a target job description to run match analysis.")
            else:
                with st.spinner("Analyzing skill match and generating recommendations..."):
                    match_res = analyze_job_match(resume_skills, job_desc)
                    career_recs = recommend_careers(resume_skills)
                    
                    st.session_state["job_match_result"] = match_res
                    st.session_state["career_recommendations"] = career_recs

                    # Persist career result and progress snapshot to SQLite bound to user_id
                    save_career_result(
                        user_id=user["id"],
                        target_job=job_desc[:50],
                        matched_skills=match_res["matched_skills"],
                        missing_skills=match_res["missing_skills"],
                        match_percentage=match_res["match_percentage"],
                        recommended_careers=career_recs
                    )
                    save_progress_snapshot(
                        user_id=user["id"],
                        technical_score=match_res["match_percentage"],
                        readiness_score=match_res["match_percentage"]
                    )
                    st.success("Analysis complete and saved to your database history!")

    # Check for latest saved results in SQLite if session is fresh
    if "job_match_result" not in st.session_state:
        latest_car = get_user_latest_career_result(user["id"])
        if latest_car:
            st.session_state["job_match_result"] = {
                "match_percentage": latest_car["match_percentage"],
                "matched_skills": latest_car["matched_skills"],
                "missing_skills": latest_car["missing_skills"],
                "has_required_skills": True
            }
            st.session_state["career_recommendations"] = latest_car["recommended_careers"]

    # Display Job Match Analysis Results
    match_res = st.session_state.get("job_match_result")
    if match_res:
        st.markdown("---")
        st.subheader("🎯 Job Match Analysis Results")
        
        if not match_res.get("has_required_skills", True):
            st.warning("⚠️ Could not detect technical skills (e.g. HTML, CSS, React, Python, SQL) in your pasted job description. Please paste a detailed job posting with technical requirements.")
        else:
            m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
            with m_col1:
                st.metric("Job Match Percentage", f"{match_res['match_percentage']}%")
            with m_col2:
                st.metric("Matched Skills Count", len(match_res["matched_skills"]))
            with m_col3:
                st.metric("Missing Skills Count", len(match_res["missing_skills"]))

            res_col1, res_col2 = st.columns(2)
            with res_col1:
                st.markdown("#### ✅ Matched Required Skills")
                if match_res["matched_skills"]:
                    matched_html = "".join([f'<span class="skill-tag">{s}</span>' for s in match_res["matched_skills"]])
                    st.markdown(matched_html, unsafe_allow_html=True)
                else:
                    st.info("No matching skills found between your resume and this job description.")

            with res_col2:
                if match_res["missing_skills"]:
                    st.markdown("#### ⚠️ Missing Skills to Learn")
                    missing_html = "".join([f'<span class="skill-tag skill-tag-missing">{s}</span>' for s in match_res["missing_skills"]])
                    st.markdown(missing_html, unsafe_allow_html=True)
                else:
                    st.markdown("#### 🎉 Skills Gap Analysis: Complete")
                    st.success("Great job! You meet all extracted skill requirements for this job description.")

    # Display Career Recommendations
    career_recs = st.session_state.get("career_recommendations")
    if career_recs:
        st.markdown("---")
        st.subheader("🚀 Recommended Career Paths")
        st.write("Top 5 career roles matching your extracted resume skills:")

        for rec in career_recs:
            with st.expander(f"⭐ {rec['career_name']} — **{rec['match_percentage']}% Match**"):
                st.write(f"**Role Description:** {rec['explanation']}")
                st.write("**Core Required Skills:** " + ", ".join(rec['required_skills']))
                if rec.get('missing_skills'):
                    st.write("**Suggested Skills to Learn:** " + ", ".join(rec['missing_skills']))
