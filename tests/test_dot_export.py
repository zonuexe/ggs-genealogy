from rdflib import Graph

from ggs.converters.dot_export import DotExporter

SAMPLE_TTL = """@prefix : <https://example.org/koseki#> .
@prefix k: <https://example.org/ns/koseki#> .
@prefix ic: <https://imi.go.jp/ns/core/rdf#> .

:household_001
    a k:戸 ;
    k:本籍 [ a ic:住所型 ; ic:表記 "京都府京都市上京区" ] ;
    k:戸主 :person_parent ;
    k:構成員 :person_parent , :person_child .

:person_parent
    a k:人物 ;
    ic:氏名 [ a ic:氏名型 ; ic:表記 "佐藤 父" ] .

:person_child
    a k:人物 ;
    ic:氏名 [ a ic:氏名型 ; ic:表記 "佐藤 子" ] ;
    k:実父 :person_parent .
"""


def test_dot_export() -> None:
    g = Graph()
    g.parse(data=SAMPLE_TTL, format="turtle")

    exporter = DotExporter(g)
    dot = exporter.export_dot(title="Test Tree")

    assert "digraph GGS {" in dot
    assert "subgraph cluster_1 {" in dot
    assert "京都府京都市上京区" in dot
    assert "佐藤 父" in dot
    assert "佐藤 子" in dot
    assert 'label="実父"' in dot
