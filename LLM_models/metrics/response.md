<output>
```json
{
  "numerical": [
    "brick:hasQuantity"
  ],
  "non_numerical": [
    "rdfs:subClassOf",
    "owl:disjointWith", 
    "rdfs:seeAlso",
    "skos:definition",
    "owl:equivalentClass",
    "rdfs:comment",
    "brick:deprecatedInVersion",
    "brick:hasSubstance",
    "brick:aliasOf",
    "rdfs:label",
    "brick:isReplacedBy",
    "brick:hasAssociatedTag",
    "owl:deprecated",
    "brick:deprecationMitigationMessage"
  ]
}
```
</output>
<output>
```json
{
  "numerical": [
    "brick:hasQuantity"
  ],
  "non_numerical": [
    "rdfs:seeAlso",
    "brick:hasAssociatedTag", 
    "owl:disjointWith",
    "rdfs:subClassOf",
    "rdfs:label",
    "skos:definition"
  ]
}
```
</output>
Looking at each property, I need to determine whether it connects entities to measurable quantities/quantity concepts (numerical) or to other entities/descriptions (non-numerical).

<output>
{
  "numerical": [
    "brick:hasQuantity"
  ],
  "non_numerical": [
    "owl:equivalentClass",
    "owl:disjointWith", 
    "brick:hasSubstance",
    "rdfs:seeAlso",
    "rdfs:label",
    "rdfs:comment",
    "rdfs:subClassOf",
    "brick:hasAssociatedTag",
    "skos:definition"
  ]
}
</output>
