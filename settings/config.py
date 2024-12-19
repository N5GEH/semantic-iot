# FIWARE settings
from pathlib import Path

CB_URL = "http://137.226.248.250:1026"
IOTA_URL = "http://137.226.248.250:4041"
FIWARE_MQTT_INTERNAL_URL = "mqtt://mosquitto:1883"
QL_NOTIFY_URL = "http://quantumleap:8668/v2/notify"

FIWARE_SERVICE = 'eswc2025'
FIWARE_SERVICE_PATH = '/'
APIKEY = "eswc2025"
FIWARE_MQTT_HOST = "137.226.248.250"
FIWARE_MQTT_PORT = 1883

# openhab settings
OH_URL = "http://137.226.248.250:8080"
OH_MQTT_HOST = "134.130.49.13"
OH_MQTT_PORT = 1883

# others
LOG_LEVEL = "INFO"
project_root_path = Path(__file__).parent.parent
Controller_index = "2&3_v1"

# simulation period
# 210-240 cooling period
# 90-120 transition period
# 30-60 heating period
start_time = 230 * 24 * 60 * 60  # day * 24 hours * 60 minutes * 60 seconds
stop_time = 240 * 24 * 60 * 60  # day * 24 hours * 60 minutes * 60 seconds
#stop_time = 230 * 24 * 60 * 60 + 8 * 60 * 60

# timetable presence guests are absent during 10:00 - 18:00
# simulation timetable, absent during 8:00 - 20:00
timetable = {
            "00": True,
            "01": True,
            "02": True,
            "03": True,
            "04": True,
            "05": True,
            "06": True,
            "07": True,
            "08": True,
            "09": True,
            "10": False,
            "11": False,
            "12": False,
            "13": False,
            "14": False,
            "15": False,
            "16": False,
            "17": False,
            "18": True,
            "19": True,
            "20": True,
            "21": True,
            "22": True,
            "23": True
        }

# fmu read variables
fmu_read_vars = {
        "TRm_degC",  # "Air temperature in room in degC"
        "conCo2Rm",  # "CO2 concentration in the thermal zone in ppm"
        "TAmb_degC",  # "Ambient temperature in degC"
        "senPir",  # "Sensor PIR (passive infrared sensor)"

        "Q_flow_Rad",  # "Heat flow rate of radiator"
        "Q_flow_Sup",  # "Heat flow rate of supply air"
        "Q_flow_Fcu",  # "Heat flow rate of fan coil unit"


        "HDirNor",  # "Direct normal solar irradiation"
        "HGloHor",  # "Global horizontal solar irradiation"

        "CPUtime",

        "Q_Fcu_kWh",  # "Cooling flow of fan coil unit"
        "Q_Rad_kWh",  # "Heating flow of radiator"
        "Q_SupH_kWh",  # "Heating flow of supply air"
        "Q_SupC_kWh",  # "Cooling flow of supply air"
    }


controlParameters = {
            'control_step_time': 60,

            'deltaT_room_upper': 2,  # upper limit 2 K tolerance
            'deltaT_room_lower': -2,  # lower limit 2 K tolerance

            'deltaT_room_ukgset_lv.0': -2,
            'deltaT_room_ukgset_lv.1': 0,
            'deltaT_room_ukgset_lv.2': 1,
            'deltaT_room_ukgset_lv.3': 2,

            'ukg_fan_lv0': 0,
            'ukg_fan_lv1': 1,
            'ukg_fan_lv2': 2,
            'ukg_fan_lv3': 3,

            'airTemperatureSetpoint_cooling_without_occupancy': 27.0,
            'airTemperatureSetpoint_heating_without_occupancy': 16.0,

            "airFlow_unoccupied": 0.54 * 20,
            # Khovalyg et al. (2020) ISO 17772 and EN 16798 provide recommendations for
            # ventilation of building components during unoccupied hours. Additionally,
            # rooms should be ventilated with minimum of 0.15L/s (0.54 h/m3) per m2
            # during un-occupied hours and prior to occupation one volume of fresh air
            # within two hours should be delivered.
        }

instance_dict = {1: "base", 2: "co2", 3: "presence", 4: "timetable"}