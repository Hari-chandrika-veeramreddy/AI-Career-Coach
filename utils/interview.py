import os
import random
import pandas as pd

def load_questions_dataset():
    """Load interview questions from data/questions.csv."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "questions.csv")
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error loading questions CSV: {e}")
        return pd.DataFrame()

def generate_skill_questions(resume_skills):
    """
    Dynamically generate technical questions tailored to specific skills extracted from student resume.
    """
    if not resume_skills:
        return []

    templates = [
        ("How have you applied {skill} in your past projects, and what key architecture decisions did you make?", "Technical", "Medium", "projects, architecture, implementation, best practices"),
        ("What are the core advantages, performance trade-offs, and best use cases for {skill} in production?", "Technical", "Hard", "performance, optimization, scalability, use cases"),
        ("Explain how error handling and debugging work when developing with {skill}.", "Technical", "Easy", "debugging, error handling, exceptions, testing"),
        ("How does {skill} handle concurrency, state, or data persistence in modern applications?", "Technical", "Hard", "concurrency, state management, persistence, memory"),
        ("What are the fundamental concepts and key libraries associated with {skill}?", "Technical", "Easy", "fundamentals, concepts, syntax, core features")
    ]

    generated = []
    base_id = 1000
    for idx, skill in enumerate(resume_skills):
        for t_q, cat, diff, kws in templates:
            base_id += 1
            generated.append({
                "id": base_id,
                "question": t_q.format(skill=skill),
                "category": cat,
                "difficulty": diff,
                "role": "Skill-Targeted",
                "ideal_keywords": f"{skill.lower()}, {kws}"
            })

    return generated

def filter_questions(role="Software Developer", difficulty="Medium", asked_ids=None, resume_skills=None):
    """
    Get available questions matching role and difficulty while excluding asked_ids.
    Blends dataset questions with dynamically generated resume skill questions.
    """
    df = load_questions_dataset()
    dataset_questions = df.to_dict(orient="records") if not df.empty else []

    # Blend dynamic resume skill questions if skills are provided
    skill_questions = generate_skill_questions(resume_skills) if resume_skills else []
    all_questions = dataset_questions + skill_questions

    if asked_ids is None:
        asked_ids = []

    # Filter out already asked questions
    avail = [q for q in all_questions if q.get("id") not in asked_ids]

    if not avail:
        avail = all_questions

    # Match role or 'All' or 'Skill-Targeted'
    role_match = [q for q in avail if str(q.get("role")).lower() in [role.lower(), "all", "skill-targeted"]]
    if not role_match:
        role_match = avail

    # Match difficulty
    diff_match = [q for q in role_match if str(q.get("difficulty")).lower() == difficulty.lower()]
    if not diff_match:
        diff_match = role_match

    return diff_match
