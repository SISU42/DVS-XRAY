from typing import Union, List, Optional, Dict
from datetime import datetime

import re
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

from db_connection import DB_CONNECTION

from payloads import Insert_player_payload_non_forecast, Insert_dvs_eval_payload

from api_calls import get_db_status, get_trainer_dict, get_facility_dict, get_team_dict, get_org_dict, \
    get_workout_list, get_dvs_client_table, get_workout_id_name_dict, get_analyst_names, get_dvs_player_table, \
    get_dvs_score, check_duplicates, generate_primary_key, add_player_to_db


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
    elif db_name == "DVS Dev":
        db_name_ = DB_CONNECTION.DEV
        db_status = get_db_status(db_name_.value)
    else:
        return None

    process_db_status(db_status)

    return db_name_


# Sidebar selection
add_selectbox = st.sidebar.selectbox(
        "Select DB: ",
        ("DVS Dev", "DVS Analytics", "DVS Training", "Mayo Clinic")
)

db_connection_name = None
if add_selectbox != 'None':
    db_connection_name = connect_to_db(add_selectbox)

# Add tabs
tab_player, tab_score, tab_report, tab_x_ray, tab_compare, tab_admin, tab_logout = st.tabs(
        ["Player", "Score", "Report", "X-RAY", "Compare", "Admin", "Logout"])

# Init setup
# Facility dict
facility_dict = get_facility_dict(db_connection_name.value)
rev_facility_dict = {v: k for k,v in facility_dict.items()}

# Trainer dict
trainer_dict = get_trainer_dict(db_connection_name.value)
rev_trainer_dict = {v: k for k, v in trainer_dict.items()}

# Team dict
team_dict = get_team_dict(db_connection_name.value)
rev_team_dict = {v: k for k,v in team_dict.items()}

# Organization dict
organization_dict = get_org_dict(db_connection_name.value)
rev_organization_dict = {v: k for k, v in organization_dict.items()}


def check_required_fields(*args):
    """
    If any of the arguments is None, returns 0 else 1
    :param args:
    :return:
    """
    if 'None' in args:
        return 0
    elif "" in args:
        return 0
    else:
        return 1


def submit_player_to_add(db_name: str, table_name: str, pk: str,
                         payload_object: Insert_player_payload_non_forecast) -> bool:
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    add_player_to_db(db_name=db_name, pk=pk_to_insert, payload=payload_object)

    return True


# Player tab
def get_workout_id_from_workout(workout: str) -> int:
    """
    Return a workout id based on workout. Choose the first workout_id for a given workout name
    :param workout:
    :return:
    """
    workout_dict = {
        'Rookie': 1,
        'A'     : 7,
        'AA'    : 16
    }
    return workout_dict[workout]


