
Choose a dataset folder to run the scenarios on:
1: fiware_v1_hotel
2: fiware_v2_hotel
3: openhab_v1_hotel
4: openhab_v2_hotel
Select a subfolder by number: 1
Selected dataset folder: LLM_models/datasets\fiware_v1_hotel

Multiple JSON Entities files found:
1: fiware_entities_1room copy.json
2: fiware_entities_1room.json
3: fiware_entities_50rooms copy.json
4: fiware_entities_50rooms.json
Select a JSON Entities file by number: 1
Selected JSON Entities: fiware_entities_1room copy.json
Found JSON Example: fiware_example.json

Choose an ontology file to run the scenarios on:
Found ontology: Brick.ttl
Selected ontology file: LLM_models/ontologies\Brick.ttl

Choose an API endpoint to run the scenarios on:
1: FIWAR_ngsiV2_API_spec.json
2: openhab_API_spec.json
Select an API specification file by number: 1
Selected API endpoint: LLM_models/API_specs\FIWAR_ngsiV2_API_spec.json

Select scenarios to run (comma-separated numbers):
1: Scenario I: Generate RDF from JSON Entities
2: Scenario II: Generate RML from JSON Entities
3: Scenario III: Use Semantic-IoT Framework for RML Generation
Select scenarios by number (comma-separated): 1
Selected scenarios: ['I']

Preparing context for scenarios...

✨ Claude generating... (get_context_(0))

🛠️  Tool use... (get_endpoint_from_api_spec)
🛠️ ↪️  Tool result:
{
  "endpoint": "https://fiware.eonerc.rwth-aachen.de/v2/entities/{entityId}/attrs/{attrName}/value"
}

✨ Claude generating... (get_context_(1))

