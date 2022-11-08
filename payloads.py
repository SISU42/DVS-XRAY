from dataclasses import dataclass


@dataclass
class Insert_player_payload_non_forecast:
    client_lastname: str
    client_firstname: str
    throws: str
    birthday: str
    birthyear: int
    workout_id: int
    position: str
    current_organization: str
    dvs_trainer_id: int
    dvs_facility_id: int
    current_team: str
    client_email: str
    client_phone: str
    org_id: int
    team_id: int
    active_flag: int = 1
    jersey_number: int = 0
    high_school: str = ""
    college: str = ""
