import sqlite3
import os
import json
from datetime import datetime
import bcrypt

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "career_coach.db")

def get_connection():
    """Establish and return a SQLite connection with dict row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables automatically and apply schema column migrations."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        college TEXT NOT NULL,
        branch TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. User Profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        resume_filename TEXT,
        resume_text TEXT,
        extracted_skills TEXT,
        target_role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # 3. Career Results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS career_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        target_job TEXT,
        matched_skills TEXT,
        missing_skills TEXT,
        match_percentage REAL,
        recommended_careers TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # 4. Interview Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        score REAL DEFAULT 0.0,
        total_questions INTEGER DEFAULT 0,
        final_score REAL DEFAULT 0.0,
        difficulty_level TEXT DEFAULT 'Medium',
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # 5. Interview Answers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL DEFAULT 1,
        question TEXT NOT NULL,
        difficulty TEXT NOT NULL DEFAULT 'Medium',
        answer_text TEXT NOT NULL DEFAULT '',
        answer TEXT DEFAULT '',
        answer_type TEXT DEFAULT 'Text',
        score REAL DEFAULT 0.0,
        relevance REAL DEFAULT 0.0,
        clarity REAL DEFAULT 0.0,
        length_score REAL DEFAULT 0.0,
        relevance_score REAL DEFAULT 0.0,
        clarity_score REAL DEFAULT 0.0,
        quality_score REAL DEFAULT 0.0,
        overall_score REAL DEFAULT 0.0,
        feedback TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES interview_sessions (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # 6. Presentation Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presentation_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        presentation_name TEXT NOT NULL,
        ppt_filename TEXT,
        duration REAL DEFAULT 0.0,
        content_score REAL NOT NULL DEFAULT 0.0,
        speech_score REAL NOT NULL DEFAULT 0.0,
        communication_score REAL NOT NULL DEFAULT 0.0,
        overall_score REAL NOT NULL DEFAULT 0.0,
        weaknesses TEXT,
        improvement_plan TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # 7. Progress History table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        interview_score REAL,
        presentation_score REAL,
        technical_score REAL,
        communication_score REAL,
        readiness_score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # Migrations for existing DB files created before schema update
    migrations = [
        "ALTER TABLE interview_sessions ADD COLUMN total_questions INTEGER DEFAULT 0;",
        "ALTER TABLE interview_sessions ADD COLUMN difficulty_level TEXT DEFAULT 'Medium';",
        "ALTER TABLE interview_sessions ADD COLUMN final_score REAL DEFAULT 0.0;",
        "ALTER TABLE interview_sessions ADD COLUMN completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE interview_answers ADD COLUMN user_id INTEGER DEFAULT 1;",
        "ALTER TABLE interview_answers ADD COLUMN answer_type TEXT DEFAULT 'Text';",
        "ALTER TABLE interview_answers ADD COLUMN quality_score REAL DEFAULT 0.0;",
        "ALTER TABLE interview_answers ADD COLUMN overall_score REAL DEFAULT 0.0;"
    ]

    for mig in migrations:
        try:
            cursor.execute(mig)
        except Exception:
            pass  # Column already exists

    conn.commit()
    conn.close()

# User Authentication Functions
def create_user(name, email, password, college, branch):
    """Hash password with bcrypt and register user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    try:
        cursor.execute("""
        INSERT INTO users (name, email, password_hash, college, branch)
        VALUES (?, ?, ?, ?, ?)
        """, (name.strip(), email.strip().lower(), pw_hash, college.strip(), branch.strip()))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, user_id, "User registered successfully."
    except sqlite3.IntegrityError:
        conn.close()
        return False, None, "An account with this email already exists."
    except Exception as e:
        conn.close()
        return False, None, f"Registration error: {str(e)}"

