import streamlit as st

# Sidebar selection
add_selectbox = st.sidebar.selectbox(
    "Select DB: ",
    ("DVS Analytics", "DVS Training", "Mayo Clinic")
)


# Add tabs
tab_player, tab_score, tab_report, tab_x_ray, tab_compare, tab_logout = st.tabs(
        ["Player", "Score", "Report", "X-RAY", "Compare", "Logoustrt"])