from typing import Dict, List, Optional

from api_calls import get_db_status, DBCONNECTException, get_facility_dict, get_trainer_dict, get_team_dict, \
    get_org_dict
from db_connection import DB_CONNECTION

db_name_dict = {
    'DVS Analytics': DB_CONNECTION.FORECAST,
    'DVS Training' : DB_CONNECTION.PROD,
    'Mayo Clinic'  : DB_CONNECTION.MAYO,
    'DVS Dev'      : DB_CONNECTION.DEV
}


def reverse_dict(dict_: Dict[int, str]) -> Dict[str, int]:
    """
    Reverse key value pairs of a dictionary
    :param list_of_dicts:
    :return:
    """
    if len(dict_) == 0:
        return {}
    else:
        return {v: k for k, v in dict_.items()}


class DB_setup:

    def __init__(self, db_name: str, st_obj):
        self.db_name = db_name
        self.st_obj = st_obj

        # Make a db connection
        self.db_connection = self.connect_to_db()

        # Initialize dictionary setup
        self.facility_dict = {}
        self.trainer_dict = {}
        self.team_dict = {}
        self.organization_dict = {}
        self.analyst_dict = {}

        self.init_dicts()

        self.reverse_facility_dict = reverse_dict(self.facility_dict)
        self.reverse_trainer_dict = reverse_dict(self.trainer_dict)
        self.reverse_team_dict = reverse_dict(self.team_dict)
        self.reverse_organization_dict = reverse_dict(self.organization_dict)
        self.reverse_analyst_dict = reverse_dict(self.analyst_dict)

    def connect_to_db(self) -> Optional[DB_CONNECTION]:
        """
        Based on the db name makes a connection to the respective databases
        :param db_name:
        :return:
        """
        db_name_enum = db_name_dict[self.db_name]

        try:
            db_status = get_db_status(db_name_enum.value)
            self.st_obj.success("Connection successful")
            return db_name_enum
        except DBCONNECTException:
            print(DBCONNECTException)
            self.st_obj("Cannot connect to db")

    def init_dicts(self):
        self.team_dict = get_team_dict(self.db_connection.value)
        if self.db_connection != DB_CONNECTION.FORECAST:
            self.facility_dict = get_facility_dict(self.db_connection.value)
            self.trainer_dict = get_trainer_dict(self.db_connection.value)
            self.organization_dict = get_org_dict(self.db_connection.value)