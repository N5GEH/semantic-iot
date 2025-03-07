# FIWARE settings
from pathlib import Path

# TODO change to valide url to access Orion Context Broker (NGSIv2) of FIWARE
CB_URL = "http://localhost:1026"

FIWARE_SERVICE = 'fiware_demo'
FIWARE_SERVICE_PATH = '/'

# others
LOG_LEVEL = "INFO"
project_root_path = Path(__file__).parent


instance_dict = {"room_type_1": "base",
                 "room_type_2": "co2",
                 "room_type_3": "presence",
                 "room_type_4": "timetable"}
