Under ``ontologies`` folder there are two scripts that relevant: RML Mapping Generator, RML Mapping Generator Post

### Step 1
Run RML Mapping Generator
1. specify the id and node type idenx
2. Specify extra attribute name to be used as node
3. Run the script
4. The preprocessed json is the flatened version of the original json, so that extra entities will be created for the specified extra attribute

### Step 2 (intermediate step)
All node tpyes will be identified.
Manual effort is required:
2. validate the auto suggested ontology terms
3. define the relationship between the node type for relationship node type
4. specify links for value node type

### Step 3 generate mapping file
Run RML Mapping Generator Post
A mapping file will be generated.

### Step 4 apply the mapping file to build KGCP
run kgcp/RDF_generator.py



### Docker
For RML preprocessor
````shell
docker run --mount type=bind,source=YOUR_LOCAL_PATH,target=/app/data iot2kg preprocessor \
    --input_file /app/data/hotel_aachen_004_hotel_100rooms.json \
    --output_file /app/data/output_rdf_node_relationship.json \
    --ontology_paths /app/data/Brick.ttl \
    --force \
    --id_key id \
    --type_keys type \
    --extra_nodes fanSpeed airFlowSetpoint temperatureSetpoint
````

For RML generator
````shell
docker run \
  --mount type=bind,source=YOUR_LOCAL_PATH,target=/app/data \
  iot2kg generator \
  --input_rnr_file /app/data/YOUR_INPUT_FILE.json \
  --output_rml_file /app/data/output_mapping.ttl
````

### Python Environment
...