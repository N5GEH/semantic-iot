

import json
from claude import ClaudeAPIProcessor
# from semantic_iot.LLM.RDF_generator_LLM import RDFGeneratorLLM


class RMLGenerator:
    def __init__(self, 
                 input_json_path, 
                 config_path,
                 max_retry: int = 3):
        self.input_json_path = input_json_path
        self.config_path = config_path
        self.used_tokens = []
        self.claude = ClaudeAPIProcessor()
        self.max_retry = max_retry


    def correct_generation(self, error_message):
        '''
        Correct generated content based on error messages.
        '''
        
        prompt = f"""
            The goal of this prompt is the same as the previous one. Now consider the error messages.

            ERROR MESSAGE:
            {error_message}
        """
        
        response = self.claude.query(prompt)
        data = response["content"][0]["text"]
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)

        print("PROMPT: \n", prompt)
        print("DATA: \n", data)
        print("TOKENS: ", tokens)

        return data


    def understanding_json (self):
        with open(self.input_json_path, 'r') as file:
            entities = json.load(file)
        
        with open(self.config_path, 'r') as file:
            config = json.load(file)
        extra_entity_nodes = config.get("JSONPATH_EXTRA_NODES")

        prompt = f"""
            GOAL:
            I will give you a JSON data containing the information of a building and its systematic components. 
            This JSON data is a response of a GET request to the API of an IoT platform, which contains all the
            available sensors and actuators. 

            The overall goal is to convert this data in an RDF Format, consisting of 
            subject, predicate, object. 
            In the following your task is to generate an RML mapping file 
            with which a RDF graph can be generated. The file will be processed with morph_kgc.

            The information contains uniquely identifiable entities.
            Every entity is an instance of a resource type.
            Every entity has a unique identifier, which is a string that is in front of every unique identifier of an entity.
            Every entity has a set of relations. The set could be empty as well.

            A Relation is either 
                one instance connected to another instance with a predicate or
                one instance connected to a value with a predicate, where the value is not part of another Relation
            

            TASKS:
            Act as an expert in knowledge graph creation and data modeling.
            Analyse the provided JSON data structure and indentify:
            1. All unique Resource types
            2. For every Resource types the unique types of Relations
            3. the name of the ...
                ... unique identifier of an entity
                ... unique type of relation that this resource has


            RESPONSE FORMAT:
            Return exclusively a list with two values 
                the first value is a list of two strings from Task 3.
                the second value is a python dictionary object with
                    the resource types as keys and
                    every unique type of relation that this resource has 
                        paired with the actual corresponding values or target resources. Extract actual values for relations (e. g. a number), not just their value type or resource types.
                    and the extra entity nodes as the values of every resource type
            
            Do not return any other text or information. 
            Remain case sensitive. 

            EXAMPLE OUTPUT FORMAT:
            [["unique_id_field", "type_field"], {{
                "ResourceType1": {{
                    "relation1": "value1",
                    "relation2": "ResourceType2"
                }},
                "ResourceType2": {{
                    "relation3": "value3",
                    "relation4": "ResourceType1"
                }}
            }}]
            

            DATA:
            JSON data: {json.dumps(entities, indent=2)}
            Extra Entity Nodes: {extra_entity_nodes}
            
            """
        # Focus on the semantic content of the JSON, not its specific structure
        print("i Waiting for response...")
        response = self.claude.query(prompt)

        data_understanding = response["content"][0]["text"]
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)    

        print(data_understanding)
        print("AI: Response generated")
        return data_understanding

    def validate_understanding (self, data, retry=0):

        # TODO all Entity types?
        # TODO all Relations types?
        # TODO all Extra Entity Nodes?

        # Check if AI makes up words
        print(f"? {retry} Check if AI makes up words")

        with open(self.input_json_path, 'r') as file:
            json_content = file.read().lower()
        
        # TODO get words
        words = {word for word in data.lower().split() if word.replace('_', '').isalpha()}
        # words = set(data.lower().split())
        print(f"Words in response: \n{words}")
        json_words = set(json_content.split())
        print(f"Words in JSON: \n{json_words}")
        missing_words = words - json_words
        
        if missing_words:
            error_message = f"Found words in response not present in JSON: {missing_words}"
            print("!", error_message)

            # TODO check extra entity nodes
            if input("Are those the extra entity nodes? (y/n)") == "n":
                if retry < self.max_retry:
                    self.validate_understanding(self.correct_generation(error_message), retry=retry+1) # TODO retry count
                else: 
                    raise Exception("! Maximum retries reached. Exiting.")

        print(f"+ All words in response are present in JSON.")
        return data



    def generate_placeholder_rml (self):

        prompt = f"""
            Use the information from the previous prompt to create a RML file that can be used to generate a RDF graph.

            1. Target ontology: 
                Brick Schema (prefix: brick, URI: https://brickschema.org/schema/Brick#)
                @prefix rec: <https://w3id.org/rec#> .

            2. Base URI pattern:
                http://example.com/
                entity identification pattern: http://example.com/{{entityType}}/{{entityID}}

            3. Relationship mappings:
                Relationships use Brick ontology predicates.
                Relationships between two entities are implemented using a parentTriplesMap with a rml:joinCondition,
                so that the nodes of the knowledge graph are connected.
                Relationships between an entity and a value are implemented using rr:predicate and rr:objectMap.

            4. Sensors:
                Implement sensor values as direct properties using rdf:value predicates that point to URIs
                Values are accessed via template URLs: https://fiware.eonerc.rwth-aachen.de/v2/entities/{{id}}/attrs/{{attribute}}/value
            
            5. Classes mappings:
                Entity types are mapped to specific Brick classes (e.g., "TemperatureSensor" → brick)

            6. Output format preferences:
                mapping using standard R2RML / RML syntax
                RML generation tool: morph_kgc
                Output format: .ttl file

            7. Source data access method:
                Source is specified as "placeholder.json" in each logical source
                Implement the logical source using rml:iterator

            8. Execution environment:
                morph_kgc is installed and available in the execution environment
                JSONPath is used as the reference formulation (ql)
                Iterators are defined to select entities by type

            Generate the complete RML file with all of the given information.
            Follow a correct syntax and structure for the RML file.
            
            Regarding the corresponding Brick classes and properties:
            An engineer needs to know the exact classes and properties matching the entities and relationships in the JSON data.
            Make a list of every entity type and relation type that you need a matching class or property for.
            In the generated RML file add a placeholder instead of the class or property. Do NOT put a prefix in front of the placeholder.
                The placeholder should be a string that contains
                information about whether it is an class or a predicate
                the name of the entity type or relation type.
                The placeholder should be in the format: "PLACEHOLDER_{{classOrPredicate}}_{{entityOrRelationType}}"
            The engineer will replace the placeholder with the correct class or property.
            
            As an output, return a JSON string with two keys: 
                "rml_content": containing the complete RML file as a string in correct syntax and structure
                "placeholders": containing the list of placeholders as a string, one placeholder per line. Add behind every placeholder the arrow symbol => and a space character.
            
        """
        # TODO extra entity nodes not present
        # TODO some properties not present
        # TODO get prefixes

        response = self.claude.query(prompt)

        data = response["content"][0]["text"]
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)

        print("i TOKENS: ", tokens)

        response_data = json.loads(data)
        rml_file_content = response_data["rml_content"]
        placeholders = response_data["placeholders"]

        # print(rml_file_content)
        # print(placeholders)

        with open(self.output_rml, 'w') as rml_file:
            rml_file.write(rml_file_content)
            print(f"i RML file saved to {self.output_rml}")

        with open(self.output_terms, 'w') as terms_file:
            terms_file.write(placeholders)
            print(f"i Terms file saved to {self.output_terms}")

    def validate_terms(self):
        with open(self.output_terms, 'r') as file:
            terms = file.readlines()
        
        for i, term in enumerate(terms):
            term = term.strip()
            if not term:  # Skip empty lines
                continue
            if "=>" not in term:
                print(f"! Missing '=>' in line {i+1}: {term}")
                return False
            try:
                placeholder, value = term.split("=>")
                if not value.strip():
                    print(f"! Missing value after '=>' in line {i+1}: {term}")
                    return False
            except ValueError:
                print(f"! Invalid format in line {i+1}: {term}")
                return False
            
        print("+ All terms are valid.")
        return True
    
    

    def replace_terms(self):
        """
        Replace the placeholder in the RML file with the terms from the terms file.
        """

        with open(self.output_rml, 'r') as file:
            rml_content = file.read()

        with open(self.output_terms, 'r') as file:
            terms = file.read()

        # Replace Terms
        for term in terms.splitlines():
            print(term)
            term = term.strip()
            print(term)
            rml_content = rml_content.replace(term.split(" => ")[0], term.split(" => ")[1])
            
        # Replace JSON input placeholder
        # rml_content = rml_content.replace("placeholder.json", self.input_json_path)

        with open(self.output_rml, 'w') as file:
            file.write(rml_content)
            print(f"+ All terms have been replaced in {self.output_rml}")

    def validate_syntax(self):
            
            with open(self.output_rml, 'r') as file: 
                rml_content = file.read()
            

            # Check syntax of the RML file
            if "placeholder" in rml_content:
                raise ValueError("Placeholder not replaced in RML file. Please check the terms file.")
            else:
                print("+ All placeholders are replaced")
            
            # Check if rr:predicate and rr:class have valid objects
            lines = rml_content.splitlines()
            for i, line in enumerate(lines):
                if "rr:predicate" in line:
                    if line.split("rr:predicate")[1].strip() == ";":
                        raise ValueError(f"Invalid RML: rr:predicate without object at line {i}")

                # if "rr:class" in line and not line.strip().endswith(";"):
                #     next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                #     if not next_line or next_line.startswith("rr:"):
                #         raise ValueError(f"Invalid RML: rr:class without object at line {i + 1}")

            with open(self.output_rml, 'w') as file:
                file.write(rml_content)
            print(f"Syntax is OK")
            return True


    def generate_rdf (self, retry=0):
        """
        Generate the RML file using the LLM.
        """
        
        raise ValueError("RDF generation is not implemented yet.")

        # Try Generating RDF file
        # Correct rml_content if necessary
        print(self.output_rml, type(self.output_rml))
        rdf_gen = RDFGeneratorLLM(rml_file=self.output_rml)

        if retry < self.max_retry:
            try:
                rdf_gen.generate_rdf(json_input=self.input_json_path, rdf_output=self.output_rml)

            except Exception as e:
                error_message = f"Error generating RDF: {e}"
                print("!", error_message)
                
                # give current RML file 
                return 
                self.correct_generation(error_message)
                self.generate_rml(retry=retry+1)



    def generate_rml (self, output_rml, output_terms):

        self.output_rml = output_rml
        self.output_terms = output_terms

        if True: # Skip LLM Generation
            
            self.data_understanding = self.validate_understanding(self.understanding_json())

            if input("Continue? (y/n)") == "n": 
                return

            self.generate_placeholder_rml()

            print (f"Used Tokens: {self.used_tokens}")
        

        while self.validate_terms() == False:
            print("Please fill out the terms file.")
            c = input("Continue? (enter)")

        self.replace_terms()
        self.validate_syntax()

        if input("Continue? (y/n)") == "n": 
            # correct syntax? --> TODO in first step
            # correct iterator?
            # correct joinCondition?
            # correct placeholders?
            return

        try:
            self.generate_rdf()
        except Exception as e:
            print(f"Error generating RDF: {e}")
        






if __name__ == "__main__":
    INPUT_JSON_EXAMPLE = f"examples\LLM\kgcp_config\input\example_fiware_v1.json".replace("\\", "/")
    # INPUT_JSON_EXAMPLE = f"examples\LLM\kgcp_config\input\example_oh_v1.json".replace("\\", "/")
    INPUT_PLATFORM_CONFIG = f"examples/LLM/kgcp_config/input/fiware_config.json".replace("\\", "/")

    OUTPUT_RML = f"C:\\Users\\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\examples\LLM\kgcp_config\output\\rml.ttl"
    OUTPUT_TERMS = f"C:\\Users\\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\examples\LLM\kgcp_config\\terms.txt"

    rml_generator = RMLGenerator(input_json_path=INPUT_JSON_EXAMPLE, config_path=INPUT_PLATFORM_CONFIG)
    rml_generator.generate_rml(output_rml=OUTPUT_RML, output_terms=OUTPUT_TERMS)

    print(f"Used Tokens: {rml_generator.used_tokens}")
    print(f"Total tokens used: {sum([x[0] + x[1] for x in rml_generator.used_tokens])}")