def authenticate_user(email, password):
    """Verify user credentials against stored bcrypt hash."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return False, None, "Invalid email or password."

    stored_hash = user["password_hash"].encode('utf-8')
    entered_pw = password.encode('utf-8')

    if bcrypt.checkpw(entered_pw, stored_hash):
        user_dict = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "college": user["college"],
            "branch": user["branch"],
            "created_at": user["created_at"]
        }
        return True, user_dict, "Login successful."
    else:
        return False, None, "Invalid email or password."

def get_user_by_id(user_id):
    """Fetch user details by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, college, branch, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Profile & Career Persistence
def save_profile(user_id, resume_filename="", resume_text="", extracted_skills=None, target_role=""):
    """Create or update user profile with extracted resume skills."""
    if extracted_skills is None:
        extracted_skills = []

    skills_json = json.dumps(extracted_skills)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
        UPDATE user_profiles
        SET resume_filename = ?, resume_text = ?, extracted_skills = ?, target_role = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """, (resume_filename, resume_text, skills_json, target_role, user_id))
    else:
        cursor.execute("""
        INSERT INTO user_profiles (user_id, resume_filename, resume_text, extracted_skills, target_role)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, resume_filename, resume_text, skills_json, target_role))

    conn.commit()
    conn.close()

def get_user_profile(user_id):
    """Retrieve profile for specified user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    try:
        res["extracted_skills"] = json.loads(res["extracted_skills"]) if res["extracted_skills"] else []
    except Exception:
        res["extracted_skills"] = []
    return res

def save_career_result(user_id, target_job, matched_skills, missing_skills, match_percentage, recommended_careers):
    """Save job description match and career path recommendations."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO career_results (user_id, target_job, matched_skills, missing_skills, match_percentage, recommended_careers)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        target_job,
        json.dumps(matched_skills),
        json.dumps(missing_skills),
        float(match_percentage),
        json.dumps(recommended_careers)
    ))
    conn.commit()
    conn.close()

def get_user_latest_career_result(user_id):
    """Get latest career result record for logged-in user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM career_results WHERE user_id = ? ORDER BY id DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    try:
        res["matched_skills"] = json.loads(res["matched_skills"]) if res["matched_skills"] else []
        res["missing_skills"] = json.loads(res["missing_skills"]) if res["missing_skills"] else []
        res["recommended_careers"] = json.loads(res["recommended_careers"]) if res["recommended_careers"] else []
    except Exception:
        pass
    return res

# Interview Session & Answer Persistence
def save_interview_session(user_id, role, total_questions, final_score, difficulty_level="Medium"):
    """Save an overall interview session for specific user_id and return session_id."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO interview_sessions (user_id, role, score, total_questions, final_score, difficulty_level)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, role, float(final_score), int(total_questions), float(final_score), difficulty_level))
    except sqlite3.OperationalError:
        cursor.execute("""
        INSERT INTO interview_sessions (user_id, role, score)
        VALUES (?, ?, ?)
        """, (user_id, role, float(final_score)))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def save_interview_answer(session_id, user_id, question, difficulty, answer_text, answer_type="Text", relevance_score=0.0, clarity_score=0.0, quality_score=0.0, overall_score=0.0, feedback=""):
    """Save individual interview answer evaluation bound to session_id and user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO interview_answers (session_id, user_id, question, difficulty, answer_text, answer, answer_type, score, relevance, clarity, length_score, relevance_score, clarity_score, quality_score, overall_score, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, user_id, question, difficulty, answer_text, answer_text, answer_type,
            float(overall_score), float(relevance_score), float(clarity_score), float(quality_score),
            float(relevance_score), float(clarity_score), float(quality_score), float(overall_score), feedback
        ))
    except sqlite3.OperationalError:
        cursor.execute("""
        INSERT INTO interview_answers (session_id, question, answer, score, relevance, clarity, length_score, feedback, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, question, answer_text, float(overall_score), float(relevance_score), float(clarity_score), float(quality_score), feedback, difficulty))

    conn.commit()
    conn.close()

