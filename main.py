from typing import Union, List, Optional, Dict, Callable
from datetime import datetime

import os
import sys
import re
import shutil
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

from db_connection import DB_CONNECTION

from db_setup import DB_setup

from payloads import Player_payload_non_forecast, Insert_dvs_eval_payload, Insert_dvs_eval_rom, Insert_dvs_score, \
    DVS_trainer, DVS_facility, DVS_organization, DVS_team, Player_payload_forecast

from api_calls import get_db_status, get_trainer_dict, get_facility_dict, get_team_dict, get_org_dict, \
    get_workout_list, get_dvs_client_table, get_workout_id_name_dict, get_dvs_player_table, \
    get_dvs_score, check_duplicates, generate_primary_key, add_player_to_db, add_eval_info_to_db, add_eval_rom_to_db, \
    add_dvs_score_to_db, get_analyst_dict, check_trainer_exists, add_trainer_to_db, check_facility_exists, \
    add_facility_to_db, check_org_exists, check_team_exists, add_team_to_db, DBCONNECTException, update_client_on_db, \
    update_player_on_db, update_trainer_on_db, get_dvs_trainer_table, get_dvs_facility_table, update_facility_on_db, \
    get_dvs_org_table, update_org_on_db, get_dvs_team_table, update_team_on_db

from msk.uploaded_video_file import UploadedFile, uploaded_videos_dir_name, upload_video, video_exists, get_video_bytes

# Sidebar selection
add_selectbox = st.sidebar.selectbox(
        "Select DB: ",
        ("DVS Dev", "DVS Analytics", "DVS Training", "Mayo Clinic")
)

db_connection_name = None
db_init_setup = None
if add_selectbox != 'None':
    db_init_setup = DB_setup(add_selectbox, st)
    db_connection_name = db_init_setup.db_connection

# Add tabs
tab_player, tab_score, tab_report, tab_x_ray, tab_compare, tab_admin, tab_logout = st.tabs(
        ["Player", "Score", "Report", "X-RAY", "Compare", "Admin", "Logout"])


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
    elif -1 in args:
        return 0
    else:
        return 1


def submit_player_to_add(db_name: str, table_name: str, pk: str,
                         payload_object: Player_payload_non_forecast) -> bool:
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    status_int = add_player_to_db(db_name=db_name, pk=pk_to_insert, payload=payload_object)

    if status_int == 200:
        st.success(f"Player (dvs_client_id:{pk_to_insert}) successfully added to {db_name}")
        return True
    else:
        st.error(f"Error adding player to db due to status code: {status_int}")
        return False


def submit_client_to_update(db_name: str, dvs_client_id: int, payload_object: Player_payload_non_forecast) -> bool:
    """
    :param db_name:
    :param table_name:
    :param pk:
    :param payload_object:
    :return:
    """

    # Perform the update
    status_int = update_client_on_db(db_name, dvs_client_id, payload_object)

    if status_int == 200:
        st.success(f"Player (dvs_client_id:{dvs_client_id}) successfully updated!")
        return True
    else:
        st.error(f"Error updating client to db due to status code: {status_int}")
        st.error(f"Client not updated")
        return False


def submit_player_to_update(db_name: str, dvs_player_id: int, payload_object: Player_payload_forecast) -> bool:
    """
    :param db_name:
    :param table_name:
    :param pk:
    :param payload_object:
    :return:
    """

    # Perform the update
    status_int = update_player_on_db(db_name, dvs_player_id, payload_object)

    if status_int == 200:
        st.success(f"Player (dvs_client_id:{dvs_player_id}) successfully updated!")
        return True
    else:
        st.error(f"Error adding player to db due to status code: {status_int}")
        st.error(f"Player not updated")
        return False


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
        trainer = form_add_player.selectbox(label="Trainer*", options=list(db_init_setup.trainer_dict.values()))
        facility = form_add_player.selectbox(label="Facility*", options=list(db_init_setup.facility_dict.values()))
        organization = form_add_player.selectbox(label="Organization*",
                                                 options=list(db_init_setup.organization_dict.values()))

    team = form_add_player.selectbox(label="Team*", options=list(db_init_setup.team_dict.values()))
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
            add_player_object = Player_payload_non_forecast(client_firstname=first_name,
                                                            client_lastname=last_name, throws=throws[0],
                                                            birthday=birthdate, birthyear=birthyear,
                                                            workout_id=workout_id, position=position[0],
                                                            current_organization=organization[3:],
                                                            dvs_trainer_id=int(
                                                                    db_init_setup.reverse_trainer_dict[trainer]),
                                                            dvs_facility_id=int(
                                                                    db_init_setup.reverse_facility_dict[
                                                                        facility]),
                                                            current_team=team,
                                                            client_email=email, client_phone=phone,
                                                            org_id=db_init_setup.reverse_organization_dict[
                                                                organization],
                                                            team_id=db_init_setup.reverse_team_dict[team])
            submit_player_to_add(db_connection_name.value, 'dvs_client', 'dvs_client_id',
                                 payload_object=add_player_object)

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


def get_table(connection_name, last_name, key_):
    if connection_name != DB_CONNECTION.FORECAST:
        return get_dvs_client_table(connection_name.value, last_name, key_)
    else:
        return get_dvs_player_table(last_name, key_)


