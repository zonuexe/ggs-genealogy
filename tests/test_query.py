import json

from rdflib import Graph

from ggs_genealogy.query.runner import QueryRunner

SAMPLE_TTL = """@prefix : <https://example.org/koseki#> .
@prefix k: <https://example.org/ns/koseki#> .
@prefix ic: <https://imi.go.jp/ns/core/rdf#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:household_001
    a k:戸 ;
    rdfs:label "田中家"@ja ;
    k:戸主 :person_taro ;
    k:構成員 :person_taro , :person_adopted .

:person_taro
    a k:人物 ;
    ic:氏名 [ a ic:氏名型 ; ic:表記 "田中 太郎" ] .

:person_adopted
    a k:人物 ;
    ic:氏名 [ a ic:氏名型 ; ic:表記 "田中 養之介" ] ;
    k:養父 :person_taro ;
    k:実父 :person_bio_father .

:person_bio_father
    a k:人物 ;
    ic:氏名 [ a ic:氏名型 ; ic:表記 "鈴木 実父" ] .

:event_adoption
    a k:縁組イベント ;
    ic:主体 :person_adopted ;
    k:謄本記載事由 "田中太郎の養子となる" .
"""


def test_presets_list() -> None:
    presets = QueryRunner.list_presets()
    assert "heads" in presets
    assert "adoptions" in presets


def test_preset_heads_query() -> None:
    g = Graph()
    g.parse(data=SAMPLE_TTL, format="turtle")

    runner = QueryRunner(g)
    q = QueryRunner.load_preset_query("heads")
    res = runner.execute(q)
    rows = runner.to_dict_list(res)

    assert len(rows) >= 1
    assert any(r.get("headName") == "田中 太郎" for r in rows)


def test_preset_adoptions_query() -> None:
    g = Graph()
    g.parse(data=SAMPLE_TTL, format="turtle")

    runner = QueryRunner(g)
    q = QueryRunner.load_preset_query("adoptions")
    res = runner.execute(q)
    rows = runner.to_dict_list(res)

    assert len(rows) == 1
    assert rows[0]["personName"] == "田中 養之介"
    assert rows[0]["adoptiveFatherName"] == "田中 太郎"
    assert rows[0]["bioFatherName"] == "鈴木 実父"


def test_output_formats() -> None:
    g = Graph()
    g.parse(data=SAMPLE_TTL, format="turtle")

    runner = QueryRunner(g)
    q = QueryRunner.load_preset_query("adoptions")
    res = runner.execute(q)

    json_out = runner.format_output(res, output_format="json")
    parsed = json.loads(json_out)
    assert isinstance(parsed, list)
    assert len(parsed) == 1

    csv_out = runner.format_output(res, output_format="csv")
    assert "personName" in csv_out
    assert "田中 養之介" in csv_out

    table_out = runner.format_output(res, output_format="table")
    assert "田中 養之介" in table_out
