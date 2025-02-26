## Demonstration with FIWARE
This is a demonstration of how to use the **semantic-iot** framework to build a **Knowledge Graph Construction Pipeline (KGCP)** for the FIWARE platform, specialized for smart hotel use cases.

It is assumed that data in the IoT platform conforms to specific **data models**, regardless of format.
In this demonstration, we provide data models of hotel energy systems in Python using [Pydantic](https://pydantic-docs.helpmanual.io/).
These data models can be found in `./datamodels/pydantic_models.py`.

Important is that **an example data set** can be created, which fully represents the data models being used.
In this demonstration, we provide this example data set in JSON format as `./kgcp/rml/example_hotel.json`, which can also be created using the data model script.

Additional data sets, representing different IoT systems of the same specialized IoT platform, can be provisioned to a running FIWARE platform via the script `datamodels/hotel_provision.py`. For quick start, we provide pre-provisioned data under `./hotel_dataset`. If you would like to provision the data yourself, please deploy the FIWARE platform locally. You can use the Docker configuration in `./deployment`.

### Prerequisites
Install the semantic-iot framework
```bash
git clone ...
cd semantic-iot
pip install .
```

Please change the working directory to this folder and install dependencies for this demonstration.
```bash
cd examples/fiware
pip install -r requirements.txt
```
> Note: This demonstration currently has dependency issues with the semantic-iot framework. Therefore, you will see some warnings when installing the requirements. However, **you can ignore them**. We are working on fixing this issue.

### Step 1: Data Model Identification & Vocabulary Mapping
Setting up the FIWARE platform-specific configuration is the first step.

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
        "$..temperatureSetpoint",
        "$..temperature",
        "$..co2",
        "$..pir",
        "$..temperatureAmb"
    ]
}
```
For more details about each key in this configuration, please refer to the `JSONPreprocessor` class.

#### **Choosing the Ontology**
When running the `rml_preprocess.py` script, you will be prompted to select which ontology you want to use. The ontology file name will be dynamically extracted, ensuring that the generated mappings are correctly associated with the chosen ontology.

To specify an ontology, run the following command:
```bash
python kgcp/rml_preprocess.py
```
You will see a prompt like:
```bash
Available ontologies:
- brick
- saref4bldg
Enter the ontology you want to use (brick/saref4bldg):
```
Depending on the selected ontology, the output file will be dynamically named:
```bash
kgcp/rml/rdf_node_relationship_<ontology>.json
```
For example, if you choose `saref4bldg`, the output will be:
```bash
kgcp/rml/rdf_node_relationship_saref4bldg.json
```

### Step 2: Validation and Completion
The last step generates a pre-filled **"resource node relationship"** document, which can be found as `./kgcp/rml/rdf_node_relationship_<ontology>.json`.

#### **Manual validation and completion are now required:**
1. Verify the term suggestions
2. Complete the interrelationship information between resource types
3. Complete the "link" for accessing the data

### Step 3: Generate Mapping File to Build KGCP
When running `rml_generate.py`, you will be asked to select which ontology-related JSON file to use:
```bash
python kgcp/rml_generate.py
```
You will see a prompt like:
```bash
Available validated RDF node relationship files:
- brick
- saref4bldg
Enter the RDF node relationship file you want to use (brick/saref4bldg):
```
Once selected, the script will generate the RML mapping file:
```bash
kgcp/rml/fiware_hotel_rml.ttl
```
This ensures that the KGCP is built with the appropriate ontology.

### Step 4: Apply KGCP
So far, we have collected all required information to build the KGCP, i.e., 1) the platform configuration, and 2) the RML mapping file.

`./kgcp/fiware_kgcp.py` showcases how to apply the KGCP and generate knowledge graphs for a large amount of data sets in `./hotel_dataset`.

### Step 5 (Optional): Knowledge Inference
To improve query performance, we can apply knowledge inference to the generated knowledge graph.

`./reasoning_owl_rl.py` uses the [OWL-RL](https://owl-rl.readthedocs.io/en/latest/owlrl.html) to infer new knowledge based on the existing KGs.

To give an impression, there are 103 triples in the generated KG for 10 rooms.
After inference, the number of triples increases to 934.
