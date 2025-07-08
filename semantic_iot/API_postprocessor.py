import json
import re
from pathlib import Path
from urllib.parse import urlparse
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF
from openapi3 import OpenAPI

class APIPostprocessor:
    """
    Post-process API responses and extend an RDF graph using OpenAPI 3 spec via openapi3 library.
    """
    def __init__(self, kg_path: Path, api_spec_path: Path, http_onto: Path = None):
        self.api_spec_path = api_spec_path
        self.kg = Graph()
        self._load_kg_and_ontology(kg_path, http_onto)
        self._setup_namespaces()
        # Parse spec and instantiate OpenAPI client/parser
        raw = json.loads(api_spec_path.read_text())
        self.api = OpenAPI(raw)

    def _load_kg_and_ontology(self, kg_path: Path, http_onto: Path = None):
        if not http_onto:
            http_onto = Path(__file__).parent / '_ontology/Http.ttl'
        self.kg.parse(str(kg_path), format='turtle')
        self.kg.parse(str(http_onto), format='turtle')

    def _setup_namespaces(self):
        self.HTTP = Namespace('http://www.w3.org/2011/http#')
        self.HEADERS = Namespace('http://www.w3.org/2011/http-headers#')
        self.API = Namespace('http://www.example.org/api#')
        self.kg.bind('http', self.HTTP)
        self.kg.bind('headers', self.HEADERS)
        self.kg.bind('api', self.API)

    def extend_kg(self):
        conn = self._create_connection_node()
        shared_headers, shared_queries = self._index_global_parameters()
        uris = self._gather_value_uris()
        methods_map = self._prepare_methods_map()

        for uri in uris:
            parsed = urlparse(str(uri))
            path = parsed.path
            for tpl, (regex, verbs) in methods_map.items():
                if not regex.match(path):
                    continue
                for verb in verbs:
                    clean_path = re.sub(r"\W+", '_', path)
                    req_id = f"{verb}_{clean_path}"
                    req = self.API[req_id]
                    # Use getattr to fetch the operation for the verb
                    op = getattr(self.api.paths[tpl], verb.lower(), None)
                    if not op:
                        continue
                    self._create_request_node(
                        req_id, req, verb, path, uri, parsed.netloc,
                        shared_headers, shared_queries, op, conn
                    )
                break

    def _create_connection_node(self):
        conn = self.API['Connection_Main']
        self.kg.add((conn, RDF.type, self.HTTP.Connection))
        return conn

    def _index_global_parameters(self) -> tuple:
        header_nodes = {}
        query_nodes = {}
        global_params = getattr(self.api.components, 'parameters', {}) or {}
        for name, param in global_params.items():
            clean = re.sub(r"\W+", '_', name).strip('_')
            node = self.API[f"Param_{clean}"]
            if param.in_ == 'header':
                self.kg.add((node, RDF.type, self.HTTP.MessageHeader))
                self.kg.add((node, self.HTTP.fieldName, Literal(param.name)))
                self.kg.add((node, self.HTTP.fieldValue, Literal(getattr(param, 'default', ''))))
                header_nodes[name] = node
            elif param.in_ == 'query':
                self.kg.add((node, RDF.type, self.HTTP.Parameter))
                self.kg.add((node, self.HTTP.paramName, Literal(param.name)))
                self.kg.add((node, self.HTTP.paramValue, Literal(getattr(param, 'default', ''))))
                query_nodes[name] = node
        return header_nodes, query_nodes

    def _gather_value_uris(self) -> list:
        return [ o for _, _, o in self.kg.triples((None, RDF.value, None)) if isinstance(o, URIRef) ]

    def _prepare_methods_map(self) -> dict:
        methods_map = {}
        for tpl, path_item in self.api.paths.items():
            # build regex from the template
            esc = re.escape(tpl)
            esc = re.sub(r"\\\{[^/]+\\\}", r"([^/]+)", esc)
            regex = re.compile(f"^{esc}$")

            verbs = []
            for method in ("get", "put"):  # supported HTTP methods
                op = getattr(path_item, method, None)
                if op:
                    verbs.append(method.upper())

            if verbs:
                methods_map[tpl] = (regex, verbs)

        return methods_map

    def _create_request_node(
        self, req_id, req: URIRef, verb: str, path: str,
        uri: URIRef, authority: str,
        shared_headers: dict, shared_queries: dict,
        op, conn: URIRef
    ):
        # core triples
        self.kg.add((req, RDF.type, self.HTTP.Request))
        self.kg.add((req, self.HTTP.methodName, Literal(verb)))
        self.kg.add((req, self.HTTP.absolutePath, Literal(path)))
        self.kg.add((req, self.HTTP.absoluteURI, URIRef(str(uri))))
        self.kg.add((req, self.HTTP.authority, Literal(authority)))
        self.kg.add((conn, self.HTTP.requests, req))

        # attach shared
        for node in shared_headers.values():
            self.kg.add((req, self.HTTP.headers, node))
        for node in shared_queries.values():
            self.kg.add((req, self.HTTP.params, node))

        # inline parameters
        for p in op.parameters or []:
            if p.in_ == 'body':
                continue
            if p.in_ == 'path' and p.name in ('entityId','attrName'):
                continue
            clean = re.sub(r"\W+", '_', p.name).strip('_')
            node = self.API[f"{req_id}_Param_{clean}"]
            if p.in_ == 'header':
                self.kg.add((node, RDF.type, self.HTTP.MessageHeader))
                self.kg.add((node, self.HTTP.fieldName, Literal(p.name)))
                self.kg.add((node, self.HTTP.fieldValue, Literal(getattr(p, 'default', getattr(p, 'example', '')))))
                self.kg.add((req, self.HTTP.headers, node))
            elif p.in_ == 'query':
                self.kg.add((node, RDF.type, self.HTTP.Parameter))
                self.kg.add((node, self.HTTP.paramName, Literal(p.name)))
                self.kg.add((node, self.HTTP.paramValue, Literal(getattr(p, 'default', getattr(p, 'example', '')))))
                self.kg.add((req, self.HTTP.params, node))

    def serialize(self, destination: Path):
        self.kg.serialize(destination=str(destination), format='turtle')
