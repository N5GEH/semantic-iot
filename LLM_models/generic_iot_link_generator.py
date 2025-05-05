import json
import re
from typing import Dict, Any
from LLM_models.claude import ClaudeAPIProcessor

class GenericIoTLinkGenerator:
    def __init__(self, llm_api_key: str = "", model: str = "claude-3-5-sonnet-20241022"):
        self.llm = ClaudeAPIProcessor(api_key=llm_api_key, model=model)

    def extract_relevant_paths(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts only the relevant paths from the API spec that contain placeholders for entity IDs and attribute names.
        Returns a dict of path templates and their method descriptions.
        """
        relevant = {}
        for path, methods in api_spec.get("paths", {}).items():
            if re.search(r"\{.*entity.*\}", path, re.IGNORECASE) and (
                re.search(r"\{.*attr.*\}", path, re.IGNORECASE) or 'attrs' in path or 'attribute' in path
            ):
                relevant[path] = {}
                for method, details in methods.items():
                    relevant[path][method] = {
                        "summary": details.get("summary", ""),
                        "description": details.get("description", "")
                    }
        return relevant

    def generate_attribute_link(self, api_spec_path: str, entity_id: str, attribute: str) -> str:
        """
        Generate a link to access the value of an attribute for a given entity, based on the provided API spec file.
        Only sends relevant path templates and descriptions to the LLM.
        """
        with open(api_spec_path, 'r', encoding='utf-8') as f:
            api_spec = json.load(f)
        relevant_paths = self.extract_relevant_paths(api_spec)
        host = api_spec.get("host", "")
        base_path = api_spec.get("basePath", "")
        scheme = api_spec.get("schemes", ["http"])[0]
        prompt = (
            f"Given these API path templates and their descriptions from an IoT platform OpenAPI/Swagger spec, "
            f"generate the correct URL to access the value of the attribute for the entity. "
            f"Replace placeholders with the provided entity ID and attribute name.\n"
            f"Paths: {json.dumps(relevant_paths, indent=2)}\n"
            f"Host: {host}\nBase path: {base_path}\nScheme: {scheme}\n"
            f"entityId: {entity_id}\nattribute: {attribute}\n"
            f"Return only the full URL."
        )
        link = self.llm.query(prompt)
        if isinstance(link, dict) and 'content' in link:
            return link['content'][0]['text'].strip()
        elif isinstance(link, str):
            return link.strip()
        else:
            return ""