with tab_player.expander("Add new player"):
    form_add_player = st.form(key='Add player', clear_on_submit=True)
    first_name = form_add_player.text_input(label="First name*", value=None)
    last_name = form_add_player.text_input(label="Last name*", value=None)

    if db_connection_name == DB_CONNECTION.FORECAST:
        suffix = form_add_player.text_input(label="Suffix", value=None)

    birthdate = form_add_player.date_input(label="Birthdate*", value=None)
    birthyear = int(birthdate.year)
    birthdate = birthdate.strftime('%Y-%m-%d')

    if db_connection_name != DB_CONNECTION.FORECAST:
        email = form_add_player.text_input(label="Email*", value=None)
        trainer = form_add_player.selectbox(label="Trainer*", options=list(trainer_dict.values()))
        facility = form_add_player.selectbox(label="Facility*", options=list(facility_dict.values()))
        organization = form_add_player.selectbox(label="Organization*", options=list(organization_dict.values()))

    team = form_add_player.selectbox(label="Team*", options=list(team_dict.values()))
    position = form_add_player.selectbox(label="Position", options=["Starter", "Reliever"])
    throws = form_add_player.selectbox(label="Throws", options=["Left", "Right"])

    if db_connection_name != DB_CONNECTION.FORECAST:
        workout = form_add_player.selectbox(label="Workout*", options=get_workout_list(db_connection_name.value))
        workout_id = get_workout_id_from_workout(workout)
        phone = form_add_player.text_input(label="Phone", value=None, max_chars=10)
    else:
        retired = form_add_player.selectbox(label="Retired*", options=['No', 'Yes'])
        height = form_add_player.text_input(label="Height (in)*", value=None)
        weight = form_add_player.text_input(label="Weight (lbs)*", value=None)
        mlbamid = form_add_player.text_input(label="MLBAMID", value=None)

    form_add_player.text('*Required')

    submit_form = form_add_player.form_submit_button(label="SUBMIT")

    if submit_form:
        # Check if all required fields are entered
        req_fields = check_required_fields(first_name, last_name, birthdate,
                                           email, trainer, facility, organization, team,
                                           workout)

        # Check for required fields
        if not req_fields:
            tab_player.error('All required fields must be entered')
            st.stop()

        # Check if player exists by checking birthday, first_name, last_name
        duplicate_check = check_duplicates(db_connection_name.value, birthdate, first_name, last_name)
        if not duplicate_check:
            tab_player.error('This player exists in the database')
            st.stop()

        # Submit to DB
        if db_connection_name != DB_CONNECTION.FORECAST:
            # Create a non forecast payload object
            add_player_object = Insert_player_payload_non_forecast(client_firstname=first_name,
                                                                   client_lastname=last_name, throws=throws[0],
                                                                   birthday=birthdate, birthyear=birthyear,
                                                                   workout_id=workout_id, position=position[0],
                                                                   current_organization=organization[3:],
                                                                   dvs_trainer_id=int(rev_trainer_dict[trainer]),
                                                                   dvs_facility_id=int(rev_facility_dict[facility]), current_team=team,
                                                                   client_email=email, client_phone=phone,
                                                                   org_id=organization[0], team_id=team[0])
            submit_player_to_add(db_connection_name.value, 'dvs_client', 'dvs_client_id',
                                 payload_object=add_player_object)
            st.success(f"Added player to {db_connection_name.value}")

        # else:
        #     # Create a forecast payload object


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


def strip_id_from_name(str_: str) -> Optional[str]:
    """
    Removes the preceding id from the id-val combination
    :param str_:
    :return:
    """
    pattern = re.compile(r"([\d]+) - (.*)")
    search_ = pattern.search(str_)
    if search_:
        return search_.group(2)
    else:
        return None


with tab_player.expander('Edit existing player'):
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

            if db_connection_name == DB_CONNECTION.FORECAST:
                suffix = form.text_input(label="Suffix")

            birthdate = form.date_input(label="Birthdate*", value=datetime.fromisoformat(selected_row['birthday']))

            if db_connection_name != DB_CONNECTION.FORECAST:
                email = form.text_input(label="Email*", value=selected_row['client_email'])

                trainer_list = list(trainer_dict.values())
                trainer = form.selectbox(label="Trainer*", index=trainer_list.index(selected_row['trainer_name']),
                                         options=trainer_list)

                facility_list = list(facility_dict.values())
                facility = form.selectbox(label="Facility*", index=facility_list.index(selected_row['facility_name']),
                                          options=facility_list)

                organization_list = list(organization_dict.values())
                organization = form.selectbox(label="Organization*",
                                              index=get_index(organization_list, selected_row['current_organization']),
                                              options=organization_list)

            team_list = list(team_dict.values())
            team = form.selectbox(label="Team*", index=get_index(team_list, selected_row['current_team']),
                                  options=team_list)

            db_position = get_postion(selected_row["position"])
            position_list = ["Starter", "Reliever"]
            position = form.selectbox(label="Position", index=get_index(position_list, db_position),
                                      options=["Starter", "Reliever"])

            db_throws = get_throws(selected_row["throws"])
            throws_list = ["Left", "Right"]
            throws = form.selectbox(label="Throws", index=get_index(throws_list, db_throws), options=["Left", "Right"])

            if db_connection_name != DB_CONNECTION.FORECAST:
                workout_id_name_dict = get_workout_id_name_dict(db_connection_name.value)
                workout_list = get_workout_list(db_connection_name.value)
                workout = form.selectbox(label="Workout*",
                                         index=get_index(workout_list,
                                                         workout_id_name_dict[selected_row['workout_id']]),
                                         options=workout_list)

                phone = form.text_input(label="Phone", value=selected_row['client_phone'], max_chars=12)
            else:
                retired = form.selectbox(label='Retired*', options=['Yes', 'No'])
                height_in = form.text_input(label='Height (in)*')
                weight_lbs = form.text_input(label='Weight (lbs)*')
                mlbamid = form.text_input(label='MLBAMID')

            tab_player.text('*Required')

            submit_form = form.form_submit_button(label="SUBMIT")

            if submit_form:
                req_fields = check_required_fields(first_name, last_name, birthdate,
                                                   email, trainer, facility, organization, team,
                                                   workout)
                if not req_fields:
                    st.error('All required fields must be entered')
                    st.stop()

                # Check if player exists by checking birthday, first_name, last_name
                duplicate_check = check_duplicates(db_connection_name.value, birthdate, first_name, last_name)
                if not duplicate_check:
                    tab_player.error('This player exists in the database')
                    st.stop()

                # Update db


