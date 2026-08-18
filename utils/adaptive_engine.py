import random
from utils.interview import filter_questions

def determine_next_difficulty(score):
    """
    Adaptive engine difficulty transition rules:
    - Score < 50: Easy
    - 50 <= Score <= 74: Medium
    - Score >= 75: Hard
    """
    if score < 50.0:
        return "Easy"
    elif score <= 74.0:
        return "Medium"
    else:
        return "Hard"

def get_next_adaptive_question(role, current_score=None, asked_question_ids=None, resume_skills=None):
    """
    Determine next question adaptively based on student's performance score, target role,
    and extracted resume skills. Prevents repeated questions during the session.
    """
    if asked_question_ids is None:
        asked_question_ids = []

    if current_score is None:
        difficulty = "Medium"
    else:
        difficulty = determine_next_difficulty(current_score)

    candidates = filter_questions(role=role, difficulty=difficulty, asked_ids=asked_question_ids, resume_skills=resume_skills)
    
    if not candidates:
        # Secondary fallback if no candidates exist
        candidates = filter_questions(role="All", difficulty="Medium", asked_ids=[], resume_skills=None)

    # Select a candidate from available questions
    selected_question = random.choice(candidates)
    
    return selected_question, difficulty