with tab_player.expander('Edit existing player'):
    # Add a search box
    last_name_search = st.text_input(label="Search by last name: ", max_chars=50)

    # Last name condition to display agg table
    if len(last_name_search) != 0:
        grid_response = get_table(db_connection_name, last_name_search, key_=last_name_search)

        selected_rows = grid_response['selected_rows']

        if len(selected_rows) != 0:
            edit_player_form = st.form(key='edit_player')
            selected_row = selected_rows[0]

            if db_connection_name != DB_CONNECTION.FORECAST:
                client_firstname = edit_player_form.text_input(label="First name*",
                                                               value=selected_row['client_firstname'])
                client_lastname = edit_player_form.text_input(label="Last name*", value=selected_row['client_lastname'])
                birthdate = edit_player_form.date_input(label="Birthdate*",
                                                        value=datetime.fromisoformat(selected_row['birthday']))
                birthyear = int(birthdate.year)
                birthdate = birthdate.strftime('%Y-%m-%d')

                email = edit_player_form.text_input(label="Email*", value=selected_row['client_email'])

                trainer_options = list(db_init_setup.trainer_dict.values())
                trainer = edit_player_form.selectbox(label='Trainer*', options=trainer_options,
                                                     index=trainer_options
                                                     .index(selected_row.get('trainer_name', None).strip()))

                facility_options = list(db_init_setup.facility_dict.values())
                facility = edit_player_form.selectbox(label='Facility*', options=facility_options,
                                                      index=facility_options
                                                      .index(selected_row['facility_name']))

                org_options = list(db_init_setup.organization_dict.values())
                organization = edit_player_form.selectbox(label='Organization*', options=org_options,
                                                          index=org_options.index(
                                                                  selected_row['current_organization']))

                team_options = list(db_init_setup.team_dict.values())
                team = edit_player_form.selectbox(label="Team*", options=team_options,
                                                  index=team_options.index(selected_row['current_team']))

                position_options = ['R', 'S']
                position = edit_player_form.selectbox(label="Position", options=position_options,
                                                      index=position_options.index(selected_row['position'].strip()))

                throws_options = ['L', 'R']
                throws = edit_player_form.selectbox(label="Throws", options=throws_options,
                                                    index=throws_options.index(selected_row['throws']))

                workout = edit_player_form.number_input(label="Workout*", value=selected_row['workout_id'])
                phone = edit_player_form.text_input(label="Phone", value=selected_row['client_phone'])
                active_flag_options = [0, 1]
                active_flag = edit_player_form.selectbox(label="Active_flag", options=active_flag_options,
                                                         index=active_flag_options.index(selected_row['active_flag']))

                tab_player.text('*Required')
                submit_form = edit_player_form.form_submit_button(label="SUBMIT")

                if submit_form:
                    req_fields = check_required_fields(client_firstname, client_lastname, birthdate,
                                                       email, trainer, facility, organization, team,
                                                       workout)
                    if not req_fields:
                        st.error('All required fields must be entered')
                        st.stop()

                    # Check if player exists by checking birthday, first_name, last_name
                    duplicate_check = check_duplicates(db_connection_name.value, birthdate, client_firstname,
                                                       client_lastname)
                    if not duplicate_check:
                        tab_player.error('This player exists in the database')
                        st.stop()

                    add_client_object = Player_payload_non_forecast(client_firstname=client_firstname,
                                                                    client_lastname=client_lastname, throws=throws[0],
                                                                    birthday=birthdate, birthyear=birthyear,
                                                                    workout_id=workout_id, position=position[0],
                                                                    current_organization=organization[3:],
                                                                    dvs_trainer_id=int(
                                                                            db_init_setup.reverse_trainer_dict[
                                                                                trainer]),
                                                                    dvs_facility_id=int(
                                                                            db_init_setup.reverse_facility_dict[
                                                                                facility]),
                                                                    current_team=team,
                                                                    client_email=email, client_phone=phone,
                                                                    org_id=db_init_setup.reverse_organization_dict[
                                                                        organization],
                                                                    team_id=db_init_setup.reverse_team_dict[team])

                    submit_client_to_update(db_connection_name.value, selected_row['dvs_client_id'], add_client_object)

            else:
                first_name = edit_player_form.text_input(label="First name*", value=selected_row['first_name'])
                last_name = edit_player_form.text_input(label="Last name*", value=selected_row['last_name'])
                name_suffix = edit_player_form.text_input(label="Suffix", value=selected_row['name_suffix'])
                birthdate = edit_player_form.date_input(label="Birthdate*",
                                                        value=datetime.fromisoformat(selected_row['birthdate']))
                birth_year = int(birthdate.year)
                birthdate = birthdate.strftime('%Y-%m-%d')

                team_options_ = list(db_init_setup.team_dict.values())
                team = edit_player_form.selectbox(label="Team*", options=team_options_,
                                                  index=team_options_.index(selected_row['team']))

                position_options = ["RP", "SP"]
                position = edit_player_form.selectbox(label="Position*", options=position_options,
                                                      index=position_options.index(selected_row["position"]))

                throwing_hand_options = ["R", "L"]
                throws = edit_player_form.selectbox(label="Throws*",
                                                    options=throwing_hand_options,
                                                    index=throwing_hand_options.index(selected_row["throwing_hand"]))

                height = edit_player_form.text_input(label="height*", value=selected_row["height"])
                weight = edit_player_form.text_input(label="weight*", value=selected_row["weight"])
                mlbamid = edit_player_form.text_input(label="MLBAMID", value=selected_row["mlbamid"])

                retired_options = [0, 1]
                retired = edit_player_form.selectbox(label="Retired*", options=retired_options,
                                                     index=retired_options.index(selected_row["retired"]))

                tab_player.text('*Required')
                submit_form = edit_player_form.form_submit_button(label="SUBMIT")

                if submit_form:
                    req_fields = check_required_fields(first_name, last_name, birthdate,
                                                       team, position, throws, retired, height, weight)
                    if not req_fields:
                        st.error('All required fields must be entered')
                        st.stop()

                    # Check if player exists by checking birthday, first_name, last_name
                    duplicate_check = check_duplicates(db_connection_name.value, birthdate, first_name, last_name)
                    if not duplicate_check:
                        tab_player.error('This player exists in the database')
                        st.stop()

                    add_player_object = Player_payload_forecast(first_name=first_name, last_name=last_name,
                                                                birthdate=birthdate, birth_year=birth_year, team=team,
                                                                position=position, throwing_hand=throws,
                                                                height=height, weight=weight, mlbamid=mlbamid,
                                                                retired=retired, name_suffix=name_suffix)

                    submit_player_to_update(db_connection_name.value, selected_row['dvs_player_id'], add_player_object)


