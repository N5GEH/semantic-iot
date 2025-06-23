import json
import re
from pathlib import Path
from urllib.parse import urlparse
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF

def extend_with_http(input_ttl: Path,
                     openapi_json: Path,
                     http_onto_ttl: Path,
                     out_ttl: Path):
    kg = Graph()
    kg.parse(str(input_ttl), format='turtle')
    kg.parse(str(http_onto_ttl), format='turtle')

    with open(openapi_json, 'r') as f:
        spec = json.load(f)

    global_params = {
        name: param
        for name, param in spec.get('components', {}).get('parameters', {}).items()
        if param.get('in') == 'header'
    }

    HTTP    = Namespace('http://www.w3.org/2011/http#')
    HEADERS = Namespace('http://www.w3.org/2011/http-headers#')
    API     = Namespace('http://www.example.org/api#')
    kg.bind('http', HTTP)
    kg.bind('headers', HEADERS)
    kg.bind('api', API)

    conn = API['Connection_Main']
    kg.add((conn, RDF.type, HTTP.Connection))

    value_uris = [o for s, p, o in kg.triples((None, RDF.value, None))
                  if isinstance(o, URIRef)]

    shared_headers = {}
    for header_name, header_def in global_params.items():
        clean = re.sub(r"\W+", '_', header_name).strip('_')
        hdr_node = API[f"Header_{clean}"]
        if (hdr_node, None, None) not in kg:
            kg.add((hdr_node, RDF.type, HTTP.MessageHeader))
            kg.add((hdr_node, HTTP.fieldName, Literal(header_name)))
            kg.add((hdr_node, HTTP.fieldValue, Literal(header_def.get('default', ''))))
            hdr_const = HEADERS[header_name.lower()]
            kg.add((hdr_node, HTTP.hdrName, hdr_const))
        shared_headers[header_name] = hdr_node

    def compile_path_regex(template: str):
        esc = re.escape(template)
        esc = esc.replace(r"\{entityId\}", r"([^/]+)")
        esc = esc.replace(r"\{attrName\}", r"([^/]+)")
        return re.compile(f"^{esc}$")

    methods_map = {}
    for tpl, ops in spec.get('paths', {}).items():
        if tpl.endswith('/value'):
            verbs = [m.upper() for m in ops if m.lower() in ('get', 'put')]
            if verbs:
                methods_map[tpl] = (compile_path_regex(tpl), verbs)

    for uri in value_uris:
        parsed = urlparse(str(uri))
        path, authority = parsed.path, parsed.netloc

        for tpl, (regex, verbs) in methods_map.items():
            match = regex.match(path)
            if not match:
                continue
            ent, attr = match.group(1), match.group(2)

            for verb in verbs:
                ent_safe  = re.sub(r"\W+", '_', ent).strip('_')
                attr_safe = re.sub(r"\W+", '_', attr).strip('_')
                req_id    = f"{verb}_ent_{ent_safe}_attr_{attr_safe}_value"
                req_node  = API[req_id]

                kg.add((req_node, RDF.type,        HTTP.Request))
                kg.add((req_node, HTTP.methodName,  Literal(verb)))
                kg.add((req_node, HTTP.absolutePath, Literal(path)))
                kg.add((req_node, HTTP.absoluteURI,  URIRef(str(uri))))
                kg.add((req_node, HTTP.authority,    Literal(authority)))
                kg.add((req_node, HTTP.requestURI,   URIRef(str(uri))))
                kg.add((conn,    HTTP.requests,     req_node))

                for hdr in shared_headers.values():
                    kg.add((req_node, HTTP.headers, hdr))

                op = spec['paths'][tpl][verb.lower()]
                for p in op.get('parameters', []):
                    if p.get('in') != 'header':
                        continue
                    pname  = p['name']
                    clean  = re.sub(r"\W+", '_', pname).strip('_')
                    hdr_req = API[f"{req_id}_Header_{clean}"]
                    if (hdr_req, None, None) not in kg:
                        kg.add((hdr_req, RDF.type, HTTP.MessageHeader))
                        kg.add((hdr_req, HTTP.fieldName,  Literal(pname)))
                        kg.add((hdr_req, HTTP.fieldValue, Literal(p.get('default') or p.get('example', ''))))
                        hdr_const = HEADERS[pname.lower()]
                        kg.add((hdr_req, HTTP.hdrName, hdr_const))
                    kg.add((req_node, HTTP.headers, hdr_req))
            break

    kg.serialize(destination=str(out_ttl), format='turtle')