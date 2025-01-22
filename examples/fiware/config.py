# FIWARE settings
from pathlib import Path
CB_URL = "http://134.130.166.184:1026"
FIWARE_SERVICE = 'eswc2025'
FIWARE_SERVICE_PATH = '/'

# others
LOG_LEVEL = "INFO"
project_root_path = Path(__file__).parent.parent


instance_dict = {"room_type_1": "base",
                 "room_type_2": "co2",
                 "room_type_3": "presence",
                 "room_type_4": "timetable"}