def insert_eval_info(db_name: str, table_name: str, pk: str,
                     payload_object: Insert_dvs_eval_payload) -> bool:
    """
    Function to insert into dvs_eval table based on db_name
    :param db_name:
    :param table_name:
    :param pk:
    :param payload_object:
    :return:
    """
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    response_status = add_eval_info_to_db(db_name=db_name, eval_id=pk_to_insert, payload=payload_object)

    if response_status == 200:
        return True
    else:
        st.error(f"There has been a problem while db insert with an error status: {response_status}")
        st.stop()


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
                eval_date = form_add_bio.date_input(label='Eval Date*').strftime('%Y-%m-%d')

                trainer_list = list(db_init_setup.trainer_dict.values())
                trainer = form_add_bio.selectbox(label="DVS Trainer", options=trainer_list)

                height_in = form_add_bio.number_input(label='Height (in)*')
                weight_lbs = form_add_bio.number_input(label='Weight (lbs)*')
                avg_fb_velo = form_add_bio.number_input(label='Avg FB Velo', value=-1.0)
                max_fb_velo = form_add_bio.number_input(label='Max FB Velo', value=-1.0)
                avg_fb_spin_rate = form_add_bio.number_input(label='Avg FB Spin Rate', value=-1.0)
                max_fb_spin_rate = form_add_bio.number_input(label='Max FB Spin Rate', value=-1.0)
                avg_cb_velo = form_add_bio.number_input(label='Avg CB Velo', value=-1.0)
                max_cb_velo = form_add_bio.number_input(label='Max CB Velo', value=-1.0)
                avg_cb_spin_rate = form_add_bio.number_input(label='Avg CB Spin Rate', value=-1.0)
                max_cb_spin_rate = form_add_bio.number_input(label='Max CB Spin Rate', value=-1.0)

                st.text('*Required')

                submit_form = form_add_bio.form_submit_button(label='ADD')

                if submit_form:
                    # Check if all required fields are entered
                    req_fields = check_required_fields(eval_date, height_in, weight_lbs)

                    # Check for required fields
                    if not req_fields:
                        tab_player.error('All required fields must be entered')
                        st.stop()

                    payload = Insert_dvs_eval_payload(eval_date=eval_date,
                                                      dvs_trainer_id=int(db_init_setup.reverse_trainer_dict[trainer]),
                                                      height=float(height_in), weight=float(weight_lbs),
                                                      dvs_client_id=selected_rows[0]['dvs_client_id'],
                                                      fb_velocity_avg=avg_fb_velo,
                                                      fb_velocity_max=max_fb_velo, fb_spin_avg=avg_fb_spin_rate,
                                                      fb_spin_max=max_fb_spin_rate, cb_velocity_avg=avg_cb_velo,
                                                      cb_velocity_max=max_cb_velo, cb_spin_avg=avg_cb_spin_rate,
                                                      cb_spin_max=max_cb_spin_rate)
                    insert_eval_info(db_connection_name.value, "dvs_eval", "eval_id", payload)
                    st.success(f"Bio and performance data has been successfully added for client_id " \
                               f"{selected_rows[0]['dvs_client_id']}")


def insert_eval_rom(db_name, table_name, pk, payload_obj: Insert_dvs_eval_rom):
    """
    Function to insert into dvs_eval_rom table
    :param db_name:
    :param table_name:
    :param pk:
    :param payload_obj:
    :return:
    """
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    response_status = add_eval_rom_to_db(db_name=db_name, eval_id=pk_to_insert, payload=payload_obj)

    if response_status == 200:
        return True
    else:
        st.error(f"There has been a problem while db insert with an error status: {response_status}")
        st.stop()


with tab_player.expander('Add range of motion data'):
    if db_connection_name == DB_CONNECTION.FORECAST:
        st.write('DOES NOT APPLY TO DVS ANALYTICS')
    else:
        # Add a search box
        last_name_search = st.text_input(label="Search by last name: ", max_chars=50,
                                         key='Add range of motion data')

        # Last name condition to display agg table
        if len(last_name_search) != 0:
            grid_response = get_dvs_client_table(db_connection_name.value, last_name_search, key_=last_name_search)
            selected_rows = grid_response['selected_rows']

            if len(selected_rows) > 0:
                form_add_motion = st.form(key='add_motion')
                eval_date = form_add_motion.date_input(label='Eval Date*').strftime('%Y-%m-%d')

                trainer_list = list(db_init_setup.trainer_dict.values())
                trainer = form_add_motion.selectbox(label="DVS Trainer", options=trainer_list)

                d_ir = form_add_motion.number_input(label='D_IR', value=-1)
                d_er = form_add_motion.number_input(label='D_ER', value=-1)
                nd_ir = form_add_motion.number_input(label='ND_IR', value=-1)
                nd_er = form_add_motion.number_input(label='ND_ER', value=-1)
                d_tam = form_add_motion.number_input(label='D_TAM', value=-1)
                nd_tam = form_add_motion.number_input(label='ND_TAM', value=-1)
                d_flex = form_add_motion.number_input(label='D_FLEX', value=-1)
                nd_flex = form_add_motion.number_input(label='ND_FLEX', value=-1)
                d_cuff_str = form_add_motion.number_input(label='D_CUFF_STR', value=-1)
                nd_cuff_str = form_add_motion.number_input(label='ND_CUFF_STR', value=-1)
                d_ir_cuff_str = form_add_motion.number_input(label='D_IR_CUFF_STR', value=-1)
                d_er_cuff_str = form_add_motion.number_input(label='D_ER_CUFF_STR', value=-1)
                nd_ir_cuff_str = form_add_motion.number_input(label='ND_IR_CUFF_STR', value=-1)
                nd_er_cuff_str = form_add_motion.number_input(label='ND_ER_CUFF_STR', value=-1)
                d_kibler = form_add_motion.number_input(label='D_Kibler', value=-1)
                nd_kibler = form_add_motion.number_input(label='ND_Kibler', value=-1)
                kibler = form_add_motion.number_input(label='Kibler', value=-1)

                st.write('*Required')

                submit_form_add_motion = form_add_motion.form_submit_button('ADD')

                if submit_form_add_motion:
                    # Check if all required fields are entered
                    req_fields = check_required_fields(eval_date)

                    # Check for required fields
                    if not req_fields:
                        tab_player.error('All required fields must be entered')
                        st.stop()

                    payload = Insert_dvs_eval_rom(eval_date=eval_date, dvs_client_id=selected_rows[0]['dvs_client_id'],
                                                  dvs_trainer_id=int(db_init_setup.reverse_trainer_dict[trainer]),
                                                  dir=d_ir, der=d_er, ndir=nd_ir, nder=nd_er, dtam=d_tam, ndtam=nd_tam,
                                                  dflex=d_flex, ndflex=nd_flex, d_cuff_strength=d_cuff_str,
                                                  kibler=kibler, nd_cuff_strength=nd_cuff_str,
                                                  d_ir_cuff_strength=d_ir_cuff_str, d_er_cuff_strength=d_er_cuff_str,
                                                  nd_ir_cuff_strength=nd_ir_cuff_str,
                                                  nd_er_cuff_strength=nd_er_cuff_str,
                                                  d_kibler=d_kibler, nd_kibler=nd_kibler)
                    insert_eval_rom(db_connection_name.value, "dvs_eval_rom", "eval_id", payload)
                    st.success(f"Range of motion data has been successfully added for client_id "
                               f"{selected_rows[0]['dvs_client_id']}")


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


