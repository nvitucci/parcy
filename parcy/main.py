import sys

from lark.reconstruct import Reconstructor
from parser import Parser, _parser

# TODO: make this more flexible and robust
if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args):
        query = args[0]
    else:
        query = """
            MATCH (n) RETURN n
        """

    parser = Parser(query)

    print(parser.query_object)
    print(parser.tree.pretty())

    def postproc(items):
        for item in items:
            yield f"{item} "

    print(parser.tree)
    reconstructed = Reconstructor(_parser).reconstruct(parser.tree, postproc=postproc)
    print(reconstructed)
