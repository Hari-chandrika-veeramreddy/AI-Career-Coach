import re
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@st.cache_resource
def load_sentence_transformer_model():
    """Load cached SentenceTransformer model with fallback handling."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        print(f"SentenceTransformer load failed: {e}. Falling back to TF-IDF cosine similarity.")
        return None

def compute_relevance_score(question_text, answer_text, ideal_keywords=""):
    """
    Calculate semantic relevance score (0 - 100) using SentenceTransformers embeddings
    or TF-IDF cosine similarity fallback.
    """
    if not answer_text.strip():
        return 0.0

    target_text = f"{question_text}. {ideal_keywords}".strip()
    model = load_sentence_transformer_model()

    if model is not None:
        try:
            embeddings = model.encode([target_text, answer_text], convert_to_tensor=False)
            sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            # Rescale similarity into percentage range (0.0 to 1.0 -> 0 to 100)
            score = max(0.0, float(sim)) * 100.0
            return round(score, 1)
        except Exception as e:
            print(f"Embedding similarity computation error: {e}")

    # Fallback: TF-IDF cosine similarity
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform([target_text, answer_text])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(max(0.0, float(sim)) * 100.0, 1)
    except Exception:
        return 50.0

def compute_length_score(answer_text):
    """
    Calculate length score (0 - 100).
    Ideal answer length for interview response: 40 to 150 words.
    """
    words = [w for w in re.split(r'\s+', answer_text.strip()) if w]
    word_count = len(words)

    if word_count == 0:
        return 0.0
    elif word_count < 15:
        return round((word_count / 15.0) * 40.0, 1)
    elif 15 <= word_count < 40:
        return round(40.0 + ((word_count - 15) / 25.0) * 50.0, 1)
    elif 40 <= word_count <= 150:
        return 100.0
    elif 150 < word_count <= 250:
        return round(100.0 - ((word_count - 150) / 100.0) * 30.0, 1)
    else:
        return 60.0

def compute_clarity_score(answer_text):
    """
    Calculate clarity score (0 - 100) based on sentence structure, punctuation, and filler words.
    """
    if not answer_text.strip():
        return 0.0

    words = [w.lower() for w in re.split(r'\s+', answer_text.strip()) if w]
    word_count = len(words)
    
    if word_count == 0:
        return 0.0

    # Filler words penalty
    filler_words = {"like", "um", "uh", "you know", "basically", "actually", "literally", "sort of", "kind of"}
    filler_count = sum(1 for w in words if w in filler_words)
    filler_ratio = filler_count / word_count
    
    # Base score
    clarity = 100.0 - (filler_ratio * 150.0)
    
    # Sentence punctuation check
    sentences = re.split(r'[.!?]+', answer_text)
    valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
    
    if len(valid_sentences) == 0:
        clarity -= 20.0
    
    return round(max(20.0, min(100.0, clarity)), 1)

def evaluate_answer(question_text, answer_text, ideal_keywords=""):
    """
    Main evaluation pipeline for text interview responses.
    Overall score breakdown:
    - Relevance: 60%
    - Length: 20%
    - Clarity: 20%
    """
    if not answer_text or not answer_text.strip():
        return {
            "score": 0.0,
            "relevance": 0.0,
            "length": 0.0,
            "clarity": 0.0,
            "feedback": "No answer provided. Please enter a complete response."
        }

    relevance = compute_relevance_score(question_text, answer_text, ideal_keywords)
    length_score = compute_length_score(answer_text)
    clarity = compute_clarity_score(answer_text)

    # Weighted overall score formula
    overall_score = round((relevance * 0.60) + (length_score * 0.20) + (clarity * 0.20), 1)

    # Generate meaningful feedback based on overall score
    if overall_score >= 75.0:
        feedback = "Excellent response! Your answer is highly relevant, clear, and well-structured. To make it even stronger, consider adding a specific real-world example or metric from your past experience."
    elif 50.0 <= overall_score < 75.0:
        feedback = "Good response with a solid foundation. You covered the core concepts well, but expanding your technical depth and explaining the concept with a practical example will boost your score."
    else:
        feedback = "Your answer needs improvement. Focus directly on the main question requirements, avoid filler words, and structure your explanation clearly with key technical terms."

    return {
        "score": overall_score,
        "relevance": relevance,
        "length": length_score,
        "clarity": clarity,
        "feedback": feedback
    }
