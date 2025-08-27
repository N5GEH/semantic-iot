

# Setup

Put 'ANTROPIC_API' File in Code Folder 

> **Note**: The ``/metrics`` folder is for saving the intermediate results necessary.
> The final results will still be copied to the corresponding results folder under ``/datasets``.

# Adding a New Dataset

## Dataset Folder

- **Name**: `<IoTPlatform>_<dataModel>_<dataset_name>`

## Files in dataset folder

### JSON Entities File (Required)
- **Description**: JSON response from IoT platform API containing all literal entities of a building
- **Content**: Systematic components, sensors, and actuators data

### JSON Example File (Optional)
- **Description**: Sample data containing unique entity types from the main JSON entities file
- **Purpose**: Represents data structure with one instance per entity type


## Files in parent folder

### Ontology File (Required)
- **Description**: RDF format standard defining data structure classes and properties
- **Purpose**: Terminology mapping
- **Access**: Use `term_mapper` tool

### IoT Platform API Specification (Required)
- **Description**: Documentation of API endpoints, request/response formats, and authentication
- **Content**: Link patterns for accessing sensor/actuator data
- **Access**: Use `get_endpoint_from_api_spec` tool


## How to Add Your Dataset

1. Prepare your JSON entities file from your IoT platform API
2. Ensure you have the corresponding ontology file
3. Provide the API specification document
4. Optionally, create a JSON example file for easier structure understanding
5. Place files in the appropriate dataset directory
6. Access files using the specified tools mentioned above
