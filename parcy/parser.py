import pathlib

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union

import lark.exceptions
from lark import Lark, Transformer, Tree
from lark.lexer import Token


class Direction(str, Enum):
    NONE = "none"
    BOTH = "both"
    RIGHT = "right"
    LEFT = "left"


class Operator(str, Enum):
    COMP_EQ = "="
    COMP_NEQ = "<>"
    COMP_LT = "<"
    COMP_LTE = "<="
    COMP_GT = ">"
    COMP_GTE = ">="


class Atom(ABC):
    pass


class Expression(Atom, ABC):
    pass


@dataclass
class Literal(Atom):
    value: Union[str, int, list]


@dataclass
class Property:
    name: str


@dataclass
class Variable(Atom):
    name: str


@dataclass
class PartialComparison(Expression):
    op: Operator
    expr: Expression


@dataclass
class Comparison(Expression):
    expr1: Expression
    expr2: Expression


@dataclass
class SortItem:
    var: Variable
    direction: str


@dataclass
class Order:
    vars: List[SortItem]


@dataclass(frozen=True)
class Range:
    low: int
    high: Optional[int]


@dataclass
class BaseExpression(Expression):
    # TODO: is this the best name?
    expr1: object


@dataclass
class AndExpression(Expression):
    exprs: List[Expression]


@dataclass
class OrExpression(Expression):
    exprs: List[Expression]


@dataclass
class XorExpression(Expression):
    exprs: List[Expression]


@dataclass
class NotExpression(Expression):
    expr: Expression
    neg: bool = False


@dataclass
class ProjectionItem:
    expr: Expression
    var: Optional[Variable] = None


@dataclass
class Projection:
    projections: List[ProjectionItem]
    distinct: bool = False
    order: Optional[SortItem] = None
    skip: Optional[Expression] = None
    limit: Optional[Expression] = None


@dataclass
class NodePattern:
    variable: Optional[Variable] = None
    labels: List[str] = field(default_factory=list)
    properties: dict = field(default_factory=dict)


@dataclass
class RelationshipPattern:
    direction: Direction
    variable: Optional[Variable] = None
    types: list = field(default_factory=list)
    range: Range = Range(1, 1)
    properties: dict = field(default_factory=dict)


@dataclass
class PatternElement:
    rel: RelationshipPattern
    node: NodePattern


@dataclass
class Match:
    pattern: List[Union[NodePattern, PatternElement]]
    where: Optional[Expression] = None


@dataclass
class Query:
    matches: List[Match]
    ret: Projection


@dataclass
class PropertyLabelExpression(Expression):
    atom: Atom
    properties: list = field(default_factory=list)
    node_labels: list = field(default_factory=list)


