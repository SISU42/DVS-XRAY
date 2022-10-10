import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# Sidebar selection
add_selectbox = st.sidebar.selectbox(
    "Select DB: ",
    ("None", "DVS Analytics", "DVS Training", "Mayo Clinic")
)


# Add tabs
tab_player, tab_score, tab_report, tab_x_ray, tab_compare, tab_logout = st.tabs(
        ["Player", "Score", "Report", "X-RAY", "Compare", "Logout"])

# Player tab
with st.expander("Add new player"):
    with st.form(key="add_new_player"):
        first_name = st.text_input(label="First name")
        last_name = st.text_input(label="Last name")
        birthdate = st.date_input(label="Birthdate")
        email = st.text_input(label="Email")
        trainer = st.selectbox(label="Trainer", options=["This", "list", "needs", "to", "be", "populated"])
        facility = st.selectbox(label="Facility", options=["This", "list", "needs", "to", "be", "populated"])
        organization = st.selectbox(label="Organization", options=["This", "list", "needs", "to", "be", "populated"])
        team = st.selectbox(label="Team", options=["This", "list", "needs", "to", "be", "populated"])
        position = st.selectbox(label="Position", options=["Starter", "Reliever"])
        throws = st.selectbox(label="Throws", options=["Left", "Right"])
        workout = st.selectbox(label="Workout", options=["This", "list", "needs", "to", "be", "populated"])
        phone = st.text_input(label="Phone", max_chars=10)

        submit_form = st.form_submit_button(label="SUBMIT")





with st.expander('Edit existing player'):
    st.text('Edit existing player')

    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})


    gd = GridOptionsBuilder.from_dataframe(df)
    gd.configure_selection(selection_mode='multiple', use_checkbox=True)
    gridoptions = gd.build()

    AgGrid(df, gridOptions=gridoptions)

with st.expander('Update bio and performance data'):
    st.text('update bio')

with st.expander('Add range of motion data'):
    st.text('Add a range of motion data')



# Score tab

# Report tab

# X-RAY tab

# Compare tab

# Logout tab