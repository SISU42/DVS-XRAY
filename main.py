from typing import Union, List, Optional

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

from db_connection import DB_CONNECTION

from api_calls import get_db_status, get_trainer_list, get_facility_list, get_team_list, get_org_list, \
    get_workout_list, get_dvs_client_table, get_workout_id_name_dict


def process_db_status(db_status: Union[int, str]) -> None:
    if db_status == '1':
        st.success("Connection successful")
    else:
        st.error("Cannot connect to db")
    return


def connect_to_db(db_name: str) -> Union[None, DB_CONNECTION]:
    db_status = None
    db_name_ = None
    if db_name == 'DVS Analytics':
        db_name_ = DB_CONNECTION.FORECAST
        db_status = get_db_status(db_name_.value)
    elif db_name == "DVS Training":
        db_name_ = DB_CONNECTION.PROD
        db_status = get_db_status(db_name_.value)
    elif db_name == "Mayo Clinic":
        db_name_ = DB_CONNECTION.MAYO
        db_status = get_db_status(db_name_.value)
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


def check_required_fields(*args):
    """
    If any of the arguments is None, returns 0 else 1
    :param args:
    :return:
    """
    if 'None' in args:
        return 0
    else:
        return 1


# Player tab
with st.expander("Add new player"):
    with st.form(key="add_new_player"):
        first_name = st.text_input(label="First name*", value=None)
        last_name = st.text_input(label="Last name*", value=None)

        if db_connection_name == DB_CONNECTION.FORECAST:
            suffix = st.text_input(label="Suffix", value=None)

        birthdate = st.date_input(label="Birthdate*", value=None)

        if db_connection_name != DB_CONNECTION.FORECAST:
            email = st.text_input(label="Email*", value=None)
            trainer = st.selectbox(label="Trainer*", options=get_trainer_list(db_connection_name.value))
            facility = st.selectbox(label="Facility*", options=get_facility_list(db_connection_name.value))
            organization = st.selectbox(label="Organization*", options=get_org_list(db_connection_name.value))

        team = st.selectbox(label="Team*", options=get_team_list(db_connection_name.value))
        position = st.selectbox(label="Position", options=["Starter", "Reliever"])
        throws = st.selectbox(label="Throws", options=["Left", "Right"])

        if db_connection_name != DB_CONNECTION.FORECAST:
            workout = st.selectbox(label="Workout*", options=get_workout_list(db_connection_name.value))
            phone = st.text_input(label="Phone", value=None, max_chars=10)
        else:
            retired = st.selectbox(label="Retired*", options=['No', 'Yes'])
            height = st.text_input(label="Height (in)*", value=None)
            weight = st.text_input(label="Weight (lbs)*", value=None)
            mlbamid = st.text_input(label="MLBAMID", value=None)

        st.text('*Required')

        submit_form = st.form_submit_button(label="SUBMIT")

        if submit_form:
            req_fields = check_required_fields(first_name, last_name, birthdate,
                                               email, trainer, facility, organization, team,
                                               workout)
            if not req_fields:
                st.error('All required fields must be entered')
            else:
                st.success('Form is successfully submitted')


def get_index(list_, value_):
    """
    Get index value from list. If there is a value error, return 0
    :param list_:
    :param value_:
    :return:
    """
    try:
        index = list_.index(value_)
        return index
    except ValueError:
        return 0


def get_postion(pos: str) -> Optional[str]:
    """
    Based on position code return the actual position
    :param pos:
    :return:
    """
    if pos == 'S':
        return 'Starter'
    elif pos == 'R':
        return 'Reliever'
    else:
        return None


def get_throws(thrw: str) -> Optional[str]:
    """
    Based on throwing code return left or right
    :param thrw:
    :return:
    """
    if thrw == 'R':
        return 'Right'
    elif thrw == 'L':
        return 'Left'
    else:
        return None


with st.expander('Edit existing player'):

    # Add a search box
    last_name_search = st.text_input(label="Search by last name: ", max_chars=50)

    # Last name condition to display agg table
    if len(last_name_search) != 0:
        grid_response = get_dvs_client_table(db_connection_name.value, last_name_search, key_=last_name_search)

        selected_rows = grid_response['selected_rows']

        if len(selected_rows) != 0:
            form = st.form(key='edit_player')
            selected_row = selected_rows[0]
            first_name = form.text_input(label="First name*", value=selected_row['client_firstname'])
            last_name = form.text_input(label="Last name*", value=selected_row['client_lastname'])
            birthdate = form.text_input(label="Birthdate*", value=selected_row['birthday'])
            email = form.text_input(label="Email*", value=selected_row['client_email'])

            trainer_list = get_trainer_list(db_connection_name.value)
            trainer = form.selectbox(label="Trainer*", options=trainer_list)

            facility_list = get_facility_list(db_connection_name.value)
            facility = form.selectbox(label="Facility*", index=facility_list.index(selected_row['facility_name']),
                                    options=facility_list)

            organization_list = get_org_list(db_connection_name.value)
            organization = form.selectbox(label="Organization*",
                                        index=get_index(organization_list, selected_row['current_organization']),
                                        options=organization_list)

            team_list = get_team_list(db_connection_name.value)
            team = form.selectbox(label="Team*", index=get_index(team_list, selected_row['current_team']),
                                options=team_list)

            db_position = get_postion(selected_row["position"])
            position_list = ["Starter", "Reliever"]
            position = form.selectbox(label="Position", index=get_index(position_list, db_position),
                                    options=["Starter", "Reliever"])

            db_throws = get_throws(selected_row["throws"])
            throws_list = ["Left", "Right"]
            throws = form.selectbox(label="Throws", index=get_index(throws_list, db_throws), options=["Left", "Right"])

            workout_id_name_dict = get_workout_id_name_dict(db_connection_name.value)
            workout_list = get_workout_list(db_connection_name.value)
            workout = form.selectbox(label="Workout*",
                                   index=get_index(workout_list, workout_id_name_dict[selected_row['workout_id']]),
                                   options=workout_list)

            phone = form.text_input(label="Phone", value=selected_row['client_phone'], max_chars=12)

            st.text('*Required')

            submit_form = form.form_submit_button(label="SUBMIT")

            if submit_form:
                req_fields = check_required_fields(first_name, last_name, birthdate,
                                                   email, trainer, facility, organization, team,
                                                   workout)
                if not req_fields:
                    st.error('All required fields must be entered')
                else:
                    st.success('Form is successfully submitted')



# with st.expander('Update bio and performance data'):
#     grid_response = get_dvs_client_table(db_connection_name.value, "")
#     selected_rows = grid_response['selected_rows']
#
#     if selected_rows:
#         form = st.form(key='update_bio')
#         selected_row = selected_rows[0]
#         form.text(f"Selected player: {selected_row['client_firstname']} {selected_row['client_lastname']}")



with st.expander('Add range of motion data'):
    st.text('Add a range of motion data')

# Score tab

# Report tab

# X-RAY tab

# Compare tab

# Logout tab