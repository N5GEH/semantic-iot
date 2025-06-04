




class PromptsLoader:
    """
    A class to load prompts and templates from files.
    """

    # LOAD FILES =====================================================================
    def __init__(self):

        self.template_paths = {
            "rdf" : "LLM_models/templates/rdf_template.ttl",
            "RML" : "LLM_models/templates/rml_template.ttl",
            # "RNR" : "semantic_iot/LLM_models/templates/resource_node_relationship_template.ttl",
            "config" : "LLM_models/templates/platform_config_template.json",
        }
        self.templates = {}
        for key, path in self.template_paths.items():
            with open(path, "r") as f: 
                self.templates[key] = f.read()

        # IN-BETWEEN VARIABLES ================================================================

        self.ontology_path = None
        self.api_spec_path = None

        self.JEN_content = None
        self.JEX_content = None

        self.context_content = None
        self.prefixes = None

        self.rnr_content = None

        self.update_variables()


    def update_variables(self):

        # TEXT BLOCKS ==================================================================

        self.ROLE = f""" <role>
        You are an expert in engineering who is specialized in developing knowledge graphps 
        for building automation with IoT platforms. 
        </role>"""
        self.SYSTEM = f"""<system>
        - Be precise and concise.
        - You may use tools, only call them when needed, then you will receive its output in the next interaction.
        - If you dont have tools, dont try to call a tool, the prompt contains all information you need.
        - In your thinking, include the requirements for a human to be able to output the same result, e. g.:
        Example task: Complete the pattern: 1, 2, 5, 8,
        Example thinking: <thinking> - Basic arithmetic skills (addition and subtraction). - Pattern recognition abilities, specifically recognizing changes between numbers. - Logical thinking to identify the alternating difference pattern. </thinking>
        </system>"""
        self.OUTPUT_FORMAT = f"""<output>
        Put the relevant output data in <output> tags.
        What are requirements for a human to be able to output the same result? Put the answer in <req> tags.
        </output>"""

        
        # INPUT FILES ================================================================

        self.jen = f"""<input>
        # file: JSON Entities file
            description:
                This JSON data is a response of a GET request to the API of an IoT platform, 
                which contains all the literal entities of a building and its systematic components, available sensors and actuators. 
            content:
                <data>{self.JEN_content}</data>
        </input>"""

        self.jex = f"""<input> 
        # file: JSON Example file
            description:
                The JSON Example file is a sample data file that contains all unique entity types of the JSON Entities file, a response of a GET request to the API of an IoT platform.
                It represents the data structure of the JSON Entities file, but with only one instance of each entity type.
            content:
                <data>{self.JEX_content}</data>
        </input>"""


        # GOAL ================================================================

        self.GOAL = f"""<context>
        # Controller Configuration 
        The overall goal is to generate a configuration for a building's ventilation system based on the available sensors and actuators.

        file: Controller Configuration file
            Requirements for the configuration file based on the SPARQL queries:

            1. List of all rooms in the building (identified by their URIs).
            2. For each room:
                - All ventilation devices (Air Systems) associated with the room.
                    - For each device: 
                        - All actuation points (e.g., setpoints, commands) and their access methods/values.
                - All CO2 sensors available in the room, including their access methods/values.
                - All presence (occupancy count) sensors available in the room, including their access methods/values.

            The configuration file must map each room to its available sensors and actuators, specifying how to access their data or control them.

        This is done by querying a extended knowledge graph with SPARQL to extract information about the building's systematic components, like:
        - Which rooms are available in the building?
        - Which ventilation devices are available in each room?
        - How to access the actuation points of each ventilation device?


        # Extended Knowledge Graph 
        The extended knowledge graph is based on the original knowledge graph and includes additional classes and properties from a given ontology.
        The additional classes and properties are being created through inheritance from the ontology classes or properties.
        </context>"""

        # PROJECT FILES ================================================================

        self.KG = f"""
        # Knowledge Graph 
        The knowledge graph is a structured representation of the building's systematic components, including rooms, ventilation devices, sensors, and their relationships. 
        It is built from the provided JSON entities file of a GET request to a specific IoT platform.

        <constraints>MOST IMPORTANT: RDF should follow a valid turtle syntax!</constraints>

        <template>\n{self.templates["rdf"]}\n</template>
        <data>\n{self.prefixes}\n</data>
        """

        self.RML = f"""
        # RML Mapping File 
        The RML mapping file is used to generate the RDF knowledge graph from the JSON Entities data.

        The knowledge graph looks like this: \n{self.KG}

        <constraints>MOST IMPORTANT: RML should follow a valid turtle syntax!</constraints>

        <template>\n{self.templates["RML"]}\n</template>
        <data>\n{self.prefixes}\n</data>
        """
        
        self.PC = f""" 
        # file: Platform Configuration file
            The configuration file should contain the following information:

            - The ID_KEY is the key in the JSON data that uniquely identifies each entity.
            - The TYPE_KEYS are the keys in the JSON data that identify the type of each entity.
            - The JSONPATH_EXTRA_NODES are the JSONpath Expressions to the extra nodes that should be included in the mapping. 

            template: <template>\n{self.templates["config"]}\n</template>
        """ # Use the recursive descent operator
        
        self.RNR = f"""
        # Resource Node Relationship Document 
        The RML Mapping file can be generated automatically based on a validated Resource Node Relationship Document.
        The Resource Node Relationship Document is a prefilled document that contains the necessary information to generate the RML Mapping file.

        file: Resource Node Relationship Document
            content: \n{self.rnr_content}
        """

        # CONTEXT PROMPTS ================================================================

        self.context = f"""
        <context>
        {self.jex}
        Ontology path: '{self.ontology_path}'
        API Specification path: '{self.api_spec_path}'
        </context>

        <steps>
        1. Find the suitable API endpoint for accessing numerical values of entities

        1. Map JSON Entities to ontology Classes.

        2. Decide which relations in the JSON file are 'numeric properties' and 'relational properties'.
            numeric properties are properties that have a numerical value, like temperature, humidity, etc.
            relational properties are properties that have a relation to another entity, like 'is located in', 'has sensor', etc.
        
        2.1 Map the relational properties to ontology properties.
            Do not map the numerical properties to ontology properties.

        2.2 Check if the selected ontology classes for the entities of the numerical properties have an (inherited) numerical property.
        
        2.3 If there are extra nodes to be added, add a new JSON entity to an imagenary list of extra nodes.
            The extra nodes should have the name of the property they come from
            Map this newly created entity to an ontology class by using the query '{{property_name}} (value of {{parentEntity}})'.

        3. Now check again, if the newly created entities have an (inherited) numerical property and do steps 2.2 and 2.3 again before continuing.
        </steps>

        <output>
        Return a JSON, containg:
        - the API endpoint for data access
        - enumeration of the numerical properties and relational properties
        - the mapping of the JSON Entities to ontology classes and properties
        - the name of the properties, that will be added to the JSON Entities as Extra Nodes and the names of the Extra Nodes
        </output>
        
        """

        # SCENARIO PROMPTS ====================================================================

        self.prompt_I = f"""
        {self.jen}
        <context>
        # Results of Preprocessing of the JSON file: \n{self.context_content}
        {self.KG}
        </context>

        <instructions>
        Generate the RDF knowledge graph from the provided JSON Entities data of a GET request to the IoT platform based on the template.
        For every entity in the JSON Entities file and for every Extra Node, create a corresponding entity in the RDF graph.
        For each RDF entity, choose a suitable block from the template and fill out the placeholders with the results of Preprocessing of the JSON file.
        For connecting extra nodes to the parent entities, choose a previously mapped ontology property for relations.
        Use the given prefixes.
        For the 'http://example.com/' URI, do not use a prefix, but use the full URI in angle brackets.

        Do not use any other information to fill out the RDF graph.
        If you have any doubts, fill in a marker at the point and add a comment with your question.
        </instructions>

        <output> Return the knowledge graph in Turtle format. </output>
        """
        # Replace the placeholders in curly brackets in the RDF template with the results of Preprocessing of the JSON file:
        # - The Ontology classes and properties
        # - The correct prefixes from the ontology
        # - The API endpoint for data access
        # - Consider extra nodes as part of the original JSON file

        self.prompt_II = f"""
        {self.jex}
        <context>
        # Results of Preprocessing of the JSON file: \n{self.context_content}
        {self.RML}
        </context>

        <instructions>
        Generate the RML mapping file from the provided JSON Example file needed for generating the knowledge graph based on the template.
        For every entity in the JSON Example file and for every Extra Node, create a corresponding entity in the RML mapping file.
        For each RML entity, choose a suitable block from the template and fill out the placeholders with the results of Preprocessing of the JSON file.
        Do not replace the '{{id}}' but all other placeholders that are in curly brackets AND in uppercase.
        For connecting extra nodes to the parent entities, choose a previously mapped ontology property for relations.
        For every prefix you use in the document, there need to be a corresponding decalaration of the prefix choosen from the Ontology Prefixes input.
 
        Do not use any other information to fill out the RML mapping file.
        If you have any doubts, fill in a marker at the point and add a comment with your question.
        </instructions>

        <output> Return the RML Mapping file in Turtle format. </output>
        """

        self.prompt_IIIc = f"""
        {self.jex}
        <context>
        # Results of Preprocessing of the JSON file: \n{self.context_content}
        {self.PC}
        </context>

        <instructions>
        Generate the Platform Configuration file based on the JSON Example file.
        Consider extra nodes if present. 

        <constraints>
        Ensure all JSONPath expressions use simple, widely supported operators.
        - Allowed: '$', '*', '.'
        - Not allowed: '?', '@', filter expressions
        </constraints>
        </instructions>

        <output> Return the Platform Configuration file in JSON format. </output>
        """

        self.prompt_III = f"""
        {self.jex}
        <context>
        # Results of Preprocessing of the JSON file: \n{self.context_content}
        {self.RNR}
        </context>

        <instructions>
        Fill out the preprocessed Resource Node Relationship Document based on the results of Preprocessing of the JSON file.

        Do not change anything in the Resource Node Relationship Document but the following:

        - For the value of every "class" key: 
            - Ignore any prefilled value and replace it with the mapped Ontology Class for the "nodetype" value of the entity.
        - For the value of every "property" key:
            - Ignore any prefilled value and replace it with the mapped Ontology Property for the "rawdataidentifier" value of the entity.
        - For the value of every "hasdataaccess" key: 
            - Ignore any prefilled value and replace it with string of the correct API endpoint for data access
        
        </instructions>

        <output> Return the Resource Node Relationship Document in JSON format. </output>
        """ # TODO remove self.jex out of prompt

        self.system_default = f"""
        {self.ROLE}
        {self.SYSTEM}
        {self.GOAL}
        {self.OUTPUT_FORMAT}
        """



        # Metrics ====================================================================

        self.HUMAN_EFFORT_METRICS = f"""
        - Difficulty

            - Thinking Quantity (number of total thinking steps needed to do)
            - Thinking complexity (number of cognitive operations required in total)

            - Decision quantity (number of decisions needed to do)
            - Decision complexity (number of options considered when making decisions)

            - Knowledge Prerequisites (amount of required spzialized background knowledge)
            - Working memory load (amount of background information needed to keep in mind)

        - Estimation

            - Duration
            - Cognitive Load (amount of cognitive effort required)
            - Error Potential (Likelihood of making mistakes)
            
        """



    def load_ontology_path(self, ontology_path):
        self.ontology_path = ontology_path
        self.update_variables()

    def load_api_spec_path(self, api_spec_path):
        self.api_spec_path = api_spec_path
        self.update_variables()

    def load_JEN(self, jen_path):
        with open(jen_path, "r") as f:
            self.JEN_content = f.read()
        self.update_variables()

    def load_JEX(self, jex_path):
        with open(jex_path, "r") as f:
            self.JEX_content = f.read()
        self.update_variables()

    def load_context(self, context):
        self.context_content = context
        self.update_variables()

    def load_prefixes(self, prefixes):
        self.prefixes = prefixes
        self.update_variables()

    def load_RNR(self, rnr_path):
        with open(rnr_path, "r") as f:
            self.rnr_content = f.read()
        self.update_variables()

