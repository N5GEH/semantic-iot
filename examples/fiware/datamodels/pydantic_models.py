from typing import Optional
from filip.models.ngsi_v2.context import ContextEntityKeyValues
from pydantic import BaseModel


class Hotel(BaseModel):
    """Represents a hotel with basic information."""
    name: str = None
    address: Optional[str] = None


class HotelFiware(Hotel, ContextEntityKeyValues):
    """Extends the Hotel class to include Fiware-specific properties."""
    type: str = "Hotel"


class HotelRoom(BaseModel):
    """Represents a hotel room with basic information."""
    name: str = None
    hasLocation: str = None  # Which floor


class HotelRoomFiware(HotelRoom, ContextEntityKeyValues):
    """Extends the HotelRoom class to include Fiware-specific properties."""
    type: str = "HotelRoom"


# sensors
class Sensor(BaseModel):
    """Base class for sensors."""
    hasLocation: str = None


class SensorFiware(ContextEntityKeyValues):
    """Base class for Fiware-compatible sensors."""

    def get_sensor_attribute(self):
        """Retrieves attributes specific to the sensor."""
        sensor_keys = Sensor.model_fields.keys()
        context_entity_keys = ContextEntityKeyValues.model_fields.keys()
        return self.model_dump(exclude=sensor_keys | context_entity_keys)


class PresenceSensor(Sensor):
    """Represents a presence sensor with PIR data."""
    pir: Optional[float] = 0


class PresenceSensorFiware(PresenceSensor, SensorFiware):
    """Extends the PresenceSensor class to include Fiware-specific properties."""
    type: str = "PresenceSensor"


class TemperatureSensor(Sensor):
    """Represents a temperature sensor."""
    temperature: Optional[float] = 0


class TemperatureSensorFiware(TemperatureSensor, SensorFiware):
    """Extends the TemperatureSensor class to include Fiware-specific properties."""
    type: str = "TemperatureSensor"


class CO2Sensor(Sensor):
    """Represents a CO2 sensor."""
    co2: Optional[float] = 0


class CO2SensorFiware(CO2Sensor, SensorFiware):
    """Extends the CO2Sensor class to include Fiware-specific properties."""
    type: str = "CO2Sensor"


class TemperatureSensorAmb(Sensor):
    """Represents an ambient temperature sensor."""
    temperatureAmb: Optional[float] = 0
    hasLocation: Optional[str] = None  # Set hasLocation as optional


class TemperatureSensorAmbFiware(TemperatureSensorAmb, SensorFiware):
    """Extends the TemperatureSensorAmb class to include Fiware-specific properties."""
    type: str = "AmbientTemperatureSensor"


# actuators
class Actuator(BaseModel):
    """Base class for actuators."""
    hasLocation: Optional[str] = None


class ActuatorFiware(ContextEntityKeyValues):
    """Base class for Fiware-compatible actuators."""

    def get_actuator_attribute(self):
        """Retrieves attributes specific to the actuator."""
        actuator_keys = Actuator.model_fields.keys()
        context_entity_keys = ContextEntityKeyValues.model_fields.keys()
        return self.model_dump(exclude=actuator_keys | context_entity_keys)


class FreshAirVentilation(Actuator):
    """Represents a fresh air ventilation system."""
    airFlowSetpoint: Optional[float] = 0


class FreshAirVentilationFiware(FreshAirVentilation, ActuatorFiware):
    """Extends the FreshAirVentilation class to include Fiware-specific properties."""
    type: str = "FreshAirVentilation"


class CoolingCoil(Actuator):
    """Represents a cooling coil."""
    brand: Optional[str] = None
    fanSpeed: Optional[float] = 0


class CoolingCoilFiware(CoolingCoil, ActuatorFiware):
    """Extends the CoolingCoil class to include Fiware-specific properties."""
    type: str = "CoolingCoil"


class RadiatorThermostat(Actuator):
    """Represents a radiator thermostat."""
    temperatureSetpoint: Optional[float] = 0


class RadiatorThermostatFiware(RadiatorThermostat, ActuatorFiware):
    """Extends the RadiatorThermostat class to include Fiware-specific properties."""
    type: str = "RadiatorThermostat"
