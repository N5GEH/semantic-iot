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