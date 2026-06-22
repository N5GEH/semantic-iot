import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, DCTERMS
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
        self.HTTP_VOC_onto = http_onto
        self._setup_namespaces()

        self._parse_spec(api_spec_path)

    def _parse_spec(self, api_spec_path):
        try:
            self.parser = ResolvingParser(str(api_spec_path), lazy=False, strict=False)
        except ValidationError as e:
            raise RuntimeError(f"Spec validation failed: {e}")

        self.spec = self.parser.specification

        if 'swagger' in self.spec:
            self._spec_version = 'swagger2'
        else:
            self._spec_version = 'openapi3'

        self.base_paths = self._get_server_base_paths()

    def _load_kg_and_ontology(self, kg_path: Path):
        self.kg.parse(str(kg_path), format='turtle')


    def _setup_namespaces(self):
        self.HTTP_VOC = Namespace('http://www.w3.org/2011/http#')
        self.HEADERS = Namespace('http://www.w3.org/2011/http-headers#')
        self.API = Namespace('http://www.example.org/api#')
        self.SCHEMA = Namespace('http://www.example.org/schema#')
        self.DCTERMS = DCTERMS
        self.kg.bind('http_voc', self.HTTP_VOC)
        self.kg.bind('headers', self.HEADERS)
        self.kg.bind('api', self.API)
        self.kg.bind('api_schema', self.SCHEMA)
        self.kg.bind('dcterms', self.DCTERMS)

    def _get_server_base_paths(self) -> list[str]:
        if self._spec_version == 'swagger2':
            return self._swagger2_base_paths()
        return self._openapi3_base_paths()

    def _swagger2_base_paths(self) -> list[str]:
        bases = set()
        bp = (self.spec.get('basePath') or '').strip()
        if bp:
            bp = '/' + bp.lstrip('/')
            bp = bp.rstrip('/')
            if bp != '/':
                bases.add(bp)
        return sorted(bases) or [""]

    def _openapi3_base_paths(self) -> list[str]:
        bases = set()
        for s in (self.spec.get('servers') or []):
            url = (s or {}).get('url', '')
            try:
                p = urlparse(url)
                bp = (p.path or '').rstrip('/')
                if bp and bp != '/':
                    bases.add(bp)
            except Exception:
                pass
        return sorted(bases) or [""]

    def extend_kg(self, add_http_ontology: bool = False):
        if add_http_ontology:
            # Optionally load HTTP ontology
            self.kg.parse(str(self.HTTP_VOC_onto), format='turtle')
        shared_headers, shared_queries = self._index_global_parameters()
        value_links = self._gather_value_links()
        methods_map = self._prepare_methods_map()

        if not methods_map:
            raise RuntimeError(
                "No operations collected from spec. "
                "Check servers/basePath and that paths contain supported HTTP methods."
            )

        for source_node, uri in value_links:
            parsed = urlparse(str(uri))
            orig_path = re.sub(r'/+', '/', parsed.path or '/')

            matched = False
            for candidate in self._matching_candidates(orig_path):
                for tpl, (tpl_segments, verbs) in methods_map.items():
                    if not self._match_path_to_template(candidate, tpl_segments):
                        continue

                    for verb in verbs:
                        req_id = self._build_request_id(source_node, verb, uri)
                        req = self.API[req_id]

                        op = self._get_operation(tpl, verb.lower())
                        if not op:
                            continue

                        self._create_request_node(
                            req_id, req, verb, orig_path, tpl, uri,
                            parsed.netloc, shared_headers,
                            shared_queries, op
                        )
                        self.kg.remove((source_node, RDF.value, uri))
                        self.kg.add((source_node, RDF.value, req))
                    matched = True
                    break
                if matched:
                    break

    @staticmethod
    def _build_request_id(source_node: URIRef, verb: str, uri: URIRef) -> str:
        """Create a short deterministic request identifier from stable request inputs."""
        key = f"{str(source_node)}|{verb.upper()}|{str(uri)}"
        digest = hashlib.blake2s(key.encode("utf-8"), digest_size=8).hexdigest()
        return f"req_{verb.lower()}_{digest}"

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
        return (
            self._swagger2_global_params()
            if self._spec_version == 'swagger2'
            else self._openapi3_global_params()
        )

    def _swagger2_global_params(self) -> tuple:
        header_nodes = {}
        query_nodes = {}
        global_params = self.spec.get('parameters', {}) or {}
        for name, p in global_params.items():
            if isinstance(p, dict) and '$ref' in p:
                continue
            clean = re.sub(r"\W+", '_', name).strip('_')
            node = self.API[f"Param_{clean}"]
            if p.get('in') == 'header':
                self.kg.add((node, RDF.type, self.HTTP_VOC.MessageHeader))
                self.kg.add((node, self.HTTP_VOC.fieldName, Literal(p.get('name', name))))
                self.kg.add((node, self.HTTP_VOC.fieldValue, Literal(self._param_default_value(p))))
                header_nodes[name] = node
            elif p.get('in') == 'query':
                self.kg.add((node, RDF.type, self.HTTP_VOC.Parameter))
                self.kg.add((node, self.HTTP_VOC.paramName, Literal(p.get('name', name))))
                self.kg.add((node, self.HTTP_VOC.paramValue, Literal(self._param_default_value(p))))
                query_nodes[name] = node
        return header_nodes, query_nodes

    def _openapi3_global_params(self) -> tuple:
        header_nodes = {}
        query_nodes = {}
        global_params = (
            (self.spec.get('components') or {}).get('parameters', {}) or {}
        )
        for name, p in global_params.items():
            if isinstance(p, dict) and '$ref' in p:
                continue
            clean = re.sub(r"\W+", '_', name).strip('_')
            node = self.API[f"Param_{clean}"]
            if p.get('in') == 'header':
                self.kg.add((node, RDF.type, self.HTTP_VOC.MessageHeader))
                self.kg.add((node, self.HTTP_VOC.fieldName, Literal(p.get('name', name))))
                self.kg.add((node, self.HTTP_VOC.fieldValue, Literal(self._param_default_value(p))))
                header_nodes[name] = node
            elif p.get('in') == 'query':
                self.kg.add((node, RDF.type, self.HTTP_VOC.Parameter))
                self.kg.add((node, self.HTTP_VOC.paramName, Literal(p.get('name', name))))
                self.kg.add((node, self.HTTP_VOC.paramValue, Literal(self._param_default_value(p))))
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

    def _gather_value_links(self) -> list:
        return [
            (s, o) for s, _, o in self.kg.triples((None, RDF.value, None))
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

        if self._spec_version == 'swagger2':
            base_path = self.spec.get("basePath", "").strip("/")
        else:
            base_path = self.base_paths[0].strip("/") if self.base_paths else ""

        for tpl, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            keys_lower = {k.lower() for k in path_item.keys()}
            verbs = [m.upper() for m in ALL if m in keys_lower]
            if not verbs:
                continue
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

    def _create_request_node(
        self, req_id, req: URIRef, verb: str, path: str, tpl: str,
        uri: URIRef, authority: str,
        shared_headers: dict, shared_queries: dict,
        op: dict
    ):
        # core triples
        self.kg.add((req, RDF.type, self.HTTP_VOC.Request))
        self.kg.add((req, self.HTTP_VOC.methodName, Literal(verb)))
        self.kg.add((req, self.HTTP_VOC.absolutePath, Literal(path)))
        self.kg.add((req, self.HTTP_VOC.absoluteURI, URIRef(str(uri))))
        self.kg.add((req, self.HTTP_VOC.authority, Literal(authority)))

        # attach shared
        for node in shared_headers.values():
            self.kg.add((req, self.HTTP_VOC.headers, node))
        for node in shared_queries.values():
            self.kg.add((req, self.HTTP_VOC.params, node))

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
                self.kg.add((node, RDF.type, self.HTTP_VOC.MessageHeader))
                self.kg.add((node, self.HTTP_VOC.fieldName, Literal(p.get('name', ''))))
                self.kg.add((node, self.HTTP_VOC.fieldValue,
                             Literal(self._param_default_value(p))))
                self.kg.add((req, self.HTTP_VOC.headers, node))

            elif p.get('in') == 'query':
                self.kg.add((node, RDF.type, self.HTTP_VOC.Parameter))
                self.kg.add((node, self.HTTP_VOC.paramName, Literal(p.get('name', ''))))
                self.kg.add((node, self.HTTP_VOC.paramValue,
                             Literal(self._param_default_value(p))))
                self.kg.add((req, self.HTTP_VOC.params, node))

        # attach schema conformance
        self._attach_schema_conformance(req, op, tpl, verb)


    def _attach_schema_conformance(self, req: URIRef, op: dict, tpl: str, verb: str) -> None:
        verb_lower = verb.lower()
        is_read = verb_lower in ('get', 'head', 'options', 'trace')
        is_write = verb_lower in ('put', 'post', 'patch')

        if self._spec_version == 'swagger2':
            if is_read:
                self._swagger2_response_schemas(req, op, tpl, verb)
            if is_write:
                self._swagger2_request_schemas(req, op, tpl, verb)
        else:
            if is_read:
                self._openapi3_response_schemas(req, op, tpl, verb)
            if is_write:
                self._openapi3_request_schemas(req, op, tpl, verb)

    def _swagger2_response_schemas(self, req, op, tpl, verb):
        prod = op.get('produces') or self.spec.get('produces') or ['application/json']
        tpl_safe = re.sub(r'\W+', '_', tpl.strip('/'))
        seen = set()
        for status_code, response in (op.get('responses') or {}).items():
            if not self._is_success_status(status_code):
                continue
            schema = response.get('schema')
            for media_type in prod:
                label = f"{verb}_{tpl_safe}_response_{status_code}_{media_type.replace('/', '_')}"
                if label in seen:
                    continue
                seen.add(label)
                if schema:
                    self.kg.add((req, self.SCHEMA["responseSchema"], Literal(json.dumps(schema))))
                self._attach_media_header(req, "Accept", media_type, verb, tpl_safe)

    def _openapi3_response_schemas(self, req, op, tpl, verb):
        tpl_safe = re.sub(r'\W+', '_', tpl.strip('/'))
        seen = set()
        for status_code, response in (op.get('responses') or {}).items():
            if not self._is_success_status(status_code):
                continue
            for media_type, content in (response.get('content') or {}).items():
                label = f"{verb}_{tpl_safe}_response_{status_code}_{media_type.replace('/', '_')}"
                if label in seen:
                    continue
                seen.add(label)
                schema = content.get('schema')
                if schema:
                    self.kg.add((req, self.SCHEMA["responseSchema"], Literal(json.dumps(schema))))
                self._attach_media_header(req, "Accept", media_type, verb, tpl_safe)

    def _swagger2_request_schemas(self, req, op, tpl, verb):
        cons = op.get('consumes') or self.spec.get('consumes') or ['application/json']
        tpl_safe = re.sub(r'\W+', '_', tpl.strip('/'))
        seen = set()
        for p in (op.get('parameters') or []):
            if p.get('in') != 'body':
                continue
            schema = p.get('schema')
            for media_type in cons:
                label = f"{verb}_{tpl_safe}_request_{media_type.replace('/', '_')}"
                if label in seen:
                    continue
                seen.add(label)
                if schema:
                    self.kg.add((req, self.SCHEMA["bodySchema"], Literal(json.dumps(schema))))
                self._attach_media_header(req, "Content-Type", media_type, verb, tpl_safe)

    def _openapi3_request_schemas(self, req, op, tpl, verb):
        tpl_safe = re.sub(r'\W+', '_', tpl.strip('/'))
        seen = set()
        request_body = op.get('requestBody') or {}
        for media_type, content in (request_body.get('content') or {}).items():
            schema = content.get('schema')
            label = f"{verb}_{tpl_safe}_request_{media_type.replace('/', '_')}"
            if label in seen:
                continue
            seen.add(label)
            if schema:
                self.kg.add((req, self.SCHEMA["bodySchema"], Literal(json.dumps(schema))))
            self._attach_media_header(req, "Content-Type", media_type, verb, tpl_safe)

    @staticmethod
    def _is_success_status(status_code: str) -> bool:
        return status_code.lower().startswith('2')

    def _attach_media_header(self, req, header_name, media_type, verb, tpl_safe):
        clean = re.sub(r"\W+", '_', header_name).strip('_')
        node = self.API[f"Header_{clean}_{verb}_{tpl_safe}"]
        self.kg.add((node, RDF.type, self.HTTP_VOC.MessageHeader))
        self.kg.add((node, self.HTTP_VOC.fieldName, Literal(header_name)))
        self.kg.add((node, self.HTTP_VOC.fieldValue, Literal(media_type)))
        self.kg.add((req, self.HTTP_VOC.headers, node))

    def serialize(self, destination: Path):
        self.kg.serialize(destination=str(destination), format='turtle')