def get_user_interview_history(user_id):
    """Retrieve full interview session history strictly filtered for specified user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT * FROM interview_sessions WHERE user_id = ? ORDER BY id DESC
    """, (user_id,))
    raw_sessions = [dict(s) for s in cursor.fetchall()]
    sessions = []

    for s in raw_sessions:
        final_sc = s.get("final_score") if s.get("final_score") is not None else s.get("score", 0.0)
        t_q = s.get("total_questions", 0)
        c_at = s.get("completed_at") or s.get("created_at") or "Recent"
        
        cursor.execute("""
        SELECT * FROM interview_answers WHERE session_id = ? ORDER BY id ASC
        """, (s["id"],))
        raw_ans = [dict(a) for a in cursor.fetchall()]
        answers = []
        for a in raw_ans:
            answers.append({
                "question": a.get("question", ""),
                "difficulty": a.get("difficulty", "Medium"),
                "answer_text": a.get("answer_text") or a.get("answer", ""),
                "overall_score": a.get("overall_score") if a.get("overall_score") is not None else a.get("score", 0.0),
                "feedback": a.get("feedback", "")
            })

        if t_q == 0 and len(answers) > 0:
            t_q = len(answers)

        sessions.append({
            "id": s["id"],
            "user_id": s["user_id"],
            "role": s["role"],
            "total_questions": t_q,
            "final_score": final_sc,
            "difficulty_level": s.get("difficulty_level", "Medium"),
            "completed_at": c_at,
            "answers": answers
        })

    conn.close()
    return sessions

# Presentation Persistence
def save_presentation_session(user_id, presentation_name, ppt_filename="", duration=0.0, content_score=0.0, speech_score=0.0, communication_score=0.0, overall_score=0.0, weaknesses=None, improvement_plan=None):
    """Save presentation evaluation bound to user_id."""
    if weaknesses is None:
        weaknesses = []
    if improvement_plan is None:
        improvement_plan = []

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO presentation_sessions (user_id, presentation_name, ppt_filename, duration, content_score, speech_score, communication_score, overall_score, weaknesses, improvement_plan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, presentation_name, ppt_filename, float(duration),
            float(content_score), float(speech_score), float(communication_score), float(overall_score),
            json.dumps(weaknesses), json.dumps(improvement_plan)
        ))
    except sqlite3.OperationalError:
        cursor.execute("""
        INSERT INTO presentations (user_id, title, score, feedback)
        VALUES (?, ?, ?, ?)
        """, (user_id, presentation_name, float(overall_score), json.dumps(improvement_plan)))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_user_presentation_history(user_id):
    """Retrieve presentation history strictly filtered for specified user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        SELECT * FROM presentation_sessions WHERE user_id = ? ORDER BY id DESC
        """, (user_id,))
        raw_pres = [dict(p) for p in cursor.fetchall()]
        presentations = []
        for p in raw_pres:
            w_list = json.loads(p["weaknesses"]) if p.get("weaknesses") else []
            plan_list = json.loads(p["improvement_plan"]) if p.get("improvement_plan") else []
            presentations.append({
                "id": p["id"],
                "user_id": p["user_id"],
                "presentation_name": p["presentation_name"],
                "overall_score": p["overall_score"],
                "content_score": p["content_score"],
                "speech_score": p["speech_score"],
                "weaknesses": w_list,
                "improvement_plan": plan_list,
                "created_at": p.get("created_at", "Recent")
            })
    except sqlite3.OperationalError:
        cursor.execute("SELECT * FROM presentations WHERE user_id = ? ORDER BY id DESC", (user_id,))
        raw_pres = [dict(p) for p in cursor.fetchall()]
        presentations = []
        for p in raw_pres:
            presentations.append({
                "id": p["id"],
                "user_id": p["user_id"],
                "presentation_name": p.get("title", "Presentation"),
                "overall_score": p.get("score", 0.0),
                "content_score": p.get("score", 0.0),
                "speech_score": p.get("score", 0.0),
                "weaknesses": [],
                "improvement_plan": [p.get("feedback", "")],
                "created_at": p.get("created_at", "Recent")
            })

    conn.close()
    return presentations