# def insert_dvs_eval(payload: Insert_dvs_eval_payload) -> bool:
#     """
#     Inserts a row into dvs_eval table
#     :param payload:
#     :return:
#     """
#     # TODO get the value of eval id
#
#     # TODO perform insert


with tab_player.expander('Add bio and performance data'):
    if db_connection_name == DB_CONNECTION.FORECAST:
        st.write('DOES NOT APPLY TO DVS ANALYTICS')
    else:
        # Add a search box
        last_name_search = st.text_input(label="Search by last name: ", max_chars=50,
                                         key='Add bio and performance data')

        # Last name condition to display agg table
        if len(last_name_search) != 0:
            grid_response = get_dvs_client_table(db_connection_name.value, last_name_search, key_=last_name_search)
            selected_rows = grid_response['selected_rows']

            if len(selected_rows) != 0:
                form_add_bio = st.form(key='add_bio')
                eval_date = form_add_bio.date_input(label='Eval Date*')

                trainer_list = list(trainer_dict.values())
                trainer = form_add_bio.selectbox(label="DVS Trainer", options=trainer_list)

                height_in = form_add_bio.text_input(label='Height (in)*')
                weight_lbs = form_add_bio.text_input(label='Weight (lbs)*')
                avg_fb_velo = form_add_bio.text_input(label='Avg FB Velo')
                max_fb_velo = form_add_bio.text_input(label='Max FB Velo')
                avg_fb_spin_rate = form_add_bio.text_input(label='Avg FB Spin Rate')
                avg_cb_velo = form_add_bio.text_input(label='Avg CB Velo')
                avg_cb_spin_rate = form_add_bio.text_input(label='Avg CB Spin Rate')

                st.text('*Required')

                submit_form = form_add_bio.form_submit_button(label='ADD')

                if submit_form:
                    # Check if all required fields are entered
                    req_fields = check_required_fields(eval_date, height_in, weight_lbs)

                    # Check for required fields
                    if not req_fields:
                        tab_player.error('All required fields must be entered')
                        st.stop()

with tab_player.expander('Add range of motion data'):
    if db_connection_name == DB_CONNECTION.FORECAST:
        st.write('DOES NOT APPLY TO DVS ANALYTICS')
    else:
        form_add_motion = st.form(key='add_motion')
        eval_date = form_add_motion.date_input(label='Eval Date*')

        trainer_list = list(trainer_dict.values())
        trainer = form_add_motion.selectbox(label="DVS Trainer", options=trainer_list)

        d_ir = form_add_motion.text_input(label='D_IR')
        d_er = form_add_motion.text_input(label='D_ER')
        nd_ir = form_add_motion.text_input(label='ND_IR')
        nd_er = form_add_motion.text_input(label='ND_ER')
        d_tam = form_add_motion.text_input(label='D_TAM')
        nd_tam = form_add_motion.text_input(label='ND_TAM')
        d_flex = form_add_motion.text_input(label='D_FLEX')
        nd_flex = form_add_motion.text_input(label='ND_FLEX')
        d_cuff_str = form_add_motion.text_input(label='D_CUFF_STR')
        nd_cuff_str = form_add_motion.text_input(label='ND_CUFF_STR')
        d_ir_cuff_str = form_add_motion.text_input(label='D_IR_CUFF_STR')
        d_er_cuff_str = form_add_motion.text_input(label='D_ER_CUFF_STR')
        nd_ir_cuff_str = form_add_motion.text_input(label='ND_IR_CUFF_STR')
        nd_er_cuff_str = form_add_motion.text_input(label='ND_ER_CUFF_STR')
        d_kibler = form_add_motion.text_input(label='D_Kibler')
        nd_kibler = form_add_motion.text_input(label='ND_Kibler')
        kibler = form_add_motion.text_input(label='Kibler')

        st.write('*Required')

        submit_form_add_motion = form_add_motion.form_submit_button('SUBMIT')


