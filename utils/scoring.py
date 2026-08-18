def calculate_overall_readiness(resume_match=None, interview_score=None, tech_score=None, comm_score=None, presentation_score=None):
    """
    Calculate weighted Overall Career Readiness Score.
    Weighted calculation:
    - Resume / Job Match: 20%
    - Interview Performance: 30%
    - Technical Skills: 20%
    - Communication Skills: 15%
    - Presentation Skills: 15%

    Handles missing/unevaluated components dynamically without treating missing data as 0%.
    Returns:
    - overall_score (float or None)
    - status_label (str: 'Excellent', 'Good', 'Needs Improvement', 'Not Evaluated')
    - breakdown (dict)
    """
    components = [
        ("Resume / Job Match", resume_match, 0.20),
        ("Interview Performance", interview_score, 0.30),
        ("Technical Skills", tech_score, 0.20),
        ("Communication Skills", comm_score, 0.15),
        ("Presentation Skills", presentation_score, 0.15)
    ]

    total_weight = 0.0
    weighted_sum = 0.0
    breakdown = {}

    for name, value, weight in components:
        if value is not None and isinstance(value, (int, float)) and value >= 0:
            weighted_sum += value * weight
            total_weight += weight
            breakdown[name] = {
                "status": f"{round(value, 1)}%",
                "raw_value": round(value, 1),
                "evaluated": True
            }
        else:
            breakdown[name] = {
                "status": "Not evaluated",
                "raw_value": None,
                "evaluated": False
            }

    if total_weight > 0:
        overall_score = round(weighted_sum / total_weight, 1)
        if overall_score >= 80.0:
            status_label = "Excellent"
        elif overall_score >= 60.0:
            status_label = "Good"
        else:
            status_label = "Needs Improvement"
    else:
        overall_score = None
        status_label = "Not Evaluated"

    return overall_score, status_label, breakdown

def generate_7_day_improvement_plan(missing_skills=None, weaknesses=None):
    """
    Generate a dynamic 7-Day Improvement Plan tailored to detected skill gaps.
    """
    if missing_skills is None:
        missing_skills = []
    if weaknesses is None:
        weaknesses = []

    plan = {}
    top_missing = missing_skills[:3] if missing_skills else ["Core CS Fundamentals"]

    skill_1 = top_missing[0] if len(top_missing) > 0 else "Technical Skill Gap"
    skill_2 = top_missing[1] if len(top_missing) > 1 else "Database/SQL Queries"
    skill_3 = top_missing[2] if len(top_missing) > 2 else "System Architecture"

    plan["Day 1"] = f"Practice core fundamentals and key syntax for {skill_1}."
    plan["Day 2"] = f"Build a mini practice project or script demonstrating {skill_2}."
    plan["Day 3"] = f"Review technical interview questions and code challenges involving {skill_3}."
    plan["Day 4"] = "Conduct a 5-question Adaptive Technical Mock Interview focusing on STAR framework responses."
    plan["Day 5"] = "Record a 3-minute technical project presentation and review speech pace (aim for 130-150 WPM)."
    plan["Day 6"] = "Refine presentation slides: eliminate wall-of-text slides and use 3-5 concise bullet points."
    plan["Day 7"] = "Take a complete end-to-end Career Readiness Mock Assessment and review final progress dashboard analytics."

    return plan
