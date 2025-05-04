import sys
import os
import streamlit as st
import yaml

# Internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.config import load_config
from app.debate_manager import DebateManager
from ui.pages.ContradictionHeatmap import render_contradiction_heatmap

st.set_page_config(layout="wide")
st.title("🧠 Autonomous Debate Engine")

# ─── Session State Initialization ───────────────────────
if "debate_complete" not in st.session_state:
    st.session_state.debate_complete = False
    st.session_state.session_id = None
    st.session_state.summary_md = None
    st.session_state.contradiction_log = None
    st.session_state.dm = None
    st.session_state.cfg_text = None

# ─── Upload Config ──────────────────────────────────────
st.sidebar.header("📁 Configuration")
uploaded_config = st.sidebar.file_uploader("Upload Config (.yaml)", type=["yaml", "yml"])

if uploaded_config:
    cfg_text = uploaded_config.read().decode()
    st.session_state.cfg_text = cfg_text  # ✅ persist config
    st.sidebar.text_area("YAML Preview", value=cfg_text, height=300)

if st.session_state.cfg_text:
    os.makedirs("tmp", exist_ok=True)
    temp_path = os.path.join("tmp", "temp_uploaded.yaml")
    with open(temp_path, "w") as f:
        f.write(st.session_state.cfg_text)

    config = load_config(temp_path)

    # ─── Start Debate ──────────────────────────────────
    if st.sidebar.button("🚀 Start Debate"):
        with st.spinner("Running Debate..."):
            dm = DebateManager(config)
            st.session_state.dm = dm

            # Display the topic
            topic = dm.config.get("topic", "No Topic Specified")
            st.subheader(f"📜 Debate Topic: {topic}")
            feedback_box = st.empty()
            feedback_buffer = {"current_agent": None, "text": ""}

            def stream_feedback(agent_name: str, current_message_chunk: str):
                debug_chunk_preview = current_message_chunk[:100].replace('\\n', ' ')
                print(f"DEBUG UI Callback: Agent='{agent_name}', Chunk='{debug_chunk_preview}...'")

                if agent_name != feedback_buffer["current_agent"]:
                    feedback_buffer["current_agent"] = agent_name
                    feedback_buffer["text"] = current_message_chunk
                else:
                    feedback_buffer["text"] += current_message_chunk

                feedback_box.markdown(f'🗣️ **{feedback_buffer["current_agent"]}:** {feedback_buffer["text"]}▌')

            dm.start(feedback_callback=stream_feedback)

            # Clear the feedback box after the debate finishes
            feedback_box.empty()

            # Store results after debate ends
            st.session_state.debate_complete = True
            st.session_state.session_id = dm.session_id
            st.session_state.contradiction_log = dm.contradiction_log

            # Correct indentation for reading summary file
            try:
                with open(f"sessions/{dm.session_id}/summary.md") as f:
                    st.session_state.summary_md = f.read()
            except FileNotFoundError:
                st.session_state.summary_md = "Summary file not found."
                st.warning(f"Could not find summary file: sessions/{dm.session_id}/summary.md")

        st.success("✅ Debate completed!")

# ─── Output Results ─────────────────────────────────────
if st.session_state.debate_complete:
    st.subheader("📜 Debate Summary")
    st.markdown(st.session_state.summary_md)

    st.subheader("📦 Session ID")
    st.code(st.session_state.session_id)

    # Safe checkbox persistence
    if "show_heatmap" not in st.session_state:
        st.session_state.show_heatmap = False

    if st.checkbox("📊 Show Contradiction Heatmap", value=st.session_state.show_heatmap):
        st.session_state.show_heatmap = True
        if st.session_state.contradiction_log:
            render_contradiction_heatmap(st.session_state.contradiction_log)
        else:
            st.warning("No contradiction log available.")

else:
    st.info("Please upload a YAML config file to begin.")
