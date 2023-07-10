import pytest

from parcy.parser import (
    AndExpression,
    Comparison,
    Direction,
    Match,
    Literal,
    NodePattern,
    OrExpression,
    NotExpression,
    ParseError,
    Parser,
    PartialComparison,
    Projection,
    ProjectionItem,
    Property,
    PropertyLabelExpression,
    Range,
    RelationshipPattern,
    Query,
    Variable,
    Operator,
    PatternElement,
)


class TestParser:
    def test_match_without_return(self):
        query = "MATCH (n)"

        with pytest.raises(ParseError):
            Parser(query)

    def test_match(self):
        query = "MATCH (n) RETURN n"
        parser = Parser(query)

        test_qo = Query(
            [Match([NodePattern(Variable("n"))])],
            Projection([ProjectionItem(PropertyLabelExpression(Variable("n")))]),
        )

        assert parser.query_object == test_qo

    def test_match_label(self):
        query = "MATCH (n:Person) RETURN n"
        parser = Parser(query)

        test_qo = Query(
            [Match([NodePattern(Variable("n"), ["Person"])])],
            Projection([ProjectionItem(PropertyLabelExpression(Variable("n")))]),
        )

        assert parser.query_object == test_qo

    def test_match_props(self):
        query = "MATCH (n {name: 'Alice'}) RETURN n"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                            [],
                            {
                                "name": PropertyLabelExpression(
                                    Literal("'Alice'"),
                                ),
                            },
                        )
                    ]
                )
            ],
            Projection([ProjectionItem(PropertyLabelExpression(Variable("n")))]),
        )

        assert parser.query_object == test_qo

    def test_match_label_props(self):
        query = "MATCH (n:Person {name: 'Alice'}) RETURN n"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                            ["Person"],
                            {
                                "name": PropertyLabelExpression(
                                    Literal("'Alice'"),
                                ),
                            },
                        )
                    ]
                )
            ],
            Projection([ProjectionItem(PropertyLabelExpression(Variable("n")))]),
        )

        assert parser.query_object == test_qo

    def test_match_label_props_return_prop(self):
        query = "MATCH (n:Person {name: 'Alice'}) RETURN n.name"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                            ["Person"],
                            {
                                "name": PropertyLabelExpression(
                                    Literal("'Alice'"),
                                ),
                            },
                        )
                    ]
                )
            ],
            Projection([ProjectionItem(PropertyLabelExpression(Variable("n"), [Property("name")]))]),
        )

        assert parser.query_object == test_qo

    @pytest.mark.parametrize(
        "pattern, exp_direction",
        [
            ("(n)-[r]-(m)", Direction.NONE),
            ("(n)-[r]->(m)", Direction.RIGHT),
            ("(n)<-[r]-(m)", Direction.LEFT),
            ("(n)<-[r]->(m)", Direction.BOTH),
        ],
    )
    def test_empty_rel_pattern(self, pattern, exp_direction):
        query = f"MATCH {pattern} RETURN *"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                        ),
                        PatternElement(
                            RelationshipPattern(
                                exp_direction,
                                Variable("r"),
                            ),
                            NodePattern(Variable("m")),
                        ),
                    ],
                )
            ],
            Projection(
                ["*"],
            ),
        )

        assert parser.query_object == test_qo

    @pytest.mark.parametrize(
        "pattern, range_",
        [
            ("(n)-[r*0..]-(m)", Range(0, None)),
            ("(n)-[r*3]-(m)", Range(3, 3)),
            ("(n)-[r*..3]-(m)", Range(1, 3)),
            ("(n)-[r*1..5]-(m)", Range(1, 5)),
            ("(n)-[r*]-(m)", Range(1, None)),
        ],
    )
    def test_empty_rel_range(self, pattern, range_):
        query = f"MATCH {pattern} RETURN *"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                        ),
                        PatternElement(
                            RelationshipPattern(Direction.NONE, Variable("r"), range=range_),
                            NodePattern(Variable("m")),
                        ),
                    ],
                )
            ],
            Projection(
                ["*"],
            ),
        )

        assert parser.query_object == test_qo

    def test_where_or(self):
        query = "MATCH (n:Person) WHERE name = 'Alice' OR age = 42 RETURN n"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                            ["Person"],
                        ),
                    ],
                    OrExpression(
                        [
                            Comparison(
                                PropertyLabelExpression(Variable("name")),
                                PartialComparison(
                                    Operator.COMP_EQ,
                                    PropertyLabelExpression(Literal("'Alice'")),
                                ),
                            ),
                            Comparison(
                                PropertyLabelExpression(Variable("age")),
                                PartialComparison(
                                    Operator.COMP_EQ,
                                    PropertyLabelExpression(Literal("42")),
                                ),
                            ),
                        ]
                    ),
                ),
            ],
            Projection(
                [
                    ProjectionItem(
                        PropertyLabelExpression(Variable("n")),
                    )
                ],
            ),
        )

        assert parser.query_object == test_qo

    def test_where_and(self):
        query = "MATCH (n:Person) WHERE name = 'Alice' AND age = 42 RETURN n"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                            ["Person"],
                        ),
                    ],
                    AndExpression(
                        [
                            Comparison(
                                PropertyLabelExpression(Variable("name")),
                                PartialComparison(
                                    Operator.COMP_EQ,
                                    PropertyLabelExpression(Literal("'Alice'")),
                                ),
                            ),
                            Comparison(
                                PropertyLabelExpression(Variable("age")),
                                PartialComparison(
                                    Operator.COMP_EQ,
                                    PropertyLabelExpression(Literal("42")),
                                ),
                            ),
                        ]
                    ),
                ),
            ],
            Projection(
                [
                    ProjectionItem(
                        PropertyLabelExpression(Variable("n")),
                    )
                ],
            ),
        )

        assert parser.query_object == test_qo

    def test_where_or_and_not(self):
        query = "MATCH (n:Person) WHERE name = 'Alice' OR (age < 42 AND NOT age >= 20) RETURN n"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                            ["Person"],
                        ),
                    ],
                    OrExpression(
                        [
                            Comparison(
                                PropertyLabelExpression(Variable("name")),
                                PartialComparison(
                                    Operator.COMP_EQ,
                                    PropertyLabelExpression(Literal("'Alice'")),
                                ),
                            ),
                            PropertyLabelExpression(
                                AndExpression(
                                    [
                                        Comparison(
                                            PropertyLabelExpression(Variable("age")),
                                            PartialComparison(
                                                Operator.COMP_LT,
                                                PropertyLabelExpression(Literal("42")),
                                            ),
                                        ),
                                        NotExpression(
                                            Comparison(
                                                PropertyLabelExpression(Variable("age")),
                                                PartialComparison(
                                                    Operator.COMP_GTE,
                                                    PropertyLabelExpression(Literal("20")),
                                                ),
                                            ),
                                            True,
                                        ),
                                    ]
                                )
                            ),
                        ]
                    ),
                ),
            ],
            Projection(
                [
                    ProjectionItem(
                        PropertyLabelExpression(Variable("n")),
                    )
                ],
            ),
        )

        assert parser.query_object == test_qo

    def test_query(self):
        query = "MATCH (n:Person {name: 'Alice', age: 42})-[r:KNOWS]->(m:Person) RETURN n.name AS fullName"
        parser = Parser(query)

        test_qo = Query(
            [
                Match(
                    [
                        NodePattern(
                            Variable("n"),
                            ["Person"],
                            {
                                "age": PropertyLabelExpression(
                                    Literal("42"),
                                ),
                                "name": PropertyLabelExpression(
                                    Literal("'Alice'"),
                                ),
                            },
                        ),
                        PatternElement(
                            RelationshipPattern(
                                Direction.RIGHT,
                                Variable("r"),
                                ["KNOWS"],
                            ),
                            NodePattern(Variable("m"), ["Person"]),
                        ),
                    ],
                )
            ],
            Projection(
                [
                    ProjectionItem(
                        PropertyLabelExpression(Variable("n"), [Property("name")]),
                        Variable("fullName"),
                    )
                ],
            ),
        )

        assert parser.query_object == test_qo
