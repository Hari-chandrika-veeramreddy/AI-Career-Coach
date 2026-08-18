import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from utils.scoring import calculate_overall_readiness, generate_7_day_improvement_plan
from database.database import (
    get_dashboard_stats, get_user_profile, get_user_latest_career_result,
    get_user_interview_history, get_user_presentation_history,
    get_user_progress_history, get_user_recent_activities
)

def create_matplotlib_progress_chart(progress_snapshots):
    """Generate Matplotlib line plot for progress history."""
    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor='#1e293b')
    ax.set_facecolor('#1e293b')

    attempts = [f"Attempt {idx+1}" for idx in range(len(progress_snapshots))]
    readiness_scores = [r["readiness_score"] if r["readiness_score"] is not None else 0 for r in progress_snapshots]
    interview_scores = [r["interview_score"] if r["interview_score"] is not None else 0 for r in progress_snapshots]

    ax.plot(attempts, readiness_scores, marker='o', color='#10b981', linewidth=2.5, label='Readiness Score')
    ax.plot(attempts, interview_scores, marker='s', color='#2563eb', linewidth=2, linestyle='--', label='Interview Score')

    ax.set_ylim(0, 105)
    ax.set_title("Score Progression Across Attempts", color='#ffffff', fontsize=12, pad=12, fontweight='bold')
    ax.set_xlabel("Attempt Session", color='#94a3b8', fontsize=9)
    ax.set_ylabel("Score (%)", color='#94a3b8', fontsize=9)
    ax.tick_params(colors='#94a3b8', labelsize=8)
    ax.grid(True, color='#334155', linestyle=':', alpha=0.6)

    # Style legend
    legend = ax.legend(facecolor='#0f172a', edgecolor='#334155', fontsize=8)
    for text in legend.get_texts():
        text.set_color('#f8fafc')

    # Spines styling
    for spine in ax.spines.values():
        spine.set_color('#334155')

    plt.tight_layout()
    return fig

def create_matplotlib_category_chart(breakdown):
    """Generate Matplotlib bar chart for category breakdown."""
    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor='#1e293b')
    ax.set_facecolor('#1e293b')

    categories = list(breakdown.keys())
    scores = [b["raw_value"] if b["raw_value"] is not None else 0 for b in breakdown.values()]
    colors = ['#0284c7', '#2563eb', '#6366f1', '#8b5cf6', '#10b981']

    bars = ax.barh(categories, scores, color=colors[:len(categories)], height=0.5)
    ax.set_xlim(0, 105)
    ax.set_title("Readiness by Category (%)", color='#ffffff', fontsize=12, pad=12, fontweight='bold')
    ax.tick_params(colors='#94a3b8', labelsize=8)
    ax.grid(True, color='#334155', linestyle=':', alpha=0.6, axis='x')

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 2, bar.get_y() + bar.get_height()/2, f'{round(width, 1)}%',
                va='center', color='#f8fafc', fontsize=8, fontweight='bold')

    for spine in ax.spines.values():
        spine.set_color('#334155')

    plt.tight_layout()
    return fig