prompts = PromptsLoader()



if __name__ == "__main__":
    # Example usage
    prompts = PromptsLoader()

    # print(prompts.prompt_I)  



    # prompts.load_JSON_files("path/to/jen.json", "path/to/jex.json")
    prompts.load_context("THE CONTEXT IS TOO BIG")
    # prompts.load_RNR_file("path/to/rnr.json")

    # print(prompts.prompt_I)

    # print(prompts.prompts["prompt_I"])  # Print the first prompt



# Claude Prompt Tags ===================================================
"""
Common Claude Prompt Tags:

Input/Output Tags
<input> - Wraps user input data
<output> - Specifies expected output format
<example> - Provides examples of desired behavior
<task> - Defines the specific task to perform

Context and Instructions
<context> - Provides background information
<instructions> - Contains detailed task instructions
<rules> - Specifies constraints and guidelines
<role> - Defines the AI's role or persona
<system> - System-level instructions

Reasoning and Process
<thinking> - Encourages step-by-step reasoning
<analysis> - Requests analytical breakdown
<reasoning> - Shows logical thought process
<steps> - Breaks down tasks into steps

Content Organization
<requirements> - Lists specific requirements
<constraints> - Defines limitations
<format> - Specifies output formatting
<template> - Provides structure templates
<schema> - Defines data schemas

Data and References
<document> - References external documents
<data> - Contains data to process
<source> - References source material
<citation> - For citation requirements

Quality Control
<validation> - Validation criteria
<checks> - Quality checkpoints
<review> - Review instructions
<critique> - Self-critique prompts
"""

