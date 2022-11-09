from typing import List, Dict, Union, Any

import pandas as pd
from st_aggrid import AgGridReturn, GridOptionsBuilder, AgGrid, GridUpdateMode

import requests
import random
import json

from db_connection import DB_CONNECTION

from payloads import Insert_player_payload_non_forecast

MLB_TEAMS = ['SEA', 'WAS', 'BAL', 'CLE', 'ANA', 'NYN', 'SDN', 'TEX', 'ARI', 'CHA', 'HOU', 'MIL', 'PHI', 'SLN', 'BOS',
             'COL', 'LAN', 'NYA', 'SFN', 'TOR', 'ATL', 'CIN', 'KCA', 'MIN', 'PIT', 'TBA', 'CHN', 'DET', 'MIA', 'OAK']


def get_random_string() -> str:
    corpus = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    random_sample = random.sample(corpus, 16)
    return "".join(random_sample)


def get_db_status(db_name: str) -> str:
    """
    GET THE STATUS OF CONNECTION TOO DB
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/get_db_status?db_name={db_name}"

    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)

    return response.text


def get_trainer_dict(db_name: str) -> Dict[int, str]:
    """
    Get all the trainers list based on db_name
    :param db_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/trainer_list/{db_name}"

    headers = {
        'access_token': 'dv$2022'
    }
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return {int(i['dvs_trainer_id']): f"{i['trainer_firstname']} {i['trainer_lastname']}" for i in response.json()}


def get_facility_dict(db_name: str) -> Dict[int, str]:
    """
    Get all the facility names list based on the db_name
    :param db_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/facility_list/{db_name}"

    payload = {}
    headers = {
        'access_token': 'dv$2022'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return {int(i['dvs_facility_id']): f"{i['facility_name']}" for i in response.json()}


def get_team_dict(db_name: str) -> Union[list[Union[str, Any]], Dict[int, str]]:
    """
    Get all the team names and team ids
    :param db_name:
    :return:
    """
    if db_name == DB_CONNECTION.FORECAST.value:
        return MLB_TEAMS
    else:
        url = f"https://deliveryvaluesystemapidev.azurewebsites.net/team_list/{db_name}"

        payload = {}
        headers = {
            'access_token': 'dv$2022'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        return {int(i['team_id']):  f"{i['team_name']}" for i in response.json()}


def get_org_dict(db_name: str) -> Dict[int, str]:
    """
    Get all the team names and team ids
    :param db_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/org_list/{db_name}"

    payload = {}
    headers = {
        'access_token': 'dv$2022'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return {int(i['org_id']): f"{i['org_name']}" for i in response.json()}


def get_workout_list(db_name: str) -> List[str]:
    """
    Get workout names list based on db name
    :param db_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/workout_names_list/{db_name}"

    payload = {}
    headers = {
        'access_token': 'dv$2022'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return [i['workout_name'] for i in response.json()]


def convert_to_aggrid(df: pd.DataFrame, key_: str) -> AgGridReturn:
    """
    Create a
    :param df:
    :return:
    """

    gd = GridOptionsBuilder.from_dataframe(df)
    gd.configure_selection(selection_mode='single', use_checkbox=True)
    # gd.configure_pagination(paginationAutoPageSize=True)
    gridoptions = gd.build()

    return AgGrid(df, gridOptions=gridoptions,
                  update_mode=GridUpdateMode.GRID_CHANGED,
                  key=key_)


def get_dvs_client_table(db_name: str, last_name_search: str, key_: str) -> AgGridReturn:
    """
    Get dvs client table as an Aggrid dataframe
    :param db_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/dvs_client_table/{db_name}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    df = pd.DataFrame.from_records(response)

    # Filter based on last_name_search
    filter_0 = df['client_lastname'].apply(lambda x: x.lower()) == last_name_search.lower()

    df = df.where(filter_0) \
        .sort_values(['client_lastname']) \
        .dropna(axis=0, how='all')

    return convert_to_aggrid(df, key_)


def get_dvs_player_table(last_name_search: str, key_: str) -> AgGridReturn:
    """
    Same functionality as dvs_client but for forecaster db on dvs_player
    :param last_name_search:
    :param key_:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/dvs_player_table/"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    df = pd.DataFrame.from_records(response)

    # Filter based on last_name_search
    filter_0 = df['last_name'].apply(lambda x: x.lower()) == last_name_search.lower()

    df = df.where(filter_0) \
        .sort_values(['last_name']) \
        .dropna(axis=0, how='all')

    return convert_to_aggrid(df, key_)


def get_workout_id_name_dict(db_name: str) -> Dict[int, str]:
    """
    Return a workout id name dict based on db_name
    :param db_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/workout_id_dict/{db_name}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()


def get_analyst_names(db_name: str) -> List[str]:
    """
    Based on db_name return unique analyst names and ids
    :param db_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/analyst_names/{db_name}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    return [f"{i['dvs_analyst_id']}: {i['analyst_name']}" for i in response]


def get_dvs_score(db_name: str, client_id: int, key_: str) -> AgGridReturn:
    """
    Get the agg grid table of scores from dvs_score
    :param key_:
    :param db_name:
    :param client_id:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/dvs_scores/{db_name}/{client_id}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    df = pd.DataFrame.from_records(response)

    df = df.sort_values(['score_date'], ascending=False) \
        .dropna(axis=0, how='all')

    return convert_to_aggrid(df, key_)


def check_duplicates(db_name: str, birthday: str, first_name: str, last_name: str) -> bool:
    """
    Checks if duplcates exist and returns a boolean according to the condition
    :param db_name:
    :param birthday:
    :param first_name:
    :param last_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/check_dup_clients/{db_name}/" \
          f"{birthday}/{first_name}/{last_name}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    if response == -1:
        return True
    else:
        return False


def generate_primary_key(pk: str, db_name: str) -> int:
    """
    Generate a primary key for the client/player tables
    :param pk:
    :param db_name:
    :return:
    """
    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/max_pk/{pk}/{db_name}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    if response == -1:
        return -1
    else:
        return int(response) + 1


def add_player_to_db(db_name: str, pk: int, payload: Insert_player_payload_non_forecast) -> None:
    """
    Add a player to the db
    :param payload:
    :param db_name:
    :param pk:
    :return:
    """

    url = f"https://deliveryvaluesystemapidev.azurewebsites.net/insert_into_dvs_client/{pk}/{db_name}"

    headers = {
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload.__dict__))

    return None