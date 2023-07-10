import dataclasses
import json

from parser import Parser


query = """
    MATCH (n:Person)-[r:KNOWS]->(m:Person)-[:GOES|:WALKS]->(p:Place)
    WHERE n.name = 'Alice' AND m:Person
    RETURN *, n, m.name AS nn, p
    ORDER BY n DESC
    SKIP 10
    LIMIT 1
"""

parser = Parser(query)

print(parser.query_object)
print(json.dumps(dataclasses.asdict(parser.query_object), indent=2))