# Score tab
def get_selected_player_display(raw_dict: Dict, db_connection: DB_CONNECTION) -> str:
    """
    Based on the DB_CONNECTION value return selected player to be displayed in the form
    :param raw_dict:
    :param db_connection:
    :return:
    """
    if db_connection == DB_CONNECTION.FORECAST:
        suffix = raw_dict['name_suffix']
        suffix = suffix if suffix else ""
        return f"{raw_dict['first_name']} {raw_dict['last_name']} {suffix}"
    else:
        return f"{raw_dict['client_firstname']} {raw_dict['client_lastname']}"


with tab_score.expander('Add new DVS Score'):
    # Add a search box
    last_name_search = st.text_input(label="Search by last name: ", max_chars=50, key='add_new_score')

    # Last name condition to display agg table - forecast db fetches data from dvs_player, others from dvs_client
    if len(last_name_search) != 0:
        if db_connection_name != DB_CONNECTION.FORECAST:
            grid_response = get_dvs_client_table(db_connection_name.value, last_name_search,
                                                 key_=f"{last_name_search}_score")
        else:
            grid_response = get_dvs_player_table(last_name_search, key_=f"{last_name_search}_score")

        selected_rows = grid_response['selected_rows']

        if len(selected_rows) != 0:
            form_add_score = st.form(key='add_score')
            selected_row = selected_rows[0]

            selected_player = get_selected_player_display(selected_row, db_connection_name)
            form_add_score.markdown(f"Selected player: {selected_player}")

            score_date = form_add_score.date_input(label='Score date*')

            # TODO Waiting on permissions for dvs_client table on dvs_forecast db
            # dvs_analyst = form_add_score.selectbox(label='DVS Analyst',
            #                                        options=get_analyst_names(db_connection_name.value))

            mm_score = form_add_score.number_input(label='MM_SCORE*')
            mm_stop = form_add_score.number_input(label='MM_STOP')
            mm_deg = form_add_score.number_input(label='MM_DEG')

            as_score = form_add_score.number_input(label='AS_SCORE*')
            as_r = form_add_score.number_input(label='AS_R')
            as_h = form_add_score.number_input(label='AS_H')
            as_b = form_add_score.number_input(label='AS_B')
            as_r_deg = form_add_score.number_input(label='AS_R_DEG')
            as_h_deg = form_add_score.number_input(label='AS_H_DEG')

            p_score = form_add_score.number_input(label='P_SCORE*')
            p_flex_deg = form_add_score.number_input(label='P_FLEX_DEG')
            p_ext_deg = form_add_score.number_input(label='P_EXT_DEG')
            p_chg_deg = form_add_score.number_input(label='P_CHG_DEG')

            pafs_score = form_add_score.number_input(label='PAFS_SCORE*')
            pafs_below = form_add_score.number_input(label='PAFS_BELOW')
            pafs_vert = form_add_score.number_input(label='PAFS_VERT')
            pafs_spine = form_add_score.number_input(label='PAFS_SPINE')
            pafs_dir = form_add_score.number_input(label='PAFS_DIR')
            pafs_vstrike_deg = form_add_score.number_input(label='PAFS_VSTRIKE_DEG')
            pafs_stretch_deg = form_add_score.number_input(label='PAFS_STRETCH_DEG')
            pafs_horiz_deg = form_add_score.number_input(label='PAFS_HORIZ_DEG')
            pafs_vert_deg = form_add_score.number_input(label='PAFS_VERT_DEG')

            paa_score = form_add_score.number_input(label='PAA_SCORE*')
            paa_bow_deg = form_add_score.number_input(label='PAA_BOW_DEG')
            paa_deg = form_add_score.number_input(label='PAA_DEG')
            paa_os = form_add_score.number_input(label='PAA_OS')
            paa_spine_deg = form_add_score.number_input(label='PAA_SPINE_DEG')
            paa_chest_deg = form_add_score.number_input(label='PAA_CHEST_DEG')
            paa_vext_deg = form_add_score.number_input(label='PAA_VEXT_DEG')

            f_score = form_add_score.number_input(label='F_SCORE*')
            f_bf = form_add_score.number_input(label='F_BF')
            f_par = form_add_score.number_input(label='F_PAR')
            f_oh = form_add_score.number_input(label='F_OH')
            f_hd = form_add_score.number_input(label='F_HD')
            f_par_deg = form_add_score.number_input(label='F_PAR_DEG')
            f_oh_deg = form_add_score.number_input(label='F_OH_DEG')

            ap1_score = form_add_score.number_input(label='ap1_score')
            total_dvs_score = form_add_score.number_input(label='total_dvs_score*')

            form_add_score.write('Required*')

            submit_form_add_score = form_add_score.form_submit_button('SUBMIT')


