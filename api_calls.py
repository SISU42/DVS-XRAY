from typing import List, Dict

import pandas as pd
from st_aggrid import AgGridReturn, GridOptionsBuilder, AgGrid, GridUpdateMode

import requests
import random

from db_connection import DB_CONNECTION


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


def get_trainer_list(db_name: str) -> List:
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
    return [f"{i['dvs_trainer_id']} - {i['trainer_firstname']} - {i['trainer_lastname']}" for i in response.json()]


def get_facility_list(db_name: str) -> List:
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

    return [f"{i['facility_name']}" for i in response.json()]


def get_team_list(db_name: str) -> List:
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

        return [f"{i['team_id']} - {i['team_name']}" for i in response.json()]


def get_org_list(db_name: str) -> List:
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

    return [f"{i['org_name']}" for i in response.json()]


def get_workout_list(db_name: str) -> List:
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