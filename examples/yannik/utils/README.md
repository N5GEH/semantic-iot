# Ontology Matcher Utilities

These utilities help process large ontology class files and match them to resource types using the Claude LLM API.

## Overview

When working with large ontology files like Brick Schema, the file size often exceeds the context window of LLMs like Claude. This utility:

1. Splits large ontology files into manageable chunks
2. Processes each chunk with Claude to match ontology classes to resource types
3. Combines the results into a single output file

## Usage

```bash
# Set your Claude API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Run the matcher with your resource types
python match_ontology.py --resource-types temperature humidity occupancy light energy hvac water air_quality
```

### Arguments

- `--ontology-file`: Path to the ontology classes JSON file (default: "kgcp_config/output/ontology_classes.json")
- `--resource-types`: List of resource types to match against ontology (required)
- `--output-file`: Path to save the matches output file (default: "kgcp_config/output/resource_type_matches.json")
- `--chunk-size`: Number of ontology classes per chunk (default: 100)
- `--api-key`: Claude API key (if not provided, uses ANTHROPIC_API_KEY environment variable)

## Example Output

The output will be a JSON file with a structure like:

```json
{
  "temperature": [
    {
      "ontology_class": "temperature sensor",
      "uri": "https://brickschema.org/schema/Brick#Temperature_Sensor",
      "reason": "This class directly represents temperature sensing devices"
    },
    {
      "ontology_class": "air temperature sensor",
      "uri": "https://brickschema.org/schema/Brick#Air_Temperature_Sensor",
      "reason": "This is a specialized temperature sensor for air temperature"
    }
  ],
  "humidity": [
    {
      "ontology_class": "humidity sensor",
      "uri": "https://brickschema.org/schema/Brick#Humidity_Sensor",
      "reason": "This class directly represents humidity sensing devices"
    }
  ]
}
```