🛠️  Tool use... (term_mapper)
🔍 Mapping terms: {
  "Hotel": "class",
  "AmbientTemperatureSensor": "class",
  "HotelRoom": "class",
  "TemperatureSensor": "class",
  "CO2Sensor": "class",
  "PresenceSensor": "class",
  "FreshAirVentilation": "class",
  "RadiatorThermostat": "class",
  "CoolingCoil": "class"
} using ontology: LLM_models/ontologies\Brick.ttl

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'Hotel')
🔍✅ Semantic search completed in 30.33 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Shelter
🔍 Prefix found: rec:Shelter (URI: https://w3id.org/rec#Shelter)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'AmbientTemperatureSensor')
🔍✅ Semantic search completed in 22.99 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Temperature_Sensor
🔍 Prefix found: brick:Temperature_Sensor (URI: https://brickschema.org/schema/Brick#Temperature_Sensor)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'HotelRoom')
🔍✅ Semantic search completed in 25.30 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Room
🔍 Prefix found: rec:Room (URI: https://w3id.org/rec#Room)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'TemperatureSensor')
🔍✅ Semantic search completed in 21.55 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Temperature_Sensor
🔍 Prefix found: brick:Temperature_Sensor (URI: https://brickschema.org/schema/Brick#Temperature_Sensor)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'CO2Sensor')
🔍✅ Semantic search completed in 22.86 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: CO2_Sensor
🔍 Prefix found: brick:CO2_Sensor (URI: https://brickschema.org/schema/Brick#CO2_Sensor)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'PresenceSensor')
🔍✅ Semantic search completed in 24.23 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Occupancy_Sensor
🔍 Prefix found: brick:Occupancy_Sensor (URI: https://brickschema.org/schema/Brick#Occupancy_Sensor)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'FreshAirVentilation')
🔍✅ Semantic search completed in 22.86 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Ventilation_Air_System
🔍 Prefix found: brick:Ventilation_Air_System (URI: https://brickschema.org/schema/Brick#Ventilation_Air_System)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'RadiatorThermostat')
🔍✅ Semantic search completed in 22.28 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Radiator
🔍 Prefix found: brick:Radiator (URI: https://brickschema.org/schema/Brick#Radiator)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'CoolingCoil')
🔍✅ Semantic search completed in 22.20 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Cooling_Coil
🔍 Prefix found: brick:Cooling_Coil (URI: https://brickschema.org/schema/Brick#Cooling_Coil)
🛠️ ↪️  Tool result:
{
  "mapped_terms": {
    "Hotel": "rec:Shelter",
    "AmbientTemperatureSensor": "brick:Temperature_Sensor",
    "HotelRoom": "rec:Room",
    "TemperatureSensor": "brick:Temperature_Sensor",
    "CO2Sensor": "brick:CO2_Sensor",
    "PresenceSensor": "brick:Occupancy_Sensor",
    "FreshAirVentilation": "brick:Ventilation_Air_System",
    "RadiatorThermostat": "brick:Radiator",
    "CoolingCoil": "brick:Cooling_Coil"
  }
}

✨ Claude generating... (get_context_(2))

🛠️  Tool use... (term_mapper)
🔍 Mapping terms: {
  "hasLocation": "property"
} using ontology: LLM_models/ontologies\Brick.ttl

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology property for 'hasLocation')
🔍✅ Semantic search completed in 24.10 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: hasLocation
🔍 Prefix found: brick:hasLocation (URI: https://brickschema.org/schema/Brick#hasLocation)
🛠️ ↪️  Tool result:
{
  "mapped_terms": {
    "hasLocation": "brick:hasLocation"
  }
}

✨ Claude generating... (get_context_(3))

🛠️  Tool use... (get_non_numeric_classes)
🔍 Getting non-numeric classes for: ['brick:Temperature_Sensor', 'brick:CO2_Sensor', 'brick:Occupancy_Sensor', 'brick:Ventilation_Air_System', 'brick:Radiator', 'brick:Cooling_Coil'] using ontology: LLM_models/ontologies\Brick.ttl

==================== PROCESSING CLASS: brick:Temperature_Sensor ====================
Found 5 superclasses for brick:Temperature_Sensor
Found 7 properties for brick:Temperature_Sensor
  - rdfs:label
  - rdfs:seeAlso
  - rdfs:subClassOf
  - owl:disjointWith
  - skos:definition
  - brick:hasAssociatedTag
  - brick:hasQuantity

==================== PROCESSING CLASS: brick:CO2_Sensor ====================
Found 6 superclasses for brick:CO2_Sensor
Found 8 properties for brick:CO2_Sensor
  - rdfs:label
  - rdfs:seeAlso
  - rdfs:subClassOf
  - owl:disjointWith
  - skos:definition
  - brick:hasAssociatedTag
  - brick:hasQuantity
  - brick:hasSubstance

==================== PROCESSING CLASS: brick:Occupancy_Sensor ====================
Found 5 superclasses for brick:Occupancy_Sensor
Found 7 properties for brick:Occupancy_Sensor
  - rdfs:label
  - rdfs:seeAlso
  - rdfs:subClassOf
  - owl:disjointWith
  - skos:definition
  - brick:hasAssociatedTag
  - brick:hasQuantity

==================== PROCESSING CLASS: brick:Ventilation_Air_System ====================
Found 9 superclasses for brick:Ventilation_Air_System
Found 6 properties for brick:Ventilation_Air_System
  - rdfs:comment
  - rdfs:label
  - rdfs:subClassOf
  - owl:equivalentClass
  - skos:definition
  - brick:hasAssociatedTag

==================== PROCESSING CLASS: brick:Radiator ====================
Found 8 superclasses for brick:Radiator
Found 5 properties for brick:Radiator
  - rdfs:comment
  - rdfs:label
  - rdfs:subClassOf
  - skos:definition
  - brick:hasAssociatedTag

==================== PROCESSING CLASS: brick:Cooling_Coil ====================
Found 9 superclasses for brick:Cooling_Coil
Found 6 properties for brick:Cooling_Coil
  - rdfs:comment
  - rdfs:label
  - rdfs:subClassOf
  - owl:equivalentClass
  - skos:definition
  - brick:hasAssociatedTag

Total unique properties across all classes: 10

✨ Claude generating... (classify_props_LLM_(0))
✨↪️  Model reply: I'll classify these properties into numerical and non-numerical categories based on whether they connect an entity with a measurable quantity.

```json
{
  "numerical": [
    "brick:hasQuantity"
  ],
  "non_numerical": [
    "owl:disjointWith",
    "rdfs:subClassOf",
    "brick:hasSubstance",
    "rdfs:seeAlso",
    "owl:equivalentClass",
    "skos:definition",
    "rdfs:comment",
    "brick:hasAssociatedTag",
    "rdfs:label"
  ]
}
```

The only numerical property in this list is "brick:hasQuantity", which by its name indicates it connects an entity with a measurable quantity. All other properties are non-numerical as they describe relationships between entities or provide descriptive information rather than measurable quantities.

Classification result: {
  "numerical": [
    "brick:hasQuantity"
  ],
  "non_numerical": [
    "owl:disjointWith",
    "rdfs:subClassOf",
    "brick:hasSubstance",
    "rdfs:seeAlso",
    "owl:equivalentClass",
    "skos:definition",
    "rdfs:comment",
    "brick:hasAssociatedTag",
    "rdfs:label"
  ]
}
Numerical properties: ['brick:hasQuantity']
Class brick:Temperature_Sensor has numerical properties: ['brick:hasQuantity']
Class brick:CO2_Sensor has numerical properties: ['brick:hasQuantity']
Class brick:Occupancy_Sensor has numerical properties: ['brick:hasQuantity']
Class brick:Ventilation_Air_System does not have numerical properties
Class brick:Radiator does not have numerical properties
Class brick:Cooling_Coil does not have numerical properties

Extra nodes to be added: ['brick:Ventilation_Air_System', 'brick:Radiator', 'brick:Cooling_Coil']
🛠️ ↪️  Tool result:
{
  "non_numeric_classes": [
    "brick:Ventilation_Air_System",
    "brick:Radiator",
    "brick:Cooling_Coil"
  ]
}

✨ Claude generating... (get_context_(4))

🛠️  Tool use... (term_mapper)
🔍 Mapping terms: {
  "temperatureAmb": "class",
  "temperature": "class",
  "co2": "class",
  "pir": "class",
  "airFlowSetpoint": "class",
  "temperatureSetpoint": "class",
  "fanSpeed": "class"
} using ontology: LLM_models/ontologies\Brick.ttl

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'temperatureAmb')
🔍✅ Semantic search completed in 21.98 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Temperature_Sensor
🔍 Prefix found: brick:Temperature_Sensor (URI: https://brickschema.org/schema/Brick#Temperature_Sensor)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'temperature')
🔍✅ Semantic search completed in 22.49 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: TemperatureQuantityShape
🔍 Prefix found: bsh:TemperatureQuantityShape (URI: https://brickschema.org/schema/BrickShape#TemperatureQuantityShape)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'co2')
🔍✅ Semantic search completed in 26.67 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: CO2_ConcentrationQuantityShape
🔍 Prefix found: bsh:CO2_ConcentrationQuantityShape (URI: https://brickschema.org/schema/BrickShape#CO2_ConcentrationQuantityShape)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'pir')
🔍✅ Semantic search completed in 43.69 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: PIR_Sensor
🔍 Prefix found: brick:PIR_Sensor (URI: https://brickschema.org/schema/Brick#PIR_Sensor)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'airFlowSetpoint')
🔍✅ Semantic search completed in 29.76 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Air_Flow_Setpoint
🔍 Prefix found: brick:Air_Flow_Setpoint (URI: https://brickschema.org/schema/Brick#Air_Flow_Setpoint)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'temperatureSetpoint')
🔍✅ Semantic search completed in 31.45 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Temperature_Setpoint
🔍 Prefix found: brick:Temperature_Setpoint (URI: https://brickschema.org/schema/Brick#Temperature_Setpoint)

Ontology index loaded from LLM_models/ontologies\Brick_index.json
🔍⏳ Semantic search... (ontology class for 'fanSpeed')
🔍✅ Semantic search completed in 32.11 seconds

✨ Claude generating... (find_match_(0))
✨↪️  Model reply: Fan_Speed_Command
🔍 Prefix found: brick:Fan_Speed_Command (URI: https://brickschema.org/schema/Brick#Fan_Speed_Command)
🛠️ ↪️  Tool result:
{
  "mapped_terms": {
    "temperatureAmb": "brick:Temperature_Sensor",
    "temperature": "bsh:TemperatureQuantityShape",
    "co2": "bsh:CO2_ConcentrationQuantityShape",
    "pir": "brick:PIR_Sensor",
    "airFlowSetpoint": "brick:Air_Flow_Setpoint",
    "temperatureSetpoint": "brick:Temperature_Setpoint",
    "fanSpeed": "brick:Fan_Speed_Command"
  }
}

✨ Claude generating... (get_context_(5))

🛠️  Tool use... (get_non_numeric_classes)
🔍 Getting non-numeric classes for: ['brick:Temperature_Sensor', 'bsh:TemperatureQuantityShape', 'bsh:CO2_ConcentrationQuantityShape', 'brick:PIR_Sensor', 'brick:Air_Flow_Setpoint', 'brick:Temperature_Setpoint', 'brick:Fan_Speed_Command'] using ontology: LLM_models/ontologies\Brick.ttl

==================== PROCESSING CLASS: brick:Temperature_Sensor ====================
Found 5 superclasses for brick:Temperature_Sensor
Found 7 properties for brick:Temperature_Sensor
  - rdfs:label
  - rdfs:seeAlso
  - rdfs:subClassOf
  - owl:disjointWith
  - skos:definition
  - brick:hasAssociatedTag
  - brick:hasQuantity

==================== PROCESSING CLASS: bsh:TemperatureQuantityShape ====================
Found 2 superclasses for bsh:TemperatureQuantityShape
Found 1 properties for bsh:TemperatureQuantityShape
  - rdfs:subClassOf

==================== PROCESSING CLASS: bsh:CO2_ConcentrationQuantityShape ====================
Found 2 superclasses for bsh:CO2_ConcentrationQuantityShape
Found 1 properties for bsh:CO2_ConcentrationQuantityShape
  - rdfs:subClassOf

==================== PROCESSING CLASS: brick:PIR_Sensor ====================
Found 6 superclasses for brick:PIR_Sensor
Found 7 properties for brick:PIR_Sensor
  - rdfs:label
  - rdfs:seeAlso
  - rdfs:subClassOf
  - owl:disjointWith
  - skos:definition
  - brick:hasAssociatedTag
  - brick:hasQuantity

==================== PROCESSING CLASS: brick:Air_Flow_Setpoint ====================
Found 6 superclasses for brick:Air_Flow_Setpoint
Found 8 properties for brick:Air_Flow_Setpoint
  - rdfs:label
  - rdfs:seeAlso
  - rdfs:subClassOf
  - owl:disjointWith
  - skos:definition
  - brick:hasAssociatedTag
  - brick:hasQuantity
  - brick:hasSubstance

==================== PROCESSING CLASS: brick:Temperature_Setpoint ====================
Found 5 superclasses for brick:Temperature_Setpoint
Found 7 properties for brick:Temperature_Setpoint
  - rdfs:label
  - rdfs:seeAlso
  - rdfs:subClassOf
  - owl:disjointWith
  - skos:definition
  - brick:hasAssociatedTag
  - brick:hasQuantity

==================== PROCESSING CLASS: brick:Fan_Speed_Command ====================
Found 6 superclasses for brick:Fan_Speed_Command
Found 5 properties for brick:Fan_Speed_Command
  - rdfs:label
  - rdfs:subClassOf
  - owl:disjointWith
  - skos:definition
  - brick:hasAssociatedTag

Total unique properties across all classes: 8

✨ Claude generating... (classify_props_LLM_(0))
✨↪️  Model reply: I'll classify these properties into numerical and non-numerical categories based on whether they connect an entity with a measurable quantity or with another entity/description.

```json
{
  "numerical": [
    "brick:hasQuantity"
  ],
  "non_numerical": [
    "owl:disjointWith",
    "rdfs:subClassOf",
    "brick:hasSubstance",
    "rdfs:seeAlso",
    "skos:definition",
    "brick:hasAssociatedTag",
    "rdfs:label"
  ]
}
```

Explanation:
- "brick:hasQuantity" is numerical because it connects an entity with a measurable quantity
- The rest are non-numerical as they typically connect entities with other entities or provide descriptions:
  - "owl:disjointWith" indicates class disjointness in ontologies
  - "rdfs:subClassOf" indicates class hierarchy
  - "brick:hasSubstance" indicates what substance an entity contains/involves
  - "rdfs:seeAlso" provides references to other resources
  - "skos:definition" provides textual definitions
  - "brick:hasAssociatedTag" links to associated tags/labels
  - "rdfs:label" provides human-readable labels for resources

Classification result: {
  "numerical": [
    "brick:hasQuantity"
  ],
  "non_numerical": [
    "owl:disjointWith",
    "rdfs:subClassOf",
    "brick:hasSubstance",
    "rdfs:seeAlso",
    "skos:definition",
    "brick:hasAssociatedTag",
    "rdfs:label"
  ]
}
Numerical properties: ['brick:hasQuantity']
Class brick:Temperature_Sensor has numerical properties: ['brick:hasQuantity']
Class bsh:TemperatureQuantityShape does not have numerical properties
Class bsh:CO2_ConcentrationQuantityShape does not have numerical properties
Class brick:PIR_Sensor has numerical properties: ['brick:hasQuantity']
Class brick:Air_Flow_Setpoint has numerical properties: ['brick:hasQuantity']
Class brick:Temperature_Setpoint has numerical properties: ['brick:hasQuantity']
Class brick:Fan_Speed_Command does not have numerical properties

Extra nodes to be added: ['bsh:TemperatureQuantityShape', 'bsh:CO2_ConcentrationQuantityShape', 'brick:Fan_Speed_Command']
🛠️ ↪️  Tool result:
{
  "non_numeric_classes": [
    "bsh:TemperatureQuantityShape",
    "bsh:CO2_ConcentrationQuantityShape",
    "brick:Fan_Speed_Command"
  ]
}

✨ Claude generating... (get_context_(6))
✨↪️  Model reply: 
{
  "numericalProperties": [
    "temperatureAmb",
    "temperature",
    "co2",
    "pir",
    "airFlowSetpoint",
    "temperatureSetpoint",
    "fanSpeed"
  ],
  "relationalProperties": [
    "hasLocation"
  ],
  "entityMappings": {
    "Hotel": "rec:Shelter",
    "HotelRoom": "rec:Room",
    "AmbientTemperatureSensor": "brick:Temperature_Sensor",
    "TemperatureSensor": "brick:Temperature_Sensor",
    "CO2Sensor": "brick:CO2_Sensor",
    "PresenceSensor": "brick:Occupancy_Sensor",
    "FreshAirVentilation": "brick:Ventilation_Air_System",
    "RadiatorThermostat": "brick:Radiator",
    "CoolingCoil": "brick:Cooling_Coil"
  },
  "propertyMappings": {
    "hasLocation": "brick:hasLocation"
  },
  "extraNodes": [
    {
      "id": "airFlowSetpoint:FreshAirVentilation:example_room",
      "type": "airFlowSetpoint",
      "value": {
        "type": "Number",
        "value": 0.0
      },
      "ontologyMapping": "brick:Air_Flow_Setpoint"
    },
    {
      "id": "temperatureSetpoint:RadiatorThermostat:example_room",
      "type": "temperatureSetpoint",
      "value": {
        "type": "Number",
        "value": 0.0
      },
      "ontologyMapping": "brick:Temperature_Setpoint"
    },
    {
      "id": "fanSpeed:CoolingCoil:example_room",
      "type": "fanSpeed",
      "value": {
        "type": "Number",
        "value": 0.0
      },
      "ontologyMapping": "brick:Fan_Speed_Command"
    }
  ]
}

Ontology prefixes:
@prefix bacnet: <http://data.ashrae.org/bacnet/2020#> .
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix bsh: <https://brickschema.org/schema/BrickShape#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix qudt: <http://qudt.org/schema/qudt/> .
@prefix qudtqk: <http://qudt.org/vocab/quantitykind/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rec: <https://w3id.org/rec#> .
@prefix rec: <https://w3id.org/rec#> .
@prefix ref: <https://brickschema.org/schema/Brick/ref#> .
@prefix s223: <http://data.ashrae.org/standard223#> .
@prefix sdo: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix sdo: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix tag: <https://brickschema.org/schema/BrickTag#> .
@prefix unit: <http://qudt.org/vocab/unit/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
Context prepared: ('\n{\n  "numericalProperties": [\n    "temperatureAmb",\n    "temperature",\n    "co2",\n    "pir",\n    "airFlowSetpoint",\n    "temperatureSetpoint",\n    "fanSpeed"\n  ],\n  "relationalProperties": [\n    "hasLocation"\n  ],\n  "entityMappings": {\n    "Hotel": "rec:Shelter",\n    "HotelRoom": "rec:Room",\n    "AmbientTemperatureSensor": "brick:Temperature_Sensor",\n    "TemperatureSensor": "brick:Temperature_Sensor",\n    "CO2Sensor": "brick:CO2_Sensor",\n    "PresenceSensor": "brick:Occupancy_Sensor",\n    "FreshAirVentilation": "brick:Ventilation_Air_System",\n    "RadiatorThermostat": "brick:Radiator",\n    "CoolingCoil": "brick:Cooling_Coil"\n  },\n  "propertyMappings": {\n    "hasLocation": "brick:hasLocation"\n  },\n  "extraNodes": [\n    {\n      "id": "airFlowSetpoint:FreshAirVentilation:example_room",\n      "type": "airFlowSetpoint",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Air_Flow_Setpoint"\n    },\n    {\n      "id": "temperatureSetpoint:RadiatorThermostat:example_room",\n      "type": "temperatureSetpoint",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Temperature_Setpoint"\n    },\n    {\n      "id": "fanSpeed:CoolingCoil:example_room",\n      "type": "fanSpeed",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Fan_Speed_Command"\n    }\n  ]\n}\n', '@prefix bacnet: <http://data.ashrae.org/bacnet/2020#> .\n@prefix brick: <https://brickschema.org/schema/Brick#> .\n@prefix bsh: <https://brickschema.org/schema/BrickShape#> .\n@prefix dcterms: <http://purl.org/dc/terms/> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n@prefix qudt: <http://qudt.org/schema/qudt/> .\n@prefix qudtqk: <http://qudt.org/vocab/quantitykind/> .\n@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n@prefix rec: <https://w3id.org/rec#> .\n@prefix ref: <https://brickschema.org/schema/Brick/ref#> .\n@prefix s223: <http://data.ashrae.org/standard223#> .\n@prefix sdo: <http://schema.org/> .\n@prefix sh: <http://www.w3.org/ns/shacl#> .\n@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n@prefix sosa: <http://www.w3.org/ns/sosa/> .\n@prefix tag: <https://brickschema.org/schema/BrickTag#> .\n@prefix unit: <http://qudt.org/vocab/unit/> .\n@prefix vcard: <http://www.w3.o@prefix sdo: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix tag: <https://brickschema.org/schema/BrickTag#> .
@prefix unit: <http://qudt.org/vocab/unit/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
Context prepared: ('\n{\n  "numericalProperties": [\n    "temperatureAmb",\n    "temperature",\n    "co2",\n    "pir",\n    "airFlowSetpoint",\n    "temperatureSetpoint",\n    "fanSpeed"\n  ],\n  "relationalProperties": [\n    "hasLocation"\n  ],\n  "entityMappings": {\n    "Hotel": "rec:Shelter",\n    "HotelRoom": "rec:Room",\n    "AmbientTemperatureSensor": "brick:Temperature_Sensor",\n    "TemperatureSensor": "brick:Temperature_Sensor",\n    "CO2Sensor": "brick:CO2_Sensor",\n    "PresenceSensor": "brick:Occupancy_Sensor",\n    "FreshAirVentilation": "brick:Ventilation_Air_System",\n    "RadiatorThermostat": "brick:Radiator",\n    "CoolingCoil": "brick:Cooling_Coil"\n  },\n  "propertyMappings": {\n    "hasLocation": "brick:hasLocation"\n  },\n  "extraNodes": [\n    {\n      "id": "airFlowSetpoint:FreshAirVentilation:example_room",\n      "type": "airFlowSetpoint",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Air_Flow_Setpoint"\n    },\n    {\n      "id": "temperatureSetpoint:RadiatorThermostat:example_room",\n      "type": "temperatureSetpoint",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Temperature_Setpoint"\n    },\n    {\n      "id": "fanSpeed:CoolingCoil:example_room",\n      "type": "fanSpeed",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Fan_Speed_Command"\n    }\n  ]\n}\n', '@prefix bacnet: <http://data.ashrae.org/bacnet/2020#> .\n@prefix brick: <https://brickschema.org/schema/Brick#> .\n@prefix bsh: <https://brickschema.org/schema/BrickShape#> .\n@prefix dcterms: <http://purl.org/dc/terms/> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n@prefix qudt: <http://qudt.org/schema/qudt/> .\n@prefix qudtqk: <http://qudt.org/vocab/quantitykind/> .\n@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n@prefix rec: <https://w3id@prefix sdo: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix tag: <https://brickschema.org/schema/BrickTag#> .
@prefix unit: <http://qudt.org/vocab/unit/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
Context prepared: ('\n{\n  "numericalProperties": [\n    "temperatureAmb",\n    "temperature",\n    "co2",\n    "pir",\n    "airFlowSetpoint",\n    "temperatureSetpoint",\n    "fanSpeed"\n  ],\n  "relationalProperties": [\n    "hasLocation"\n  ],\n  "entityMappings": {\n    "Hotel": "rec:Shelter",\n    "HotelRoom": "rec:Room",\n    "AmbientTemperatureSensor": "brick:Temperature_Sensor",\n    "TemperatureSensor": "brick:Temperature_Sensor",\n    "CO2Sensor": "brick:CO2_Sensor",\n    "PresenceSensor": "brick:Occupancy_Sensor",\n    "FreshAirVentilation": "brick:Ventilation_Air_System",\n    "RadiatorThermostat": "brick:Radiator",\n    "CoolingCoil": "brick:Cooling_Coil"\n  },\n  "propertyMappings": {\n    "hasLocation": "brick:hasLocation"\n  },\n  "extraNodes": [\n    {\n      "id": "airFlowSetpoint:FreshAirVentilation:example_room",\n      "type": "airFlowSetpoint",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Air_Flow_Setpoint"\n    },\n    {\n      "id": "temperatureSetpoint:RadiatorThermostat:example_room",\n      "type": "temperatureSetpoint",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Temperature_Setpoint"\n    },\n    {\n      "id": "fanSpeed:CoolingCoil:example_room",\n      "type": "fanSpeed",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Fan_Speed_Command"\n    }\n  ]\n}\n', '@prefix bacnet: <http://data.ashrae.org/bacnet/2020#> .\n@prefix brick: <@prefix sdo: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix tag: <https://brickschema.org/schema/BrickTag#> .
@prefix unit: <http://qudt.org/vocab/unit/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
Context prepared: ('\n{\n  "numericalProperties": [\n    "temperatureAmb",\n    "temperature",\n    "co2",\n    "pir",\n    "airFlowSetpoint",\n    "temperatureSetpoint",\n    "fanSpeed"\n  ],\n  "relationalProperties": [\n    "hasLocation"\n  ],\n  "entityMappings": {\n    "Hotel": "rec:Shelter",\n    "HotelRoom": "rec:Room",\n    "AmbientTemperatureSensor": "brick:Temperature_Sensor",\n    "TemperatureSensor": "brick:Temperature_Sensor",\n    "@prefix sdo: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix tag: <https://brickschema.org/schema/BrickTag#> .
@prefix unit: <http://qudt.org/vocab/unit/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
Context prepared: ('\n{\n  "numericalProperties": [\n    "temperatureAmb",\n    "temperature",\n    "co2",\n    "pir",\n    "airFlowSetpoint",\n    "temperatureSetpoint",\n    "fanSpeed"\n  ],\n  "relationalProperties": [\n    "hasLocation"\n  ],\n  "entityMappings": {\n    "Hotel": "rec:Shelter",\n    "HotelRoom": "rec:Room",\n    "AmbientTemperatureSensor": "brick:Temperature_Sensor",\n    "TemperatureSensor": "brick:Temperature_Sensor",\n    "CO2Sensor": "brick:CO2_Sensor",\n    "PresenceSensor": "brick:Occupancy_Sensor",\n    "FreshAirVentilation": "brick:Ventilation_Air_System",\n    "RadiatorThermostat": "brick:Radiator",\n    "CoolingCoil": "brick:Cooling_Coil"\n  },\n  "propertyMappings": {\n    "hasLocation": "brick:hasLocation"\n  },\n  "extraNodes": [\n    {\n      "id": "airFlowSetpoint:FreshAirVentilation:example_room",\n      "type": "airFlowSetpoint",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Air_Flow_Setpoint"\n    },\n    {\n      "id": "temperatureSetpoint:RadiatorThermostat:example_room",\n      "type": "temperatureSetpoint",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Temperature_Setpoint"\n    },\n    {\n      "id": "fanSpeed:CoolingCoil:example_room",\n      "type": "fanSpeed",\n      "value": {\n        "type": "Number",\n        "value": 0.0\n      },\n      "ontologyMapping": "brick:Fan_Speed_Command"\n    }\n  ]\n}\n', '@prefix bacnet: <http://data.ashrae.org/bacnet/2020#> .\n@prefix brick: <https://brickschema.org/schema/Brick#> .\n@prefix bsh: <https://brickschema.org/schema/BrickShape#> .\n@prefix dcterms: <http://purl.org/dc/terms/> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n@prefix qudt: <http://qudt.org/schema/qudt/> .\n@prefix qudtqk: <http://qudt.org/vocab/quantitykind/> .\n@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n@prefix rec: <https://w3id.org/rec#> .\n@prefix ref: <https://brickschema.org/schema/Brick/ref#> .\n@prefix s223: <http://data.ashrae.org/standard223#> .\n@prefix sdo: <http://schema.org/> .\n@prefix sh: <http://www.w3.org/ns/shacl#> .\n@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n@prefix sosa: <http://www.w3.org/ns/sosa/> .\n@prefix tag: <https://brickschema.org/schema/BrickTag#> .\n@prefix unit: <http://qudt.org/vocab/unit/> .\n@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .')