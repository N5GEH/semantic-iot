# Semantic-IoT
Semantic-IoT is an innovative framework for generating knowledge graphs from data provisioned in IoT platforms.
It aims to enhance the interoperability across different IoT platforms.
This framework utilizes the [RDF Mapping Language (RML)](https://rml.io/specs/rml/) to facilitate the mapping of heterogeneous IoT data into structured and expressive knowledge graphs.

### Framework Overview
Following image gives an overview of the Semantic-IoT framework.

![](.\figures\framework_overview.png "Framework overview")

Its main components are:

**RML Generation**
- **RML Processor**: processes example dataset of an IoT platform to generate an intermediate document for further usage. This document need to be manually validated and completed.
- **RML Generator**: generate RML mapping file based on the manual validated document.

**Knowledge Graph Construction Pipeline**
- **RDF Generator**: utilize the RML mapping file to generate knowledge graphs for any data provisioned in IoT platforms (most likely different platform instances).

### Work with Python

#### Installation
```bash
git clone https://github.com/N5GEH/semantic-iot.git
cd semantic-iot
pip install .
```

#### Usage
Please check the [example](examples/fiware) for a detailed instruction on how to use the Semantic-IoT framework with Python. A FIWARE platform specialized for smart hotel use cases is demonstrated. 

### Work with Docker
Coming soon...



