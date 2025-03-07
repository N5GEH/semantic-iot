"""
This script utilizes the datamodels and provision entities based on the configuration for
hotel dataset in ./hotel_dataset/config. After creating all entities in FIWARE, the data
will be downloaded to ./hotel_dataset.

"""
import os
import json
import requests
from filip.clients.ngsi_v2.cb import ContextBrokerClient
from filip.models import FiwareHeader
from filip.utils.cleanup import clear_all
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from datamodels.hotel_provision import initialize_room_entities, \
    add_relationships, TemperatureSensorAmbFiware, HotelFiware
from pathlib import Path

CB_URL = "http://localhost:1026"  # TODO change to valide url to access Orion Context Broker (NGSIv2) of FIWARE
FIWARE_SERVICE = 'fiware_demo'
FIWARE_SERVICE_PATH = '/'
project_root_path = Path(__file__).parent
instance_dict = {"room_type_1": "base",
                 "room_type_2": "co2",
                 "room_type_3": "presence",
                 "room_type_4": "timetable"}

if __name__ == '__main__':
    config_files = [
        "2rooms.json",
        "10rooms.json",
        "50rooms.json",
        "100rooms.json",
        "500rooms.json",
        "1000rooms.json"
    ]
    for config_file in config_files:
        # load config
        hotels_config_path = os.path.join(project_root_path,
                                          "hotel_dataset", "config", config_file)
        with open(hotels_config_path, "r") as f:
            hotel_config = json.load(f)
            hotel_name = hotel_config["name"]
            rooms = hotel_config["rooms"]

        # initialize clients
        fiware_header = FiwareHeader(service=FIWARE_SERVICE,
                                     service_path=FIWARE_SERVICE_PATH)

        retry_strategy = Retry(
            total=3,  # Maximum number of retries
            backoff_factor=1,  # Exponential backoff (1, 2, 4, 8, etc.)
            status_forcelist=[
                422,
                429,
                500,
                502,
                503,
                504,
            ],  # Retry on these HTTP status codes
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        cbc = ContextBrokerClient(url=CB_URL,
                                  fiware_header=fiware_header,
                                  session=session)

        # clear iotagent and orion
        clear_all(cb_client=cbc,
                  fiware_header=fiware_header)

        # initialize hotel entities
        hotel_fiware = HotelFiware(id=f"Hotel:{hotel_name}", name=hotel_name)
        entities_hotel = [hotel_fiware,
                          TemperatureSensorAmbFiware(id="AmbientTemperatureSensor")]
        # Post entities to context broker
        cbc.update(entities=entities_hotel, action_type="append",
                   update_format="keyValues")
        # add relationships
        add_relationships(entities=entities_hotel, cb_client=cbc)

        # initialize entities in rooms
        # create dict of type1: base, type2: co2, type3: presence, type4: timetable
        for room_type_id, num in rooms.items():
            room_type = instance_dict[room_type_id]
            for i in range(1, num + 1):
                room_name = f"room_{room_type}_{i}"
                entities_in_room = initialize_room_entities(
                    room_name=room_name,
                    room_type=room_type,
                    hotel_id=hotel_fiware.id,
                )

                # Post entities to context broker
                cbc.update(entities=entities_in_room, action_type="append",
                           update_format="keyValues")
                # Add relationships to the entities
                add_relationships(entities=entities_in_room, cb_client=cbc)
                print(f"Successfully created entity for {room_name}\n")

        # save all entities in a file
        all_entities = cbc.get_entity_list()
        all_entities_serialize = [entity.model_dump() for entity in all_entities]
        meta_info = config_file.split(".")[0]
        dataset_file_name = f"fiware_entities_{meta_info}.json".replace(":", "_")
        hotel_dataset_path = os.path.join(project_root_path,
                                          "hotel_dataset",
                                          dataset_file_name)
        with open(hotel_dataset_path, "w") as f:
            json.dump(all_entities_serialize, f, indent=2)

        # clear orion
        clear_all(cb_client=cbc,
                  fiware_header=fiware_header)
