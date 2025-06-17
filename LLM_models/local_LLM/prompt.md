<role>You are an ontology expert</role>

<data>
Extraction of available Ontology Properties
### Relevant Classes (Hierarchical)
- Class
  - Collection
    - System
      - Heating_Ventilation_Air_Conditioning_System
        - Air_System: The equipment, distribution systems and terminals that introduce or exhaust, either collectively or individually, the air into and from the building
          - Ventilation_Air_System: The equipment, devices, and conduits that handle the introduction and distribution of ventilation air in the building
  - Equipment
    - HVAC_Equipment
      - Air_Handler_Unit: Assembly consisting of sections containing a fan or fans and other necessary equipment to perform one or more of the following functions: circulating, filtration, heating, cooling, heat recovery, humidifying, dehumidifying, and mixing of air. Is usually connected to an air-distribution system.
      - Air_Plenum: A component of the HVAC the receives air from the air handling 
      - Chiller
      - Damper
      - Fan
      - Filter
        - Mixed_Air_Filter: A filter that is applied to the mixture of recirculated and outside air
      - Humidifier: A device that adds moisture to air or other gases
      - Terminal_Unit
        - Air_Diffuser: A device that is a component of the air distribution system 
        - Chilled_Beam
  - Location
    - Space
      - Architecture
        - Room
          - ExhibitionRoom
          - Laboratory
            - Hot_Box: hot air chamber forming part of an air handler.
          - PersonalHygiene
            - Sauna
  - Point
    - Alarm
      - Air_Alarm
        - Air_Flow_Alarm: An alarm related to air flow.
        - Discharge_Air_Smoke_Detection_Alarm
        - Supply_Air_Smoke_Detection_Alarm
      - Smoke_Alarm
        - Smoke_Detection_Alarm
- Entity
- Resource
  - Asset
  - Event
    - PointEvent
      - ObservationEvent
        - AbsoluteHumidityObservation
        - AccelerationObservation
        - PowerObservation

</data>

<input>
Domain Entity: FreshAirVentilation
</input>

<instructions>
Identify the most appropriate ontology class for the domain entity
The goal is to inherit the attributes and relations from the selected Ontology Class or Property.

MAPPING CRITERIA: (in order of priority)
1. Exact semantic match
2. Functional equivalence (same purpose/behavior)
3. Hierarchical relationship (parent/child concepts)
4. Attribute similarity (same properties/characteristics)

SPECIAL CONSIDERATIONS:
- Distinguish locations, air systems, devices, actuation points, sensors
- Avoid category errors: don't confuse the thing itself with infrastructure that supports the thing
- Respect system hierarchies (building → floor → room → equipment)
</instructions>

Return exclusively the selected class, do not provide an explaination or any other output