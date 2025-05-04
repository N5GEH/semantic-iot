## Demonstration with FIWARE
This is a demonstration of how to use **semantic-iot** framework to build up a Knowledge Graph Construction Pipline (**KGCP**) for FIWARE platform specialized for smart hotel use cases.

It is assumed that data in IoT platform conforms with specific **data models**, no matter in which format.
In this demonstration, we provide data models of hotel energy systems in Python using [Pydantic](https://pydantic-docs.helpmanual.io/).
These data models can be found in [`./datamodels/pydantic_models.py`](./datamodels/pydantic_models.py).

Important is that **an example data set** can be created, which fully represents the data models being used.
In this demonstration, we provide this example data set in JSON format as [`./kgcp/rml/example_hotel.json`](./kgcp/rml/example_hotel.json), which can also be created using the data model script.

Additional data sets, representing different IoT systems of the same specialized IoT platform can be provisioned to a running FIWARE platform via the script [`datamodels/hotel_provision.py`](datamodels/hotel_provision.py). For quick start, we provide a pre-provisioned data under `./hotel_dataset`. If you do like to provision the data by yourself, please deploy the FIWARE platform locally. You can use the docker configuration in `./deployment`.

### Prerequisites
Install the **semantic-iot** framework:
```bash
git clone https://github.com/N5GEH/semantic-iot.git
cd semantic-iot
pip install .
```

Install extra dependencies needed for this demonstration.

```bash
pip install -r examples/fiware/requirements.txt
```
> **Note**: This demonstration currently has dependency issues with the **semantic-iot** framework. Therefore, you may see some warnings when installing the requirements. However, **you can ignore them**. We are working on fixing this issue.

### Step 1 data model identification & vocabulary mapping
Set up the FIWARE platform specific configuration is the first step.
In this demonstration, we provide a configuration file [`./kgcp/rml/fiware_config.json`](./kgcp/rml/fiware_config.json) for the specialized FIWARE platform:
```json
{
    "ID_KEY": "id",
    "TYPE_KEYS": [
        "type"
    ],
    "JSONPATH_EXTRA_NODES": [
        "$..fanSpeed",
        "$..airFlowSetpoint",
        "$..temperatureSetpoint"
    ]
}
```
The ``JSONPATH_EXTRA_NODES`` is used to append extra resource types, which are not directly modeled as entities in the JSON dataset. For example `fanSpeed` is modeled as a property of `CoolingCoil`, but it should be mapped to a separate resource type in the knowledge graph.

After understanding this, you can start the data model identification and vocabulary mapping by running the script [`./kgcp/rml/rml_preprocess.py`](./kgcp/rml/rml_preprocess.py). In this case, the above configuration file and the domain ontology for building energy system, brick, are given as input.

### Step 2 validation and completion
The last step generate a pre-filled **"resource node relationship"** document, which can be found as [`./kgcp/rml/rdf_node_relationship.json`](./kgcp/rml/rdf_node_relationship.json).
In this document, the data models are identified as different **resource types** and the terminology-mappings to specific term of the ontology are suggested based on the string similarity.

Manual validation and completion are now required for:
1. Verify the terminology-mappings. For example, the correct mapping for `PresenceSensor` should be `brick:Occupancy_Count_Sensor`.
2. Complete the interrelationship information between resource types. For example, `TemperatureSensor` is related to `HotelRoom` via the predicate `brick:isPointOf`.
3. Complete the "link" for accessing the data. For example, the link for `TemperatureSensor` should be `https://<host>/v2/entities/{id}/attrs/temperature/value`.

For the resource type `TemperatureSensor`, this is the generated **"resource node relationship"** document:
````json
{
    "identifier": "id",
    "nodetype": "TemperatureSensor",
    "extraNode": false,
    "iterator": "$[?(@.type=='TemperatureSensor')]",
    "class": "**TODO: PLEASE CHECK** brick:Temperature_Sensor",
    "hasRelationship": [
        {
            "relatedNodeType": null,
            "propertyClass": null,
            "rawdataidentifier": null
        }
    ],
    "link": null
}
````

And after validation and completion, it should look like this:
````json
{
    "identifier": "id",
    "nodetype": "TemperatureSensor",
    "extraNode": false,
    "iterator": "$[?(@.type=='TemperatureSensor')]",
    "class": "brick:Air_Temperature_Sensor",
    "hasRelationship": [
        {
            "relatedNodeType": "HotelRoom",
            "propertyClass": "brick:isPointOf",
            "rawdataidentifier": "hasLocation.value"
        }
    ],
    
    "link": "https://fiware.eonerc.rwth-aachen.de/v2/entities/{id}/attrs/temperature/value"
}
````

A validated and completed **"resource node relationship"** document for this example is provided in [`./kgcp/rml/rdf_node_relationship_validated.json`](./kgcp/rml/rdf_node_relationship_validated.json).

### Step 3 generate mapping file to build KGCP
Based on the completed **"resource node relationship"** document, we can generate the RML mapping file for the KGCP.
In this demonstration, this step can be conducted by running the script [`./kgcp/rml_generate.py`](./kgcp/rml_generate.py).
The generated RML mapping file can be found in [`./kgcp/rml/fiware_hotel_rml.ttl`](./kgcp/rml/fiware_hotel_rml.ttl).

### Step 4 apply KGCP
So far, we have collected all required information to build the KGCP.
[``./kgcp/fiware_kgcp.py``](./kgcp/fiware_kgcp.py) showcases how to apply the KGCP and generate knowledge graphs for different volumes of data sets (range from 2 to 1000 rooms) in [``./hotel_dataset``](./hotel_dataset).

### Step 5 automated service deployment
The generated knowledge graph of a hotel IoT system can be used to deploy services, for example a building automation program, automatically.

To enable generic information extraction, we can apply logical inference, i.e., reasoning, to the generated knowledge graph. The script
[``./application_deployment/reasoning_owl_rl.py``](./application_deployment/reasoning_owl_rl.py) uses the [OWL-RL](https://owl-rl.readthedocs.io/en/latest/owlrl.html) to infer new knowledge based on the used brick ontology and the existing knowledge graphs. The inferred knowledge graph for the hotel with 10 rooms is provided as an example in [`./application_deployment/fiware_entities_10rooms_inferred.ttl`](./application_deployment/fiware_entities_10rooms_inferred.ttl). After the inference, the number of triples increases from 263 to 1597.

Since a lot of class subsumption relationships are inferred, generic information extraction can be applied to the inferred knowledge graph. For example, the class ``Ventilation_Air_System`` is inferred to be a subclass of ``Air_System`` and ``HVAC_System``. Therefor, all existing actuation for the air system in hotel rooms can be retrieved by the following SPARQL query:
```sparql
PREFIX brick: <https://brickschema.org/schema/Brick#>
PREFIX rec: <https://w3id.org/rec#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?room ?airSystem ?actuation ?actuation_type ?actuation_access
WHERE {
  ?room a rec:Room .
  ?airSystem a brick:Air_System ;
             brick:hasLocation ?room .
  OPTIONAL {
    ?actuation a ?actuation_type ;
               brick:isPointOf ?airSystem ;
               rdf:value ?actuation_access .
    VALUES ?actuation_type { brick:Setpoint brick:Command }
  }
}
```
By applying this approach to extract information about the presence of sensors and actuators, and data interactions via the platform API, building automation programs can be configured automatically:
```yaml
- controller_function: Ventilation  # Control function Ventilation/Heating/Cooling
  controller_mode: <...>  # co2/presence/timetable
  inputs:
    sensor_access: <...>  # URL to access the sensor data
  outputs:
    actuation_access: <...>  # URL to access the actuation function
```

An example of such automated configuration is provided in [`./application_deployment/controller_configuration.py`](./application_deployment/controller_configuration.py). 
The result is a configuration file for the distributed air systems in hotel, e.g., [`./application_deployment/controller_configs/fiware_entities_10rooms_inferred.yml`](./application_deployment/controller_configs/fiware_entities_10rooms_inferred.yml). 