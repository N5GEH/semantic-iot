I need your help to classify properties from an ontology. I want to know if the ontology would allow to connect a numerical value with a class through a property
Given a list of properties, classify them into numerical and non-numerical categories.
Properties are numerical if they (directly or inderictly through another class and property) connect an entity with a measurable quantity or quantity concept, such as temperature, count, or speed.
Properties are non-numerical if they connect an entity with a another entity or description
Return a JSON object with two keys: 'numerical' and 'non_numerical' and both a list of properties as values.The input properties are:
 ['rdfs:subClassOf', 'owl:disjointWith', 'rdfs:seeAlso', 'skos:definition', 'owl:equivalentClass', 'rdfs:comment', 'brick:deprecatedInVersion', 'brick:hasQuantity', 'brick:hasSubstance', 'brick:aliasOf', 'rdfs:label', 'brick:isReplacedBy', 'brick:hasAssociatedTag', 'owl:deprecated', 'brick:deprecationMitigationMessage']
I need your help to classify properties from an ontology. I want to know if the ontology would allow to connect a numerical value with a class through a property
Given a list of properties, classify them into numerical and non-numerical categories.
Properties are numerical if they (directly or inderictly through another class and property) connect an entity with a measurable quantity or quantity concept, such as temperature, count, or speed.
Properties are non-numerical if they connect an entity with a another entity or description
Return a JSON object with two keys: 'numerical' and 'non_numerical' and both a list of properties as values.The input properties are:
 ['rdfs:seeAlso', 'brick:hasQuantity', 'brick:hasAssociatedTag', 'owl:disjointWith', 'rdfs:subClassOf', 'rdfs:label', 'skos:definition']
I need your help to classify properties from an ontology. I want to know if the ontology would allow to connect a numerical value with a class through a property
Given a list of properties, classify them into numerical and non-numerical categories.
Properties are numerical if they (directly or inderictly through another class and property) connect an entity with a measurable quantity or quantity concept, such as temperature, count, or speed.
Properties are non-numerical if they connect an entity with a another entity or description
Return a JSON object with two keys: 'numerical' and 'non_numerical' and both a list of properties as values.The input properties are:
 ['owl:equivalentClass', 'owl:disjointWith', 'brick:hasSubstance', 'rdfs:seeAlso', 'rdfs:label', 'brick:hasQuantity', 'rdfs:comment', 'rdfs:subClassOf', 'brick:hasAssociatedTag', 'skos:definition']
