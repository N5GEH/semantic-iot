import json


SYSTEM_PROMPT = (
    "You are an expert in semantic web technologies and IoT ontologies."
    "You validate and correct RDF term mappings for a Knowledge Graph Construction pipeline."
)


def build_validation_prompt(report: dict, ontology_context: str, ontology_name: str) -> str:
    return f"""You must validate and correct an intermediate report that maps IoT platform entity types to ontology classes and properties.

Fields marked with **TODO: PLEASE CHECK** contain auto-generated candidates — pick exactly ONE correct value for each.

<ontology_name>{ontology_name}</ontology_name>

<ontology_context>
{ontology_context}
</ontology_context>

<intermediate_report>
{json.dumps(report, indent=2)}
</intermediate_report>

<instructions>
For EACH entry in @data:
1. "class" — select the single best-matching ontology class from the candidates listed after **TODO: PLEASE CHECK**. Use prefixed form (e.g. "brick:Temperature_Sensor"). If none of the candidates fits, choose the most appropriate class from the ontology.
2. "hasRelationship[].propertyClass" — select the single correct object property. Consider semantic direction: the property domain must match the subject node class and range must match the object node class.
3. Keep all other fields (nodetype, iterator, hasDataAccess, rawdataidentifier, relatedNodeType) unchanged.
4. Do NOT add or remove node types or relationships.
</instructions>

<constraints>
- Return ONLY a valid JSON object with the same structure (@context + @data).
- Every "class" and "propertyClass" must be a single prefixed string — no TODO markers, no multiple values, no nulls.
- No explanation text outside the JSON.
</constraints>"""