class CustomTransformer(Transformer):
    def sort_item(self, c):
        return SortItem(c[0], c[1].value)

    def order(self, c):
        return Order(c)

    def and_expression(self, c):
        return AndExpression(c)

    def or_expression(self, c):
        return OrExpression(c)

    def xor_expression(self, c):
        return XorExpression(c)

    def not_expression(self, c):
        assert len(c) > 1

        # Count and cancel out the NOTs
        is_not = len(c[:-1]) % 2 == 1
        # The expression is always the last element
        expr = c[-1]

        return NotExpression(expr, is_not)

    def projection_body(self, c):
        return Projection(
            distinct=True if len(c) > 1 and c[0] is not None else False,
            projections=c[0] if len(c) >= 1 else None,
            order=c[1] if len(c) > 2 else None,
            skip=c[2] if len(c) > 3 else None,
            limit=c[3] if len(c) > 4 else None,
        )

    def projection_items(self, c):
        return [el.value if isinstance(el, Token) else el for el in c]

    def projection_item(self, c):
        if len(c) == 1:
            return ProjectionItem(c[0])
        elif len(c) == 2:
            return ProjectionItem(c[0], c[1])
        else:
            raise ValueError(f"ProjectionItem {c} has wrong length")

    def comparison_expression(self, c):
        if len(c) == 1:
            return BaseExpression(c[0])
        elif len(c) == 2:
            return Comparison(c[0], c[1])
        else:
            raise NotImplementedError("Comparison with multiple expressions not supported")

    def partial_comparison_expression(self, c):
        return PartialComparison(Operator[c[0].type], c[1])

    def property_or_labels_expression(self, c):
        return PropertyLabelExpression(
            c[0],
            [el for el in c if isinstance(el, Property)],
            c[-1] if c[-1] is not None else [],
        )

    def atom(self, c):
        assert len(c) == 1
        return c[0]

    def literal(self, c):
        if isinstance(c[0], Tree):
            return Literal(c[0].data.value)
        elif isinstance(c[0], Token):
            return Literal(c[0].value)
        elif isinstance(c[0], list) or isinstance(c[0], int):
            return Literal(c[0])
        else:
            raise ValueError(f"Unknown type for {c}")

    def number_literal(self, c):
        assert len(c) == 1

        return int(c[0])

    def list_literal(self, c):
        return [el for el in c]

    def map_literal(self, c):
        properties = [el.name for i, el in enumerate(c) if i % 2 == 0]
        values = [el for i, el in enumerate(c) if i % 2 == 1]
        return dict(zip(properties, values))

    def property_key_name(self, c):
        return Property(c[0].value)

    def variable(self, c):
        assert len(c) == 1

        return Variable(c[0].value)

    def label_name(self, c):
        assert len(c) == 1
        assert isinstance(c[0], Token)

        return c[0].value

    def node_label(self, c):
        assert len(c) == 1

        return c[0]

    def node_labels(self, c):
        return c

    def node_pattern(self, c):
        return NodePattern(
            c[0] if len(c) else None,
            c[1] if len(c) > 1 and c[1] is not None else [],
            c[2] if len(c) > 2 and c[2] is not None else {},
        )

    def rel_type_name(self, c):
        assert len(c) == 1
        assert isinstance(c[0], Token)

        return c[0].value

    def relationship_types(self, c):
        return c

    def range_literal(self, c):
        upper_bound = None

        if c is not None:
            assert len(c) == 3

            # Do not use structural pattern matching to it is compatible with Python < 3.10
            if c[0] is not None and c[2] is not None:
                range_ = (int(c[0].value), int(c[2].value))
            elif c[0] is not None and c[2] is None:
                if c[1] is not None:
                    range_ = (int(c[0].value), upper_bound)
                else:
                    range_ = (int(c[0].value), int(c[0].value))
            elif c[0] is None and c[2] is not None:
                range_ = (1, int(c[2].value))
            else:
                range_ = (1, upper_bound)
        else:
            range_ = (1, 1)

        return Range(range_[0], range_[1])

    def relationship_pattern(self, c):
        # TODO: use symbol? e.g. `parser.get_terminal("DASH").pattern.value`
        if c[0] == "<" and c[1] == "-":
            if c[-1] == ">":
                direction = Direction.BOTH
            else:
                assert c[-1] == "-"
                direction = Direction.LEFT

            rel = c[2]
        else:
            assert c[0] == "-"

            if c[-1] == ">":
                direction = Direction.RIGHT
            else:
                assert c[-1] == "-"
                direction = Direction.NONE

            rel = c[1]

        return RelationshipPattern(
            direction,
            rel.children[0],
            rel.children[1] if rel.children[1] is not None else [],
            rel.children[2] if rel.children[2] else Range(1, 1),
            rel.children[3] if rel.children[3] is not None else {},
        )

    def pattern_element_chain(self, c):
        return PatternElement(c[0], c[1])

    def pattern(self, c):
        return c

    def match(self, c):
        return Match(c[0], c[1] if len(c) > 1 else None)

    def single_query(self, c):
        return Query(c[:-1], c[-1])


with open(pathlib.Path(__file__).parent / "grammar.txt") as f:
    _grammar = "".join(f.readlines())

_parser = Lark(_grammar, start="single_query", parser="lalr", maybe_placeholders=False)


class Parser:
    def __init__(self, query):
        try:
            self.tree = _parser.parse(query)
        except lark.exceptions.ParseError as e:
            raise ParseError(e)
        self.query_object = CustomTransformer().transform(self.tree)


class ParseError(Exception):
    pass