def insert_to_dvs_score_table(db_name: str, table_name: str, pk, payload_obj: Insert_dvs_score):
    """
    Function to insert into dvs_eval_rom table
    :param db_name:
    :param table_name:
    :param pk:
    :param payload_obj:
    :return:
    """
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    add_dvs_score_to_db(db_name=db_name, score_id=pk_to_insert, payload=payload_obj)

    return True


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

            score_date = form_add_score.date_input(label='Score date*').strftime('%Y-%m-%d')

            # TODO Waiting on permissions for dvs_client table on dvs_forecast db
            dvs_analyst = form_add_score.selectbox(label='DVS Analyst',
                                                   options=db_init_setup.analyst_dict.values())

            mm_score = form_add_score.number_input(label='MM_SCORE*', value=-1)
            mm_stop = form_add_score.number_input(label='MM_STOP', value=-1)
            mm_deg = form_add_score.number_input(label='MM_DEG', value=-1)

            as_score = form_add_score.number_input(label='AS_SCORE*', value=-1)
            as_r = form_add_score.number_input(label='AS_R', value=-1)
            as_h = form_add_score.number_input(label='AS_H', value=-1)
            as_b = form_add_score.number_input(label='AS_B', value=-1)
            as_r_deg = form_add_score.number_input(label='AS_R_DEG', value=-1)
            as_h_deg = form_add_score.number_input(label='AS_H_DEG', value=-1)

            p_score = form_add_score.number_input(label='P_SCORE*', value=-1)
            p_flex_deg = form_add_score.number_input(label='P_FLEX_DEG', value=-1)
            p_ext_deg = form_add_score.number_input(label='P_EXT_DEG', value=-1)
            p_chg_deg = form_add_score.number_input(label='P_CHG_DEG', value=-1)

            pafs_score = form_add_score.number_input(label='PAFS_SCORE*', value=-1)
            pafs_below = form_add_score.number_input(label='PAFS_BELOW', value=-1)
            pafs_vert = form_add_score.number_input(label='PAFS_VERT', value=-1)
            pafs_spine = form_add_score.number_input(label='PAFS_SPINE', value=-1)
            pafs_dir = form_add_score.number_input(label='PAFS_DIR', value=-1)
            pafs_vstrike_deg = form_add_score.number_input(label='PAFS_VSTRIKE_DEG', value=-1)
            pafs_stretch_deg = form_add_score.number_input(label='PAFS_STRETCH_DEG', value=-1)
            pafs_horiz_deg = form_add_score.number_input(label='PAFS_HORIZ_DEG', value=-1)
            pafs_vert_deg = form_add_score.number_input(label='PAFS_VERT_DEG', value=-1)

            paa_score = form_add_score.number_input(label='PAA_SCORE*', value=-1)
            paa_bow_deg = form_add_score.number_input(label='PAA_BOW_DEG', value=-1)
            paa_deg = form_add_score.number_input(label='PAA_DEG', value=-1)
            paa_os = form_add_score.number_input(label='PAA_OS', value=-1)
            paa_spine_deg = form_add_score.number_input(label='PAA_SPINE_DEG', value=-1)
            paa_chest_deg = form_add_score.number_input(label='PAA_CHEST_DEG', value=-1)
            paa_vext_deg = form_add_score.number_input(label='PAA_VEXT_DEG', value=-1)

            f_score = form_add_score.number_input(label='F_SCORE*', value=-1)
            f_bf = form_add_score.number_input(label='F_BF', value=-1)
            f_par = form_add_score.number_input(label='F_PAR', value=-1)
            f_oh = form_add_score.number_input(label='F_OH', value=-1)
            f_hd = form_add_score.number_input(label='F_HD', value=-1)
            f_par_deg = form_add_score.number_input(label='F_PAR_DEG', value=-1)
            f_oh_deg = form_add_score.number_input(label='F_OH_DEG', value=-1)

            ap1_score = form_add_score.number_input(label='ap1_score', value=-1)
            total_dvs_score = form_add_score.number_input(label='total_dvs_score*', value=-1)

            form_add_score.write('Required*')

            submit_form_add_score = form_add_score.form_submit_button('SUBMIT')

            if submit_form_add_score:
                # Check if all required fields are entered
                req_fields = check_required_fields(score_date, mm_score, as_score, p_score, pafs_score,
                                                   paa_score, f_score, total_dvs_score)

                # Check for required fields
                if not req_fields:
                    st.error('All required fields must be entered')
                    st.stop()

                payload = Insert_dvs_score(dvs_client_id=selected_rows[0]['dvs_client_id'], score_date=score_date,
                                           dvs_analyst_id=db_init_setup.reverse_analyst_dict.get(dvs_analyst, -1),
                                           mm_score=mm_score,
                                           mm_stop=mm_stop, mm_deg=mm_deg,
                                           as_score=as_score, as_r=as_r, as_h=as_h, as_b=as_b, as_r_deg=as_r_deg,
                                           as_h_deg=as_h_deg, p_score=p_score, p_flex_deg=p_flex_deg,
                                           p_ext_deg=p_ext_deg, p_chg_deg=p_chg_deg, pafs_score=pafs_score,
                                           pafs_below=pafs_below, pafs_vert=pafs_vert, pafs_spine=pafs_spine,
                                           pafs_dir=pafs_dir, pafs_vstrike_deg=pafs_vstrike_deg,
                                           pafs_stretch_deg=pafs_stretch_deg, pafs_horiz_deg=pafs_horiz_deg,
                                           pafs_vert_deg=pafs_vert_deg,
                                           paa_score=paa_score, paa_bow_deg=paa_bow_deg, paa_deg=paa_deg, paa_os=paa_os,
                                           paa_spine_deg=paa_spine_deg, paa_chest_deg=paa_chest_deg,
                                           paa_vext_deg=paa_vext_deg,
                                           f_score=f_score, f_bf=f_bf, f_par=f_par, f_oh=f_oh, f_hd=f_hd,
                                           f_par_deg=f_par_deg, f_oh_deg=f_oh_deg, ap1_score=ap1_score,
                                           total_dvs_score=total_dvs_score)
                insert_to_dvs_score_table(db_name=db_connection_name.value, table_name="dvs_score",
                                          pk="dvs_score_id", payload_obj=payload)
                st.success(f"Scores have been successfully added for client_id "
                           f"{selected_rows[0]['dvs_client_id']}")


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


