
import textwrap

class PromptsLoader:
    """
    A class to load prompts and templates from files.
    """

    # LOAD FILES =====================================================================
    def __init__(self):

        self.template_paths = {
            "rdf" : "LLM_eval/templates/rdf_template.ttl",
            "RML" : "LLM_eval/templates/rml_template.ttl",
            "config" : "LLM_eval/templates/platform_config_template.json",
            "context" : "LLM_eval/templates/context_template.json"
        }
        self.templates = {}
        for key, path in self.template_paths.items():
            with open(path, "r") as f: 
                self.templates[key] = f.read()

        # IN-BETWEEN VARIABLES ================================================================

        self.ontology_path = None
        self.api_spec_path = None
        self.host_path = "https://fiware.eonerc.rwth-aachen.de/" # default

        self.result_folder = None

        self.JEX_content = None

        self.context_content = None
        self.prefixes = None

        self.rnr_content = None
        self.PC_content = None

        self.update_variables()


    def update_variables(self):

        # SYSTEM CONTEXT PROMPT ==================================================================
        self.ROLE = textwrap.dedent(f"""<role>
        You are a semantic web engineer specializing in IoT knowledge graph development for building automation systems. 
        You work systematically, following established semantic web standards and best practices.
        </role>""")
        self.SYSTEM = textwrap.dedent(f"""<system>
        - Be precise and concise.
        - You may use tools, only call them when needed, then you will receive its output in the next interaction.
        </system>""")
        self.OUTPUT_FORMAT = textwrap.dedent(f"""<output>
        Put the relevant output data in <output> tags. Avoid URL-encoded characters.
        </output>""")

        self.system_default = textwrap.dedent(f"""
        {self.ROLE}
        {self.SYSTEM}
        {self.OUTPUT_FORMAT}
        """).strip()



        
        # INPUT FILES ================================================================

        self.jex = textwrap.dedent(f"""<input> 
        # JSON EXAMPLE FILE
        The JSON Example file is a sample data file that contains all unique entity types of the JSON response of a GET request to the API of an IoT platform.
        It represents the data structure of the literal entities of a building and its systematic components, available sensors and actuators, but with only one instance of each entity type.
        content: <data>\n{self.JEX_content}</data>
        </input>""")





        # CONTEXT PROMPTS ================================================================

        term_mapping_instructions = textwrap.dedent(f"""
        # TERM MAPPING INSTRUCTIONS: 
        <instructions>
        Based on the extraction of available Ontology Classes and Properties and the list of terms that need to be mapped to the ontology,
        for each term, you need to select the most appropriate ontology class or property for the domain entity or relation.
        Do not choose a class or property that is not in the list of available ontology classes or properties.
        The goal is to inherit the attributes and relations from the selected Ontology Class or Property.

        MAPPING CRITERIA: (in order of priority)
        1. Exact semantic match
        2. Hierarchical relationship (parent/child concepts)
        3. Functional equivalence (same purpose/behavior)
        4. Attribute similarity (same properties/characteristics)

        SPECIAL CONSIDERATIONS:
        - Distinguish locations, systems, devices, actuation points, sensors
        - Avoid category errors: don't confuse the thing itself with top-level infrastructure that supports the thing

        JUST FOR CLASSES:
        - Respect system hierarchies (building → floor → room → equipment)
        - If the term seems to be a relation, select a class that would have this relation as a property.

        JUST FOR PROPERTIES:
        - Maintain the original direction of the relationship (subject → predicate → object), e. g.: is_instance_of NOT EQUAL TO is_instanciated_by
        </instructions>
        """)

        self.context = textwrap.dedent(f"""
        <context>
        {self.jex}
        {term_mapping_instructions}
        </context>

        <instructions>
        You need to examine the available API endpoints and identify the most specific endpoint which returns only the raw numerical values of entity attributes.
        Merge the API endpoint with the host path to create a complete API endpoint URL.
        
        Each top-level object in the JSON file represents an entity, having a unique identifier.
        The key of the unique identifier that is equal across all entities, should be outputted as identifier_key.

        Each top-level object can be described by a specific class, which is then represented by an ontology class.

        # SEMANTIC-DRIVEN CLASS KEY SELECTION:
        Analyze all keys that appear in all top-level objects and evaluate their semantic contribution:

        Select class_keys by choosing keys that:
        - Provide meaningful semantic distinction between entities
        - Help differentiate entities that would otherwise appear similar
        - Contribute to more precise ontology class mapping
        - Create classes that represent distinct functional or behavioral categories
        
        Avoid keys that only provide:
        - Pure metadata (timestamps, IDs, technical configuration)
        - Values that change frequently (current states, measurements)
        - Implementation details that don't affect semantic meaning

        The combination of selected class_keys should create semantically meaningful and distinct entity classes.


        The class of the top-level object is a string that contains the values of the class_keys joined by underscores in senseful order.
        For each top-level object in the JSON (unique value of class_keys) retrieve suitable ontology classes.
        Use the Term Mapping Instructions to select the most appropriate ontology classes.

        Each entity can have multiple properties, which are represented as key-value pairs inside a top-level object in the JSON file.

        Within the JSON structure, you'll encounter properties that define relationships between top-level objects (such as location associations, containment relationships, or other connections). 
        These relational properties should be mapped to appropriate ontology properties.
        The ontology structure should represent the relatonships between top-level objects through relational properties.

        Within the JSON structure, you'll encounter entities, that can have a numerical value (accesible by the API endpoint).
        You need to make sure, that those entities that need to have a numerical value in the JSON, also can have a numerical value in the ontology.
        Therefore you need to check if the selected ontology class for the entity having a numerical value supports having a numerical property, either directly or through inheritance.
        
        If gaps exist and additional structural elements are needed, create supplementary entities to fill these gaps, creating a valid connection of the original entity and a numeric property.
        
        If there are the newly created entities (extra nodes), they need to be mapped to ontology classes as well.
        It should be ensured that these new ontology classes now have the numerical property capabilities, either directly or through inheritance.
        The entire structure requires assessment to ensure all numerical property requirements are properly addressed. This verification and enhancement process should continue until the mapping is complete and all numerical values have appropriate ontological representation.

        In the JSON file, the added extra nodes are connected to the parent entities through a relation.
        Find an ontology property for the relation of the extra node to the parent entity. 
        Pay attention to the direction of the property to be from the extra node TO the parent entity (extra node → parent entity)!
        Use the term_mapper tool with an appropriate query.
        If there are no extra nodes, leave empty.
        </instructions>

        <output>{self.templates['context']}</output>
        
        """)


        # PROMPTS ====================================================================
        # SCENARIO III
               
        PC_template = f"<template>\n{self.templates['config']}\n</template>"
        PC_content = f"Content: <data>{self.PC_content}</data>"
        self.PC = textwrap.dedent(f""" 
        # PLATFORM CONFIGURATION FILE
        The configuration file should contain the following information:
        - The ID_KEY is the key in the JSON data that uniquely identifies each entity and is equal to the identifier_key in the context
        - The TYPE_KEYS are the keys in the JSON data that identify the type of each entity and is equal to the class_keys in the context
        - The JSONPATH_EXTRA_NODES are the JSONpath Expressions to the {{EXTRA_NODES}} that should be included in the mapping. 
                                  
        <constraints>
        Ensure all JSONPath expressions use simple, widely supported operators. Note the type of the root level object in the JSON file. 
        - Allowed: '$', '*', '.'
        - Not allowed: '?', '@', filter expressions
        </constraints>
        
        Terms in brackets {{}} are placeholders for values given in the context. Strictly choose the values from the preprocessing of the JSON file, except for the variables inside API_ENDPOINT_URL, which can be adapted to match the use case.

        {PC_content if self.PC_content else PC_template}
        """) # Use the recursive descent operator

        
        self.RNR = textwrap.dedent(f"""
        # RESOURCE NODE RELATIONSHIP DOCUMENT
        The RML Mapping file can be generated automatically based on a validated Resource Node Relationship Document.
        The Resource Node Relationship Document is a prefilled document that contains the necessary information to generate the RML Mapping file.
        
        content: <data>\n{self.rnr_content}</data>
        """)


        self.prompt_IIIc = textwrap.dedent(f"""
        <context>
        {self.jex}
        # RESULTS OF PREPROCESSING OF THE JSON FILE: \n{self.context_content}
        {self.PC}
        </context>

        <instructions>
        Generate the Platform Configuration file based on the JSON Example file.
        Consider extra nodes if present in the context. 
        </instructions>

        <output> Return the Platform Configuration file in JSON format.</output>
        """)

        self.prompt_III = textwrap.dedent(f"""
        <context>
        {self.jex}
        # RESULTS OF PREPROCESSING OF THE JSON FILE: \n{self.context_content} \n The mapping of the relatedTo relation to the ontology property is {self.context_content['extra_node_relation_to_parent'] if self.context_content else 'value of extra_node_relation_to_parent key'}.
        {self.PC}
        {self.RNR}
        </context>

        <instructions>
        Fill out the preprocessed Resource Node Relationship Document based on the results of Preprocessing of the JSON file.

        Preserve the structure and strictly do not change ANYTHING in the Resource Node Relationship Document except:
        - For the value of every "class" key: 
            - Ignore any prefilled value and replace it with the mapped {{ONTOLOGY_CLASS}} for the "nodetype" value of the entity.
        - For the value of every "property" key:
            - Ignore any prefilled value and replace it with the mapped {{ONTOLOGY_PROPERTY}} for the "rawdataidentifier" value of the entity.
        - For the value of every "hasdataaccess" key: 
            - If entity has a numerical property: Ignore any prefilled value, replace it with the template {{API_ENDPOINT_URL}} and adapt its variables to match the attribute of this entity and '{id}' instead of the ID_KEY for the API call.
            - If an entity has an associated extra node, fill out the API_ENDPOINT_URL just for the extra node, not for the original entity.
        Terms in brackets {{}} are placeholders for values given in the context. Strictly choose the values from the preprocessing of the JSON file, except for the variables inside API_ENDPOINT_URL, which can be adapted to match the use case.
        </instructions>

        <output> Return the Resource Node Relationship Document in JSON format.</output>
        """)
    



        

    def load_prefixes(self, ontology_path):
        with open(ontology_path, 'r', encoding='utf-8') as f:
            ontology_lines = f.readlines()

        prefixes_list = ["Ontology prefixes:"]
        for line in ontology_lines:
            line = line.strip()
            if line.startswith('@prefix') or line.startswith('PREFIX'):
                prefixes_list.append(line)
            elif line and not line.startswith('#') and not line.startswith('@prefix') and not line.startswith('PREFIX'):
                break

        self.prefixes = '\n'.join(prefixes_list)
        self.update_variables()

    def load_ontology_path(self, ontology_path):
        self.load_prefixes(ontology_path)
        self.ontology_path = ontology_path
        self.update_variables()

    def load_api_spec_path(self, api_spec_path):
        self.api_spec_path = api_spec_path
        self.update_variables()

    def load_JEX(self, jex_path):
        with open(jex_path, "r") as f:
            self.JEX_content = f.read()
        self.update_variables()

    def load_context(self, context):
        self.context_content = context
        self.update_variables()

    def load_RNR(self, rnr_path):
        with open(rnr_path, "r") as f:
            self.rnr_content = f.read()
        self.update_variables()
    
    def load_PC(self, pc_path):
        with open(pc_path, "r") as f:
            self.PC_content = f.read()
        self.update_variables()

prompts = PromptsLoader()



if __name__ == "__main__":
    print(prompts.cot_extraction)


