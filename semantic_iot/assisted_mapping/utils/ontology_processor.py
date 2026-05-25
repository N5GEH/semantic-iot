import re
from rdflib import Graph, RDFS, URIRef
from rdflib.namespace import SKOS


class OntologyContext:
    """Builds an ontology context string to help the LLM validate term mappings."""

    def __init__(self, ontology_path: str):
        self.graph = Graph(bind_namespaces="none")
        self.graph.parse(ontology_path, format="ttl")

    def build_context_string(self, report: dict) -> str:
        """Return ontology descriptions for every candidate class/property in the report."""
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