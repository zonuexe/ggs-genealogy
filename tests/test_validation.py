from ggs_genealogy.validation.validator import run_validation

VALID_TTL = """@prefix : <https://example.org/koseki#> .
@prefix k: <https://example.org/ns/koseki#> .
@prefix ic: <https://imi.go.jp/ns/core/rdf#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:household_001
    a k:戸 ;
    k:本籍 [
        a ic:住所型 ;
        ic:表記 "東京都千代田区千代田1-1"
    ] ;
    k:戸主 :person_taro ;
    k:構成員 :person_taro , :person_ichiro .

:person_taro
    a k:人物 ;
    ic:氏名 [
        a ic:氏名型 ;
        ic:表記 "田中 太郎"
    ] ;
    ic:生年月日 [
        a ic:日付型 ;
        ic:表記 "明治15年1月1日" ;
        ic:標準型日時 "1882-01-01"^^xsd:date
    ] .

:person_ichiro
    a k:人物 ;
    ic:氏名 [
        a ic:氏名型 ;
        ic:表記 "田中 一郎"
    ] ;
    k:実父 :person_taro ;
    ic:生年月日 [
        a ic:日付型 ;
        ic:表記 "明治40年5月5日" ;
        ic:標準型日時 "1907-05-05"^^xsd:date
    ] .
"""

INVALID_PARENT_BORN_AFTER_CHILD_TTL = """@prefix : <https://example.org/koseki#> .
@prefix k: <https://example.org/ns/koseki#> .
@prefix ic: <https://imi.go.jp/ns/core/rdf#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:household_001
    a k:戸 ;
    k:本籍 [
        a ic:住所型 ;
        ic:表記 "東京都千代田区千代田1-1"
    ] ;
    k:戸主 :person_taro ;
    k:構成員 :person_taro , :person_ichiro .

:person_taro
    a k:人物 ;
    ic:氏名 [ a ic:氏名型 ; ic:表記 "田中 太郎" ] ;
    ic:生年月日 [
        a ic:日付型 ;
        ic:標準型日時 "1920-01-01"^^xsd:date
    ] .

:person_ichiro
    a k:人物 ;
    ic:氏名 [ a ic:氏名型 ; ic:表記 "田中 一郎" ] ;
    k:実父 :person_taro ;
    ic:生年月日 [
        a ic:日付型 ;
        ic:標準型日時 "1900-01-01"^^xsd:date
    ] .
"""


def test_validation_passes_on_valid_data() -> None:
    report = run_validation(VALID_TTL)
    assert report.conforms is True
    assert len(report.violations) == 0


def test_validation_fails_when_parent_born_after_child() -> None:
    report = run_validation(INVALID_PARENT_BORN_AFTER_CHILD_TTL)
    assert report.conforms is False
    assert len(report.violations) > 0
    assert any("実親" in v.message for v in report.violations)