# with tab_score.expander('Edit existing DVS Score'):
#     # Add a search box
#     last_name_search = st.text_input(label="Search by last name: ", max_chars=50, key='edit_existing_score')
#
#     # Last name condition to display agg table - forecast db fetches data from dvs_player, others from dvs_client
#     if len(last_name_search) != 0:
#         if db_connection_name != DB_CONNECTION.FORECAST:
#             grid_response = get_dvs_client_table(db_connection_name.value, last_name_search,
#                                                  key_=f"{last_name_search}_score")
#         else:
#             grid_response = get_dvs_player_table(last_name_search, key_=f"{last_name_search}_score")
#
#         selected_player_rows = grid_response['selected_rows']
#
#         if len(selected_player_rows) > 0:
#             selected_player_row = selected_player_rows[0]
#
#             client_id = get_client_player_id(db_connection_name, selected_player_row)
#             grid_response_score = get_dvs_score(db_connection_name.value, client_id,
#                                                 key_=f"{last_name_search}_{client_id}")
#
#             selected_scores = grid_response_score['selected_rows']
#
#             if len(selected_scores) > 0:
#                 form_edit_score = st.form(key='edit_score')
#                 selected_score = replace_none(selected_scores[0])
#
#                 selected_player = get_selected_player_display(selected_player_row, db_connection_name)
#                 form_edit_score.markdown(f"Selected player: {selected_player}")
#                 score_date = form_edit_score.date_input(label='Score date*',
#                                                         value=datetime
#                                                         .fromisoformat(selected_score['score_date']))
#
#                 # TODO Waiting on permissions for dvs_client table on dvs_forecast db
#                 # dvs_analyst = form_add_score.selectbox(label='DVS Analyst',
#                 #                                        options=get_analyst_names(db_connection_name.value))
#
#                 mm_score = form_edit_score.number_input(label='MM_SCORE*', value=selected_score['mm_score'])
#                 mm_stop = form_edit_score.number_input(label='MM_STOP', value=selected_score['mm_stop'])
#                 mm_deg = form_edit_score.number_input(label='MM_DEG', value=selected_score['mm_deg'])
#
#                 as_score = form_edit_score.number_input(label='AS_SCORE*', value=selected_score['as_score'])
#                 as_r = form_edit_score.number_input(label='AS_R', value=selected_score['as_r'])
#                 as_h = form_edit_score.number_input(label='AS_H', value=selected_score['as_h'])
#                 as_b = form_edit_score.number_input(label='AS_B', value=selected_score['as_b'])
#                 as_r_deg = form_edit_score.number_input(label='AS_R_DEG', value=selected_score['as_r_deg'])
#                 as_h_deg = form_edit_score.number_input(label='AS_H_DEG', value=selected_score['as_h_deg'])
#
#                 p_score = form_edit_score.number_input(label='P_SCORE*', value=selected_score['p_score'])
#                 p_flex_deg = form_edit_score.number_input(label='P_FLEX_DEG', value=selected_score['p_flex_deg'])
#                 p_ext_deg = form_edit_score.number_input(label='P_EXT_DEG', value=selected_score['p_ext_deg'])
#                 p_chg_deg = form_edit_score.number_input(label='P_CHG_DEG', value=selected_score['p_chg_deg'])
#
#                 pafs_score = form_edit_score.number_input(label='PAFS_SCORE*', value=selected_score['pafs_score'])
#                 pafs_below = form_edit_score.number_input(label='PAFS_BELOW', value=selected_score['pafs_below'])
#                 pafs_vert = form_edit_score.number_input(label='PAFS_VERT', value=selected_score['pafs_vert'])
#                 pafs_spine = form_edit_score.number_input(label='PAFS_SPINE', value=selected_score['pafs_spine'])
#                 pafs_dir = form_edit_score.number_input(label='PAFS_DIR', value=selected_score['pafs_dir'])
#                 pafs_vstrike_deg = form_edit_score.number_input(label='PAFS_VSTRIKE_DEG',
#                                                                 value=selected_score['pafs_vstrike_deg'])
#                 pafs_stretch_deg = form_edit_score.number_input(label='PAFS_STRETCH_DEG',
#                                                                 value=selected_score['pafs_stretch_deg'])
#                 pafs_horiz_deg = form_edit_score.number_input(label='PAFS_HORIZ_DEG',
#                                                               value=selected_score['pafs_horiz_deg'])
#                 pafs_vert_deg = form_edit_score.number_input(label='PAFS_VERT_DEG',
#                                                              value=selected_score['pafs_vert_deg'])
#
#                 paa_score = form_edit_score.number_input(label='PAA_SCORE*', value=selected_score['paa_score'])
#                 paa_bow_deg = form_edit_score.number_input(label='PAA_BOW_DEG', value=selected_score['paa_bow_deg'])
#                 paa_deg = form_edit_score.number_input(label='PAA_DEG', value=selected_score['paa_deg'])
#                 paa_os = form_edit_score.number_input(label='PAA_OS', value=selected_score['paa_os'])
#                 paa_spine_deg = form_edit_score.number_input(label='PAA_SPINE_DEG',
#                                                              value=selected_score['paa_spine_deg'])
#                 paa_chest_deg = form_edit_score.number_input(label='PAA_CHEST_DEG',
#                                                              value=selected_score['paa_chest_deg'])
#                 paa_vext_deg = form_edit_score.number_input(label='PAA_VEXT_DEG',
#                                                             value=selected_score['paa_vext_deg'])
#
#                 f_score = form_edit_score.number_input(label='F_SCORE*', value=selected_score['f_score'])
#                 f_bf = form_edit_score.number_input(label='F_BF', value=selected_score['f_bf'])
#                 f_par = form_edit_score.number_input(label='F_PAR', value=selected_score['f_par'])
#                 f_oh = form_edit_score.number_input(label='F_OH', value=selected_score['f_oh'])
#                 f_hd = form_edit_score.number_input(label='F_HD', value=selected_score['f_hd'])
#                 f_par_deg = form_edit_score.number_input(label='F_PAR_DEG', value=selected_score['f_par_deg'])
#                 f_oh_deg = form_edit_score.number_input(label='F_OH_DEG', value=selected_score['f_oh_deg'])
#
#                 ap1_score = form_edit_score.number_input(label='ap1_score', value=selected_score['ap1_score'])
#                 total_dvs_score = form_edit_score.number_input(label='total_dvs_score*',
#                                                                value=selected_score['total_dvs_score'])
#
#                 form_edit_score.write('Required*')
#
#                 submit_form_add_score = form_edit_score.form_submit_button('SUBMIT')
#
#         # form_edit_score = st.form(key='edit_score')
#         #
#         # score_date = form_edit_score.date_input(label='Score date*', value=grid_response_score['score_date'])


