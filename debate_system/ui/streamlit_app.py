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
            
            def stream_feedback(agent_name: str, current_message_chunk: str):
                # If this is a new message (first chunk), add it to our chronological list
                if agent_name not in st.session_state.get("current_speakers", set()):
                    # Track that this agent is now speaking
                    if "current_speakers" not in st.session_state:
                        st.session_state.current_speakers = set()
                    
                    st.session_state.current_speakers.add(agent_name)
                    
                    # Create a new message entry
                    message_index = len(messages_chronological)
                    messages_chronological.append({
                        "agent": agent_name,
                        "text": current_message_chunk,
                        "box": feedback_container.empty()
                    })
                else:
                    # Find the most recent message from this agent
                    for message in reversed(messages_chronological):
                        if message["agent"] == agent_name:
                            message["text"] += current_message_chunk
                            break
                
                # Clear speakers set when an agent finishes (this assumes chunks come in sequence)
                if agent_name == "Delphi" or agent_name == "Final Consensus" or agent_name == "Audit Report":
                    # Reset speakers after Delphi/final outputs which mark end of a phase
                    st.session_state.current_speakers = set()
                
                # Update the UI for this message
                for message in messages_chronological:
                    # Apply special formatting based on agent type
                    if message["agent"] == "Round_Marker":
                        # For round markers, use distinct styling with dividers
                        message["box"].markdown(f'<div style="text-align:center; margin:20px 0; border-top:1px solid #ddd; border-bottom:1px solid #ddd; padding:8px 0;">{message["text"]}</div>', unsafe_allow_html=True)
                    elif message["agent"] == "Delphi":
                        prefix = "🧠 **Delphi Synthesis (Round " + str(len(st.session_state.get("completed_rounds", [])) + 1) + ")**:"
                        message["box"].markdown(f'{prefix} {message["text"]}▌')
                    elif message["agent"] == "Mediator":
                        prefix = "🧑‍⚖️ **Mediator**:"
                        message["box"].markdown(f'{prefix} {message["text"]}▌')
                    elif message["agent"] == "Final Consensus":
                        prefix = "✅ **Final Consensus**:"
                        message["box"].markdown(f'{prefix} {message["text"]}▌')
                    elif message["agent"] == "Audit Report":
                        prefix = "📋 **Audit Report**:"
                        message["box"].markdown(f'{prefix} {message["text"]}▌')
                    else:
                        prefix = f'🗣️ **{message["agent"]}**:'
                        message["box"].markdown(f'{prefix} {message["text"]}▌')
                
                # Track completed rounds when Delphi speaks
                if agent_name == "Delphi":
                    if "completed_rounds" not in st.session_state:
                        st.session_state.completed_rounds = []
                    st.session_state.completed_rounds.append(True)

            dm.start(feedback_callback=stream_feedback)

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
