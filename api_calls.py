from typing import List

import requests


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

    return [f"{i['dvs_facility_id']} - {i['facility_name']}" for i in response.json()]


def get_team_list(db_name: str) -> List:
    """
    Get all the team names and team ids
    :param db_name:
    :return:
    """
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

    return [f"{i['org_id']} - {i['org_name']}" for i in response.json()]


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
