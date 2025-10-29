import json
import re
from pathlib import Path
from urllib.parse import urlparse
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF
from prance import ResolvingParser, ValidationError


class APIPostprocessor:
    """
    Post-process API responses and extend an RDF graph using Prance to load
    either Swagger 2.0 or OpenAPI 3.x specs via the ResolvingParser.
    """
    def __init__(self, kg_path: Path, api_spec_path: Path, http_onto: Path = None):
        self.api_spec_path = api_spec_path
        self.kg = Graph()
        self._load_kg_and_ontology(kg_path)
        if http_onto is None:
            http_onto = Path(__file__).parent / 'ontology' / 'Http.ttl'
        self.http_onto = http_onto
        self._setup_namespaces()

        # Parse and validate spec
        try:
            self.parser = ResolvingParser(str(api_spec_path), lazy=False, strict=True)
        except ValidationError as e:
            raise RuntimeError(f"Spec validation failed: {e}")

        # Raw spec dict
        self.spec = self.parser.specification

        self.base_paths = self._get_server_base_paths()

    def _load_kg_and_ontology(self, kg_path: Path):
        self.kg.parse(str(kg_path), format='turtle')


    def _setup_namespaces(self):
        self.HTTP = Namespace('http://www.w3.org/2011/http#')
        self.HEADERS = Namespace('http://www.w3.org/2011/http-headers#')
        self.API = Namespace('http://www.example.org/api#')
        self.kg.bind('http', self.HTTP)
        self.kg.bind('headers', self.HEADERS)
        self.kg.bind('api', self.API)

    def _get_server_base_paths(self) -> list[str]:
        """
        Collect base paths from Swagger 2.0 (basePath) and OAS3 (servers[*].url).
        Returns a list like ["", "/rest"] (no trailing slash; "" means no base).
        """
        bases = set()

        # Swagger 2.0
        if 'swagger' in self.spec:
            bp = (self.spec.get('basePath') or '').strip()
            if bp:
                # ensure exactly one leading slash, no trailing slash
                bp = '/' + bp.lstrip('/')
                bp = bp.rstrip('/')
                if bp != '/':
                    bases.add(bp)

        # OpenAPI 3.x
        for s in (self.spec.get('servers') or []):
            url = (s or {}).get('url', '')
            try:
                p = urlparse(url)
                bp = (p.path or '').rstrip('/')
                if bp and bp != '/':
                    bases.add(bp)
            except Exception:
                pass

        # If nothing explicit, match “no base”
        return sorted(bases) or [""]

    def extend_kg(self, add_http_ontology: bool = False):
        if add_http_ontology:
            # Optionally load HTTP ontology
            self.kg.parse(str(self.http_onto), format='turtle')
        conn = self._create_connection_node()
        shared_headers, shared_queries = self._index_global_parameters()
        uris = self._gather_value_uris()
        methods_map = self._prepare_methods_map()

        if not methods_map:
            raise RuntimeError(
                "No operations collected from spec. "
                "Check servers/basePath and that paths contain supported HTTP methods."
            )

        for uri in uris:
            parsed = urlparse(str(uri))
            orig_path = re.sub(r'/+', '/', parsed.path or '/')

            matched = False
            for candidate in self._matching_candidates(orig_path):
                for tpl, (tpl_segments, verbs) in methods_map.items():
                    if not self._match_path_to_template(candidate, tpl_segments):
                        continue

                    for verb in verbs:
                        clean_path = re.sub(r"\W+", '_', orig_path)
                        req_id = f"{verb}_{clean_path}"
                        req = self.API[req_id]

                        op = self._get_operation(tpl, verb.lower())
                        if not op:
                            continue

                        self._create_request_node(
                            req_id, req, verb, orig_path, uri,
                            parsed.netloc, shared_headers,
                            shared_queries, op, conn
                        )
                    matched = True
                    break
                if matched:
                    break

    def _get_operation(self, tpl: str, method: str) -> dict:
        """
        Return operation dict and merge any path-item parameters into it.
        """
        paths = self.spec.get('paths', {}) or {}
        path_item = paths.get(tpl, {}) or {}
        op = path_item.get(method) or {}

        # Merge path-level parameters (appear frequently in Swagger 2.0)
        if path_item.get('parameters'):
            merged = list(path_item['parameters']) + list(op.get('parameters') or [])
            # copy to avoid mutating original
            op = {**op, 'parameters': merged}

        return op

    def _matching_candidates(self, path: str) -> list[str]:
        # normalize duplicates like // -> /
        path = re.sub(r'/+', '/', path or '/')
        return [path]

    def _index_global_parameters(self) -> tuple:
        """
        Index globally-declared parameters and materialize them as shared header/query nodes.
        Handles Swagger2 (spec['parameters']) and OAS3 (spec['components']['parameters']).
        """
        header_nodes = {}
        query_nodes = {}

        # Swagger2: spec['parameters'], OAS3: spec['components']['parameters']
        if 'swagger' in self.spec:
            global_params = self.spec.get('parameters', {}) or {}
        else:
            global_params = (
                (self.spec.get('components') or {}).get('parameters', {}) or {}
            )

        for name, p in global_params.items():
            # Resolve $ref if any (Prance ResolvingParser should already do it)
            if isinstance(p, dict) and '$ref' in p:
                # In practice, ResolvingParser dereferences already; keep fallback just in case
                continue

            clean = re.sub(r"\W+", '_', name).strip('_')
            node = self.API[f"Param_{clean}"]

            if p.get('in') == 'header':
                self.kg.add((node, RDF.type, self.HTTP.MessageHeader))
                self.kg.add((node, self.HTTP.fieldName, Literal(p.get('name', name))))
                self.kg.add((node, self.HTTP.fieldValue, Literal(self._param_default_value(p))))
                header_nodes[name] = node

            elif p.get('in') == 'query':
                self.kg.add((node, RDF.type, self.HTTP.Parameter))
                self.kg.add((node, self.HTTP.paramName, Literal(p.get('name', name))))
                self.kg.add((node, self.HTTP.paramValue, Literal(self._param_default_value(p))))
                query_nodes[name] = node

        return header_nodes, query_nodes

    def _param_default_value(self, p: dict):
        """
        Extract a sensible default/example value from a parameter object across Swagger2/OAS3.
        Preference: schema.default > schema.example > default > example > "".
        """
        schema = p.get('schema') or {}
        return (
            schema.get('default')
            or schema.get('example')
            or p.get('default')
            or p.get('example')
            or ""
        )

    def _gather_value_uris(self) -> list:
        return [
            o for _, _, o in self.kg.triples((None, RDF.value, None))
            if isinstance(o, URIRef)
        ]

    def _prepare_methods_map(self) -> dict:
        """
        Collect API path templates and supported verbs,
        include basePath (Swagger) or servers (OAS3) if present.
        Return: {tpl: (segments, verbs)}
        """
        ALL = {'get', 'put', 'post', 'delete', 'patch', 'head', 'options', 'trace'}
        methods_map = {}

        paths = self.spec.get('paths') or {}

        # Swagger 2: has "swagger" key and optional "basePath"
        base_path = ""
        if "swagger" in self.spec:
            base_path = self.spec.get("basePath", "").strip("/")
        # OAS3: you already collected self.base_paths elsewhere
        elif getattr(self, "base_paths", None):
            # Take the first server/basePath as canonical
            base_path = self.base_paths[0].strip("/") if self.base_paths else ""

        for tpl, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            keys_lower = {k.lower() for k in path_item.keys()}
            verbs = [m.upper() for m in ALL if m in keys_lower]
            if not verbs:
                continue

            # Combine basePath + tpl
            full_tpl = "/".join(s for s in [base_path, tpl.strip("/")] if s)
            norm = re.sub(r'/+', '/', full_tpl).strip('/')
            segments = norm.split('/') if norm else []

            methods_map[tpl] = (segments, verbs)

        return methods_map

    def _match_path_to_template(self, uri_path: str, tpl_segments: list) -> bool:
        """
        Check if a KG path matches a template by comparing segments.
        - Literal segments must be equal
        - Template params {xyz} match anything
        """
        norm = re.sub(r'/+', '/', uri_path).strip('/')
        uri_segments = norm.split('/') if norm else []

        if len(uri_segments) != len(tpl_segments):
            return False

        for seg, tpl_seg in zip(uri_segments, tpl_segments):
            if tpl_seg.startswith('{') and tpl_seg.endswith('}'):
                continue  # param slot → always match
            if seg != tpl_seg:
                return False

        return True

    def _create_connection_node(self):
        conn = self.API['Connection_Main']
        self.kg.add((conn, RDF.type, self.HTTP.Connection))
        return conn

    def _create_request_node(
        self, req_id, req: URIRef, verb: str, path: str,
        uri: URIRef, authority: str,
        shared_headers: dict, shared_queries: dict,
        op: dict, conn: URIRef
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

        # inline parameters (ignore body)
        for p in op.get('parameters', []) or []:
            if p.get('in') == 'body':
                continue
            if p.get('in') == 'path' and p.get('name') in ('entityId', 'attrName'):
                # Skip these path params as per original behavior
                continue

            clean = re.sub(r"\W+", '_', p.get('name', 'param')).strip('_')
            node = self.API[f"{req_id}_Param_{clean}"]

            if p.get('in') == 'header':
                self.kg.add((node, RDF.type, self.HTTP.MessageHeader))
                self.kg.add((node, self.HTTP.fieldName, Literal(p.get('name', ''))))
                self.kg.add((node, self.HTTP.fieldValue,
                             Literal(self._param_default_value(p))))
                self.kg.add((req, self.HTTP.headers, node))

            elif p.get('in') == 'query':
                self.kg.add((node, RDF.type, self.HTTP.Parameter))
                self.kg.add((node, self.HTTP.paramName, Literal(p.get('name', ''))))
                self.kg.add((node, self.HTTP.paramValue,
                             Literal(self._param_default_value(p))))
                self.kg.add((req, self.HTTP.params, node))


    def serialize(self, destination: Path):
        self.kg.serialize(destination=str(destination), format='turtle')
