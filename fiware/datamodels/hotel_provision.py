from typing import List, Union, Literal
from filip.models.ngsi_v2.iot import Device, DeviceAttribute, ServiceGroup
from filip.models.ngsi_v2.context import ContextEntityKeyValues, \
    ContextAttribute, ContextEntity
from filip.models.ngsi_v2.subscriptions import Subscription
from requests import HTTPError
from fiware.datamodels.pydantic_models import HotelRoomFiware, TemperatureSensorFiware, \
    CO2SensorFiware, PresenceSensorFiware, FreshAirVentilationFiware, \
    RadiatorThermostatFiware, CoolingCoilFiware, SensorFiware, ActuatorFiware, \
    HotelFiware, TemperatureSensorAmbFiware
import os
import json
from filip.clients.ngsi_v2.cb import ContextBrokerClient
from filip.clients.ngsi_v2.iota import IoTAClient
from filip.models import FiwareHeader
from filip.utils.cleanup import clear_all
import settings.config as config


def initialize_room_entities(room_name: str,
                             room_type: Literal[
                                 "base",
                                 "co2",
                                 "presence",
                                 "timetable"],
                             hotel_id: str = "Hotel:fiware",
                             ) -> List[ContextEntityKeyValues]:
    """
    Create fiware entities based on the data model V1.
    room_name: str
        Name of the room
    room_type:
        Different room types determine the composition of the sensors.
        "base" contains temperature, co2, and presence sensors
        "co2" contains temperature and co2 sensors
        "presence" contains temperature and presence sensors
        "timetable" contains temperature sensor

    """
    entities = []
    # Room
    room = HotelRoomFiware(
        id=f"HotelRoom:{room_name}",
        name=room_name,
        hasLocation=hotel_id)
    entities.append(room)

    # Sensors
    air_t = TemperatureSensorFiware(
        id=f"TemperatureSensor:{room_name}",
        hasLocation=room.id
    )
    entities.append(air_t)
    if room_type in ("base", "co2"):
        air_co2 = CO2SensorFiware(
            id=f"CO2Sensor:{room_name}",
            hasLocation=room.id)
        entities.append(air_co2)
    if room_type in ("base", "presence"):
        presence = PresenceSensorFiware(
            id=f"PresenceSensor:{room_name}",
            hasLocation=room.id)
        entities.append(presence)

    # Actuators
    fresh_air_ventilation = FreshAirVentilationFiware(
        id=f"FreshAirVentilation:{room_name}",
        hasLocation=room.id)
    thermostat = RadiatorThermostatFiware(
        id=f"RadiatorThermostat:{room_name}",
        hasLocation=room.id)
    room_air_cooling_system = CoolingCoilFiware(
        id=f"CoolingCoil:{room_name}",
        hasLocation=room.id)
    entities.extend([fresh_air_ventilation, thermostat, room_air_cooling_system])

    return entities


def initialize_sensor_connection(sensor: SensorFiware) -> Device:
    attrs = sensor.get_sensor_attribute()
    attrs_device = [DeviceAttribute(name=key, type="Number")
                    for key in attrs.keys()]
    device = Device(
        device_id=sensor.id,
        entity_name=sensor.id,
        entity_type=sensor.type,
        transport="MQTT",
        attributes=attrs_device,
        explicitAttrs=True,
    )
    return device


def initialize_actuator_connection(actuator: ActuatorFiware) -> List[Subscription]:
    commands = actuator.get_actuator_attribute()
    location = actuator.model_dump().get("hasLocation")
    if not location and actuator.model_dump().get("isPartOf"):
        location = actuator.model_dump().get("isPartOf")
    if not location:
        location = "None"  # Default fallback if neither exists
    subscriptions = []
    for key in commands.keys():
        sub_dict = {
            "description": "MQTT Command notification",
            "subject": {
                "entities": [
                    {
                        "id": actuator.id
                    }
                ],
                "condition": {
                    "attrs": [key]
                }
            },
            "notification": {
                "attrs": [key],
                "mqttCustom": {
                    "url": "mqtt://localhost:1883",
                    "topic": f"{location}/{actuator.id}/{key}",
                    "payload": "${" + key + "}"
                }
            },
            "throttling": 0
        }
        subscriptions.append(Subscription(**sub_dict))
        print(
            f"The topic for {actuator.id} is {sub_dict['notification']['mqttCustom']['topic']}")
    return subscriptions


def initialize_timeseries_notification(entity: Union[SensorFiware, ActuatorFiware],
                                       ql_url: str):
    """
    Initialize a subscription for a Fiware entity to receive timeseries data
    :param entity:
    :param ql_url: internal URL of the QuantumLeap service
    :return:
    """
    if isinstance(entity, SensorFiware):
        attributes = entity.get_sensor_attribute()
    elif isinstance(entity, ActuatorFiware):
        attributes = entity.get_actuator_attribute()
    else:
        # if entity is not a sensor or actuator not create any subscription
        return []
    subscriptions = []
    for key in attributes.keys():
        sub_dict = {
            "description": "Time Series notification",
            "subject": {
                "entities": [
                    {
                        "id": entity.id
                    }
                ],
                "condition": {
                    "attrs": [key]
                }
            },
            "notification": {
                "attrs": [key],
                "http": {
                    "url": ql_url
                }
            },
            "throttling": 0
        }
        subscriptions.append(Subscription(**sub_dict))
    return subscriptions


