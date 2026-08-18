import streamlit as st
from utils.adaptive_engine import get_next_adaptive_question
from utils.answer_analyzer import evaluate_answer
from utils.speech_analyzer import transcribe_audio, analyze_audio_metrics
from database.database import save_interview_session, save_interview_answer, save_progress_snapshot

ROLES = [
    "Software Developer", "Data Analyst", "Data Scientist",
    "Machine Learning Engineer", "Web Developer",
    "Backend Developer", "Cyber Security Analyst"
]

def render_interview_page():
    st.markdown("""
    <div class="banner-card">
        <h1>🎯 Adaptive AI Mock Interview</h1>
        <p>Real-time AI question adaptation based on target role, performance evaluation, and voice/text analysis.</p>
    </div>
    """, unsafe_allow_html=True)

    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in to participate in mock interviews and save your progress.")
        return

    # Initialize session state for interview active flow
    if "interview_active" not in st.session_state:
        st.session_state["interview_active"] = False

    if not st.session_state["interview_active"]:
        # Configuration setup view
        st.subheader("Configure Interview Session")
        c1, c2, c3 = st.columns(3)
        with c1:
            selected_role = st.selectbox("Target Role", ROLES)
        with c2:
            mode = st.radio("Interview Mode", ["Text Answer", "Voice Answer (Audio File Upload)"])
        with c3:
            start_diff = st.selectbox("Starting Difficulty", ["Easy", "Medium", "Hard"], index=1)

        if st.button("Start Adaptive Interview", use_container_width=True):
            st.session_state["interview_active"] = True
            st.session_state["interview_role"] = selected_role
            st.session_state["interview_mode"] = mode
            st.session_state["asked_ids"] = []
            st.session_state["answers_history"] = []
            st.session_state["current_score"] = None
            
            # Fetch first question with resume skills
            resume_skills = st.session_state.get("resume_skills", [])
            first_q, diff = get_next_adaptive_question(selected_role, None, [], resume_skills=resume_skills)
            st.session_state["current_question"] = first_q
            st.session_state["current_difficulty"] = diff
            st.rerun()

    else:
        # Active interview session view
        role = st.session_state.get("interview_role", "Software Developer")
        mode = st.session_state.get("interview_mode", "Text Answer")
        curr_q = st.session_state.get("current_question", {})
        curr_diff = st.session_state.get("current_difficulty", "Medium")
        asked_ids = st.session_state.get("asked_ids", [])
        history = st.session_state.get("answers_history", [])

        # Header status row
        hdr_col1, hdr_col2 = st.columns([3, 1])
        with hdr_col1:
            st.markdown(f"**Target Role:** `{role}` | **Question {len(history) + 1}** | **Current Difficulty:** `{curr_diff}`")
        with hdr_col2:
            if history:
                if st.button("🏁 Finish & Save Session", use_container_width=True):
                    avg_score = round(sum(h["score"] for h in history) / len(history), 1)
                    
                    # Persist session to SQLite bound to user["id"]
                    session_id = save_interview_session(
                        user_id=user["id"],
                        role=role,
                        total_questions=len(history),
                        final_score=avg_score,
                        difficulty_level=curr_diff
                    )
                    
                    for h in history:
                        save_interview_answer(
                            session_id=session_id,
                            user_id=user["id"],
                            question=h["question"],
                            difficulty=h["difficulty"],
                            answer_text=h["answer"],
                            answer_type=h.get("answer_type", "Text"),
                            relevance_score=h["relevance"],
                            clarity_score=h["clarity"],
                            quality_score=h["length_score"],
                            overall_score=h["score"],
                            feedback=h["feedback"]
                        )

                    # Save progress snapshot in SQLite
                    save_progress_snapshot(
                        user_id=user["id"],
                        interview_score=avg_score,
                        readiness_score=avg_score
                    )
                    
                    st.session_state["last_interview_score"] = avg_score
                    st.session_state["interview_active"] = False
                    st.success(f"Interview session finished and saved to SQLite! Overall Score: **{avg_score}%**")
                    st.rerun()

        # Question Display Card
        st.markdown(f"""
        <div class="coach-card">
            <span class="badge-{curr_diff.lower()}">{curr_diff}</span>
            <h3 style="margin-top:0.5rem;">{curr_q.get('question', 'Tell me about your technical background.')}</h3>
            <p style="color:#94a3b8; font-size:0.9rem;">Category: {curr_q.get('category', 'Technical')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Form wrapper prevents typing latency, cursor moving, and button layout shifts
        with st.form(key=f"answer_form_{len(history)}"):
            answer_text = ""
            audio_file = None

            if "Text" in mode:
                answer_text = st.text_area(
                    "Your Answer:",
                    height=160,
                    key=f"text_input_{len(history)}",
                    placeholder="Type your detailed answer here..."
                )
            else:
                audio_file = st.file_uploader(
                    "Upload audio answer (WAV, MP3, M4A)",
                    type=["wav", "mp3", "m4a"],
                    key=f"audio_input_{len(history)}"
                )

            submit_ans = st.form_submit_button("Submit Answer & Next Question", use_container_width=True)

        if submit_ans:
            # Transcribe audio if voice mode
            if "Voice" in mode and audio_file is not None:
                with st.spinner("Transcribing audio answer using Faster-Whisper..."):
                    audio_bytes = audio_file.read()
                    answer_text = transcribe_audio(audio_bytes)
                    st.info(f"**Transcribed Speech:** \"{answer_text}\"")

            if not answer_text or not answer_text.strip():
                st.warning("Please provide an answer before submitting.")
            else:
                with st.spinner("Analyzing answer relevance, length, and clarity..."):
                    ideal_kws = curr_q.get("ideal_keywords", "")
                    eval_res = evaluate_answer(curr_q.get("question", ""), answer_text, ideal_kws)

                    # Speech metrics if audio was uploaded
                    comm_score = 75.0
                    if audio_file is not None:
                        audio_file.seek(0)
                        comm_metrics = analyze_audio_metrics(audio_file.read(), answer_text)
                        comm_score = comm_metrics["communication_score"]
                        st.session_state["latest_comm_score"] = comm_score

                    # Record in history
                    record = {
                        "question": curr_q.get("question"),
                        "answer": answer_text,
                        "answer_type": "Voice" if "Voice" in mode else "Text",
                        "difficulty": curr_diff,
                        "score": eval_res["score"],
                        "relevance": eval_res["relevance"],
                        "clarity": eval_res["clarity"],
                        "length_score": eval_res["length"],
                        "feedback": eval_res["feedback"]
                    }
                    history.append(record)
                    asked_ids.append(curr_q.get("id"))

                    st.session_state["answers_history"] = history
                    st.session_state["asked_ids"] = asked_ids
                    st.session_state["current_score"] = eval_res["score"]

                    # Show evaluation feedback
                    st.success(f"Answer Score: **{eval_res['score']}%** (Relevance: {eval_res['relevance']}%, Clarity: {eval_res['clarity']}%, Length: {eval_res['length']}%)")
                    st.info(f"**Feedback:** {eval_res['feedback']}")

                    # Adaptive next question
                    resume_skills = st.session_state.get("resume_skills", [])
                    next_q, next_diff = get_next_adaptive_question(role, eval_res["score"], asked_ids, resume_skills=resume_skills)
                    st.session_state["current_question"] = next_q
                    st.session_state["current_difficulty"] = next_diff
                    st.rerun()

        # Display history during session
        if history:
            st.markdown("---")
            st.markdown("### Session Question History")
            for idx, h in enumerate(reversed(history), 1):
                st.markdown(f"**Q{len(history) - idx + 1} ({h['difficulty']}):** {h['question']}")
                st.markdown(f"*Score:* **{h['score']}%** | *Feedback:* {h['feedback']}")