def get_client_player_id(db_connection_name: DB_CONNECTION, selected_row: Dict) -> int:
    """
    Based on the database, get player_id or client_id
    :param db_connection_name:
    :param selected_row:
    :return:
    """
    if db_connection_name == DB_CONNECTION.FORECAST:
        return selected_row['dvs_player_id']
    else:
        return selected_row['dvs_client_id']


def replace_none(raw_dict: Dict) -> Dict:
    """
    Replace None values in raw_dict with -1
    :param raw_dict:
    :return:
    """
    return {k: -1 if not v else v for k, v in raw_dict.items()}


with tab_score.expander('Edit existing DVS Score'):
    # Add a search box
    last_name_search = st.text_input(label="Search by last name: ", max_chars=50, key='edit_existing_score')

    # Last name condition to display agg table - forecast db fetches data from dvs_player, others from dvs_client
    if len(last_name_search) != 0:
        if db_connection_name != DB_CONNECTION.FORECAST:
            grid_response = get_dvs_client_table(db_connection_name.value, last_name_search,
                                                 key_=f"{last_name_search}_score")
        else:
            grid_response = get_dvs_player_table(last_name_search, key_=f"{last_name_search}_score")

        selected_player_rows = grid_response['selected_rows']

        if len(selected_player_rows) > 0:
            selected_player_row = selected_player_rows[0]

            client_id = get_client_player_id(db_connection_name, selected_player_row)
            grid_response_score = get_dvs_score(db_connection_name.value, client_id,
                                                key_=f"{last_name_search}_{client_id}")

            selected_scores = grid_response_score['selected_rows']

            if len(selected_scores) > 0:
                form_edit_score = st.form(key='edit_score')
                selected_score = replace_none(selected_scores[0])

                selected_player = get_selected_player_display(selected_player_row, db_connection_name)
                form_edit_score.markdown(f"Selected player: {selected_player}")
                score_date = form_edit_score.date_input(label='Score date*',
                                                        value=datetime
                                                        .fromisoformat(selected_score['score_date']))

                # TODO Waiting on permissions for dvs_client table on dvs_forecast db
                # dvs_analyst = form_add_score.selectbox(label='DVS Analyst',
                #                                        options=get_analyst_names(db_connection_name.value))

                mm_score = form_edit_score.number_input(label='MM_SCORE*', value=selected_score['mm_score'])
                mm_stop = form_edit_score.number_input(label='MM_STOP', value=selected_score['mm_stop'])
                mm_deg = form_edit_score.number_input(label='MM_DEG', value=selected_score['mm_deg'])

                as_score = form_edit_score.number_input(label='AS_SCORE*', value=selected_score['as_score'])
                as_r = form_edit_score.number_input(label='AS_R', value=selected_score['as_r'])
                as_h = form_edit_score.number_input(label='AS_H', value=selected_score['as_h'])
                as_b = form_edit_score.number_input(label='AS_B', value=selected_score['as_b'])
                as_r_deg = form_edit_score.number_input(label='AS_R_DEG', value=selected_score['as_r_deg'])
                as_h_deg = form_edit_score.number_input(label='AS_H_DEG', value=selected_score['as_h_deg'])

                p_score = form_edit_score.number_input(label='P_SCORE*', value=selected_score['p_score'])
                p_flex_deg = form_edit_score.number_input(label='P_FLEX_DEG', value=selected_score['p_flex_deg'])
                p_ext_deg = form_edit_score.number_input(label='P_EXT_DEG', value=selected_score['p_ext_deg'])
                p_chg_deg = form_edit_score.number_input(label='P_CHG_DEG', value=selected_score['p_chg_deg'])

                pafs_score = form_edit_score.number_input(label='PAFS_SCORE*', value=selected_score['pafs_score'])
                pafs_below = form_edit_score.number_input(label='PAFS_BELOW', value=selected_score['pafs_below'])
                pafs_vert = form_edit_score.number_input(label='PAFS_VERT', value=selected_score['pafs_vert'])
                pafs_spine = form_edit_score.number_input(label='PAFS_SPINE', value=selected_score['pafs_spine'])
                pafs_dir = form_edit_score.number_input(label='PAFS_DIR', value=selected_score['pafs_dir'])
                pafs_vstrike_deg = form_edit_score.number_input(label='PAFS_VSTRIKE_DEG',
                                                                value=selected_score['pafs_vstrike_deg'])
                pafs_stretch_deg = form_edit_score.number_input(label='PAFS_STRETCH_DEG',
                                                                value=selected_score['pafs_stretch_deg'])
                pafs_horiz_deg = form_edit_score.number_input(label='PAFS_HORIZ_DEG',
                                                              value=selected_score['pafs_horiz_deg'])
                pafs_vert_deg = form_edit_score.number_input(label='PAFS_VERT_DEG',
                                                             value=selected_score['pafs_vert_deg'])

                paa_score = form_edit_score.number_input(label='PAA_SCORE*', value=selected_score['paa_score'])
                paa_bow_deg = form_edit_score.number_input(label='PAA_BOW_DEG', value=selected_score['paa_bow_deg'])
                paa_deg = form_edit_score.number_input(label='PAA_DEG', value=selected_score['paa_deg'])
                paa_os = form_edit_score.number_input(label='PAA_OS', value=selected_score['paa_os'])
                paa_spine_deg = form_edit_score.number_input(label='PAA_SPINE_DEG',
                                                             value=selected_score['paa_spine_deg'])
                paa_chest_deg = form_edit_score.number_input(label='PAA_CHEST_DEG',
                                                             value=selected_score['paa_chest_deg'])
                paa_vext_deg = form_edit_score.number_input(label='PAA_VEXT_DEG',
                                                            value=selected_score['paa_vext_deg'])

                f_score = form_edit_score.number_input(label='F_SCORE*', value=selected_score['f_score'])
                f_bf = form_edit_score.number_input(label='F_BF', value=selected_score['f_bf'])
                f_par = form_edit_score.number_input(label='F_PAR', value=selected_score['f_par'])
                f_oh = form_edit_score.number_input(label='F_OH', value=selected_score['f_oh'])
                f_hd = form_edit_score.number_input(label='F_HD', value=selected_score['f_hd'])
                f_par_deg = form_edit_score.number_input(label='F_PAR_DEG', value=selected_score['f_par_deg'])
                f_oh_deg = form_edit_score.number_input(label='F_OH_DEG', value=selected_score['f_oh_deg'])

                ap1_score = form_edit_score.number_input(label='ap1_score', value=selected_score['ap1_score'])
                total_dvs_score = form_edit_score.number_input(label='total_dvs_score*',
                                                               value=selected_score['total_dvs_score'])

                form_edit_score.write('Required*')

                submit_form_add_score = form_edit_score.form_submit_button('SUBMIT')

        # form_edit_score = st.form(key='edit_score')
        #
        # score_date = form_edit_score.date_input(label='Score date*', value=grid_response_score['score_date'])