# Admin tab
def insert_into_dvs_trainer(db_name: str, table_name: str, pk: str, payload: DVS_trainer):
    """
    Trigger dvs_trainer insert API endpoint
    :param db_name:
    :param table_name:
    :param pk:
    :param payload:
    :return:
    """
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    add_trainer_to_db(db_name=db_name, trainer_id=pk_to_insert, payload=payload)

    return True


def update_dvs_trainer(db_name: str, dvs_trainer_id: int, payload: DVS_trainer):
    """
    Update the trainer row given a trainer id
    :param db_name:
    :param dvs_trainer_id:
    :param payload:
    :return:
    """
    update_trainer_on_db(db_name=db_name, trainer_id=dvs_trainer_id, payload=payload)
    return True


def update_dvs_facility(db_name: str, dvs_facility_id: int, payload: DVS_facility):
    """
    Update the facility row given a facility id
    :param db_name:
    :param dvs_facility_id:
    :param payload:
    :return:
    """
    update_facility_on_db(payload, dvs_facility_id, db_name)
    return True


def update_dvs_org(db_name: str, dvs_org_id: int, payload: DVS_organization):
    """
    Update the facility row given a facility id
    :param db_name:
    :param dvs_org_id:
    :param payload:
    :return:
    """
    update_org_on_db(payload, dvs_org_id, db_name)
    return True


def insert_into_dvs_facility(db_name, table_name, pk, payload):
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    add_facility_to_db(db_name=db_name, facility_id=pk_to_insert, payload=payload)

    return True


def add_ord_to_db(db_name, facility_id, payload):
    pass


def insert_into_dvs_org(db_name, table_name, pk, payload):
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    add_ord_to_db(db_name=db_name, facility_id=pk_to_insert, payload=payload)

    return True


def insert_into_dvs_team(db_name, table_name, pk, payload):
    # Generate primary key
    pk_to_insert = generate_primary_key(pk, table_name, db_name)

    if pk_to_insert == -1:
        st.error('Cannot insert this player into DB. There was an error while generating a primary key')
        st.stop()

    # Perform the insert
    add_team_to_db(db_name=db_name, team_id=pk_to_insert, payload=payload)

    return True

def update_dvs_team(db_name: str, team_id: int, payload: DVS_team):
    """
    Update the team row given a team id
    :param db_name:
    :param team_id:
    :param payload:
    :return:
    """
    update_team_on_db(payload, team_id, db_name)
    return True


