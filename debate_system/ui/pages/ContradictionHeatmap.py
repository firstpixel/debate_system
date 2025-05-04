import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from app.contradiction_log import ContradictionLog

def render_contradiction_heatmap(log: ContradictionLog):
    st.subheader("🔥 Contradiction Heatmap")

    heatmap_data = log.to_heatmap_data()

    if not heatmap_data:
        st.info("No contradictions detected yet.")
        return

    df = pd.DataFrame.from_dict(heatmap_data, orient='index', columns=["Contradiction Count"])
    df.index.name = "Agent"

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(df, annot=True, fmt="d", cmap="Reds", linewidths=1, linecolor="black", ax=ax)
    ax.set_title("Contradictions per Agent")
    st.pyplot(fig)
