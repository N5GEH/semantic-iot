from pathlib import Path
import textwrap


class PromptsLoader:
    """
    A class to load prompts and templates from files.
    """

    # LOAD FILES =====================================================================
    def __init__(self):

        root_path = Path(__file__).parent.parent.parent
        self.template_paths = {
            "rdf": str(Path(root_path, "LLM_eval/templates/rdf_template.ttl")),
            "RML": str(Path(root_path, "LLM_eval/templates/rml_template.ttl")),
            "config": str(Path(root_path, "LLM_eval/templates/platform_config_template.json")),
            "context": str(Path(root_path, "LLM_eval/templates/context_template.json")),
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

        self.JEN_content = None
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
        self.GOAL = textwrap.dedent(f"""<context>
        # Controller Configuration file
        The overall goal is to generate a configuration for a building's ventilation system based on the available sensors and actuators.

        Requirements for the configuration file based on the SPARQL queries:
        1. List of all rooms in the building (identified by their URIs).
        2. For each room:
            - All ventilation devices (Air Systems) associated with the room.
                - For each device: 
                    - All actuation points (e.g., setpoints, commands) and their access methods/values.
            - All CO2 sensors available in the room, including their access methods/values.
            - All presence sensors available in the room, including their access methods/values.

        The configuration file must map each room to its available sensors and actuators, specifying how to access their data or control them.

        This is done by querying a extended knowledge graph with SPARQL to extract information about the building's systematic components, like:
        - Which rooms are available in the building?
        - Which ventilation devices are available in each room?
        - How to access the actuation points of each ventilation device?

        # Extended Knowledge Graph file
        The extended knowledge graph is based on the original knowledge graph and includes additional classes and properties from a given ontology.
        The additional classes and properties are being created through inheritance from the ontology classes or properties.
        </context>""")


        self.system_default = textwrap.dedent(f"""
        {self.ROLE}
        {self.SYSTEM}
        {self.GOAL}
        {self.OUTPUT_FORMAT}
        """).strip()




        # COT EXTRACTION TEXT ================================================================

        BLOOM_DESCRIPTIONS = textwrap.dedent(f"""
        # BLOOM'S TAXONOMY LEVELS
        1. Knowledge: Remembering or retrieving previously learned material. 
            Examples of verbs that relate to this function are: identify, relate, list, define, recall, memorize, repeat, record, name, recognize, acquire
        2. Comprehension: The ability to grasp or construct meaning from material. 
            Examples of verbs that relate to this function are: restate, locate, report, recognize, explain, express, identify, discuss, describe, discuss, review, infer, illustrate, interpret, draw, represent, differentiate, conclude
        3. Application: The ability to use learned material, or to implement material in new and concrete situations.
            Examples of verbs that relate to this function are: relate, develop, translate, use, operate, organize, employ, restructure, interpret, demonstrate, illustrate, practice, calculate, show, exhibit
        4. Analysis: The ability to break down or distinguish the parts of material into its components so that its organizational structure may be better understood. 
            Examples of verbs that relate to this function are: compare, probe, inquire, examine, contrast, categorize, differentiate, contrast, investigate, detect, survey, classify, deduce, experiment, scrutinize, discover, inspect, dissect, discriminate, separate
        5. Synthesis: The ability to put parts together to form a coherent or unique new whole. 
            Examples of verbs that relate to this function are: compose, produce, design, assemble, create, prepare, predict, modify, tell, plan, invent, formulate, collect, set up, generalize, document, combine, relate, propose, develop, arrange, construct, organize, originate, derive, write, propose
        6. Evaluation: The ability to judge, check, and even critique the value of material for a given purpose. 
            Examples of verbs that relate to this function are: judge, assess, compare, conclude, measure, deduce, argue, decide, choose, rate, select, estimate, validate, consider, appraise, value, criticize, infer
        """)

        KNOWLEDGE_DIMENSIONS = textwrap.dedent(f"""
        # KNOWLEDGE DIMENSIONS
        - Factual Knowledge: is knowledge that is basic to specific disciplines. This dimension refers to essential facts, terminology, details or elements students must know or be familiar with in order to understand a discipline or solve a problem in it.  
        - Conceptual Knowledge: is knowledge of classifications, principles, generalizations, theories, models, or structures pertinent to a particular disciplinary area.  
        - Procedural Knowledge: refers to information or knowledge that helps students to do something specific to a discipline, subject, or area of study. It also refers to methods of inquiry, very specific or finite skills, algorithms, techniques, and particular methodologies.  
        - Metacognitive Knowledge: is the awareness of one’s own cognition and particular cognitive processes. It is strategic or reflective knowledge about how to go about solving problems, cognitive tasks, to include contextual and conditional knowledge and knowledge of self.
        """)

        QUANTITY = textwrap.dedent(f"""
        # QUANTITY 
        The quantity is the count of all targets of the action. The targets should be the actual objects being processed, created, or manipulated by the action, not the container or context.
        Examples:
        - "parsing 5 JSON objects": quantity = 5 (cognitive operation: "parse", target: "JSON objects", not the file containing them)
        - "applying a rule to 10 data points": quantity = 10 (cognitive operation: "apply validation rule", target: "data points", not the rule)
        Quantity should enable meaningful comparison across different granularity levels.
        """)

        HUMAN_EFFORT_INDEX = textwrap.dedent(f"""
        # HUMAN EFFORT INDEX
        An evaluation of the effort a human expert would require to complete this step.
        The evaluation is based on the execution of the step (challenges, difficulties, struggles, trade-offs).
        Provide a brief explanation of the challenges encountered during execution and explain the reasoning behind the score.
        Rate the effort of this step on a scale from 1 to 100, where:
        - 1-10: Trivial
        - 11-25: Easy
        - 26-40: Moderate
        - 41-60: Intermediate
        - 61-75: Advanced
        - 76-90: Expert
        - 91-100: Extreme

        The proportion of the score between steps should reflect the proportion of the effort required to complete the steps.
        Scores must be comparable across different KG generation tasks.
        """)
        # ... rate the "cognitive" effort of this step ...?
        # and the "context" that was required.

        # COT EXTRACTION PROMPT ================================================================

        self.cot_extraction = textwrap.dedent(f"""
        {self.ROLE}
        <context>
        {BLOOM_DESCRIPTIONS}
        {KNOWLEDGE_DIMENSIONS}
        {QUANTITY}
        {HUMAN_EFFORT_INDEX}
        </context>

        <instructions>
        Do the task step by step with maximum consistency and precision.
        I need a complete step-by-step execution of the task, where each step is fully printed out, even if repetitive, for future analysis and evaluation.
        
        I want to use a standardized way to compare steps across different tasks.
        Therefore it is absolutely essential to follow the given definition of steps:

        
        # STEP DEFINITION

        ## CRITICAL STEP DEFINITION RULES
        Each step must satisfy ALL of these criteria:
        - Single Action: Performs exactly one distinct cognitive operation
        - Single Bloom Level: Can be classified with exactly one level of Bloom's Taxonomy
        - Single Output: Produces exactly one concrete, measurable result
        - Deterministic: Same input always produces same type of output
        - Atomic: Cannot be meaningfully subdivided while maintaining the same cognitive operation
        - Isolated: Can be completed without simultaneous work on other steps
        - Consistent Granularity: Steps handling similar data types should have similar granularity

        - Not an Iteration Counter: Skip actions that simply count iterations, repetitions, nodes of the flowchart process
        - Not a Decision: Does NOT just refers to do another step e. g.: 'Moving to next step'
        
        ## FLOWCHART NAVIGATION RULES
        - Each step must correspond to exactly one node in the flowchart.
        - Not every flowchart node must be a step.
        - Decision diamonds are not steps, but only used to decide which step to take next.
        - Decision diamonds can only be referenced in the "NEXT" section of a step.

        ## STEP VALIDATION CHECKLIST
        Before finalizing any step, verify:
        - Can you identify exactly one primary verb that describes the action?
        - Does the step require only one type of cognitive process?
        - If you removed any part of this step, would the remaining part still be meaningful?
        - Can you complete this step without starting the next one?
        - Does the step granularity match the estimated number of steps needed to complete the task?
        If any answer is "no", subdivide the step further.

        - Do you find yourself using "and" or "then" in a step description?
        - Are there missing steps creating a logical gap between steps?
        If any answer is "yes", subdivide the step further.
        
        
        # EXECUTION PROTOCOL

        ## PHASE 1: Task Analysis and Flowchart Creation
        1. Analyze the task complete requirements, instructions and constraints.
        2. Identify all process nodes and possible decision points and alternative paths.
            - If a node has multiple possible next steps, use a decision diamond to represent the decision point.
            - If a node may not be executed every time, use a decision diamond to be able to decide if the node is executed or not (e. g. because of conditional rules).
        3. Create a flowchart to visualize the conditional task structure.
        4. Estimate the number of steps needed to complete the task.
            - Consider the flowchart process nodes and decision points on how to process the input data
            - Consider the number of times to loop the flowchart over the input data
            
        ## PHASE 2: Step-by-Step Execution
        Execute the task following the flowchart process nodes and decision points, repeating the steps with the input data as needed.
        Process exactly ONE step at a time following this format: 

        STEP [N]: [step description]
        - flowchart_node: [exact node name from flowchart]
        - context: [explicit information needed for this step only]

        EXECUTING:
        [Perform the actual work - show code, calculations, analysis, etc.]

        VALIDATION:
        [briefly confirm if all criteria on the validation checklist are met]

        EVALUATION: [verb (optionally plus descriptive noun) that describes the step action] [quantity] [the targets of the action]
        - bloom: [single level] - [specific objective in max 5 words] - [verb choosen from Bloom's Taxonomy levels examples of verbs relating to the function]
        - dim: [single Knowledge Dimension] - [specific knowledge type in max 5 words]
        - quantity: [the count of the noun that describes the target of the action] - [the noun that describes the target of the action]
        - human_effort: [1-100 score] - [brief reasoning] - [score description word from 1-100 scale]

        NEXT: STEP [N+1]: [Next Action Description]
        [if applicable, decide next step based on flowchart]
        - decision_point: [if applicable, specify the decision point]
        - next_flowchart_node: [if applicable, specify the next node in flowchart]

        </instructions>

        <output>
        # OUTPUT FORMAT
        Output exactly in this order:

        <flowchart>
        [Flowchart in mermaid syntax showing the process nodes and decision points]
        </flowchart>

        <estimation>
        [Estimated number of times to loop the flowchart over the input data]
        </estimation>

        <steps>
        [Complete step-by-step execution following the format above]
        [Every single step must be fully printed out, even if repetitive - no summarization or skipping]
        </steps>

        <output>
        [Final deliverable result of the task, e.g. JSON, RDF, etc.]
        [The output can only be a composition of the execution results of the steps]
        [Avoid URL-encoded characters]
        </output>
        </output>
        """)

        
      

        
        # INPUT FILES ================================================================

        self.jen = textwrap.dedent(f"""<input>
        # JSON ENTITIES FILE
        This JSON data is a response of a GET request to the API of an IoT platform, 
        which contains all the literal entities of a building and its systematic components, available sensors and actuators. 
        content: <data>\n{self.JEN_content}</data>
        </input>""")

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
        # TODO improve prompt:
        # Continue, if there are no more extra nodes left to add. When iterating over the same object, adjust the query 
        # adding the query: using the query '{{property_name}} (value of {{parentEntity}})'

        # There are one or more keys that appear in all top-level objects which are used to identify or describe the class even if the object seems to be a property.
        # The class should contain the functionality, meaning, description or kind of the top-level object, because it needs to be
        # mapped to an appropriate ontology class, based only on the class. 


        # SCENARIO I, II ====================================================================

        self.KG = textwrap.dedent(f"""
        # KNOWLEDGE GRAPH FILE
        The knowledge graph (KG) is a structured representation of the building's systematic components, including rooms, ventilation devices, sensors, and their relationships. 
        It is built from the provided JSON entities file of a GET request to a specific IoT platform.

        <constraints>MOST IMPORTANT: RDF should follow a valid turtle syntax!</constraints>
        <data>Available prefixes:\n{self.prefixes}\n</data>

        ## Knowledge Graph Generation Instructions
        <instructions>
        The knowledge graph must begin with:
        - A declaration of all {{ONTOLOGY_PREFIXES}} used in the file
        - The standard RDF prefix: @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        - Do not add prefixes for the API endpoint, but use the full URI in angle brackets.
        - Do not use any prefixes for the 'http://example.com/' URI, but use the full URI in angle brackets.

        Every IoT entity and each Extra Node must be declared with:
        - A unique URI following the pattern <http://example.com/{{ENTITY_TYPE}}/{{ID}}>. Preserve and use the complete id from the JSON in the KG.
        - A type classification using a {{ONTOLOGY_CLASS}} selected from the given context

        For an entity having relationships or connections to other entities,
        one or more properties using {{ONTOLOGY_PROPERTY}} and the URI of the entity must be added
        - System hierarchies must be properly represented
        - The datamodel must be represented correctly
        - Devices must be properly connected to their locations

        For an entity or extra node having a numerical property, 
        the property 'rdf:value <{{API_ENDPOINT_URL}}>' must be added. in the {{API_ENDPOINT_URL}} template, adapt its variables to match the attribute of this entity and use the identifier for the API call.
        
        Extra Nodes establish a connection between an entity and a numerical value when the entity's ontology class does not include a numerical property.
        These new entities should derive their names from the properties that necessitated their creation.
        In the JSON file, the numerical values of the entities that map to non_numeric ontology classes must be connected to their corresponding extra nodes.
        If an entity has an associated extra node, link numerical values just to the extra node, not to the original entity.

        Terms in brackets {{}} are placeholders for values given in the context. Strictly choose the values from the preprocessing of the JSON file, except for the variables inside API_ENDPOINT_URL, which can be adapted to match the use case.
        </instructions>
        
        """).strip()

        self.RML = textwrap.dedent(f"""
        # RML MAPPING FILE 
        The RML mapping file is used to generate the RDF knowledge graph from the JSON Entities data.

        The knowledge graph looks like this:
        #{self.KG}

        <constraints>MOST IMPORTANT: RML should follow a valid turtle syntax!</constraints>

        ## RML Mapping Instructions
        <instructions>
        The RML mapping must include the ontology prefixes from the knowledge graph and 
        the RML-specific prefix: @prefix ex: <http://example.com#> .

        Every IoT entity type and each extra node type must have a corresponding TriplesMap declared with
        a unique mapping URI following the pattern ex:Mapping{{ENTITY_TYPE}} and a type classification: a rr:TriplesMap.

        Each TriplesMap must define its data source via rml:logicalSource with 
        the rml:referenceFormulation ql:JSONPath, rml:source "placeholder.json" and an iterator to filter entities by type.
        ### Iterator Constraints <constraints> 
        Put iterator in single quotes.
        Avoid using spaces in the iterator string!
        Ensure all JSONPath expressions use simple, widely supported operators.
        - Allowed: '$', '*', '.'
        - Not allowed: '?', '@', filter expressions
        </constraints>

        Each TriplesMap must define a rr:subjectMap with
        rr:template "http://example.com/{{ENTITY_TYPE}}/{id}" for dynamic URI generation from data and rr:class {{ONTOLOGY_CLASS}} for type classification
        
        For entities that provide or expose numerical data via API endpoint,
        a rr:predicateObjectMap must be added with rdf:value and an objectMap for API endpoint URL with rr:template "{{API_ENDPOINT_URL}}"

        For entities that reference other entities in the data source, 
        a rr:predicateObjectMap must be added with:
        - {{ONTOLOGY_PROPERTY}} as predicate
        - an objectMap referencing rr:parentTriplesMap ex:Mapping{{ENTITY_TYPE}}
        - Join conditions must match the data source field names and structure
        - System hierarchies, the datamodel relationships and devices and their locations must be properly represented through join conditions and their child and parent

        In the JSON file, the added extra nodes are connected to the parent entities through a 'relatedTo' relation, with the parent entity's 'id' as value.
        The according ontology property is the extra_node_relation_to_parent from the context.

        Uppercase terms in brackets {{}} are placeholders for values given in the context. Strictly choose the values from the preprocessing of the JSON file, except for the variables inside API_ENDPOINT_URL, which can be adapted to match the use case.
        For the '{{id}}', use the value of the identifier_key from the context.
        </instructions>


        """)# TODO this ID is not always the same? Depends on platform config?

        # PROMPTS ====================================================================

        self.prompt_I = textwrap.dedent(f"""
        <context>
        {self.jen}
        # RESULTS OF PREPROCESSING OF THE JSON FILE: \n{self.context_content}
        {self.KG}
        </context>

        <instructions>
        Generate the RDF knowledge graph from the provided JSON Entities data of a GET request to the IoT platform based on the Knowledge Graph instructions.        
        Use the results of Preprocessing of the JSON file. Do not use any other information to fill out the RDF graph.
        </instructions>

        <output> Return the knowledge graph in Turtle format. </output>
        """).strip()

        self.prompt_II = textwrap.dedent(f"""
        <context>
        {self.jex}
        # RESULTS OF PREPROCESSING OF THE JSON FILE: \n{self.context_content}
        {self.RML}
        </context>

        <instructions>
        Generate the RML mapping file from the provided JSON Example file needed for generating the knowledge graph based on the RML instructions.
        Do not use any other information to fill out the RML mapping file.
        </instructions>

        <output> Return the RML Mapping file in Turtle format. </output>
        """).strip()


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
        """) # TODO remove self.jex out of prompt?
        # {self.jex} include again?
    



        

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


kg_rules = textwrap.dedent("""<rules>
# Knowledge Graph Rules
For the RDF graph to properly support configuration generation, the following elements are essential:

Rule 1: Entity Declaration
Always: Every IoT entity and each Extra Node must be declared with:
- A unique URI following the pattern <http://example.com/{{ENTITY_TYPE}}/{{ID}}>
- A type classification using a {{ONTOLOGY_CLASS}}

Rule 2: Ontology Prefixes
Always: The knowledge graph must begin with:
- {{ONTOLOGY_PREFIXES}} declaration
- Standard RDF prefix: @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
- Do not add prefixes for the API endpoint, but use the full URI in angle brackets.

Rule 3: Numerical Data Source
If: An entity provides or exposes numerical data (accessible by API endpoint) 
Then: Add the property rdf:value <{{API_ENDPOINT_URL}}>

Rule 4: Relational Connections
If: An entity has relationships or connections to other entities 
Then: Add one or more properties using {{ONTOLOGY_PROPERTY}} <http://example.com/{{ENTITY_TYPE}}/{{ID}}>
- System hierarchies must be properly represented
- The datamodel must be represented correctly
- Devices must be properly connected to their locations (e.g., sensors to rooms)

</rules>""").strip()





rml_rules = textwrap.dedent("""<rules>
# RML Mapping Rules
For the RML mapping to properly transform IoT data sources to RDF triples, the following RML-specific elements are essential:

Rule 1: TriplesMap Structure
Always: Every IoT entity type must have a corresponding TriplesMap declared with:
- A unique mapping URI following the pattern ex:Mapping{{ENTITY_TYPE}}
- A type classification: a rr:TriplesMap

Rule 2: RML-Specific Prefixes
Always: The RML mapping must include RML-specific prefixes:
- {{ONTOLOGY_PREFIXES}} declaration
- Standard prefixes: @prefix ex: <http://example.com#> . and @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
# - Do not add prefixes for the API endpoint, but use the full URI in template strings.

Rule 3: Data Source Configuration
Always: Each TriplesMap must define its data source via rml:logicalSource:
- rml:source "placeholder.json"
- rml:referenceFormulation ql:JSONPath (for JSON data)
- rml:iterator '$[?(@.type=="{{ENTITY_TYPE}}")]' to filter and iterate over entities by type

Rule 4: Subject Template Generation
Always: Each TriplesMap must define a rr:subjectMap with:
- rr:template "http://example.com/{{ENTITY_TYPE}}/{id}" for dynamic URI generation from data
- rr:class {{ONTOLOGY_CLASS}} for type classification

Rule 5: API Endpoint Value Mapping
If: An entity provides or exposes numerical data via API endpoint
Then: Add a rr:predicateObjectMap with:
- rr:predicate rdf:value
- rr:objectMap with rr:template "{{API_ENDPOINT_URL}}" (template-based URI generation)

Rule 6: Cross-Entity Reference Mapping
If: An entity references other entities in the data source
Then: Add a rr:predicateObjectMap with:
- rr:predicate {{ONTOLOGY_PROPERTY}}
- rr:objectMap referencing rr:parentTriplesMap ex:Mapping{{ENTITY_TYPE}}
- rr:joinCondition specifying rr:child "{{CHILD_JOIN_FIELD}}" and rr:parent "{{PARENT_JOIN_FIELD}}"
- Join conditions must match the data source field names and structure
# - System hierarchies must be properly represented through join conditions
# - The datamodel relationships must be correctly mapped
# - Devices must be properly connected to their locations through appropriate join fields

</rules>""")

bloom_taxonomy = textwrap.dedent(f"""
# Bloom's Taxonomy:
- Remembering: {{information}} (Recall information)
- Understanding: {{meaning}} (Constructing meaning from information, e. g.: interpreting, exemplifying, classifying, summarizing, inferring, comparing, or explaining)
- Applying: {{procedure}} (using a procedure through executing, or implementing.)
- Analyzing: {{analysis}} (determine how concept parts relate to each other or how they interrelate, differentiating, organizing, and attributing, as well as being able to distinguish  between the components or parts.)
- Evaluating: {{number of options considered}} (Making judgments based on criteria and standards through checking and critiquing.)
- Creating: {{newly created idea or element}} (generating new ideas or elements. not applicable if content is just a transformation of existing content.)

# Knowledge Dimensions:
- Factual Knowledge: facts, terminology, or syntax needed to understand the domain.
- Conceptual Knowledge: classifications, principles, generalizations, theories, models, or structures pertinent to a particular disciplinary area
- Procedural Knowledge: How to do something, methods of inquiry, specific or finite skills, algorithms, techniques, and particular methodologies
- Metacognitive Knowledge: awareness of own cognition, strategic or reflective knowledge considering contextual and conditional knowledge and knowledge of self.
""")




context_steps = textwrap.dedent(f"""
<steps>
1. Based on the extraction of available API endpoints, select the single most relevant endpoint for accessing numerical values of entities.

1. Map JSON Entities to ontology Classes considering the Term Mapping Instructions.

2. Decide which relations in the JSON file are 'numeric properties' and 'relational properties'.
    numeric properties are properties that have a numerical value, like temperature, humidity, etc.
    relational properties are properties that have a relation to another entity, like 'isLocatedIn', 'belongsTo', etc.

2.1 Map the relational properties to ontology properties.
    Do not map the numerical properties to ontology properties.

2.2 Check if the selected ontology classes for the entities of the numerical properties have an (inherited) numerical property.

2.3 If there are extra nodes to be added, add a new JSON entity to an imagenary list of extra nodes.
    The extra nodes should have the name of the property they come from
    Map this newly created entity to an ontology class by using the query '{{property_name}}'.

3. Now check again, if the newly created entities have an (inherited) numerical property and do steps 2.2 and 2.3 again before continuing.
</steps>
""").strip()