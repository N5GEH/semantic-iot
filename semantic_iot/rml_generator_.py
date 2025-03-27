
# TODO Validierungsfunktion & Iterationen

# TODO oder Placeholder in RML ausfüllen
# TODO RML Syntax von LLM generieren lassen

class RMLGenerator:
    def __init__(self, data, selector, prefixes):
        
        self.data = data
        self.selector = selector
        self.prefixes = prefixes


    def logical_source (self, ont_class) -> str:
        '''Source: JSON file; select only entities of a specific type.'''

        # selector = "type" # get from automatically JSON 

        return f"""
            rml:logicalSource [
                rml:source "placeholder.json";
                rml:referenceFormulation ql:JSONPath;
                rml:iterator '$[?(@.{self.selector}=="{ont_class}")]'; # TODO normale klasse; und kann auch anders aussehen
            ] ;
            """

    def subject_map(self, ont_class) -> str:
        '''Map the JSON entities to RDF subjects.'''

        prefix = "brick" # TODO get automatically (see other program)

        return f"""
            rr:subjectMap [
                rr:template "http://example.org/{ont_class}/{{id}}";
                rr:class {prefix}:{ont_class};
            ] ;
            """


    def predicate_object_maps (self, ont_class):
        
        def object_map(self, predicate, object):

            if object == "value":
                # TODO
                url = ""

                return f"""
                    rr:objectMap [
                        rr:template "{url}";
                    ];
                """
            
            if object == "entity":
                # TODO 
                type = ""
                child_ref = ""
                parent_ref = ""

                return f"""
                    rr:objectMap [ 
                        rr:parentTriplesMap ex:Mapping{type} ;
                        rr:joinCondition [
                            rr:child "{child_ref}" ;
                            rr:parent "{parent_ref}" ;
                        ]; 
                    ];
                """
        
        def predicate_object_map (relation, object):

            predicate = "brick:" + relation # TODO get automatically (see other program)
            object_map = object_map(predicate, object)

            return f"""
                rr:predicateObjectMap [
                    rr:predicate {predicate};
                    {object_map}
                ];
            """

        relations = ""

        temp = ""
        for relation in relations:
            temp += predicate_object_map (relation)
            temp += "\n"
        return temp


    # TODO Sensors (Temperature, CO2, Presence) follow one pattern then Control points (fanSpeed, airFlowSetpoint, temperatureSetpoint) follow a different pattern


    def generate(self, ont_classes, output_path):
        rml_content = self.prefixes + "\n"

        for ont_class in ont_classes:
            rml_content += f"""
                # Mapping for {ont_class}
                ex:Mapping{ont_class}
                    a rr:TriplesMap ;
                    {self.logical_source(ont_class)}
                    {self.subject_map(ont_class)}
                    {self.predicate_object_maps(ont_class)}
                    .
            """
            rml_content += ".\n\n"

        with open(output_path, 'w') as f:
            f.write(rml_content)

        print(f"RML file saved at {output_path}")