with tab_admin:
    if db_connection_name == DB_CONNECTION.FORECAST:
        st.markdown('Does not apply to *DVS Analytics*')
    else:
        with tab_admin.expander('Add trainer'):
            form_add_trainer_admin = st.form(key='add_trainer_admin')
            first_name = form_add_trainer_admin.text_input(label='First name*')
            last_name = form_add_trainer_admin.text_input(label='Last name*')
            email = form_add_trainer_admin.text_input(label='Email')
            facility = form_add_trainer_admin.selectbox(label='Facility*', options=db_init_setup.facility_dict.values())
            phone = form_add_trainer_admin.text_input(label='Phone')

            form_add_trainer_admin.markdown('*Required')

            submit_add_trainer = form_add_trainer_admin.form_submit_button(label='SUBMIT')

            if submit_add_trainer:
                # Check if all required fields are entered
                req_fields = check_required_fields(first_name, last_name, facility)

                # Check for required fields
                if not req_fields:
                    st.error('All required fields must be entered')
                    st.stop()

                # Check if firstname and lastname already exist in the table. Stop the transaction if they do exist
                if check_trainer_exists(first_name, last_name, db_connection_name.value) == 0:
                    st.error('This trainer already exists in the database. Please try a different firstname or '
                             'lastname if you want to add this trainer to the database')
                    st.stop()

                payload_obj = DVS_trainer(trainer_lastname=last_name, trainer_firstname=first_name,
                                          dvs_facility_id=int(db_init_setup.reverse_facility_dict[facility]),
                                          trainer_phone=phone,
                                          trainer_email=email)
                insert_into_dvs_facility(db_name=db_connection_name.value, table_name='dvs_facility',
                                         pk='dvs_facility_id',
                                         payload=payload_obj)
                st.success('Trainer has been successfully added!')

        with tab_admin.expander('Edit existing trainer'):
            # Add a search box
            last_name_search = st.text_input(label="Search by last name: ", max_chars=50, key='edit_trainer')
            if len(last_name_search) != 0:
                grid_response = get_dvs_trainer_table(db_connection_name.value, last_name_search,
                                                      key_=f"{last_name_search}_edit_trainer")
                selected_rows = grid_response['selected_rows']

                if len(selected_rows) != 0:
                    selected_row = selected_rows[0]
                    form_edit_trainer = st.form(key="edit_trainer")
                    trainer_firstname = form_edit_trainer.text_input(label='First name*',
                                                                     value=selected_row['trainer_firstname'])
                    trainer_lastname = form_edit_trainer.text_input(label='Last name*',
                                                                    value=selected_row['trainer_lastname'])
                    trainer_email = form_edit_trainer.text_input(label='Email', value=selected_row['trainer_email'])

                    facility_options = list(db_init_setup.facility_dict.values())
                    trainer_facility = form_edit_trainer.selectbox(label='Facility*',
                                                                   options=facility_options,
                                                                   index=facility_options.index(
                                                                           db_init_setup.facility_dict
                                                                           [selected_row['dvs_facility_id']]))
                    trainer_phone = form_edit_trainer.text_input(label='Phone', value=selected_row['trainer_phone'])

                    form_edit_trainer.markdown('*Required')

                    submit_add_trainer = form_edit_trainer.form_submit_button(label='SUBMIT')

                    if submit_add_trainer:
                        # Check if all required fields are entered
                        req_fields = check_required_fields(trainer_firstname, trainer_lastname, trainer_facility)

                        # Check for required fields
                        if not req_fields:
                            st.error('All required fields must be entered')
                            st.stop()

                        payload_obj = DVS_trainer(trainer_lastname=trainer_lastname,
                                                  trainer_firstname=trainer_firstname,
                                                  dvs_facility_id=int(
                                                          db_init_setup.reverse_facility_dict[trainer_facility]),
                                                  trainer_phone=trainer_phone,
                                                  trainer_email=trainer_email)
                        update_dvs_trainer(db_name=db_connection_name.value,
                                           dvs_trainer_id=selected_row['dvs_trainer_id'],
                                           payload=payload_obj)
                        st.success('Trainer has been successfully updated!')

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

            submit_add_facility = form_add_facility_admin.form_submit_button(label='SUBMIT')

            if submit_add_facility:
                # Check if all required fields are entered
                req_fields = check_required_fields(facility_name)

                # Check for required fields
                if not req_fields:
                    st.error('All required fields must be entered')
                    st.stop()

                # Check if firstname and lastname already exist in the table. Stop the transaction if they do exist
                if check_facility_exists(facility_name, db_connection_name.value) == 0:
                    st.error('This facility already exists in the database. Please try a different facility name')
                    st.stop()

                payload_obj = DVS_facility(facility_name=facility_name, facility_phone=phone_, facility_address=address,
                                           facility_city=city, facility_state=state, facility_country=country,
                                           facility_postcode=post_code)
                insert_into_dvs_facility(db_name=db_connection_name.value, table_name='dvs_facility',
                                         pk='dvs_facility_id',
                                         payload=payload_obj)
                st.success('Facility has been successfully added!')

        with tab_admin.expander('Edit existing facility'):
            # Add a search box
            last_name_search = st.text_input(label="Search by last name: ", max_chars=50, key='edit_facility')
            if len(last_name_search) != 0:
                grid_response = get_dvs_facility_table(db_connection_name.value, last_name_search,
                                                       key_=f"{last_name_search}_edit_trainer")
                selected_rows = grid_response['selected_rows']

                if len(selected_rows) != 0:
                    selected_row = selected_rows[0]
                    form_edit_facility = st.form(key="edit_facility")

                    facility_name = form_edit_facility.text_input(label='Facility name*',
                                                                  value=selected_row['facility_name'])
                    phone_ = form_edit_facility.text_input(label='Phone', value=selected_row['facility_phone'])
                    address = form_edit_facility.text_input(label='Address', value=selected_row['facility_address'])
                    city = form_edit_facility.text_input(label='City', value=selected_row['facility_city'])
                    state = form_edit_facility.text_input(label='State', value=selected_row['facility_state'])
                    country = form_edit_facility.text_input(label='Country', value=selected_row['facility_country'])
                    post_code = form_edit_facility.text_input(label='Post code',
                                                              value=selected_row['facility_postcode'])

                    form_edit_facility.markdown('*Required')
                    submit_edit_facility = form_edit_facility.form_submit_button(label='SUBMIT')
                    if submit_edit_facility:
                        # Check if all required fields are entered
                        req_fields = check_required_fields(facility_name)

                        # Check for required fields
                        if not req_fields:
                            st.error('All required fields must be entered')
                            st.stop()

                        payload_obj = DVS_facility(facility_name=facility_name, facility_phone=phone_,
                                                   facility_address=address, facility_city=city, facility_state=state,
                                                   facility_country=country, facility_postcode=post_code)
                        update_dvs_facility(db_name=db_connection_name.value,
                                            dvs_facility_id=selected_row['dvs_facility_id'],
                                            payload=payload_obj)
                        st.success('Facility has been successfully updated!')

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
            submit_add_org = form_add_org_admin.form_submit_button(label='SUBMIT')

            if submit_add_org:
                # Check if all required fields are entered
                req_fields = check_required_fields(name)

                # Check for required fields
                if not req_fields:
                    st.error('All required fields must be entered')
                    st.stop()

                # Check if firstname and lastname already exist in the table. Stop the transaction if they do exist
                if check_org_exists(name, db_connection_name.value) == 0:
                    st.error('This organization already exists in the database. Please try a different org name')
                    st.stop()

                payload_obj = DVS_organization(org_name=name, org_address=address_, org_city=city_, org_state=state_,
                                               org_postcode=postcode_, org_country=country_, org_president=president,
                                               org_phone=phone__, org_email=email__, org_website=website)
                insert_into_dvs_org(db_name=db_connection_name.value, table_name='dvs_organization', pk='org_id',
                                    payload=payload_obj)
                st.success('Organization has been successfully added!')

        with tab_admin.expander('Edit existing organization'):
            # Add a search box
            last_name_search = st.text_input(label="Search by last name: ", max_chars=50, key='edit_organization')
            if len(last_name_search) != 0:
                grid_response = get_dvs_org_table(db_connection_name.value, last_name_search,
                                                  key_=f"{last_name_search}_edit_facility")
                selected_rows = grid_response['selected_rows']

                if len(selected_rows) != 0:
                    selected_row = selected_rows[0]
                    form_edit_org = st.form(key="edit_org")
                    org_name = form_edit_org.text_input(label='Name*', value=selected_row['org_name'])
                    org_address = form_edit_org.text_input(label='Address', value=selected_row['org_address'])
                    org_city = form_edit_org.text_input(label='City', value=selected_row['org_city'])
                    org_state = form_edit_org.text_input(label='State', value=selected_row['org_state'])
                    org_country = form_edit_org.text_input(label='Country', value=selected_row['org_country'])
                    org_postcode = form_edit_org.text_input(label='Postcode',
                                                            value=selected_row['org_postcode'])
                    org_president = form_edit_org.text_input(label='President', value=selected_row['org_president'])
                    org_phone = form_edit_org.text_input(label='Phone', value=selected_row['org_phone'])
                    org_email = form_edit_org.text_input(label='Email', value=selected_row['org_email'])
                    org_website = form_edit_org.text_input(label='Website', value=selected_row['org_website'])
                    form_edit_org.markdown('*Required')
                    submit_edit_org = form_edit_org.form_submit_button(label='SUBMIT')
                    if submit_edit_org:
                        # Check if all required fields are entered
                        req_fields = check_required_fields(org_name)

                        # Check for required fields
                        if not req_fields:
                            st.error('All required fields must be entered')
                            st.stop()

                        payload_obj = DVS_organization(org_name, org_address, org_city, org_state, org_postcode,
                                                       org_country, org_president, org_phone, org_email, org_website)
                        update_dvs_org(db_name=db_connection_name.value,
                                                dvs_org_id=selected_row['org_id'],
                                                payload=payload_obj)
                        st.success('Organization has been successfully updated!')

        with tab_admin.expander('Add team'):
            form_add_team_admin = st.form(key='add_team_admin')
            organization_name_ = form_add_team_admin.selectbox(label='Organization*',
                                                               options=get_org_dict(db_connection_name.value).values())
            team_name = form_add_team_admin.text_input(label='Team name*')
            team_address = form_add_team_admin.text_input(label='Address')
            team_city = form_add_team_admin.text_input(label='City')
            team_state = form_add_team_admin.text_input(label='State')
            team_postcode = form_add_team_admin.text_input(label='Postcode')
            team_country = form_add_team_admin.text_input(label='Country')
            team_phone = form_add_team_admin.text_input(label='Phone')
            team_email = form_add_team_admin.text_input(label='Email')
            team_website = form_add_team_admin.text_input(label='Website')
            team_facility = form_add_team_admin.selectbox(label='Facility',
                                                          options=list(db_init_setup.team_dict.values()))
            team_trainer = form_add_team_admin.selectbox(label='Trainer',
                                                         options=list(db_init_setup.team_dict.values()))

            form_add_team_admin.markdown('*Required')
            submit_add_team = form_add_team_admin.form_submit_button(label='SUBMIT')

            if submit_add_team:
                # Check if all required fields are entered
                req_fields = check_required_fields(organization_name_, team_name)

                # Check for required fields
                if not req_fields:
                    st.error('All required fields must be entered')
                    st.stop()

                # Check if team name already exist in the table. Stop the transaction if they do exist
                if check_team_exists(team_name, db_connection_name.value) == 0:
                    st.error('This team already exists in the database. Please try a different team name')
                    st.stop()
                #
                payload_obj = DVS_team(org_id=db_init_setup.reverse_organization_dict[organization_name_],
                                       team_name=team_name,
                                       team_address=team_address, team_city=team_city, team_state=team_state,
                                       team_postcode=team_postcode, team_country=team_country, team_phone=team_phone,
                                       team_email=team_email, team_website=team_website,
                                       dvs_facility_id=db_init_setup.reverse_facility_dict.get(team_facility, -1),
                                       dvs_trainer_id=db_init_setup.reverse_trainer_dict.get(team_trainer, -1))
                insert_into_dvs_team(db_name=db_connection_name.value, table_name='dvs_team', pk='team_id',
                                     payload=payload_obj)
                st.success('Team has been successfully added!')

        with tab_admin.expander('Edit existing team'):
            # Add a search box
            last_name_search = st.text_input(label="Search by last name: ", max_chars=50, key='edit_team')
            if len(last_name_search) != 0:
                grid_response = get_dvs_team_table(db_connection_name.value, last_name_search,
                                                  key_=f"{last_name_search}_edit_team")
                selected_rows = grid_response['selected_rows']

                if len(selected_rows) != 0:
                    selected_row = selected_rows[0]
                    form_edit_team = st.form(key="edit_team")

                    org_options = list(db_init_setup.organization_dict.values())
                    org = form_edit_team.selectbox(label='Organization*', options=org_options,
                                                   index=org_options.index(
                                                           db_init_setup.organization_dict
                                                           [selected_row['org_id']]))
                    team_name = form_edit_team.text_input(label='Name*', value=selected_row['team_name'])
                    team_address = form_edit_team.text_input(label='Address',
                                                             value=selected_row['team_address'])
                    team_city = form_edit_team.text_input(label='City', value=selected_row['team_city'])
                    team_state = form_edit_team.text_input(label='State', value=selected_row['team_state'])
                    team_postcode = form_edit_team.text_input(label='Postcode', value=selected_row['team_postcode'])
                    team_country = form_edit_team.text_input(label='Country', value=selected_row['team_country'])
                    team_phone = form_edit_team.text_input(label='Phone', value=selected_row['team_phone'])
                    team_email = form_edit_team.text_input(label='Email', value=selected_row['team_email'])
                    team_website = form_edit_team.text_input(label='Website', value=selected_row['team_website'])

                    facility_options = list(db_init_setup.facility_dict.values())
                    team_facility = form_edit_team.selectbox(label='Facility', options=facility_options,
                                                             index=facility_options.
                                                             index(db_init_setup.
                                                                   facility_dict[selected_row['dvs_facility_id']]))

                    trainer_options = list(db_init_setup.trainer_dict.values())
                    team_trainer = form_edit_team.selectbox(label='Trainer', options=trainer_options,
                                                            index=trainer_options.index(
                                                                    db_init_setup.trainer_dict[
                                                                        selected_row['dvs_trainer_id']
                                                                    ]
                                                            ))

                    form_edit_team.markdown('*Required')
                    submit_edit_team = form_edit_team.form_submit_button(label='SUBMIT')
                    if submit_edit_team:
                        # Check if all required fields are entered
                        req_fields = check_required_fields(team_name)

                        # Check for required fields
                        if not req_fields:
                            st.error('All required fields must be entered')
                            st.stop()

                        payload_obj = DVS_team(db_init_setup.reverse_organization_dict[org],
                                               team_name, team_address, team_city, team_state, team_postcode,
                                               team_country, team_phone, team_email, team_website,
                                               db_init_setup.reverse_facility_dict[team_facility],
                                               db_init_setup.reverse_trainer_dict[team_trainer])
                        update_dvs_team(db_name=db_connection_name.value,
                                       team_id=selected_row['team_id'],
                                       payload=payload_obj)
                        st.success('Team has been successfully updated!')

