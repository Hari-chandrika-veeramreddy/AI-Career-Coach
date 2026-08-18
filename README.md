# AI Career Coach – Adaptive Interview and Presentation Coach for Student Career Readiness

An AI-powered career readiness platform designed to help computer science and engineering students prepare for technical job interviews, resume screening, and presentation hackathons.

---

## 🎯 Project Objective

Build an adaptive AI system that evaluates a student's resume, job alignment, technical interview responses, and presentation delivery to produce an **Overall Career Readiness Score** backed by actionable feedback, user-isolated SQLite persistence, and interactive dashboard analytics.

---

## 🚀 Key Features

1. **Resume & Job Match Analyzer**
   - Parses PDF/DOCX resumes and extracts technical skills using spaCy and regex.
   - Calculates exact job match percentage against target job descriptions or job title fallbacks (`"web developer"`, `"data analyst"`, etc.).
   - Identifies missing skill gaps to guide targeted student preparation.
2. **Career Path Recommender**
   - Calculates TF-IDF cosine similarity between student skills and 12+ tech career roles.
   - Recommends Top 5 career paths with detailed match breakdowns.
3. **Adaptive AI Mock Interview**
   - 50+ real-world HR, Technical, and Behavioral interview questions across Easy, Medium, and Hard difficulty levels.
   - Dynamically adapts question difficulty based on student performance ($<50$: Easy, $50-74$: Medium, $\ge 75$: Hard).
   - Generates customized technical questions for specific skills extracted from the student's uploaded resume.
   - Evaluates text answers using Sentence Transformers (`all-MiniLM-L6-v2`) for semantic similarity, length, and clarity.
4. **Voice & Speech Analysis**
   - Transcribes spoken audio answers using **Faster-Whisper**.
   - Computes acoustic speech metrics (WPM, pause ratios, energy) using **Librosa**.
5. **Presentation Coach**
   - Parses PowerPoint (`.pptx`) slides using `python-pptx` to analyze text density, slide count, and empty slides.
   - Transcribes presentation speech audio to assess content coverage and delivery.
   - Generates a personalized presentation improvement plan.
6. **Strict User Data Isolation & SQLite Progress Dashboard**
   - **Persistent User History**: All activities (Resume Upload, Job Match, Mock Interviews, Presentations) are bound strictly to `user_id` in SQLite.
   - **Data Isolation**: User A and User B have completely private, separated records (`WHERE user_id = ?`).
   - **Automatic Re-hydration**: Logging out and logging back in re-hydrates the user's dashboard, Plotly trend charts, previous interview Q&A history, and previous presentations directly from SQLite.
   - **Personalized 7-Day Improvement Plan**: Dynamically generated 7-day action plan tailored to detected missing skills.

---

## 🗄️ Database Architecture (SQLite)

Database File: `database/career_coach.db`

Relational Tables:
1. `users`: User account details with `bcrypt` password hashing (`id`, `name`, `email`, `password_hash`, `college`, `branch`, `created_at`).
2. `user_profiles`: User resume text and extracted skills (`id`, `user_id`, `resume_filename`, `resume_text`, `extracted_skills`, `target_role`, `updated_at`).
3. `career_results`: Job match results and career recommendations (`id`, `user_id`, `target_job`, `matched_skills`, `missing_skills`, `match_percentage`, `recommended_careers`, `created_at`).
4. `interview_sessions`: Mock interview session records (`id`, `user_id`, `role`, `total_questions`, `final_score`, `difficulty_level`, `completed_at`).
5. `interview_answers`: Individual question evaluations (`id`, `session_id`, `user_id`, `question`, `difficulty`, `answer_text`, `answer_type`, `relevance_score`, `clarity_score`, `quality_score`, `overall_score`, `feedback`, `created_at`).
6. `presentation_sessions`: Presentation evaluations (`id`, `user_id`, `presentation_name`, `ppt_filename`, `duration`, `content_score`, `speech_score`, `communication_score`, `overall_score`, `weaknesses`, `improvement_plan`, `created_at`).
7. `progress_history`: Career Readiness snapshots over time (`id`, `user_id`, `interview_score`, `presentation_score`, `technical_score`, `communication_score`, `readiness_score`, `created_at`).

---

## 🛠 Technology Stack

- **Programming:** Python 3.13.5
- **Frontend / UI:** Streamlit, Custom CSS
- **Database:** SQLite3, bcrypt (Password Hashing)
- **NLP & Embeddings:** spaCy, Sentence Transformers (`all-MiniLM-L6-v2`), Scikit-Learn (TF-IDF, Cosine Similarity)
- **Speech Processing:** Faster-Whisper, Librosa, SoundFile
- **Document Processing:** PyMuPDF (`fitz`), python-docx, python-pptx
- **Data & Visualizations:** Pandas, NumPy, Plotly

---

## 📥 Installation & Setup

```bash
# 1. Create Virtual Environment
python3.13 -m venv venv

# 2. Activate Virtual Environment (Mac/Linux)
source venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Download spaCy English Language Model
python -m spacy download en_core_web_sm
```

---

## 🏃 How to Run the Application

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🧪 Testing User Isolation & History Flow

1. **Register User A** (e.g. `alice@college.edu`) -> Upload resume, run job match, complete mock interview.
2. **View Dashboard** -> Observe Readiness Score, Recent Activity, and Previous Sessions.
3. **Log out User A**.
4. **Register User B** (e.g. `bob@college.edu`) -> Log in as User B.
5. **Observe Data Isolation** -> User B sees a brand new dashboard with zero of User A's data.
6. **Log out User B & Log in User A** -> User A's complete previous interview history, job matches, and progress trends re-hydrate automatically from SQLite!

---

## ☁️ Deployment Considerations

For local presentation demos and hackathons, SQLite provides zero-config, 100% offline persistence. For cloud deployments on platforms with ephemeral filesystems (e.g. Heroku, AWS Lambda), replacing the SQLite connection in `database/database.py` with PostgreSQL (Supabase / NeonDB) is recommended for production cloud persistence.
