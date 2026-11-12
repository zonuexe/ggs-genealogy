from rdflib import Graph

from ggs.graph.diff import SemanticDiffer, render_diff_rich

TTL_A = """@prefix : <https://example.org/koseki#> .
@prefix k: <https://example.org/ns/koseki#> .
@prefix ic: <https://imi.go.jp/ns/core/rdf#> .

:person_a a k:人物 ; ic:氏名 :name_a .
:name_a a ic:氏名型 ; ic:表記 "田中 太郎" .
"""

TTL_B = """@prefix : <https://example.org/koseki#> .
@prefix k: <https://example.org/ns/koseki#> .
@prefix ic: <https://imi.go.jp/ns/core/rdf#> .

:person_a a k:人物 ; ic:氏名 :name_a .
:name_a a ic:氏名型 ; ic:表記 "田中 太郎" .

:person_b a k:人物 ; ic:氏名 :name_b .
:name_b a ic:氏名型 ; ic:表記 "田中 次郎" .
"""


def test_semantic_diff_identical() -> None:
    g1 = Graph()
    g1.parse(data=TTL_A, format="turtle")
    g2 = Graph()
    g2.parse(data=TTL_A, format="turtle")

    diff = SemanticDiffer.diff(g1, g2)
    assert diff.is_identical is True
    assert len(diff.added_triples) == 0
    assert len(diff.removed_triples) == 0


def test_semantic_diff_differences() -> None:
    g1 = Graph()
    g1.parse(data=TTL_A, format="turtle")
    g2 = Graph()
    g2.parse(data=TTL_B, format="turtle")

    diff = SemanticDiffer.diff(g1, g2)
    assert diff.is_identical is False
    assert len(diff.added_triples) > 0
    assert len(diff.removed_triples) == 0

    # Ensure rich rendering executes cleanly
    render_diff_rich(diff, source_a_label="A", source_b_label="B")
