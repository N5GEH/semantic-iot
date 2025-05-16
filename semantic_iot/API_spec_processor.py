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
        response = claude.query(prompt)
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









'''
You are an expert API assistant.
Given the following user query and a list of API endpoints, select the single most relevant endpoint.

User query: Get Sensor Value

API endpoints:
1. GET /module-types Get all available module types.
2. GET /module-types/{moduleTypeUID} Gets a module type corresponding to the given UID.
3. GET /rules Get available rules, optionally filtered by tags and/or prefix.
4. POST /rules Creates a rule.
5. POST /rules/{ruleUID}/enable Sets the rule enabled status.
6. GET /rules/{ruleUID}/actions Gets the rule actions.
7. GET /rules/{ruleUID} Gets the rule corresponding to the given UID.
8. PUT /rules/{ruleUID} Updates an existing rule corresponding to the given UID.
9. DELETE /rules/{ruleUID} Removes an existing rule corresponding to the given UID.
10. GET /rules/{ruleUID}/conditions Gets the rule conditions.
11. GET /rules/{ruleUID}/config Gets the rule configuration values.
12. PUT /rules/{ruleUID}/config Sets the rule configuration values.
13. GET /rules/{ruleUID}/{moduleCategory}/{id} Gets the rule's module corresponding to the given Category and ID.
14. GET /rules/{ruleUID}/{moduleCategory}/{id}/config Gets the module's configuration.
15. GET /rules/{ruleUID}/{moduleCategory}/{id}/config/{param} Gets the module's configuration parameter.
16. PUT /rules/{ruleUID}/{moduleCategory}/{id}/config/{param} Sets the module's configuration parameter value.
17. GET /rules/{ruleUID}/triggers Gets the rule triggers.
18. POST /rules/{ruleUID}/runnow Executes actions of the rule.
19. GET /rules/schedule/simulations Simulates the executions of rules filtered by tag 'Schedule' within the given times.
20. GET /templates Get all available templates.
21. GET /templates/{templateUID} Gets a template corresponding to the given UID.
22. POST /actions/{thingUID}/{actionUid} Executes a thing action.
23. GET /actions/{thingUID} Get all available actions for provided thing UID
24. GET /uuid A unified unique id.
25. GET /audio/defaultsink Get the default sink if defined or the first available sink.
26. GET /audio/defaultsource Get the default source if defined or the first available source.
27. GET /audio/sinks Get the list of all sinks.
28. GET /audio/sources Get the list of all sources.
29. POST /auth/logout Delete the session associated with a refresh token.
30. GET /auth/apitokens List the API tokens associated to the authenticated user.
31. GET /auth/sessions List the sessions associated to the authenticated user.
32. POST /auth/token Get access and refresh tokens.
33. DELETE /auth/apitokens/{name} Revoke a specified API token associated to the authenticated user.
34. GET /addons Get all add-ons.
35. GET /addons/{addonId} Get add-on with given ID.
36. GET /addons/{addonId}/config Get add-on configuration for given add-on ID.
37. PUT /addons/{addonId}/config Updates an add-on configuration for given ID and returns the old configuration.
38. GET /addons/services Get all add-on types.
39. GET /addons/suggestions Get suggested add-ons to be installed.
40. GET /addons/types Get add-on services.
41. POST /addons/{addonId}/install Installs the add-on with the given ID.
42. POST /addons/url/{url}/install Installs the add-on from the given URL.
43. POST /addons/{addonId}/uninstall Uninstalls the add-on with the given ID.
44. GET /channel-types Gets all available channel types.
45. GET /channel-types/{channelTypeUID} Gets channel type by UID.
46. GET /channel-types/{channelTypeUID}/linkableItemTypes Gets the item types the given trigger channel type UID can be linked to.
47. GET /config-descriptions Gets all available config descriptions.
48. GET /config-descriptions/{uri} Gets a config description by URI.
49. GET /discovery Gets all bindings that support discovery.
50. POST /discovery/bindings/{bindingId}/scan Starts asynchronous discovery process for a binding and returns the timeout in seconds of the discovery operation.
51. POST /inbox/{thingUID}/approve Approves the discovery result by adding the thing to the registry.
52. DELETE /inbox/{thingUID} Removes the discovery result from the inbox.
53. GET /inbox Get all discovered things.
54. POST /inbox/{thingUID}/ignore Flags a discovery result as ignored for further processing.
55. POST /inbox/{thingUID}/unignore Removes ignore flag from a discovery result.
56. PUT /items/{itemName}/members/{memberItemName} Adds a new member to a group item.
57. DELETE /items/{itemName}/members/{memberItemName} Removes an existing member from a group item.
58. PUT /items/{itemname}/metadata/{namespace} Adds metadata to an item.
59. DELETE /items/{itemname}/metadata/{namespace} Removes metadata from an item.
60. PUT /items/{itemname}/tags/{tag} Adds a tag to an item.
61. DELETE /items/{itemname}/tags/{tag} Removes a tag from an item.
62. GET /items/{itemname} Gets a single item.
63. PUT /items/{itemname} Adds a new item to the registry or updates the existing item.
64. POST /items/{itemname} Sends a command to an item.
65. DELETE /items/{itemname} Removes an item from the registry.
66. GET /items Get all available items.
67. PUT /items Adds a list of items to the registry or updates the existing items.
68. GET /items/{itemname}/state Gets the state of an item.
69. PUT /items/{itemname}/state Updates the state of an item.
70. GET /items/{itemname}/metadata/namespaces Gets the namespace of an item.
71. GET /items/{itemName}/semantic/{semanticClass} Gets the item which defines the requested semantics of an item.
72. POST /items/metadata/purge Remove unused/orphaned metadata.
73. GET /links Gets all available links.
74. GET /links/{itemName}/{channelUID} Retrieves an individual link.
75. PUT /links/{itemName}/{channelUID} Links an item to a channel.
76. DELETE /links/{itemName}/{channelUID} Unlinks an item from a channel.
77. GET /links/orphans Get orphan links between items and broken/non-existent thing channels
78. POST /links/purge Remove unused/orphaned links.
79. DELETE /links/{object} Delete all links that refer to an item or thing.
80. GET /persistence/{serviceId} Gets a persistence service configuration.
81. PUT /persistence/{serviceId} Sets a persistence service configuration.
82. DELETE /persistence/{serviceId} Deletes a persistence service configuration.
83. GET /persistence/items/{itemname} Gets item persistence data from the persistence service.
84. PUT /persistence/items/{itemname} Stores item persistence data into the persistence service.
85. DELETE /persistence/items/{itemname} Deletes item persistence data from a specific persistence service in a given time range.
86. GET /persistence/items Gets a list of items available via a specific persistence service.
87. GET /persistence Gets a list of persistence services.
88. GET /profile-types Gets all available profile types.
89. GET /services/{serviceId}/config Get service configuration for given service ID.
90. PUT /services/{serviceId}/config Updates a service configuration for given service ID and returns the old configuration.
91. DELETE /services/{serviceId}/config Deletes a service configuration for given service ID and returns the old configuration.
92. GET /services Get all configurable services.
93. GET /services/{serviceId} Get configurable service for given service ID.
94. GET /services/{serviceId}/contexts Get existing multiple context service configurations for the given factory PID.
95. GET /tags Get all available semantic tags.
96. POST /tags Creates a new semantic tag and adds it to the registry.
97. GET /tags/{tagId} Gets a semantic tag and its sub tags.
98. PUT /tags/{tagId} Updates a semantic tag.
99. DELETE /tags/{tagId} Removes a semantic tag and its sub tags from the registry.
100. GET /things Get all available things.
101. POST /things Creates a new thing and adds it to the registry.
102. GET /things/{thingUID} Gets thing by UID.
103. PUT /things/{thingUID} Updates a thing.
104. DELETE /things/{thingUID} Removes a thing from the registry. Set 'force' to __true__ if you want the thing to be removed immediately.
105. GET /things/{thingUID}/config/status Gets thing config status.
106. GET /things/{thingUID}/firmware/status Gets thing's firmware status.
107. GET /things/{thingUID}/firmwares Get all available firmwares for provided thing UID
108. GET /things/{thingUID}/status Gets thing status.
109. PUT /things/{thingUID}/enable Sets the thing enabled status.
110. PUT /things/{thingUID}/config Updates thing's configuration.
111. PUT /things/{thingUID}/firmware/{firmwareVersion} Update thing firmware.
112. GET /thing-types Gets all available thing types without config description, channels and properties.
113. GET /thing-types/{thingTypeUID} Gets thing type by UID.
114. GET / Gets information about the runtime, the API version and links to resources.
115. GET /systeminfo Gets information about the system.
116. GET /systeminfo/uom Get all supported dimensions and their system units.
117. POST /sitemaps/events/subscribe Creates a sitemap event subscription.
118. GET /sitemaps/{sitemapname}/{pageid} Polls the data for one page of a sitemap.
119. GET /sitemaps/{sitemapname}/* Polls the data for a whole sitemap. Not recommended due to potentially high traffic.
120. GET /sitemaps/{sitemapname} Get sitemap by name.
121. GET /sitemaps/events/{subscriptionid}/* Get sitemap events for a whole sitemap. Not recommended due to potentially high traffic.
122. GET /sitemaps/events/{subscriptionid} Get sitemap events.
123. GET /sitemaps Get all available sitemaps.
124. GET /events/states Initiates a new item state tracker connection
125. GET /events Get all events.
126. POST /events/states/{connectionId} Changes the list of items a SSE connection will receive state updates to.
127. GET /transformations/{uid} Get a single transformation
128. PUT /transformations/{uid} Put a single transformation
129. DELETE /transformations/{uid} Get a single transformation
130. GET /transformations/services Get all transformation services
131. GET /transformations Get a list of all transformations
132. GET /ui/components/{namespace} Get all registered UI components in the specified namespace.
133. POST /ui/components/{namespace} Add a UI component in the specified namespace.
134. GET /ui/components/{namespace}/{componentUID} Get a specific UI component in the specified namespace.
135. PUT /ui/components/{namespace}/{componentUID} Update a specific UI component in the specified namespace.
136. DELETE /ui/components/{namespace}/{componentUID} Remove a specific UI component in the specified namespace.
137. GET /ui/tiles Get all registered UI tiles.
138. GET /voice/defaultvoice Gets the default voice.
139. GET /voice/interpreters/{id} Gets a single interpreter.
140. GET /voice/interpreters Get the list of all interpreters.
141. POST /voice/interpreters Sends a text to the default human language interpreter.
142. GET /voice/voices Get the list of all voices.
143. POST /voice/interpreters/{ids} Sends a text to a given human language interpreter(s).
144. POST /voice/listenandanswer Executes a simple dialog sequence without keyword spotting for a given audio source.
145. POST /voice/say Speaks a given text with a given voice through the given audio sink.
146. POST /voice/dialog/start Start dialog processing for a given audio source.
147. POST /voice/dialog/stop Stop dialog processing for a given audio source.
148. GET /logging/{loggerName} Get a single logger.
149. PUT /logging/{loggerName} Modify or add logger
150. DELETE /logging/{loggerName} Remove a single logger.
151. GET /logging Get all loggers
152. GET /iconsets Gets all icon sets.
153. GET /habpanel/gallery/{galleryName}/widgets Gets the list of widget gallery items.
154. GET /habpanel/gallery/{galleryName}/widgets/{id} Gets the details about a widget gallery item.

Reply ONLY with the number of the best matching endpoint. If none are relevant, reply with 0.



OUTPUT:
After analyzing your query and the list of API endpoints, I need to select the most relevant endpoint for "Get Sensor Value".

The request is about getting a sensor value, which in API terms would typically refer to retrieving the current state or measurement from a sensor. Looking through the provided endpoints, I notice that sensors would likely be represented as "items" in this API system.

The most relevant endpoint would be:

68. GET /items/{itemname}/state Gets the state of an item.

This endpoint allows you to retrieve the current state (value) of a specific item, which would include sensor readings. You would need to replace {itemname} with the specific identifier of your sensor.
'''