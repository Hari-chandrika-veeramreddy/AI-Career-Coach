import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def recommend_careers(resume_skills):
    """
    Recommend top 5 careers calculated from skill overlap and TF-IDF similarity.
    Reads from data/careers.csv.
    """
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "careers.csv")
    
    if not os.path.exists(csv_path):
        return []

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error loading careers dataset: {e}")
        return []

    if df.empty or not resume_skills:
        # Default top careers if skills are empty
        recommendations = []
        for _, row in df.head(5).iterrows():
            req_skills = [s.strip() for s in str(row["required_skills"]).split(",") if s.strip()]
            recommendations.append({
                "career_name": row["career_name"],
                "match_percentage": 0.0,
                "explanation": row["description"],
                "required_skills": req_skills,
                "missing_skills": req_skills
            })
        return recommendations

    student_skills_str = " ".join(resume_skills)
    student_skills_set = set(s.lower() for s in resume_skills)

    # Compute TF-IDF similarity between student skills and career required skills
    career_texts = df["required_skills"].astype(str).tolist()
    all_texts = [student_skills_str] + career_texts

    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b[\w\+\#]+\b")
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    student_vector = tfidf_matrix[0:1]
    career_vectors = tfidf_matrix[1:]
    
    similarities = cosine_similarity(student_vector, career_vectors)[0]

    results = []
    for idx, row in df.iterrows():
        req_skills_list = [s.strip() for s in str(row["required_skills"]).split(",") if s.strip()]
        
        # Calculate direct skill overlap ratio
        matched = [s for s in req_skills_list if s.lower() in student_skills_set]
        missing = [s for s in req_skills_list if s.lower() not in student_skills_set]
        
        overlap_score = len(matched) / max(len(req_skills_list), 1)
        tfidf_sim = float(similarities[idx])
        
        # Hybrid match score weighted 60% direct overlap, 40% TF-IDF cosine similarity
        hybrid_score = (overlap_score * 0.60) + (tfidf_sim * 0.40)
        match_percentage = min(round(hybrid_score * 100.0, 1), 100.0)

        explanation = f"{row['description']} You match {len(matched)} of {len(req_skills_list)} core skills."

        results.append({
            "career_name": row["career_name"],
            "match_percentage": match_percentage,
            "explanation": explanation,
            "required_skills": req_skills_list,
            "matched_skills": matched,
            "missing_skills": missing
        })

    # Sort descending by match percentage
    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return results[:5]
