from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL


class OntologyData:
    def __init__(self, input_ontologies):
        self.input_ontologies = input_ontologies

    def load_ontology_prefixes(self) -> str:
        prefixes = []
        for file_path in self.input_ontologies:
            file_path = Path(file_path)
            with open(file_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('@prefix'):
                        prefixes.append(line)
                    elif line == '':
                        break
        ontology_prefixes = '\n'.join(prefixes)

        # # convert to prefixed URIs
        # def convert_to_prefixed(uri):
        #     for prefix_uri, prefix in uri_to_prefix.items():
        #         if uri.startswith(prefix_uri):
        #             return uri.replace(prefix_uri, prefix + ":")
        #     return uri

        # context = {}
        # uri_to_prefix = {}  # converted from context
        # prefix_pattern = re.compile(r"@prefix\s+([^:]+):\s*<([^>]+)>")
        # for line in ontology_prefixes.splitlines():
        #     match = prefix_pattern.match(line)
        #     if match:
        #         prefix, uri = match.groups()
        #         context[prefix] = uri
        #         uri_to_prefix[uri] = prefix

        return ontology_prefixes

    def load_ontology_classes(self) -> dict:
        brick_graph = Graph()
        for file in self.input_ontologies:
            brick_graph.parse(file, format="ttl")

        ontology_classes = {}

        for s, p, o in brick_graph.triples((None, RDF.type, OWL.Class)):
            # label = brick_graph.value(subject=s, predicate=RDFS.label)
            # if label:
            #     ontology_classes[str(label).lower()] = str(s)
            #else:

            local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
            ontology_classes[local_name] = str(s)
        return ontology_classes

    def load_ontology_properties(self) -> dict:
        brick_graph = Graph()
        for file in self.input_ontologies:
            brick_graph.parse(file, format="ttl")

        ontology_properties = {}
        for s, p, o in brick_graph.triples((None, RDF.type, OWL.ObjectProperty)):
            label = brick_graph.value(subject=s, predicate=RDFS.label)
            if label:
                ontology_properties[str(label).lower()] = str(s)
            else:
                local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
                ontology_properties[local_name.lower()] = str(s)
        return ontology_properties

    def load_ontology(self):
        self.prefixes = self.load_ontology_prefixes()

        self.classes = self.load_ontology_classes()
        self.classes_names = str(list(self.classes.keys())).replace("'", "")
        
        self.properties = self.load_ontology_properties()
        self.properties_names = str(list(self.properties.keys())).replace("'", "")

        print("Ontology Prefixes, Classes and Properties loaded.")
