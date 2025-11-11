"""
generate_fiware_openapi_spec.py

From a Turtle KG of FIWARE entities/endpoints, emit a FIWARE-style OpenAPI 3.0.1 JSON spec
with FIWARE headers only and generic operation metadata, preserving literal entity IDs in paths.
"""
import os
import re
import json
import argparse
from urllib.parse import urlparse
from collections import OrderedDict
import rdflib
from rdflib.namespace import RDF

# Utility to extract the local name from a URI

def human_name(uri):
    """Extract the local name from a URI using urlparse: fragment or last path segment."""
    parsed = urlparse(uri)
    # If there's a fragment, use that, otherwise use the last segment of the path
    if parsed.fragment:
        return parsed.fragment
    # strip trailing slash, split path
    path = parsed.path.rstrip('/')
    return path.split('/')[-1]

# Build the OpenAPI spec from RDF

def build_spec(rdf_path, server_url, title, version):
    # Load the Turtle graph
    g = rdflib.Graph()
    g.parse(rdf_path, format="turtle")

    # Determine the server URL if not provided
    if not server_url:
        server_url = "/"
        for _, _, val in g.triples((None, RDF.value, None)):
            url = str(val)
            if url.startswith("http"):
                parts = urlparse(url)
                server_url = f"{parts.scheme}://{parts.netloc}"
                break

    # Initialize OpenAPI skeleton
    spec = OrderedDict([
        ("openapi", "3.0.1"),
        ("info", OrderedDict([
            ("title", title),
            ("description", "API specification for FIWARE IoT platform."),
            ("version", version)
        ])),
        ("servers", [{"url": server_url}]),
        ("paths", OrderedDict())
    ])

    seen = set()

    # Iterate over each rdf:value triple
    for subj, _, url_node in g.triples((None, RDF.value, None)):
        raw_url = str(url_node)
        parsed = urlparse(raw_url)

        # Preserve literal path with entity IDs
        path = parsed.path

        # Determine HTTP method by simple heuristic
        method = "put" if "attrs" in path and path.endswith("/value") and "Setpoint" in subj else "get"

        # Avoid duplicates
        key = (path, method)
        if key in seen:
            continue
        seen.add(key)

        # Derive tag and summary from the subject's class or URI
        cls = next(g.objects(subj, RDF.type), None)
        tag = human_name(str(cls)) if cls else "Operation"
        summary = f"{method.upper()} {tag}"

        # Generic responses: 200 OK with plain text
        responses = {"200": {"description": "Successful response.", "content": {"text/plain": {"schema": {"type": "string"}}}}}

        # FIWARE headers always
        parameters = [
            {"name": "Fiware-Service",     "in": "header", "required": True, "schema": {"type": "string", "default": "semantic_iot"}},
            {"name": "Fiware-ServicePath", "in": "header", "required": True, "schema": {"type": "string", "default": "/"}}
        ]
        if method == "put":
            parameters.insert(0, {"name": "Content-Type", "in": "header", "required": True, "schema": {"type": "string", "default": "text/plain"}})

        # Build operation object
        op = OrderedDict([
            ("tags", [tag]),
            ("summary", summary),
            ("operationId", re.sub(r"\W+", "", summary)),
            ("parameters", parameters),
            ("responses", responses)
        ])

        spec["paths"][path] = {method: op}

    # Add components section
    spec["components"] = {}
    spec["x-original-swagger-version"] = "2.0"

    return spec

# CLI entry point

def main():
    parser = argparse.ArgumentParser(description="Generate FIWARE-style OpenAPI JSON from a Turtle KG")
    parser.add_argument("--rdf",     required=True, help="Input Turtle file")
    parser.add_argument("--title",   default="IoT Platform API Specification", help="API title")
    parser.add_argument("--version", default="1.0", help="API version")
    parser.add_argument("--server",  default=None, help="Server URL (optional)")
    parser.add_argument("--output",  required=True, help="Output JSON file or directory")
    args = parser.parse_args()

    # If directory, default file name
    if os.path.isdir(args.output):
        args.output = os.path.join(args.output, "openapi_fiware.json")

    spec = build_spec(args.rdf, args.server, args.title, args.version)
    with open(args.output, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"Wrote FIWARE OpenAPI spec to {args.output}")

if __name__ == "__main__":
    main()
