import streamlit as st
import matplotlib.pyplot as plt
from utils.presentation import parse_pptx, evaluate_presentation
from database.database import save_presentation_session, save_progress_snapshot

def create_matplotlib_presentation_chart(eval_results):
    """Generate Matplotlib horizontal bar chart for presentation score breakdown."""
    fig, ax = plt.subplots(figsize=(6, 3), facecolor='#1e293b')
    ax.set_facecolor('#1e293b')

    metrics = ['Content Score', 'Structure Score', 'Communication', 'Coverage Score', 'Overall Score']
    scores = [
        eval_results.get('content_score', 0),
        eval_results.get('structure_score', 0),
        eval_results.get('communication_score', 0),
        eval_results.get('coverage_score', 0),
        eval_results.get('score', 0)
    ]
    colors = ['#0284c7', '#2563eb', '#6366f1', '#8b5cf6', '#10b981']

    bars = ax.barh(metrics, scores, color=colors, height=0.5)
    ax.set_xlim(0, 105)
    ax.set_title("Presentation Delivery Breakdown (%)", color='#ffffff', fontsize=11, pad=10, fontweight='bold')
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

def render_presentation_page():
    st.markdown("""
    <div class="banner-card">
        <h1>🎤 Presentation Coach</h1>
        <p>Analyze slide structure, text density, and spoken delivery to master your presentation skills.</p>
    </div>
    """, unsafe_allow_html=True)

    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in to evaluate presentations and track your progress.")
        return

    st.subheader("Presentation Setup & Uploads")
    topic = st.text_input("Presentation Topic / Title", placeholder="e.g. AI-Driven Healthcare Innovations")
    
    col1, col2 = st.columns(2)
    with col1:
        pptx_file = st.file_uploader("Upload PowerPoint (.pptx)", type=["pptx"])
    with col2:
        audio_file = st.file_uploader("Upload Presentation Audio (WAV, MP3, M4A)", type=["wav", "mp3", "m4a"])

    if st.button("Evaluate Presentation", key="evaluate_pres_btn", use_container_width=True):
        if not pptx_file:
            st.warning("Please upload a PowerPoint (.pptx) file to evaluate.")
        else:
            with st.spinner("Analyzing slide structure and transcribing speech audio..."):
                pptx_bytes = pptx_file.read()
                pptx_stats = parse_pptx(pptx_bytes)

                eval_results = evaluate_presentation(pptx_stats, topic=topic, audio_file=audio_file)
                st.session_state["presentation_evaluation"] = eval_results

                # Save presentation session to SQLite bound to user["id"]
                pres_id = save_presentation_session(
                    user_id=user["id"],
                    presentation_name=topic or pptx_file.name,
                    ppt_filename=pptx_file.name,
                    duration=eval_results.get("comm_metrics", {}).get("duration", 0.0),
                    content_score=eval_results["content_score"],
                    speech_score=eval_results["communication_score"],
                    communication_score=eval_results["communication_score"],
                    overall_score=eval_results["score"],
                    weaknesses=eval_results["weaknesses"],
                    improvement_plan=eval_results["improvement_plan"]
                )
                
                # Save progress snapshot in SQLite
                save_progress_snapshot(
                    user_id=user["id"],
                    presentation_score=eval_results["score"],
                    communication_score=eval_results["communication_score"],
                    readiness_score=eval_results["score"]
                )

                st.session_state["last_presentation_score"] = eval_results["score"]
                st.session_state["latest_comm_score"] = eval_results["communication_score"]
                st.success("Presentation evaluation completed and saved to your database history!")

    eval_results = st.session_state.get("presentation_evaluation")
    if eval_results:
        st.markdown("---")
        st.subheader("📊 Presentation Analysis & Feedback")

        # Score Overview Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Overall Score", f"{eval_results['score']}%")
        with m2:
            st.metric("Content Score", f"{eval_results['content_score']}%")
        with m3:
            st.metric("Structure Score", f"{eval_results['structure_score']}%")
        with m4:
            st.metric("Communication Score", f"{eval_results['communication_score']}%")

        st.markdown("---")
        c_chart, c_details = st.columns([1, 1])

        with c_chart:
            st.markdown("### 📈 Delivery Breakdown (Matplotlib)")
            fig_pres = create_matplotlib_presentation_chart(eval_results)
            st.pyplot(fig_pres)

        with c_details:
            st.markdown("### 🌟 Strengths")
            for s in eval_results["strengths"]:
                st.markdown(f"- ✅ {s}")

            st.markdown("### ⚠️ Areas for Improvement")
            for w in eval_results["weaknesses"]:
                st.markdown(f"- ❌ {w}")

        st.markdown("---")
        st.markdown("### 🚀 Personalized Improvement Plan")
        for p in eval_results["improvement_plan"]:
            st.markdown(f"- 🚀 {p}")

        if eval_results.get("transcript"):
            with st.expander("📝 View Spoken Speech Transcript"):
                st.write(eval_results["transcript"])