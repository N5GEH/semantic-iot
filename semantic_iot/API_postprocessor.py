# http_extension.py
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF


class APIPostprocessor:
    """
    This class is responsible for post-processing the API responses.
    It can be extended to include more complex post-processing logic.
    """

    def __init__(self, kg_path, api_spec_path, http_onto=None):
        if not http_onto:
            http_onto = Path(__file__).parent / '_ontologies/Http.ttl'
        # TODO load everything
        pass

    def postprocess(self):
        """This method will be called to perform post-processing."""
        api_spec = self.parse_api_spec()
        pass

    def extend_kg(self):
        """Populate a KG with HTTP Request nodes based on the API spec and the original KG."""
        pass

    def parse_api_spec(self):
        """
        Load and parse the OpenAPI specification
        Return a list of all possible endpoints (operations) and their supported parameters etc.
        """
        return ...



def extend_with_http(input_ttl: Path,
                     openapi_json: Path,
                     http_onto_ttl: Path,
                     out_ttl: Path):
    """
    Load a Turtle KG and the W3C HTTP ontology, then:
      1) Find every existing value node (i.e. every URI that appears as the object of rdf:value).
      2) For each of those value nodes, create http:Request nodes for supported HTTP methods (GET/PUT),
         populating http:methodName, http:absolutePath, http:absoluteURI, http:authority, and http:requestURI.
      3) Create shared HTTP.MessageHeader nodes for all global parameters (header, query, path).
      4) For each request, create inline MessageHeader nodes for operation-specific parameters (any 'in').
      5) Attach all parameter/header nodes to each request via http:headers.
      6) Link each request to a single shared Connection instance.
      7) Serialize the augmented graph out to Turtle.
    """
    # Load KG and HTTP ontology
    kg = Graph()
    kg.parse(str(input_ttl), format='turtle')
    kg.parse(str(http_onto_ttl), format='turtle')

    # Load OpenAPI spec
    with open(openapi_json, 'r') as f:
        spec = json.load(f)

    # Namespaces
    HTTP = Namespace('http://www.w3.org/2011/http#')
    HEADERS = Namespace('http://www.w3.org/2011/http-headers#')
    API = Namespace('http://www.example.org/api#')
    kg.bind('http', HTTP)
    kg.bind('headers', HEADERS)
    kg.bind('api', API)

    # Create or reuse a Connection node
    conn = API['Connection_Main']
    kg.add((conn, RDF.type, HTTP.Connection))

    # Index global parameters (all 'in' types)
    global_params = spec.get('components', {}).get('parameters', {})
    shared_nodes = {}
    for name, param in global_params.items():
        if 'in' in param:
            clean = re.sub(r"\W+", '_', name).strip('_')
            node = API[f"GlobalParam_{clean}"]
            if (node, None, None) not in kg:
                kg.add((node, RDF.type, HTTP.MessageHeader))
                kg.add((node, HTTP.fieldName, Literal(name)))
                kg.add((node, HTTP.fieldValue, Literal(param.get('default', ''))))
                if param['in'] == 'header':
                    kg.add((node, HTTP.hdrName, HEADERS[name.lower()]))
            shared_nodes[name] = node

    # Gather all rdf:value URIs
    value_uris = [o for _, _, o in kg.triples((None, RDF.value, None)) if isinstance(o, URIRef)]

    # Prepare path-to-method mapping for GET/PUT operations
    methods_map = {}
    for path_tpl, ops in spec.get('paths', {}).items():
        if path_tpl.endswith('/value'):
            # Build regex: replace {var} with capture group
            esc = re.escape(path_tpl)
            esc = re.sub(r"\\\{[^/]+\\\}", r"([^/]+)", esc)
            regex = re.compile(f"^{esc}$")
            verbs = [m.upper() for m in ops if m.lower() in ('get', 'put')]
            if verbs:
                methods_map[path_tpl] = (regex, verbs)

    # Process each value URI
    for uri in value_uris:
        parsed = urlparse(str(uri))
        path, authority = parsed.path, parsed.netloc

        for tpl, (regex, verbs) in methods_map.items():
            if not regex.match(path):
                continue
            for verb in verbs:
                # Sanitize path to generate a valid ID
                clean_path = re.sub(r"\W+", '_', path)
                req_id = f"{verb}_{clean_path}"
                req = API[req_id]
                # Create Request node
                kg.add((req, RDF.type, HTTP.Request))
                kg.add((req, HTTP.methodName, Literal(verb)))
                kg.add((req, HTTP.absolutePath, Literal(path)))
                kg.add((req, HTTP.absoluteURI, URIRef(str(uri))))
                kg.add((req, HTTP.authority, Literal(authority)))
                kg.add((req, HTTP.requestURI, URIRef(str(uri))))
                kg.add((conn, HTTP.requests, req))

                # Attach shared global parameter nodes
                for node in shared_nodes.values():
                    kg.add((req, HTTP.headers, node))

                # Handle inline operation parameters (skip path params entityId, attrName)
                op = spec['paths'][tpl][verb.lower()]
                for p in op.get('parameters', []):
                    pname = p['name']
                    if p.get('in') == 'path' and pname in ('entityId', 'attrName'):
                        continue
                    clean_p = re.sub(r"\W+", '_', pname).strip('_')
                    node = API[f"{req_id}_Param_{clean_p}"]
                    if (node, None, None) not in kg:
                        kg.add((node, RDF.type, HTTP.MessageHeader))
                        kg.add((node, HTTP.fieldName, Literal(pname)))
                        kg.add((node, HTTP.fieldValue, Literal(p.get('default', p.get('example', '')))))
                        if p.get('in') == 'header':
                            kg.add((node, HTTP.hdrName, HEADERS[pname.lower()]))
                    kg.add((req, HTTP.headers, node))
            break

    # Serialize augmented graph
    kg.serialize(destination=str(out_ttl), format='turtle')