# Admin tab
with tab_admin:
    if db_connection_name == DB_CONNECTION.FORECAST:
        st.markdown('Does not apply to *DVS Analytics*')
    else:
        with tab_admin.expander('Add trainer'):
            form_add_trainer_admin = st.form(key='add_trainer_admin')
            first_name = form_add_trainer_admin.text_input(label='First name*')
            last_name = form_add_trainer_admin.text_input(label='Last name*')
            email = form_add_trainer_admin.text_input(label='Email')
            facility = form_add_trainer_admin.text_input(label='Facility*')
            phone = form_add_trainer_admin.text_input(label='Phone')

            form_add_trainer_admin.markdown('*Required')

            form_add_trainer_admin.form_submit_button(label='SUBMIT')

        with tab_admin.expander('Edit existing trainer'):
            pass

        with tab_admin.expander('Add facility'):
            form_add_facility_admin = st.form(key='add_facility_admin')
            facility_name = form_add_facility_admin.text_input(label='Facility name*')
            phone_ = form_add_facility_admin.text_input(label='Phone')
            address = form_add_facility_admin.text_input(label='Address')
            city = form_add_facility_admin.text_input(label='City')
            state = form_add_facility_admin.text_input(label='State')
            country = form_add_facility_admin.text_input(label='Country')
            post_code = form_add_facility_admin.text_input(label='Post code')

            form_add_facility_admin.markdown('*Required')

            form_add_facility_admin.form_submit_button(label='SUBMIT')

        with tab_admin.expander('Edit existing facility'):
            pass

        with tab_admin.expander('Add organinzation'):
            form_add_org_admin = st.form(key='add_organization_admin')
            name = form_add_org_admin.text_input(label='Name*')
            address_ = form_add_org_admin.text_input(label='Address')
            city_ = form_add_org_admin.text_input(label='City')
            state_ = form_add_org_admin.text_input(label='State')
            postcode_ = form_add_org_admin.text_input(label='Postcode')
            country_ = form_add_org_admin.text_input(label='Country')
            president = form_add_org_admin.text_input(label='President')
            phone__ = form_add_org_admin.text_input(label='Phone')
            email__ = form_add_org_admin.text_input(label='Email')
            website = form_add_org_admin.text_input(label='Website')

            form_add_org_admin.markdown('*Required')
            form_add_org_admin.form_submit_button(label='SUBMIT')

        with tab_admin.expander('Edit existing organization'):
            pass

        with tab_admin.expander('Add team'):
            form_add_team_admin = st.form(key='add_team_admin')
            organization_name_ = form_add_team_admin.selectbox(label='Organization*',
                                                               options=get_org_dict(db_connection_name.value))
            team_name = form_add_team_admin.text_input(label='Team name')
            team_address = form_add_team_admin.text_input(label='Address')
            team_city = form_add_team_admin.text_input(label='City')
            team_state = form_add_team_admin.text_input(label='State')
            team_postcode = form_add_team_admin.text_input(label='Postcode')
            team_country = form_add_team_admin.text_input(label='Country')
            team_phone = form_add_team_admin.text_input(label='Phone')
            team_email = form_add_team_admin.text_input(label='Email')
            team_website = form_add_team_admin.text_input(label='Website')
            team_facility = form_add_team_admin.selectbox(label='Facility',
                                                          options=list(team_dict.values()))
            team_trainer = form_add_team_admin.selectbox(label='Trainer',
                                                         options=list(team_dict.values()))

            form_add_team_admin.markdown('*Required')
            form_add_team_admin.form_submit_button(label='SUBMIT')

        with tab_admin.expander('Edit existing team'):
            pass

# Report tab
with tab_report:
    st.markdown("This feature is under development.")
# X-RAY tab


# Compare tab
with tab_compare:
    st.markdown("This feature is under development.")

# Logout tab