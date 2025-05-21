import json
import re
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from semantic_iot.claude import ClaudeAPIProcessor



# TODO merge output with base path 

# TODO with description as context or not? Toggle?
# TODO      with semantic search preprocessing or not? Toggle?
# TODO          Die beste hälfte von den top matches neue semantischen suche nehmen und das alles mit Beschreibung der LLM geben
# TODO          Confidence score von anthropic ausgeben lassen? 

# How much difference is it?

# Perspective:
# Get rausfiltern
# example usage aus specs dateien

# TODO delete version detection



class APISpecProcessor:
    """
    Generic processor for OpenAPI/Swagger API specification files.
    Supports OpenAPI 2.0 (Swagger) and 3.x (OpenAPI) JSON files.
    """
    def __init__(self, spec_path: str, host_path: str = "https://example.com/") -> None:
        print(f"[APISpecProcessor] Initializing with spec file: {spec_path}")
        self.spec_path = spec_path
        self.host_path = host_path
        self.spec = self._load_spec()
        self.version = self._detect_version()
        self.base_url = self.spec.get('servers', [{}])[0].get('url', '')
        self.endpoints = self._extract_endpoints()
        print(f"[APISpecProcessor] Loaded {len(self.endpoints)} endpoints from spec.")

    def _load_spec(self) -> Dict[str, Any]:
        print(f"[APISpecProcessor] Loading spec from: {self.spec_path}")
        with open(self.spec_path, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        print(f"[APISpecProcessor] Spec loaded successfully.")
        return spec

    def _detect_version(self) -> str:
        print("[APISpecProcessor] Detecting OpenAPI/Swagger version...")
        if 'openapi' in self.spec:
            print(f"[APISpecProcessor] Detected OpenAPI version: {self.spec['openapi']}")
            return self.spec['openapi']
        elif 'swagger' in self.spec:
            print(f"[APISpecProcessor] Detected Swagger version: {self.spec['swagger']}")
            return self.spec['swagger']
        else:
            print("[APISpecProcessor] Unknown API spec version!")
            raise ValueError('Unknown API spec version')

    def _extract_endpoints(self) -> List[Dict[str, Any]]:
        print("[APISpecProcessor] Extracting endpoints from spec...")
        endpoints = []
        paths = self.spec.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                endpoint = {
                    'path': path,
                    'method': method.upper(),
                    'summary': details.get('summary', ''),
                    # 'description': details.get('description', ''),
                    # 'parameters': details.get('parameters', []),
                    'tags': details.get('tags', []),
                    'operationId': details.get('operationId', ''),
                }
                # Handle OpenAPI 3.x requestBody
                if self.version.startswith('3'):
                    if 'requestBody' in details:
                        endpoint['requestBody'] = details['requestBody']
                endpoints.append(endpoint)
        print(f"[APISpecProcessor] Extracted {len(endpoints)} endpoints.")
        return endpoints

    def _endpoint_to_chunk(self, endpoint: Dict[str, Any]) -> str:
        """
        Converts an endpoint dict to a text chunk for embedding/search.
        """
        return f"{endpoint.get('method', '')} {endpoint.get('path', '')} {endpoint.get('summary', '')}" # {endpoint.get('description', '')}"

    def build_chunks(self) -> List[str]:
        """
        Builds text chunks from all loaded endpoints.
        """
        print(f"[APISpecProcessor] Building text chunks for {len(self.endpoints)} endpoints...")
        chunks = [self._endpoint_to_chunk(ep) for ep in self.endpoints]
        print(f"[APISpecProcessor] Built {len(chunks)} chunks.")
        return chunks

    def semantic_prefilter (self, query: str, top_n: int = 3) -> Optional[Dict[str, Any]]:
        print(f"[APISpecProcessor] Matching query to endpoint: '{query}'")
        chunks = self.build_chunks()

        model = SentenceTransformer('all-MiniLM-L6-v2')
        chunk_vecs = model.encode(chunks, convert_to_tensor=True)
        query_vec = model.encode([query], convert_to_tensor=True)
        sims = (chunk_vecs @ query_vec.T).squeeze(1)
        
        top_indices = sims.argsort(descending=True)[:top_n]
        print(f"[APISpecProcessor] Top {top_n} matches:")
        for rank, idx in enumerate(top_indices):
            ep = self.endpoints[int(idx)]
            print(f"  {rank+1}. {ep['method']} {ep['path']} (score: {float(sims[idx]):.4f})")
            print(f"        Summary: {ep['summary']}")
            # print(f"        Description: {ep['description'][:100]}...")
        best_idx = int(top_indices[0])
        if float(sims[best_idx]) > 0:
            print(f"[APISpecProcessor] Best matching endpoint: {self.endpoints[best_idx]['method']} {self.endpoints[best_idx]['path']}")
            return self.endpoints[best_idx]
        print("[APISpecProcessor] No relevant endpoint found for the query.")
        return None
    
    def get_endpoint(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Matches a user query to the best endpoint using Anthropic Claude API.
        """
        print(f"[APISpecProcessor] Matching query to endpoint using LLM: '{query}'")
        # Prepare endpoint descriptions
        chunks = self.build_chunks()
        endpoint_list = "\n".join([
            f"{i+1}. {chunk}" for i, chunk in enumerate(chunks)
        ])
        prompt = (
            f"You are an expert API assistant.\n"
            f"Given the following user query and a list of API endpoints, select the single most relevant endpoint.\n"
            f"\nUser query: {query}\n\nAPI endpoints:\n{endpoint_list}\n\n"
            f"Reply ONLY with the number of the best matching endpoint. If none are relevant, reply with 0."
        )

        print(f"[APISpecProcessor] Sending prompt to LLM:\n{prompt}")
        claude = ClaudeAPIProcessor()
        response = claude.query(prompt, step_name="get_endpoint", tool_use=False)
        print(response)

        # Extract the number from the response
        match = re.search(r"(\d+)", str(response))
        if match:
            idx = int(match.group(1))
            if 1 <= idx <= len(self.endpoints):
                endpoint = self.endpoints[idx-1]

                # Prepend base_url if available and not already present
                full_path = endpoint['path']
                if self.base_url and not full_path.startswith(self.base_url):
                    full_path = self.base_url.rstrip('/') + '/' + full_path.lstrip('/')
                # Prepend host_path if not already present
                if self.host_path and not full_path.startswith(self.host_path):
                    full_path = self.host_path.rstrip('/') + '/' + full_path.lstrip('/')
                
                print(f"[APISpecProcessor] LLM selected endpoint {idx}: {endpoint['method']} {full_path}")
                endpoint_with_full_path = endpoint.copy()
                endpoint_with_full_path['full_path'] = full_path
                return endpoint_with_full_path
            else:
                raise ValueError("[APISpecProcessor] LLM did not find a relevant endpoint.")
        raise ValueError(f"[APISpecProcessor] Could not parse LLM response: {response}")


if __name__ == "__main__":

    # INPUT
    HOST_PATH = "https://fiware.eonerc.rwth-aachen.de/"

    API_SPEC_PATH = "LLM_models/API_specs/openhab_API_spec.json"
    API_SPEC_PATH = "LLM_models\API_specs\FIWAR_ngsiV2_API_spec.json"

    # Example usage
    processor = APISpecProcessor(API_SPEC_PATH, HOST_PATH)

    user_query = "Get Sensor Value"
    best_endpoint_path = processor.get_endpoint(user_query)

    print(f"\n\nBest matching endpoint path: {best_endpoint_path['full_path']}")
