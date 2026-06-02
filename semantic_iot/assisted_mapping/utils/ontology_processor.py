import re
from rdflib import Graph, RDFS, URIRef, RDF, OWL
from rdflib.namespace import SKOS


class OntologyContext:
    """Builds an ontology context string to help the LLM validate term mappings."""

    def __init__(self, ontology_path: str):
        self.graph = Graph(bind_namespaces="none")
        self.graph.parse(ontology_path, format="ttl")

    def build_context_string(self, report: dict, bind_all: bool = False,
                              max_depth: int = None) -> str:
        """Return ontology descriptions for every candidate class/property in the report.

        When bind_all=True, includes ALL ontology classes and properties (optionally
        filtered by max_depth), not just those that appear as candidates in the report.
        This gives the LLM the full ontology to reason over when similarity matching
        produces poor results.
        """
        if bind_all:
            return self._build_full_context_string(report, max_depth)
        return self._build_candidate_context_string(report)

    def _build_candidate_context_string(self, report: dict) -> str:
        """Build context string for only the candidates that appear in the report."""
        context_prefixes = report.get("@context", {})
        lines = []
        seen = set()

        for item in report.get("@data", []):
            for cand in self._extract_candidates(item.get("class", "")):
                if cand not in seen:
                    seen.add(cand)
                    iri = self._resolve(cand, context_prefixes)
                    if iri:
                        lines.append(self._describe_class(cand, iri))

            for rel in item.get("hasRelationship", []):
                for cand in self._extract_candidates(rel.get("propertyClass", "")):
                    if cand not in seen:
                        seen.add(cand)
                        iri = self._resolve(cand, context_prefixes)
                        if iri:
                            lines.append(self._describe_property(cand, iri))

        return "\n".join(lines) if lines else "(no additional ontology context)"

    def _build_full_context_string(self, report: dict,
                                    max_depth: int = None) -> str:
        """Build context string with ALL ontology classes and object properties,
        optionally filtered by max superclass depth."""
        lines = []
        context_prefixes = report.get("@context", {})

        # Collect entity types from the report for the LLM to reference
        entity_types = [item.get("nodetype", "") for item in report.get("@data", [])]
        lines.append("ENTITY TYPES from platform data model:")
        for et in sorted(set(entity_types)):
            lines.append(f"  - {et}")
        lines.append("")

        # Compute depth for all classes if max_depth is set
        class_depths = {}
        if max_depth is not None:
            class_depths = self._compute_class_depths()

        # Include ALL ontology classes (not just report candidates)
        lines.append("ALL ONTOLOGY CLASSES:")
        for s, p, o in self.graph.triples((None, RDF.type, OWL.Class)):
            if not isinstance(s, URIRef):
                continue
            # Filter by depth if requested
            if max_depth is not None:
                depth = class_depths.get(str(s), 999)
                if depth > max_depth:
                    continue
            prefixed = self._iri_to_prefixed(str(s), context_prefixes)
            if prefixed:
                lines.append(self._describe_class(prefixed, str(s)))

        # Also include ancestor classes not typed as owl:Class
        known_iris = {str(s) for s, _, _ in self.graph.triples((None, RDF.type, OWL.Class))}
        for s in list(known_iris):
            s_uri = URIRef(s)
            for ancestor in self.graph.transitive_objects(s_uri, RDFS.subClassOf):
                ancestor_s = str(ancestor)
                if not isinstance(ancestor, URIRef) or ancestor_s in known_iris:
                    continue
                if max_depth is not None:
                    depth = class_depths.get(ancestor_s, 999)
                    if depth > max_depth:
                        continue
                known_iris.add(ancestor_s)
                prefixed = self._iri_to_prefixed(ancestor_s, context_prefixes)
                if prefixed:
                    lines.append(self._describe_class(prefixed, ancestor_s))

        # Include ALL object properties
        lines.append("")
        lines.append("ALL ONTOLOGY OBJECT PROPERTIES:")
        for s, p, o in self.graph.triples((None, RDF.type, OWL.ObjectProperty)):
            if not isinstance(s, URIRef):
                continue
            prefixed = self._iri_to_prefixed(str(s), context_prefixes)
            if prefixed:
                lines.append(self._describe_property(prefixed, str(s)))

        return "\n".join(lines) if lines else "(no ontology context)"

    def _compute_class_depths(self) -> dict:
        """Compute the superclass chain depth for every class in the ontology.

        Depth is the length of the longest rdfs:subClassOf* chain from the class
        to a root (a class with no superclasses). Returns {iri_str: depth}.
        """
        depths = {}

        def _depth(iri: URIRef, visited: set = None) -> int:
            key = str(iri)
            if key in depths:
                return depths[key]
            if visited is None:
                visited = set()
            if key in visited:
                return 0  # cycle detection
            visited.add(key)
            parents = [p for p in self.graph.objects(iri, RDFS.subClassOf)
                       if isinstance(p, URIRef)]
            if not parents:
                depths[key] = 0
                return 0
            max_parent_depth = max(_depth(p, visited.copy()) for p in parents)
            depths[key] = 1 + max_parent_depth
            return depths[key]

        for s, _, _ in self.graph.triples((None, RDF.type, OWL.Class)):
            if isinstance(s, URIRef):
                _depth(s)

        return depths

    def _iri_to_prefixed(self, iri_str: str, context: dict) -> str | None:
        """Convert a full IRI string to prefixed form using the context prefixes."""
        for prefix, ns in context.items():
            if iri_str.startswith(ns):
                return iri_str.replace(ns, prefix + ":")
        return None

    @staticmethod
    def _extract_candidates(s: str) -> list:
        cleaned = re.sub(r"\*\*TODO.*?\*\*\s*", "", s or "").strip()
        return [t for t in cleaned.split() if ":" in t]

    @staticmethod
    def _resolve(prefixed: str, context: dict) -> str | None:
        if ":" not in prefixed:
            return None
        prefix, local = prefixed.split(":", 1)
        ns = context.get(prefix)
        return (ns + local) if ns else None

    def _label(self, node: URIRef) -> str:
        lbl = self.graph.value(node, RDFS.label)
        if lbl:
            return str(lbl)
        iri = str(node)
        return iri.split("#")[-1] if "#" in iri else iri.split("/")[-1]

    def _description(self, node: URIRef) -> str | None:
        for pred in (RDFS.comment, SKOS.definition):
            val = self.graph.value(node, pred)
            if val:
                return str(val)[:180]
        return None

    def _describe_class(self, prefixed: str, iri: str) -> str:
        node = URIRef(iri)
        parts = [f"CLASS {prefixed} (label: '{self._label(node)}')"]
        desc = self._description(node)
        if desc:
            parts.append(f"description: {desc}")
        parents = [
            str(p).split("#")[-1] if "#" in str(p) else str(p).split("/")[-1]
            for p in self.graph.objects(node, RDFS.subClassOf)
            if isinstance(p, URIRef)
        ]
        if parents:
            parts.append(f"subClassOf: {', '.join(parents[:4])}")
        return "\n".join(parts)

    def _describe_property(self, prefixed: str, iri: str) -> str:
        node = URIRef(iri)
        parts = [f"PROPERTY {prefixed} (label: '{self._label(node)}')"]
        desc = self._description(node)
        if desc:
            parts.append(f"description: {desc}")

        def local(u):
            s = str(u)
            return s.split("#")[-1] if "#" in s else s.split("/")[-1]

        domains = [local(d) for d in self.graph.objects(node, RDFS.domain) if isinstance(d, URIRef)]
        ranges = [local(r) for r in self.graph.objects(node, RDFS.range) if isinstance(r, URIRef)]
        if domains:
            parts.append(f"domain: {', '.join(domains[:3])}")
        if ranges:
            parts.append(f"range: {', '.join(ranges[:3])}")
        return "\n".join(parts)