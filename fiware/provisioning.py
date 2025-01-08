import os
import json
from filip.clients.ngsi_v2.cb import ContextBrokerClient
from filip.clients.ngsi_v2.iota import IoTAClient
from filip.models import FiwareHeader
from filip.utils.cleanup import clear_all
import settings.config as config
from fiware.datamodels.hotel_provision import initialize_room_entities, \
    add_relationships, TemperatureSensorAmbFiware, HotelFiware

CB_URL = config.CB_URL
IOTA_URL = config.IOTA_URL
MQTT_INTERNAL_URL = config.FIWARE_MQTT_INTERNAL_URL
QL_NOTIFY_URL = config.QL_NOTIFY_URL
APIKEY = config.APIKEY
FIWARE_SERVICE = config.FIWARE_SERVICE
FIWARE_SERVICE_PATH = config.FIWARE_SERVICE_PATH

if __name__ == '__main__':
    # load config to provision hotels
    config_files = ["hotel_2rooms.json",
                    "hotel_10rooms.json",
                    "hotel_50rooms.json",
                    "hotel_100rooms.json"]
    for config_file in config_files:
        # load config
        hotels_config_path = os.path.join(config.project_root_path, "fiware",
                                          "hotel_dataset", "config", config_file)
        with open(hotels_config_path, "r") as f:
            hotel_config = json.load(f)
            hotel_name = hotel_config["name"]
            rooms = hotel_config["rooms"]

        # initialize clients
        fiware_header = FiwareHeader(service=FIWARE_SERVICE,
                                     service_path=FIWARE_SERVICE_PATH)
        cbc = ContextBrokerClient(url=CB_URL,
                                  fiware_header=fiware_header)
        iotac = IoTAClient(url=IOTA_URL,
                           fiware_header=fiware_header)

        # clear iotagent and orion
        clear_all(cb_client=cbc,
                  iota_url=IOTA_URL,
                  fiware_header=fiware_header)

        # initialize hotel entities
        hotel_fiware = HotelFiware(id=f"Hotel:{hotel_name}", name=hotel_name)
        entities_hotel = [hotel_fiware,
                          TemperatureSensorAmbFiware(id="AmbientTemperatureSensor")]
        # Post entities to context broker
        for entity in entities_hotel:
            cbc.post_entity(entity=entity, key_values=True)
            print(f"Successfully posted {entity.id}")
        # create connections
        add_relationships(entities=entities_hotel, cb_client=cbc)

        # initialize entities in rooms
        # Choose initialization function based on instance ID and version
        # create dict of 1: base, 2: co2, 3: presence, 4: timetable
        instance_dict = config.instance_dict
        for room_name, assignment in rooms.items():
            instance_id = assignment["instance_id"]
            version = assignment["version"]
            room_type = instance_dict[instance_id]
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
        dataset_file_name = f"{hotel_name}_{meta_info}.json".replace(":", "_")
        hotel_dataset_path = os.path.join(config.project_root_path, "fiware",
                                          "hotel_dataset",
                                          dataset_file_name)
        with open(hotel_dataset_path, "w") as f:
            json.dump(all_entities_serialize, f, indent=2)