# Progress Snapshots
def save_progress_snapshot(user_id, interview_score=None, presentation_score=None, technical_score=None, communication_score=None, readiness_score=None):
    """Save Career Readiness score snapshot over time for progress tracking."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO progress_history (user_id, interview_score, presentation_score, technical_score, communication_score, readiness_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            float(interview_score) if interview_score is not None else None,
            float(presentation_score) if presentation_score is not None else None,
            float(technical_score) if technical_score is not None else None,
            float(communication_score) if communication_score is not None else None,
            float(readiness_score) if readiness_score is not None else None
        ))
        conn.commit()
    except Exception:
        pass
    conn.close()

def get_user_progress_history(user_id):
    """Fetch chronological progress snapshots for user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT * FROM progress_history WHERE user_id = ? ORDER BY id ASC
        """, (user_id,))
        rows = [dict(r) for r in cursor.fetchall()]
    except Exception:
        rows = []
    conn.close()
    return rows

def get_user_recent_activities(user_id, limit=10):
    """
    Fetch unified recent activity timeline for user_id combining interviews,
    presentations, and resume analyses.
    """
    activities = []
    int_hist = get_user_interview_history(user_id)
    for i in int_hist:
        dt = i.get("completed_at", "Recent")
        activities.append({
            "date": dt[:10] if isinstance(dt, str) and len(dt) >= 10 else "Recent",
            "raw_date": dt,
            "activity": f"Mock Interview ({i.get('role', 'Technical')})",
            "score": f"{round(i['final_score'], 1)}%"
        })

    pres_hist = get_user_presentation_history(user_id)
    for p in pres_hist:
        dt = p.get("created_at", "Recent")
        activities.append({
            "date": dt[:10] if isinstance(dt, str) and len(dt) >= 10 else "Recent",
            "raw_date": dt,
            "activity": f"Presentation ({p.get('presentation_name', 'Slide Deck')})",
            "score": f"{round(p['overall_score'], 1)}%"
        })

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT created_at as date, target_job, match_percentage FROM career_results WHERE user_id = ? ORDER BY id DESC
        """, (user_id,))
        for r in cursor.fetchall():
            dt = r["date"] or "Recent"
            activities.append({
                "date": dt[:10] if isinstance(dt, str) and len(dt) >= 10 else "Recent",
                "raw_date": dt,
                "activity": f"Resume & Job Match ({r.get('target_job') or 'General'})",
                "score": f"{round(r['match_percentage'], 1)}%"
            })
    except Exception:
        pass
    conn.close()

    activities.sort(key=lambda x: str(x.get("raw_date", "")), reverse=True)
    return activities[:limit]

def get_dashboard_stats(user_id):
    """Calculate aggregate dashboard statistics strictly for logged-in user_id."""
    int_hist = get_user_interview_history(user_id)
    pres_hist = get_user_presentation_history(user_id)
    latest_car = get_user_latest_career_result(user_id)

    avg_interview = round(sum(i["final_score"] for i in int_hist) / len(int_hist), 1) if int_hist else None
    avg_presentation = round(sum(p["overall_score"] for p in pres_hist) / len(pres_hist), 1) if pres_hist else None
    avg_communication = round(sum(p.get("speech_score", 75.0) for p in pres_hist) / len(pres_hist), 1) if pres_hist else None
    latest_resume_match = round(latest_car["match_percentage"], 1) if latest_car else None

    return {
        "avg_interview": avg_interview,
        "total_interviews": len(int_hist),
        "avg_presentation": avg_presentation,
        "total_presentations": len(pres_hist),
        "avg_communication": avg_communication,
        "latest_resume_match": latest_resume_match
    }
