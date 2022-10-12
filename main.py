from typing import Union

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

from api_calls import get_db_status, get_trainer_list, get_facility_list, get_team_list, get_org_list, get_workout_list


def process_db_status(db_status: Union[int, str]) -> None:
    if db_status == '1':
        st.success("Connection successful")
    else:
        st.error("Cannot connect to db")
    return


def connect_to_db(db_name: str) -> Union[None, str]:
    db_status = None
    db_name_ = None
    if db_name == 'DVS Analytics':
        db_name_ = 'forecast'
        db_status = get_db_status(db_name_)
    elif db_name == "DVS Training":
        db_name_ = 'prod'
        db_status = get_db_status(db_name_)
    elif db_name == "Mayo Clinic":
        db_name_ = 'mayo'
        db_status = get_db_status(db_name_)
    else:
        return None

    process_db_status(db_status)

    return db_name_


# Sidebar selection
add_selectbox = st.sidebar.selectbox(
    "Select DB: ",
    ("None", "DVS Analytics", "DVS Training", "Mayo Clinic")
)

db_connection_name = None
if add_selectbox != 'None':
    db_connection_name = connect_to_db(add_selectbox)


# Add tabs
tab_player, tab_score, tab_report, tab_x_ray, tab_compare, tab_logout = st.tabs(
        ["Player", "Score", "Report", "X-RAY", "Compare", "Logout"])

# Player tab
with st.expander("Add new player"):
    with st.form(key="add_new_player"):
        first_name = st.text_input(label="First name*")
        last_name = st.text_input(label="Last name*")
        birthdate = st.date_input(label="Birthdate*")
        email = st.text_input(label="Email*")
        trainer = st.selectbox(label="Trainer*", options=get_trainer_list(db_connection_name))
        facility = st.selectbox(label="Facility*", options=get_facility_list(db_connection_name))
        organization = st.selectbox(label="Organization*", options=get_org_list(db_connection_name))
        team = st.selectbox(label="Team*", options=get_team_list(db_connection_name))
        position = st.selectbox(label="Position", options=["Starter", "Reliever"])
        throws = st.selectbox(label="Throws", options=["Left", "Right"])
        workout = st.selectbox(label="Workout*", options=get_workout_list(db_connection_name))
        phone = st.text_input(label="Phone", max_chars=10)

        st.text('*Required')

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