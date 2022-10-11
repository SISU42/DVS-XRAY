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