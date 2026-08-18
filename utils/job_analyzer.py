import os
import pandas as pd
from utils.skill_extractor import extract_skills

def analyze_job_match(resume_skills, job_description_text):
    """
    Analyze skill overlap between resume skills and job description.
    Returns dictionary with required skills, matched skills, missing skills, and match percentage.
    Automatically resolves role names (e.g. 'web developer') if raw text contains role titles.
    """
    if not job_description_text or not isinstance(job_description_text, str):
        return {
            "required_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": 0.0,
            "has_required_skills": False
        }

    required_skills = extract_skills(job_description_text)
    
    # Fallback: Check if user entered a job title (e.g., 'web developer') matching careers.csv
    if not required_skills:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "careers.csv")
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                text_lower = job_description_text.strip().lower()
                for _, row in df.iterrows():
                    career_title = str(row["career_name"]).lower()
                    if career_title in text_lower or text_lower in career_title:
                        req_str = str(row["required_skills"])
                        required_skills = [s.strip() for s in req_str.split(",") if s.strip()]
                        break
            except Exception as e:
                print(f"Error matching role title: {e}")

    if not required_skills:
        return {
            "required_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": 0.0,
            "has_required_skills": False
        }

    resume_skills_set = set(s.lower() for s in resume_skills)
    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        if skill.lower() in resume_skills_set:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    match_percentage = round((len(matched_skills) / len(required_skills)) * 100.0, 1)

    return {
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage,
        "has_required_skills": True
    }