def render_dashboard_page():
    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in to view your personalized Career Readiness Dashboard.")
        return

    st.markdown(f"""
    <div class="banner-card">
        <h1>📊 WELCOME BACK, {user['name'].upper()}</h1>
        <p>College: <b>{user['college']}</b> | Branch: <b>{user['branch']}</b> | Personal Performance Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Fetch User-Isolated SQLite Data
    user_id = user["id"]
    db_stats = get_dashboard_stats(user_id)
    profile = get_user_profile(user_id)
    latest_career = get_user_latest_career_result(user_id)
    interview_hist = get_user_interview_history(user_id)
    pres_hist = get_user_presentation_history(user_id)
    progress_snapshots = get_user_progress_history(user_id)
    recent_activities = get_user_recent_activities(user_id)

    # Calculate metrics
    resume_match = db_stats.get("latest_resume_match")
    interview_score = db_stats.get("avg_interview")
    presentation_score = db_stats.get("avg_presentation")
    comm_score = db_stats.get("avg_communication")
    tech_score = resume_match

    overall_score, status_label, breakdown = calculate_overall_readiness(
        resume_match=resume_match,
        interview_score=interview_score,
        tech_score=tech_score,
        comm_score=comm_score,
        presentation_score=presentation_score
    )

    # 2. Metric Score Cards
    m1, m2, m3, m4, m5, m6 = st.columns(6)

    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Resume Match</div>
            <div class="metric-value">{breakdown['Resume / Job Match']['status']}</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Interview Score</div>
            <div class="metric-value">{breakdown['Interview Performance']['status']}</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Technical Skills</div>
            <div class="metric-value">{breakdown['Technical Skills']['status']}</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Communication</div>
            <div class="metric-value">{breakdown['Communication Skills']['status']}</div>
        </div>
        """, unsafe_allow_html=True)

    with m5:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Presentation</div>
            <div class="metric-value">{breakdown['Presentation Skills']['status']}</div>
        </div>
        """, unsafe_allow_html=True)

    with m6:
        overall_display = f"{overall_score}%" if overall_score is not None else "Not evaluated"
        st.markdown(f"""
        <div class="metric-box" style="border-left-color: #10b981;">
            <div class="metric-title">Readiness Score</div>
            <div class="metric-value" style="color:#10b981;">{overall_display}</div>
            <div style="font-size:0.75rem; font-weight:700; color:#059669; margin-top:0.2rem;">{status_label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 3. Recent Activity & Matplotlib Charts Section
    c_act, c_chart = st.columns([1, 1])

    with c_act:
        st.markdown("### 🕒 Recent Activity")
        if recent_activities:
            df_act = pd.DataFrame([
                {"Date": a["date"], "Activity": a["activity"], "Score": a["score"]}
                for a in recent_activities
            ])
            st.dataframe(df_act, use_container_width=True, hide_index=True)
        else:
            st.info("No recent activities recorded yet. Complete an analysis or interview to build your timeline!")

    with c_chart:
        st.markdown("### 📉 Progress Over Time (Matplotlib)")
        if progress_snapshots:
            fig_prog = create_matplotlib_progress_chart(progress_snapshots)
            st.pyplot(fig_prog)
        else:
            st.info("Progress trend chart will appear as you complete multiple assessments.")

    st.markdown("---")

    # Matplotlib Category Breakdown Chart & Activity Overview
    c_cat, c_plan = st.columns(2)
    
    with c_cat:
        st.markdown("### 🎯 Skill Category Breakdown (Matplotlib)")
        fig_cat = create_matplotlib_category_chart(breakdown)
        st.pyplot(fig_cat)

    with c_plan:
        st.markdown("### 🗓️ Personalized 7-Day Improvement Plan")
        missing_skills = latest_career.get("missing_skills", []) if latest_career else []
        plan_dict = generate_7_day_improvement_plan(missing_skills=missing_skills)
        for day, task in plan_dict.items():
            st.markdown(f"**{day}:** {task}")

    st.markdown("---")

    # 4. Previous Interview Sessions & Previous Presentations Section
    c_int_hist, c_pres_hist = st.columns(2)

    with c_int_hist:
        st.markdown("### 🎯 Previous Interview Sessions")
        if interview_hist:
            for s in interview_hist:
                s_date = s["completed_at"][:10] if s.get("completed_at") else "Recent"
                with st.expander(f"🗓️ {s_date} — {s['role']} | **Score: {round(s['final_score'], 1)}%** ({s['total_questions']} Qs)"):
                    st.write(f"**Difficulty Level:** {s.get('difficulty_level', 'Medium')}")
                    if s.get("answers"):
                        st.markdown("**Per-Question Answers:**")
                        for idx, ans in enumerate(s["answers"], 1):
                            st.markdown(f"**Q{idx} ({ans['difficulty']}):** {ans['question']}")
                            st.markdown(f"*Your Answer:* \"{ans['answer_text']}\"")
                            st.markdown(f"*Score:* **{round(ans['overall_score'], 1)}%** | *Feedback:* {ans['feedback']}")
                            st.markdown("---")
        else:
            st.info("No previous mock interview sessions found.")

    with c_pres_hist:
        st.markdown("### 🎤 Previous Presentations")
        if pres_hist:
            for p in pres_hist:
                p_date = p["created_at"][:10] if p.get("created_at") else "Recent"
                with st.expander(f"📁 {p_date} — {p['presentation_name']} | **Score: {round(p['overall_score'], 1)}%**"):
                    st.write(f"**Content Score:** {round(p['content_score'], 1)}% | **Speech Score:** {round(p['speech_score'], 1)}%")
                    if p.get("weaknesses"):
                        st.markdown("**Detected Weaknesses:**")
                        for w in p["weaknesses"]:
                            st.markdown(f"- ❌ {w}")
                    if p.get("improvement_plan"):
                        st.markdown("**Improvement Plan:**")
                        for plan_item in p["improvement_plan"]:
                            st.markdown(f"- 🚀 {plan_item}")
        else:
            st.info("No previous presentation evaluations found.")