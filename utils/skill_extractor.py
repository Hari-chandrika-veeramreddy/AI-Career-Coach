import re
import streamlit as st

# Controlled dictionary of tech skills with display names and search patterns
SKILL_DICTIONARY = {
    # Programming
    "Python": [r"\bpython\b", r"\bpy3\b"],
    "Java": [r"\bjava\b"],
    "C": [r"\bc\b"],
    "C++": [r"\bc\+\+\b", r"\bcpp\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],

    # Web
    "HTML": [r"\bhtml\b", r"\bhtml5\b"],
    "CSS": [r"\bcss\b", r"\bcss3\b"],
    "React": [r"\breact\b", r"\breactjs\b", r"\breact\.js\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "FastAPI": [r"\bfastapi\b"],

    # Database
    "SQL": [r"\bsql\b", r"\bsqlite\b"],
    "MySQL": [r"\bmysql\b"],
    "PostgreSQL": [r"\bpostgresql\b", r"\bpostgres\b"],
    "MongoDB": [r"\bmongodb\b", r"\bmongo\b"],

    # Data
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "Matplotlib": [r"\bmatplotlib\b"],
    "Power BI": [r"\bpower bi\b", r"\bpowerbi\b"],
    "Tableau": [r"\btableau\b"],
    "Excel": [r"\bexcel\b", r"\bms excel\b"],

    # AI/ML
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Deep Learning": [r"\bdeep learning\b", r"\bdl\b"],
    "NLP": [r"\bnlp\b", r"\bnatural language processing\b"],
    "Scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
    "TensorFlow": [r"\btensorflow\b", r"\btf\b"],
    "PyTorch": [r"\bpytorch\b"],
    "Computer Vision": [r"\bcomputer vision\b", r"\bcv\b"],
    "OpenCV": [r"\bopencv\b"],

    # Cloud/DevOps
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Docker": [r"\bdocker\b"],
    "Git": [r"\bgit\b"],
    "GitHub": [r"\bgithub\b"],
    "Linux": [r"\blinux\b", r"\bubuntu\b"],

    # Cybersecurity
    "Cyber Security": [r"\bcyber security\b", r"\bcybersecurity\b", r"\binformation security\b"],
    "Networking": [r"\bnetworking\b", r"\btcp/ip\b", r"\bnetwork security\b"],
    "Ethical Hacking": [r"\bethical hacking\b", r"\bpenetration testing\b", r"\bpen testing\b"]
}

@st.cache_resource
def load_spacy_nlp():
    """Load spaCy model with graceful fallback if model is not pre-installed."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        try:
            import spacy
            from spacy.lang.en import English
            return English()
        except Exception:
            return None

def extract_skills(text):
    """
    Extract normalized tech skills from text using controlled regex patterns and spaCy processing.
    Returns a sorted list of unique, canonical skill names.
    """
    if not text or not isinstance(text, str):
        return []

    found_skills = set()
    text_lower = text.lower()

    # Search controlled skill dictionary
    for canonical_name, patterns in SKILL_DICTIONARY.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found_skills.add(canonical_name)
                break

    # Additional spaCy entity extraction if available
    nlp = load_spacy_nlp()
    if nlp is not None and len(text_lower) < 100000:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT"]:
                    ent_str = ent.text.strip()
                    for canonical_name in SKILL_DICTIONARY:
                        if canonical_name.lower() == ent_str.lower():
                            found_skills.add(canonical_name)
        except Exception:
            pass

    return sorted(list(found_skills))
