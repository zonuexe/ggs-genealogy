from typing import TYPE_CHECKING

from lxml import etree
from rdflib import Graph
from rdflib.compare import isomorphic, to_isomorphic

from ggs_genealogy.converters.gramps_export import GrampsExporter
from ggs_genealogy.converters.gramps_import import GrampsImporter

if TYPE_CHECKING:
    from pathlib import Path

SAMPLE_TTL = """@prefix : <https://example.org/koseki#> .
@prefix k: <https://example.org/ns/koseki#> .
@prefix ic: <https://imi.go.jp/ns/core/rdf#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:household_001
    a k:戸 ;
    k:本籍 [
        a ic:住所型 ;
        ic:表記 "東京都台東区上野1-1"
    ] ;
    k:戸主 :person_taro ;
    k:構成員 :person_taro , :person_hanako .

:person_taro
    a k:人物 ;
    ic:氏名 [
        a ic:氏名型 ;
        ic:表記 "山田 太郎" ;
        ic:姓 "山田" ;
        ic:名 "太郎"
    ] ;
    k:在籍戸 :household_001 ;
    k:戸主との続柄 "戸主" ;
    ic:生年月日 [
        a ic:日付型 ;
        ic:表記 "明治20年1月1日" ;
        ic:標準型日時 "1887-01-01"^^xsd:date
    ] .

:person_hanako
    a k:人物 ;
    ic:氏名 [
        a ic:氏名型 ;
        ic:表記 "山田 花子" ;
        ic:姓 "山田" ;
        ic:名 "花子"
    ] ;
    k:在籍戸 :household_001 ;
    k:戸主との続柄 "妻" ;
    ic:生年月日 [
        a ic:日付型 ;
        ic:表記 "明治25年5月10日" ;
        ic:標準型日時 "1892-05-10"^^xsd:date
    ] .
"""


def test_roundtrip_isomorphism() -> None:
    original = Graph()
    original.parse(data=SAMPLE_TTL, format="turtle")

    exporter = GrampsExporter(original)
    xml_str = exporter.export_xml()

    importer = GrampsImporter(xml_str)
    reconstructed = importer.to_rdf_graph()

    iso_orig = to_isomorphic(original)
    iso_recon = to_isomorphic(reconstructed)

    assert isomorphic(iso_orig, iso_recon)


def test_gramps_xml_top_level_element_order() -> None:
    g = Graph()
    g.parse(data=SAMPLE_TTL, format="turtle")

    exporter = GrampsExporter(g)
    xml_str = exporter.export_xml()

    root = etree.fromstring(xml_str.encode("utf-8"))
    tag_names = [etree.QName(child).localname for child in root]

    # Expected order: header -> tags -> events -> people -> families -> citations -> sources -> places -> notes
    expected_order = [
        "header",
        "tags",
        "events",
        "people",
        "families",
        "citations",
        "sources",
        "places",
        "notes",
    ]
    assert tag_names == expected_order


def test_compressed_gramps_file_roundtrip(tmp_path: Path) -> None:
    g = Graph()
    g.parse(data=SAMPLE_TTL, format="turtle")

    out_file = tmp_path / "export.gramps"
    exporter = GrampsExporter(g)
    exporter.export_to_file(out_file, compress=True)

    importer = GrampsImporter.from_file(out_file)
    reconstructed = importer.to_rdf_graph()

    assert isomorphic(to_isomorphic(g), to_isomorphic(reconstructed))
