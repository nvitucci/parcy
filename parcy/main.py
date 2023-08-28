import dataclasses
import json
import sys

from parser import Parser


# TODO: make this more flexible and robust
if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args):
        query = args[0]
    else:
        query = """
            MATCH (n:Person)-[r:KNOWS]->(m:Person)
            WHERE n.name = 'Alice'
            RETURN *
        """

    parser = Parser(query)

    print(parser.query_object)
    print(json.dumps(dataclasses.asdict(parser.query_object), indent=2))
