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
            
            # Create a container for all feedback
            feedback_container = st.container()
            # Track messages chronologically
            messages_chronological = []
            
            def stream_feedback(agent_name: str, full_message: str, round_number: int = 1):
                if "messages_chronological" not in st.session_state:
                    st.session_state.messages_chronological = []
                if "completed_rounds" not in st.session_state:
                    st.session_state.completed_rounds = []

                # ── Round Marker (visual section divider) ──
                if agent_name == "Round_Marker":
                    message_entry = {
                        "agent": agent_name,
                        "round_id": round_number,
                        "text": full_message,
                        "box": feedback_container.empty()
                    }
                    st.session_state.messages_chronological.append(message_entry)
                    message_entry["box"].markdown(
                        f'<div style="text-align:center; margin:20px 0; border-top:1px solid #ddd; border-bottom:1px solid #ddd; padding:8px 0;">{full_message}</div>',
                        unsafe_allow_html=True
                    )
                    return

                # ── Add new message box with full content ──
                message_entry = {
                    "agent": agent_name,
                    "round_id": round_number,
                    "text": full_message,
                    "box": feedback_container.empty()
                }
                st.session_state.messages_chronological.append(message_entry)

                # ── Format and render the box ──
                if agent_name == "Delphi":
                    prefix = f"🧠 **Delphi Synthesis (Round {round_number})**:"
                elif agent_name == "Mediator":
                    prefix = f"🧑‍⚖️ **Mediator (Round {round_number})**:"
                elif agent_name == "Final Consensus":
                    prefix = "✅ **Final Consensus**:"
                elif agent_name == "Audit Report":
                    prefix = "📋 **Audit Report**:"
                else:
                    prefix = f'🗣️ **{agent_name} (Round {round_number})**:'

                message_entry["box"].markdown(f"{prefix} {full_message}")

                # ── Track round completion if Delphi finishes ──
                if agent_name == "Delphi":
                    st.session_state.completed_rounds.append(True)

            # Wrapper to extract round number from debate manager callback
            def feedback_callback(agent_name, full_message, round_number=None):
                import re
                if round_number is not None:
                    rn = round_number
                elif agent_name == "Round_Marker":
                    m = re.search(r"Round (\d+)", full_message)
                    rn = int(m.group(1)) if m else 1
                else:
                    rn = len(st.session_state.completed_rounds) + 1
                stream_feedback(agent_name, full_message, rn)

            dm.start(feedback_callback=feedback_callback)

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
