# ui/components.py

import streamlit as st

def display_markdown_log(markdown_text: str):
    st.markdown(markdown_text, unsafe_allow_html=True)

def show_agent_profiles(personas: list):
    st.subheader("🤖 Agent Profiles")
    for p in personas:
        st.markdown(f"**{p['name']}** – _{p['role']}_")