def add_relationships(entities: List[ContextEntityKeyValues],
                      cb_client: ContextBrokerClient):
    # go through all entities and their attributes
    # try to check the attribute value as an entity id
    # if the attribute value is an entity id, assign this attribute as relationship
    for _entity in entities:
        # get entity from orion
        entity = cb_client.get_entity(entity_id=_entity.id)
        for key, value in entity.model_dump(exclude={"id", "type"}).items():
            if isinstance(value, dict):
                ref_id = value.get("value")
                try:
                    # get entity by id
                    ref_entity = cb_client.get_entity(entity_id=ref_id)
                    if ref_entity.id == ref_id:
                        # this attribute is a relationship
                        # change type to relationship
                        entity.update_attribute(
                            {key: ContextAttribute(**{
                                "type": "Relationship",
                                "value": ref_id
                            })
                             }
                        )
                        new_entity = ContextEntity(id=entity.id, type=entity.type,
                                                   **entity.model_dump(exclude={"id",
                                                                                "type"}))
                        cb_client.post_entity(entity=new_entity, update=True)
                        print(
                            f"Successfully added {ref_id} as location value to {entity.id}")
                except HTTPError:
                    pass


def create_connections(entities: List[ContextEntityKeyValues],
                       cb_client: ContextBrokerClient,
                       iota_client: IoTAClient,
                       internal_mqtt_url: str,
                       apikey: str,
                       ql_url: str
                       ):
    any_device = False
    for entity in entities:
        if isinstance(entity, SensorFiware):
            device = initialize_sensor_connection(entity)
            # post device
            iota_client.post_device(device=device)
            any_device = True
            print(f"Device {device.device_id} created for {entity.id}")
        elif isinstance(entity, ActuatorFiware):
            # if one actuator has multiple commands,
            # multiple subscriptions will be created
            subscriptions = initialize_actuator_connection(entity)
            for subscription in subscriptions:
                # replace mqtt URL
                subscription.notification.mqttCustom.url = internal_mqtt_url
                # post subscriptions
                cb_client.post_subscription(subscription=subscription)
            print(f"Notification created for {entity.id}")
        # create timeseries notification
        subscriptions = initialize_timeseries_notification(entity=entity, ql_url=ql_url)
        for subscription in subscriptions:
            cb_client.post_subscription(subscription=subscription)
    if any_device:
        try:
            existing_groups = iota_client.get_group(resource="/iot/json", apikey=apikey)
            if existing_groups.apikey == apikey:
                print(
                    f"ServiceGroup with API key '{apikey}' already exists, skipping creation.")
            else:
                # create service group for devices
                iota_client.post_group(ServiceGroup(**{
                    "resource": "/iot/json",
                    "apikey": apikey,
                    "autoprovision": False,
                    "explicitAttrs": True,
                    "ngsiVersion": "v2"
                }))
        except Exception as e:
            # create service group for devices
            iota_client.post_group(ServiceGroup(**{
                "resource": "/iot/json",
                "apikey": apikey,
                "autoprovision": False,
                "explicitAttrs": True,
                "ngsiVersion": "v2"
            }))


if __name__ == '__main__':

    # initialize clients
    fiware_header = FiwareHeader(service=config.FIWARE_SERVICE,
                                 service_path=config.FIWARE_SERVICE_PATH)
    cbc = ContextBrokerClient(url=config.CB_URL,
                              fiware_header=fiware_header)

    # clear iotagent and orion
    clear_all(cb_client=cbc,
              fiware_header=fiware_header)

    # initialize hotel entities
    hotel_name = "example_hotel"
    hotel_fiware = HotelFiware(id=f"Hotel:{hotel_name}", name=hotel_name)
    entities_hotel = [hotel_fiware,
                      TemperatureSensorAmbFiware(id="AmbientTemperatureSensor")]
    # Post entities to context broker
    for entity in entities_hotel:
        cbc.post_entity(entity=entity, key_values=True)
        print(f"Successfully posted {entity.id}")
    # create connections
    add_relationships(entities=entities_hotel, cb_client=cbc)

    room_name = "example_room"
    entities_in_room = initialize_room_entities(
        room_name=room_name,
        room_type="base")

    # Post entities to context broker
    for entity in entities_in_room:
        cbc.post_entity(entity=entity, key_values=True)
        print(f"Successfully posted {entity.id}")

    # Add relationships to the entities
    add_relationships(entities=entities_in_room, cb_client=cbc)

    print(f"Successfully created entity for {room_name}\n")

    # save all entities in a file
    all_entities = cbc.get_entity_list()
    all_entities_serialize = [entity.model_dump() for entity in all_entities]
    hotel_dataset_path = os.path.join(config.project_root_path, "fiware",
                                      "datamodels", "example_hotel.json")
    with open(hotel_dataset_path, "w") as f:
        json.dump(all_entities_serialize, f, indent=2)
