You are an expert API assistant.
Given the following user query and a list of API endpoints, select the single most relevant endpoint.

User query: Get Sensor Value

API endpoints:
1. GET /v2 Retrieve API Resources
2. GET /v2/entities List Entities
3. POST /v2/entities Create Entity
4. GET /v2/entities/{entityId} Retrieve Entity
5. DELETE /v2/entities/{entityId} Remove Entity
6. GET /v2/entities/{entityId}/attrs Retrieve Entity Attributes
7. PUT /v2/entities/{entityId}/attrs Replace all entity attributes
8. POST /v2/entities/{entityId}/attrs Update or Append Entity Attributes
9. PATCH /v2/entities/{entityId}/attrs Update Existing Entity Attributes
10. GET /v2/entities/{entityId}/attrs/{attrName} Get attribute data
11. PUT /v2/entities/{entityId}/attrs/{attrName} Update Attribute Data
12. DELETE /v2/entities/{entityId}/attrs/{attrName} Remove a Single Attribute
13. GET /v2/entities/{entityId}/attrs/{attrName}/value Get Attribute Value
14. PUT /v2/entities/{entityId}/attrs/{attrName}/value Update Attribute Value
15. GET /v2/types/ List Entity Types
16. GET /v2/types/{entityType} Retrieve entity type
17. GET /v2/subscriptions List Subscriptions
18. POST /v2/subscriptions Create Subscription
19. GET /v2/subscriptions/{subscriptionId} Retrieve Subscription
20. DELETE /v2/subscriptions/{subscriptionId} Delete subscription
21. PATCH /v2/subscriptions/{subscriptionId} Update Subscription
22. GET /v2/registrations List Registrations
23. POST /v2/registrations Create Registration
24. GET /v2/registrations/{registrationId} Retrieve Registration
25. DELETE /v2/registrations/{registrationId} Delete Registration
26. PATCH /v2/registrations/{registrationId} Update Registration
27. POST /v2/op/update Update
28. POST /v2/op/query Query
29. POST /v2/op/notify Notify

Reply ONLY with the number of the best matching endpoint. If none are relevant, reply with 0.
You are an expert API assistant.
Given the following user query and a list of API endpoints, select the single most relevant endpoint.

User query: Get Sensor Value

API endpoints:
1. GET /v2 Retrieve API Resources
2. GET /v2/entities List Entities
3. POST /v2/entities Create Entity
4. GET /v2/entities/{entityId} Retrieve Entity
5. DELETE /v2/entities/{entityId} Remove Entity
6. GET /v2/entities/{entityId}/attrs Retrieve Entity Attributes
7. PUT /v2/entities/{entityId}/attrs Replace all entity attributes
8. POST /v2/entities/{entityId}/attrs Update or Append Entity Attributes
9. PATCH /v2/entities/{entityId}/attrs Update Existing Entity Attributes
10. GET /v2/entities/{entityId}/attrs/{attrName} Get attribute data
11. PUT /v2/entities/{entityId}/attrs/{attrName} Update Attribute Data
12. DELETE /v2/entities/{entityId}/attrs/{attrName} Remove a Single Attribute
13. GET /v2/entities/{entityId}/attrs/{attrName}/value Get Attribute Value
14. PUT /v2/entities/{entityId}/attrs/{attrName}/value Update Attribute Value
15. GET /v2/types/ List Entity Types
16. GET /v2/types/{entityType} Retrieve entity type
17. GET /v2/subscriptions List Subscriptions
18. POST /v2/subscriptions Create Subscription
19. GET /v2/subscriptions/{subscriptionId} Retrieve Subscription
20. DELETE /v2/subscriptions/{subscriptionId} Delete subscription
21. PATCH /v2/subscriptions/{subscriptionId} Update Subscription
22. GET /v2/registrations List Registrations
23. POST /v2/registrations Create Registration
24. GET /v2/registrations/{registrationId} Retrieve Registration
25. DELETE /v2/registrations/{registrationId} Delete Registration
26. PATCH /v2/registrations/{registrationId} Update Registration
27. POST /v2/op/update Update
28. POST /v2/op/query Query
29. POST /v2/op/notify Notify

Reply ONLY with the number of the best matching endpoint. If none are relevant, reply with 0.
I need your help to classify properties from an ontology. I want to know if the ontology would allow to connect a numerical value with a class through a property
Given a list of properties, classify them into numerical and non-numerical categories.
Properties are numerical if they (directly or inderictly through another class and property) connect an entity with a measurable quantity or quantity concept, such as temperature, count, or speed.
Properties are non-numerical if they connect an entity with a another entity or description
Return a JSON object with two keys: 'numerical' and 'non_numerical' and both a list of properties as values.The input properties are:
 ['brick:hasSubstance', 'brick:hasAssociatedTag', 'owl:disjointWith', 'owl:equivalentClass', 'rdfs:subClassOf', 'rdfs:comment', 'brick:hasQuantity', 'skos:definition', 'rdfs:label', 'rdfs:seeAlso']
I need your help to classify properties from an ontology. I want to know if the ontology would allow to connect a numerical value with a class through a property
Given a list of properties, classify them into numerical and non-numerical categories.
Properties are numerical if they (directly or inderictly through another class and property) connect an entity with a measurable quantity or quantity concept, such as temperature, count, or speed.
Properties are non-numerical if they connect an entity with a another entity or description
Return a JSON object with two keys: 'numerical' and 'non_numerical' and both a list of properties as values.The input properties are:
 ['owl:disjointWith', 'brick:hasQuantity', 'brick:hasAssociatedTag', 'rdfs:seeAlso', 'owl:equivalentClass', 'rdfs:subClassOf', 'skos:definition', 'rdfs:label', 'rdfs:comment', 'brick:hasSubstance']
