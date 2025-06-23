

HOST_PATH = "https://fiware.eonerc.rwth-aachen.de/" # TODO put into setup

kg_template_string = """<rules>
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

</rules>""".strip()





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
        </system>"""
        self.OUTPUT_FORMAT = f"""<output>
        Put the relevant output data in <output> tags.</output>
        """

        
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

        <data>\n{self.prefixes}\n</data>
        {kg_template_string}
        """ # <template>\n{self.templates["rdf"]}\n</template>

        self.RML = f"""
        # RML Mapping File 
        The RML mapping file is used to generate the RDF knowledge graph from the JSON Entities data.

        The knowledge graph looks like this: \n{self.KG}

        <constraints>MOST IMPORTANT: RML should follow a valid turtle syntax!</constraints>
        <data>\n{self.prefixes}\n</data>
        <template>\n{self.templates["RML"]}\n</template>
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

        self.term_mapping = f"""
        <term_mapping_instructions>
        <instructions>
        Based on the extraction of available Ontology Classes and Properties and
        the list of terms that need to be mapped to the ontology,
        for each term, you need to select the most appropriate ontology class or property for the domain entity or relation.
        The goal is to inherit the attributes and relations from the selected Ontology Class or Property.

        MAPPING CRITERIA: (in order of priority)
        1. Exact semantic match
        2. Functional equivalence (same purpose/behavior)
        3. Hierarchical relationship (parent/child concepts)
        4. Attribute similarity (same properties/characteristics)

        SPECIAL CONSIDERATIONS:
        - Distinguish locations, air systems, devices, actuation points, sensors
        - Avoid category errors: don't confuse the thing itself with infrastructure that supports the thing

        JUST FOR CLASSES:
        - Respect system hierarchies (building → floor → room → equipment)
        - When the Domain Entity seems to be a relation, select a class that would have this relation as a property.

        JUST FOR PROPERTIES:
        - Maintain the direction of the relationship original (subject → predicate → object), e. g.: is_instance_of NOT EQUAL TO is_instanciated_by
        </instructions>
        </term_mapping_instructions>
        """

        self.context = f"""
        <context>
        {self.jex}
        API Specification path: '{self.api_spec_path}'
        Ontology path: '{self.ontology_path}'
        Term Mapping Instructions: 
        {self.term_mapping}
        </context>

        <steps>
        1. Based on the extraction of available API endpoints, select the single most relevant endpoint for accessing numerical values of entities.

        1. Map JSON Entities to ontology Classes considering the Term Mapping Instructions.

        2. Decide which relations in the JSON file are 'numeric properties' and 'relational properties'.
            numeric properties are properties that have a numerical value, like temperature, humidity, etc.
            relational properties are properties that have a relation to another entity, like 'is located in', 'has sensor', etc.
        
        2.1 Map the relational properties to ontology properties.
            Do not map the numerical properties to ontology properties.

        2.2 Check if the selected ontology classes for the entities of the numerical properties have an (inherited) numerical property.
        
        2.3 If there are extra nodes to be added, add a new JSON entity to an imagenary list of extra nodes.
            The extra nodes should have the name of the property they come from
            Map this newly created entity to an ontology class by using the query '{{property_name}}'.

        3. Now check again, if the newly created entities have an (inherited) numerical property and do steps 2.2 and 2.3 again before continuing.
        </steps>

        <output>
        Return a JSON, containg:
        - the API endpoint for data access merged with the host path
        - enumeration of the numerical properties and relational properties
        - the mapping of the JSON Entities to ontology classes and properties
        - the name of the properties, that will be added to the JSON Entities as Extra Nodes and the names of the Extra Nodes and their mapped ontology classes.
        </output>
        
        """ 
        # TODO improve prompt:
        # give template for output?
        # Continue, if there are no more extra nodes left to add. When iterating over the same object, adjust the query 
        # adding the query: using the query '{{property_name}} (value of {{parentEntity}})'


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
        Preserve and use the complete id from the JEN in the KG.
        For each RDF entity, choose a suitable block from the template and fill out the placeholders with the results of Preprocessing of the JSON file.
        For connecting extra nodes to the parent entities, choose a previously mapped ontology property for relations.
        Use the given prefixes.
        For the 'http://example.com/' URI, do not use a prefix, but use the full URI in angle brackets.

        Do not use any other information to fill out the RDF graph.
        If you have any doubts, fill in a marker at the point and add a comment with your question.
        </instructions>

        <output> Return the knowledge graph in Turtle format. </output>
        """
        # Explain Extra Nodes:
        # Extra Nodes always have numerical value property, but their parent does not.
        # They are created to represent properties that are not numerical values, but still need to be represented in the RDF graph.


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
            - If entity has a numerical property: Ignore any prefilled value, replace it with a string of the correct API endpoint for data access
        
        </instructions>

        <output> Return the Resource Node Relationship Document in JSON format. </output>
        """ # TODO remove self.jex out of prompt?

        self.system_default = f"""
        {self.ROLE}
        {self.SYSTEM}
        {self.GOAL}
        {self.OUTPUT_FORMAT}
        """



        # Metrics ====================================================================

        # depricated
        self.bloom_taxonomy = f"""
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
        """

        self.bloom_descriptions = f"""
        # Bloom's Taxonomy Categories:
        1. Knowledge: Remembering or retrieving previously learned material. Examples of verbs that relate to this function are: know identify relate list  define recall memorize repeat  record name recognize acquire
        2. Comprehension: The ability to grasp or construct meaning from material. Examples of verbs that relate to this function are: restate locate report recognize explain express  identify discuss describe discuss review infer  illustrate interpret draw represent differentiate conclude
        3. Application: The ability to use learned material, or to implement material in new and concrete situations. Examples of verbs that relate to this function are: apply relate develop translate use operate  organize employ restructure interpret demonstrate illustrate  practice calculate show exhibi
        4. Analysis: The ability to break down or distinguish the parts of material into its components so that its organizational structure may be better understood. Examples of verbs that relate to this function are:  analyze compare probe inquire examine contrast categorize  differentiate contrast investigate detect survey classify deduce  experiment scrutinize discover inspect dissect discriminate separate
        5. Synthesis: The ability to put parts together to form a coherent or unique new whole. Examples of verbs that relate to this function are: compose produce design assemble create prepare predict modify tell  plan invent formulate collect set up generalize document combine relate  propose develop arrange construct organize originate derive write propose
        6. Evaluation: The ability to judge, check, and even critique the value of material for a given purpose. Examples of verbs that relate to this function are: judge assess compare evaluate conclude measure deduce  argue decide choose rate select estimate  validate consider appraise value criticize infer
        """

        self.knowledge_dimensions = f"""
        # Knowledge Dimensions:
        - Factual Knowledge: is knowledge that is basic to specific disciplines. This dimension refers to essential facts, terminology, details or elements students must know or be familiar with in order to understand a discipline or solve a problem in it.  
        - Conceptual Knowledge: is knowledge of classifications, principles, generalizations, theories, models, or structures pertinent to a particular disciplinary area.  
        - Procedural Knowledge: refers to information or knowledge that helps students to do something specific to a discipline, subject, or area of study. It also refers to methods of inquiry, very specific or finite skills, algorithms, techniques, and particular methodologies.  
        - Metacognitive Knowledge: is the awareness of one’s own cognition and particular cognitive processes. It is strategic or reflective knowledge about how to go about solving problems, cognitive tasks, to include contextual and conditional knowledge and knowledge of self.
        """

        self.quantity = f"""
        # Quantity 
        In the step description, consisting of a verb that describes the action and the targets of the action, the quantity is the count of all targets of the action.
        **Target Identification Rule**: The targets should be the actual objects being processed, created, or manipulated by the action, not the container or context.
        Examples:
        - "parsing 5 JSON objects": quantity = 5 (cognitive operation: "parse", target: "JSON objects", not the file containing them)
        - "applying a rule to 10 data points": quantity = 10 (cognitive operation: "apply validation rule", target: "data points", not the rule)
        Quantity should enable meaningful comparison across different granularity levels.
        """
        # The number of identical repetitions of this exact step needed to process all objects of attention in the task.
        # Count only direct repetitions of the same cognitive operation, not variations or different steps.


        self.human_effort_index = f"""
        # Human Effort Index
        Evaluation of the effort of a qualified expert required to complete this step.
        Based on own evaluation considering the following factors:
        - The amount of cognitive load required to complete this step
        - The amount of time needed to complete this step
        (from 1 to 100, where 1 is very easy and 100 is very hard)
        Provide a short reasoning for the score.
        It is crucial to provide a score that is comparable to other steps in the task.
        The proportion of the score between two steps should reflect the proportion of the effort required to complete the steps.
        """.strip()
        # TODO reference Bloom Class and Knowledge Dimension as base of the human effort index

        self.scope_complexity = f"""
        """

        self.abtraction_level = f"""
        """



        # Pointwise 
        self.cot_extraction = f"""
        <context>
        {self.bloom_descriptions}
        {self.knowledge_dimensions}
        {self.quantity}
        {self.human_effort_index}
        </context>

        <instructions>
        Do the task step by step with maximum consistency and precision.
        I need a complete step-by-step execution of the task, where each step is fully printed out, even if repetitive, for future analysis and evaluation.

        ### CRITICAL STEP DEFINITION RULES
        Each step must satisfy ALL of these criteria:
        - **Single Action**: Performs exactly one distinct cognitive operation
        - **Single Bloom Level**: Can be classified with exactly one Bloom's Taxonomy category
        - **Single Output**: Produces exactly one concrete, measurable result
        - **Atomic**: Cannot be meaningfully subdivided while maintaining the same cognitive operation
        - **Isolated**: Can be completed without simultaneous work on other steps
        - **Deterministic**: Same input always produces same type of output
        - A step is not a decision what to do next
        
        ### STEP VALIDATION CHECKLIST
        Before finalizing any step, verify:
        1. Can you identify exactly one primary verb that describes the action?
        2. Does the step require only one type of cognitive process?
        3. If you removed any part of this step, would the remaining part still be meaningful?
        4. Can you complete this step without starting the next one?

        If any answer is "no", subdivide the step further.

        
        ### FLOWCHART NAVIGATION RULES
        - Each step must correspond to exactly one node in the flowchart.
        - Not every flowchart node must be a step.
        - Decision diamonds are not steps, but only used to decide which step to take next.
        - Decision diamonds can only be referenced in the "NEXT" section of a step.


        ### EXECUTION PROTOCOL

        #### Phase 1: Task Analysis and Flowchart Creation
        1. Analyze the task complete requirements, instructions and constraints.
        2. Identify all process nodes and possible decision points and alternative paths.
            - If a node has multiple possible next steps, use a decision diamond to represent the decision point.
            - If a node may not be executed every time, use a decision diamond to be able to decide if the node is executed or not (e. g. because of conditional rules).
        3. Create a flowchart to visualize the conditional task structure.
        4. Estimate the number of steps needed to complete the task.
            - Consider the flowchart process nodes and decision points on how to process the input data
            - Consider the number of times to loop the flowchart over the input data

            
        #### Phase 2: Step-by-Step Execution
        Remember: Execute the task following the flowchart process nodes and decision points, repeating the steps with the input data as needed.
        Process exactly ONE step at a time following this format: 

        STEP [N]: [verb (optionally plus descriptive noun) that describes the step action] [quantity] [the targets of the action]
        - flowchart_node: [exact node name from flowchart]
        - context: [explicit information needed for this step only]

        EXECUTING:
        [Perform the actual work - show code, calculations, analysis, etc.]

        VALIDATION:
        - single_bloom_check: [confirm if this step uses only one Bloom level]
        - subdivision_check: [confirm if this cannot be meaningfully subdivided]
        - step_validation_checklist: [confirm if all validation criteria are met]

        EVALUATION:
        - bloom: [single level] - [specific objective in max 7 words]
        - dim: [single Knowledge Dimension]
        - quantity: [the count of the noun that describes the target of the action]
        - human_effort: [1-100 score] - [brief reasoning]

        NEXT: STEP [N+1]: [Next Action Description]
        [if applicable, decide next step based on flowchart]
        - decision_point: [if applicable, specify the decision point]
        - next_flowchart_node: [if applicable, specify the next node in flowchart]



        #### Phase 3: Consistency Verification
        After completing all steps, verify:
        - All steps are represented in flowchart process nodes
        - No steps combine multiple Bloom levels
        - Similar cognitive operations have consistent granularity
        - Quantity measurements are meaningful for comparison

        ### ERROR PREVENTION RULES
        - **Multi-Bloom Detection**: If you find yourself using "and" or "then" in a step description, subdivide it
        - **Multiple Tasks**: If you find multiple tasks in the same step, subdivide them into separate steps
        - **Granularity Consistency**: Steps handling similar data types should have similar granularity
        - **Missing Intermediate Steps**: If there's a logical gap between steps, add the missing step
        - Does the number of steps match the estimated number of steps needed to complete the task?

        </instructions>

        <output>
        ### OUTPUT FORMAT
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
        </output>

        <verification>
        Total Steps: [count]
        Flowchart Compliance: [yes/no - if all steps are represented in flowchart process nodes]
        Bloom Consistency: [yes/no - if all steps use only one Bloom level]
        Granularity Check: [yes/no - if all steps have consistent abstraction level]
        </verification>

        """
        # TODO adjust prompt

        # 4. For each process node (not decision diamond), specify:
            # - Expected Bloom Taxonomy level
            # - Expected Knowledge Dimension
            # - Brief description of the cognitive operation
        # {"[Include Bloom/Knowledge Dimension for each process node]" if False else ""}


        # - In your thinking, include the requirements for a human to be able to output the same result and put the answer in <thinking> tags., e. g.:
        # Prompt: Complete the pattern: 1, 2, 4, 7, ...
        # Response: <output>11</output><thinking> - Basic arithmetic skills (addition and subtraction). - Pattern recognition abilities, specifically recognizing changes between numbers. - Logical thinking to identify the alternating difference pattern. </thinking>
        # </output>"""

        # Tree of Thought specific prompting
        # Output possible next steps, Count number of options



        div = f"""
        In <steps> tags, return a JSON object in which the steps and their Bloom's Taxonomy category (bloom) and Knowledge Dimension (dim) and how many times this same step needs to be repeated to process all items (quantity).
        The triviality score is based on your own evaluation of the step, where 0 is trivial at all and 5 is the most complex.
        Also add the Result of the substep in JSON format, if applicable.
        Example:
        [
            {{
                "step": "Step Name",
                "bloom": "Understanding",
                "dim": "Factual Knowledge",
                "quantity": 1,
                "triviality_score": 0,
                "result": "Result of the step"
            }},
            {{
                "step": "Step Name",
                "bloom": "Applying",
                "dim": "Conceptual Knowledge",
                "quantity": 2,
                "triviality_score": 0,
                "result": "Result of the step"
            }}
        ]
        </output>
        """
          

        self.step_definition = f"""
        I want to use a standardized way to evaluate the difficulty of the task in order to compare it with other tasks.
        Therefore it is essential to follow the given definition of steps

        A step is valid if it meets all of the following:
        - Acts on exactly one conceptual target: entity, property, relationship, path, or configuration key.
        - Performs one logical action: mapping, transformation, ...
        - Is invariant across domain context
        - Can be counted and evaluated independently

        A step is defined as something that can be categorized into a Bloom's Taxonomy category and a Knowledge Dimension and that is not devidable into smaller steps that can be categorized as well.
        Consecutive steps that can be categorized into the same Bloom's Taxonomy category and Knowledge Dimension, can NOT be put in one step.
        Steps that are done multiple times with different conceptual targets, are counted as multiple steps.
        </instructions>
        """
        # self.OUTPUT_FORMAT += self.cot_extraction_est

        self.predefined_steps = f"""
        <context>
        Predefined Tasks:
        - For each entity in the JSON file, 
            - choose a template block
            - fill out the placeholders
            - Create RDF triples for the entity
        - For each extra node in the JSON file,
            - choose a template block
            - fill out the placeholders
            - Create RDF triples for the entity
        </context>
        <instructions>
        Do the predefined subtasks step by step.
        In <steps> tags, return a JSON object in which the steps and the explicit results of this steps are listed.
        </instructions>
        <output>
        Return a JSON object with the following structure:
        {{
            "steps": [
                {{
                    "step": "Map Hotel Term",
                    "quantity": 1,
                    "number_of_decisions": 1,
                    "number_of_options": 10,
                    "step_result": "rec:Room"
                }},
                ...
            ]
        }}
        </output>
        """

        
        
        # HUMAN EFFORT METRICS ================================================================
        # Top Level
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
        

        output:
        - what is the difficulty here?
        - challenges? trade-offs? struggles? where did you needed to think?
        - which mistakes would a dumb human make?


        use vocab for prompt:
        - choose
        - compose
        - classify
        - requiers expert knowledge
        - straight forward
        - semantic disambiguation / Ambiguity or uncertainty
        - reasoning
        - interpretation

        cognitive effort (how hard something was)
        uncertainty or complexity
        decisions made or alternatives considered
        what required extra modeling or attention

        Prompt Design Principles:
        ✅ Explicitly ask for reflections on difficulty
        ✅ Ask the model to note challenges, decisions, or trade-offs
        ✅ Request structured reasoning per entity or component
        ✅ Use consistent formatting so it's easy to parse later


        Let LLM output thinking in this vocab
        --> count words (e. g. decision points)

        specified <thinking> output template defined

        + addition:
        let LLM evaluate its own thinking and decisions and give score right away

            
        """

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


