# ParCy: a Parser for Cypher

Tool for parsing a Cypher query into Python object and JSON format.

Example Cypher query:

```
MATCH (n:Person) RETURN n
```

Resulting Python object:

```
Query(
    [Match([NodePattern(Variable("n"), ["Person"])])],
    Projection([ProjectionItem(PropertyLabelExpression(Variable("n")))]),
)
```

## FAQ

- What version of Cypher does the parser use?

openCypher only (current version is M23). The reference EBNF grammar is downloaded from http://opencypher.org/resources/.

- How much of the code is AI-generated?

None. Any similarity with existing code is either coincidental or referenced to the original.

## TODO

- Convert to proper package (move `tests` folder out, create `setup.py`/`pyproject.toml`, etc.)
- Confirm the chosen license is the best one
- Add query creation/reconstruction