# <template> RML
# - for classes and properties, use only the mapped terms from earlier, do NOT find suitable terms on your own!
# - use the correct prefixes for the ontology classes and properties
# - instead of using <#> syntax for mapping names, declare an example namespace
# - the logical source should be "placeholder.json"
# - the rdf:value property should have the correct API endpoint as object but without angle brackets around URI
# - establish proper relationships between entities through rr:parentTriplesMap and rr:joinCondition
# - do not use spaces in filter expressions and use single and double quotes like this:'$[?(@.type=="name")]'
# - use 'a rr:TriplesMap ;' declerations
# </template>



# <template> RDF
# For the RDF graph to properly support configuration generation, the following elements are essential:

# 1. Accurate Entity Classification
# - Entities must map to correct ontology classes
# - You can use the prefix `http://example.com/` for entities that are not in the ontology
# - But use the correct prefixes from the input

# 2. Complete Data Access Information
# - Each entity that has a numerical value property in the JSON, needs a value property in the knowledge graph.
# - For this, use the ontology property `rdf:value` everytime.
# - For the object, instead of a literal number use an URI to the IoT-platform API endpoint for data access
# - This URI to the IoT-platform API should not contain a prefix, but be a complete URI in angle brackets

# 3. Proper Relationship Structure
# - Relationships between entities that are not numerical values must use correct ontology predicates 
# - System hierarchies must be properly represented
# - The datamodel must be represented correctly
# - Devices must be properly connected to their locations (e.g., sensors to rooms)

# 4. Prefix Usage
# - Use syntactically correct prefixes for URIs
# </template>