# Report tab
with tab_report:
    st.markdown("This feature is under development.")


# X-RAY tab
def show_page():
    # Drag and drop video file - also write a call back function here that would generate a tracker csv as the video gets
    # uploaded
    raw_video_file = st.file_uploader("Choose a video file (in mp4 or mov format)",
                                      type=['mp4', 'mov'])

    if raw_video_file is not None:
        st.markdown("## Uploaded video")

        bytes_data = raw_video_file.getvalue()
        st.video(bytes_data)

        # Upload file
        uploaded_video_file_path = os.path.join(uploaded_videos_dir_name, raw_video_file.name)
        upload_video(bytes_data, uploaded_video_file_path)

        # # Create Uploaded file object
        uploaded_file = UploadedFile(uploaded_video_file_path)

        st.markdown('## MSK overlay')

        filtered_video_path = os.path.join("filtered_mks",
                                           f"{raw_video_file.name.split('.')[0]}_joint_tracker_filtered.mp4")

        with st.spinner("Processing video in the background (This may take a few mins)..."):

            st.write(filtered_video_path)

            if not video_exists(filtered_video_path):
                filtered_video_path = uploaded_file.process_video()
            else:
                print(f"Filtered video for this file already exists - {filtered_video_path}")

            print(filtered_video_path)
            st.video(get_video_bytes(filtered_video_path))

        st.success("File processing is done!")


with tab_x_ray:
    show_page()

# Compare tab
with tab_compare:
    st.markdown("This feature is under development.")

# Logout tab