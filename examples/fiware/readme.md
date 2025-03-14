## Demonstration with FIWARE
This is a demonstration of how to use **semantic-iot** framework to build up a Knowledge Graph Construction Pipline (**KGCP**) for FIWARE platform specialized for smart hotel use cases.

It is assumed that data in IoT platform conforms with specific **data models**, no matter in which format.
In this demonstration, we provide data models of hotel energy systems in Python using [Pydantic](https://pydantic-docs.helpmanual.io/).
These data models can be found in `./datamodels/pydantic_models.py`.

Important is that **an example data set** can be created, which fully represents the data models being used.
In this demonstration, we provide this example data set in JSON format as `./kgcp/rml/example_hotel.json`, which can also be created using the data model script.

Additional data sets, representing different IoT systems of the same specialized IoT platform can be provisioned to a running FIWARE platform via the script `datamodels/hotel_provision.py`. For quick start, we provide a pre-provisioned data under `./hotel_dataset`. If you do like to provision the data by yourself, please deploy the FIWARE platform locally. You can use the docker configuration in `./deployment`.

### Prerequisites
Install the semantic-iot framework:
```bash
git clone https://github.com/N5GEH/semantic-iot.git
cd semantic-iot
pip install .
```

Install extra dependencies needed for this demonstration.

```bash
pip install -r examples/fiware/requirements.txt
```
> **Note**: This demonstration currently has dependency issues with the `semantic-iot` framework. Therefore, you may see some warnings when installing the requirements. However, **you can ignore them**. We are working on fixing this issue.

### Step 1 data model identification & vocabulary mapping
Set up the FIWARE platform specific configuration is the first step.
In this demonstration, we provide a configuration file `./kgcp/rml/fiware_config.json` for the specialized FIWARE platform:
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
For more details about each key of this configuration, please refer to the ``JSONPreprocessor`` class.

After that, we can start the data model identification and vocabulary mapping with the script ``./kgcp/rml_preprocess.py``, in which the domain ontologies and the example JSON data set are given as input.

### Step 2 validation and completion
The last step generate a pre-filled **"resource node relationship"** document, which can be found as `./kgcp/rml/rdf_node_relationship.json`.
In this document, the data models are identified as different **resource types** and specific term from the ontologies are suggested based on the text similarity.

Manual validation and completion are now required:
1. Verify the term suggestions
2. Complete the interrelationship information between resource types
3. Complete the "link" for accessing the data

For example this is the resource type `TemperatureSensor` from the generated **"resource node relationship"** document:
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
            "relatedAttribute": null,
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
            "relatedAttribute": "brick:isPointOf",
            "rawdataidentifier": "hasLocation.value"
        }
    ],
    
    "link": "https://fiware.eonerc.rwth-aachen.de/v2/entities/{id}/attrs/temperature/value"
}
````

### Step 3 generate mapping file to build KGCP
Based on the completed **"resource node relationship"** document, we can generate the RML mapping file for the KGCP.
In this demonstration, this step is conducted in the script `./kgcp/rml_generate.py`.

### Step 4 apply KGCP
So far, we have collected all required information to build the KGCP, i.e., 1) the platform configuration, and 2) the RML mapping file.
``./kgcp/fiware_kgcp.py`` showcases how to apply the KGCP and generate knowledge graphs for a large amount of data sets in ``./hotel_dataset``

### Step 5 (optional) knowledge inference
To improve the query performance, we can apply knowledge inference to the generated knowledge graph.
``./reasoning_owl_rl.py`` uses the [OWL-RL](https://owl-rl.readthedocs.io/en/latest/owlrl.html)  to infer new knowledge based on the existing KGs.

To give an impression, there are 103 triples in the generated KG for 10 rooms.
After inference, the number of triples increase to 934.
