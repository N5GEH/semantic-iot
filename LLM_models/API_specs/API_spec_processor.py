import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from claude import ClaudeAPIProcessor

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))







# TODO Die beste hälfte von den top matches neue semantischen suche nehmen und das alles mit Beschreibung der LLM geben
# TODO Anderes Embedding Modell verwenden
# TODO Confidence score von anthropic ausgeben lassen? 










class APISpecProcessor:
    """
    Generic processor for OpenAPI/Swagger API specification files.
    Supports OpenAPI 2.0 (Swagger) and 3.x (OpenAPI) JSON files.
    """
    def __init__(self, spec_path: str):
        print(f"[APISpecProcessor] Initializing with spec file: {spec_path}")
        self.spec_path = spec_path
        self.spec = self._load_spec()
        self.version = self._detect_version()
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
                    'description': details.get('description', ''),
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
        
    def save_endpoints_to_file(self, output_path: str) -> None:
        """
        Saves all endpoints to a JSON file.
        
        Args:
            output_path: Path where the endpoints will be saved
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.endpoints, f, indent=2)

        print(f"Endpoints saved to {output_path}")

    def _endpoint_to_chunk(self, endpoint: Dict[str, Any]) -> str:
        """
        Converts an endpoint dict to a text chunk for embedding/search.
        """
        return f"{endpoint.get('method', '')} {endpoint.get('path', '')} {endpoint.get('summary', '')} {endpoint.get('description', '')}"

    def build_chunks(self) -> List[str]:
        """
        Builds text chunks from all loaded endpoints.
        """
        print(f"[APISpecProcessor] Building text chunks for {len(self.endpoints)} endpoints...")
        chunks = [self._endpoint_to_chunk(ep) for ep in self.endpoints]
        print(f"[APISpecProcessor] Built {len(chunks)} chunks.")
        return chunks

    def match_query_to_endpoint(self, query: str, top_n: int = 3) -> Optional[Dict[str, Any]]:
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
            print(f"        Description: {ep['description'][:100]}...")
        best_idx = int(top_indices[0])
        if float(sims[best_idx]) > 0:
            print(f"[APISpecProcessor] Best matching endpoint: {self.endpoints[best_idx]['method']} {self.endpoints[best_idx]['path']}")
            return self.endpoints[best_idx]
        print("[APISpecProcessor] No relevant endpoint found for the query.")
        return None
    
    def match_query_to_endpoint_LLM(self, query: str, top_n: int = 3) -> Optional[Dict[str, Any]]:
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
        # Call Claude
        # claude = ClaudeAPIProcessor()
        # response = claude.query(prompt)
        print(prompt)
        response = input("Claude response: ")
        # Extract the number from the response
        import re
        match = re.search(r"(\d+)", str(response))
        if match:
            idx = int(match.group(1))
            if 1 <= idx <= len(self.endpoints):
                print(f"[APISpecProcessor] LLM selected endpoint {idx}: {self.endpoints[idx-1]['method']} {self.endpoints[idx-1]['path']}")
                return self.endpoints[idx-1]
            else:
                print("[APISpecProcessor] LLM did not find a relevant endpoint.")
                return None
        print("[APISpecProcessor] Could not parse LLM response:", response)
        return None

if __name__ == "__main__":
    # Example usage for matching a query to an endpoint
    # processor = APISpecProcessor('endpoints.json')
    processor = APISpecProcessor('LLM_models\API_specs\FIWAR_ngsiV2_API_spec.json')
    processor = APISpecProcessor('LLM_models/API_specs/openhab_API_spec.json')

    processor.save_endpoints_to_file('LLM_models\API_specs\endpoints.json')

    user_query = input("Enter your API-related question: ")
    if not user_query.strip():
        user_query = "Get only the value of an attribute for an entity"

    use_llm = input("Use LLM for matching? (y/n): ").strip().lower() == 'y'
    if use_llm:
        best_endpoint = processor.match_query_to_endpoint_LLM(user_query, top_n=5)
    else:
        best_endpoint = processor.match_query_to_endpoint(user_query, top_n=5)
    if best_endpoint:
        print("\nBest matching endpoint:")
        print(f"Path: {best_endpoint['path']}")
        print(f"Method: {best_endpoint['method']}")
    else:
        print("No relevant endpoint found for your query.")



