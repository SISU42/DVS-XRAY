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


@dataclass
class Insert_dvs_eval_payload:
    eval_date: str
    dvs_trainer_id: int
    height: float
    weight: float
    dvs_client_id: int
    fb_velocity_avg: float
    fb_velocity_max: float
    fb_spin_avg: float
    fb_spin_max: float
    cb_velocity_avg: float
    cb_velocity_max: float
    cb_spin_avg: float
    cb_spin_max: float
    cb_break: float = -1.0
    bullpen_pitch_count: int = -1
    bullpen_strikes_total: int = -1
    bullpen_strikes_right: int = -1
    bullpen_strikes_left: int = -1
    strength_rating: float = -1.0
    shoulder_1: float = -1.0
    shoulder_2: float = -1.0
    shoulder_3: float = -1.0
    shoulder_4: float = -1.0
    FMS_DS: float = -1.0
    FMS_HS: float = -1.0
    FMS_ILL: float = -1.0
    FMS_SM: float = -1.0
    FMS_ASLR: float = -1.0
    FMS_TSPU: float = -1.0
    FMS_RS: float = -1.0
    FMS_TOTAL: float = -1.0
    release_height: float = -1.0

@dataclass
class Insert_dvs_eval_rom:
    eval_date: str
    dvs_client_id: int
    dvs_trainer_id: int
    dir: int = -1
    der: int = -1
    ndir: int = -1
    nder: int = -1
    dtam: int = -1
    ndtam: int = -1
    dflex: int = -1
    ndflex: int = -1
    d_cuff_strength: float = -1.0
    kibler: int = -1
    nd_cuff_strength: float = -1.0
    d_ir_cuff_strength: float = -1.0
    d_er_cuff_strength: float = -1.0
    nd_ir_cuff_strength: float = -1.0
    nd_er_cuff_strength: float = -1.0
    d_kibler: int = -1
    nd_kibler: int = -1
