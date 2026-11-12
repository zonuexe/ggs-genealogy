> **アーカイブ:** 本書は、未決事項を含む初期の対話をエージェントがまとめた叩き台であり、経緯を残す目的でのみ保管している。方針は [ADR-0](../adr/0000-north-star.md) が優先する。

# Project Handoff Specification: `ggs-genealogy` (Genealogical Graph System)

## 1. プロジェクト概要と目的
日本の戸籍（明治民法下の旧戸籍・改製原戸籍・除籍謄本・現行戸籍）を、西欧の核家族モデル（GEDCOM）による情報欠落なしに RDF/Turtle で厳密に管理し、かつ既存の系譜ビューアである **Gramps**（Gramps XML 1.7.1）や **Graphviz (DOT)** と双方向・非破壊で相互運用するための Python パッケージおよび CLI ツール。

* **PyPI パッケージ名**: `ggs-genealogy`
* **CLI コマンド名 / トップレベルモジュール名**: `ggs`
* **正式名称**: Genealogical Graph System (GGS)
* **ターゲット Python バージョン**: Python 3.11 以上

---

## 2. 厳守事項・禁止事項（CRITICAL RULES）
1. **禁止語句**: 開発初期の会話で言及された日本語の俗称・語呂合わせ（アルファベット6文字および日本語4文字の表記）は、コード内のシンボル、文字列リテラル、コメント、ドキュメント、テストケース、コミットメッセージの**いかなる場所にも絶対に使用しないこと**。正式名称は常に `Genealogical Graph System` または `ggs` とする。
2. **SSOT と非破壊往復（Lossless Round-trip）**:
   * RDF/Turtle 側を SSOT（Single Source of Truth）とする。
   * Gramps XML への順変換（Export）および逆変換（Import）において、URI アンカリング（`<attribute type="ggs:uri">`）と BlankNode のインプレース更新により、`rdflib.compare.to_isomorphic` で同型性が保たれること。
3. **トップレベル要素順序の厳守**:
   * Gramps XML 1.7.1 の DTD 制約に従い、`<database>` 直下の要素は必ず `header` → `tags` → `events` → `people` → `families` → `citations` → `sources` → `places` → `notes` の順序で出力すること。

---

## 3. ディレクトリ構成

```text
ggs/
├── pyproject.toml
├── README.md                      # [残タスク: 新規作成]
├── src/
│   └── ggs/
│       ├── __init__.py            # __version__ = "0.1.0"
│       ├── cli.py                 # [残タスク: 全サブコマンド統合実装]
│       ├── config.py              # [実装済] ggs.toml の読み込み・Pydantic設定モデル
│       ├── graph/
│       │   ├── __init__.py
│       │   └── diff.py            # [実装済] RDFグラフ間の意味論的差分 (SemanticDiffer)
│       ├── converters/
│       │   ├── __init__.py
│       │   ├── gramps_export.py   # [実装済] Turtle -> Gramps XML 1.7.1 変換
│       │   ├── gramps_import.py   # [実装済] Gramps XML 1.7.1 -> Turtle 逆変換・3-Wayマージ
│       │   └── dot_export.py      # [実装済] Turtle -> Graphviz DOT 出力
│       ├── validation/
│       │   ├── __init__.py
│       │   └── validator.py       # [実装済] pyshacl による戸籍整合性検証エンジン
│       ├── query/
│       │   ├── __init__.py
│       │   └── runner.py          # [実装済] SPARQL 実行およびプリセットクエリ管理
│       ├── agent/
│       │   ├── __init__.py
│       │   └── prompt_builder.py  # [実装済] 謄本テキストからTurtleを生成するLLMプロンプト組立
│       └── resources/
│           ├── __init__.py
│           ├── ontology/
│           │   ├── __init__.py
│           │   └── koseki.ttl     # [実装済] IMIコア語彙2.4.2拡張の戸籍OWLオントロジー
│           ├── shapes/
│           │   ├── __init__.py
│           │   └── koseki_shacl.ttl # [実装済] 戸籍論理制約 SHACL ルール
│           └── queries/
│               ├── __init__.py
│               ├── heads.rq       # [実装済] 歴代戸主・家督相続履歴の抽出クエリ
│               └── adoptions.rq   # [実装済] 養子縁組・実親養親対照抽出クエリ
└── tests/
    ├── test_config.py             # [実装済]
    ├── test_validation.py         # [実装済]
    ├── test_roundtrip.py          # [実装済]
    ├── test_dot_export.py         # [実装済]
    ├── test_diff.py               # [実装済]
    └── test_query.py              # [実装済]
```
※ `importlib.resources.files("ggs.resources...")` が確実に動作するよう、`resources/` 配下の各サブディレクトリにも空の `__init__.py` を配置すること。

---

## 4. 確定済みファイル仕様と実装コード

### 4.1 `pyproject.toml`

```toml
[build-system]
requires = ["hatchling>=1.25.0"]
build-backend = "hatchling.build"

[project]
name = "ggs-genealogy"
version = "0.1.0"
description = "Genealogical Graph System - Japanese Koseki RDF & Gramps Bridge"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [
    { name = "Kenta Usami" }
]
keywords = [
    "genealogy",
    "gramps",
    "koseki",
    "rdf",
    "owl",
    "shacl",
    "imi",
    "semantic-web",
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Sociology :: Genealogy",
]

dependencies = [
    "rdflib>=7.0.0",
    "pyshacl>=0.26.0",
    "lxml>=5.2.0",
    "typer>=0.12.0",
    "rich>=13.7.0",
    "pydantic>=2.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
    "lxml-stubs>=0.5.1",
]

[project.scripts]
ggs = "ggs.cli:app"

[project.urls]
Homepage = "[https://github.com/rigortype/ggs](https://github.com/rigortype/ggs)"
Repository = "[https://github.com/rigortype/ggs](https://github.com/rigortype/ggs)"

[tool.hatch.build.targets.wheel]
packages = ["src/ggs"]

[tool.hatch.build.targets.wheel.force-include]
"src/ggs/resources" = "ggs/resources"

[tool.ruff]
target-version = "py311"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
mypy_path = "src"
packages = ["ggs"]

[[tool.mypy.overrides]]
module = ["pyshacl.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

---

### 4.2 パッケージ同梱リソース (`src/ggs/resources/`)

#### `src/ggs/resources/ontology/koseki.ttl`
```turtle
@prefix :        [https://example.org/ns/koseki#](https://example.org/ns/koseki#) .
@prefix ic:      [https://imi.go.jp/ns/core/rdf#](https://imi.go.jp/ns/core/rdf#) .
@prefix owl:     [http://www.w3.org/2002/07/owl#](http://www.w3.org/2002/07/owl#) .
@prefix rdf:     [http://www.w3.org/1999/02/22-rdf-syntax-ns#](http://www.w3.org/1999/02/22-rdf-syntax-ns#) .
@prefix rdfs:    [http://www.w3.org/2000/01/rdf-schema#](http://www.w3.org/2000/01/rdf-schema#) .
@prefix xsd:     [http://www.w3.org/2001/XMLSchema#](http://www.w3.org/2001/XMLSchema#) .

[https://example.org/ns/koseki](https://example.org/ns/koseki)
    a owl:Ontology ;
    rdfs:label "戸籍オントロジー (Minimal Japanese Koseki Ontology)"@ja ;
    rdfs:comment "IMIコア語彙2.4.2を拡張し、戸籍（戸・戸主・身分事項・除籍）を管理するための語彙体系。"@ja .

:戸
    a owl:Class ;
    rdfs:label "戸（家）"@ja ;
    rdfs:comment "戸籍簿における公簿単位（旧民法下の「家」、または現行戸籍の単位）。"@ja .

:人物
    a owl:Class ;
    rdfs:subClassOf ic:人型 ;
    rdfs:label "人物"@ja ;
    rdfs:comment "戸籍に記載される個人。IMIの人型を継承。"@ja .

:身分事項イベント
    a owl:Class ;
    rdfs:subClassOf ic:イベント型 ;
    rdfs:label "身分事項イベント"@ja ;
    rdfs:comment "戸籍欄内に記載される個人の身分変動（出生、死亡、婚姻、縁組、家督相続、除籍等）。"@ja .

:家督相続イベント
    a owl:Class ;
    rdfs:subClassOf :身分事項イベント ;
    rdfs:label "家督相続イベント"@ja .

:縁組イベント
    a owl:Class ;
    rdfs:subClassOf :身分事項イベント ;
    rdfs:label "縁組イベント"@ja .

:除籍イベント
    a owl:Class ;
    rdfs:subClassOf :身分事項イベント ;
    rdfs:label "除籍イベント"@ja ;
    rdfs:comment "死亡、婚姻、分家、転籍等に伴い個人の身分事項欄が抹消（除籍）された事由。"@ja .

:本籍
    a owl:ObjectProperty ;
    rdfs:domain :戸 ;
    rdfs:range ic:住所型 ;
    rdfs:subPropertyOf ic:住所 ;
    rdfs:label "本籍"@ja .

:戸主
    a owl:ObjectProperty ;
    rdfs:domain :戸 ;
    rdfs:range :人物 ;
    rdfs:label "戸主"@ja .

:筆頭者
    a owl:ObjectProperty ;
    rdfs:subPropertyOf :戸主 ;
    rdfs:domain :戸 ;
    rdfs:range :人物 ;
    rdfs:label "筆頭者"@ja .

:構成員
    a owl:ObjectProperty ;
    rdfs:domain :戸 ;
    rdfs:range :人物 ;
    owl:inverseOf :在籍戸 ;
    rdfs:label "構成員"@ja .

:除籍簿化
    a owl:DatatypeProperty ;
    rdfs:domain :戸 ;
    rdfs:range xsd:boolean ;
    rdfs:label "除籍簿フラグ"@ja .

:在籍戸
    a owl:ObjectProperty ;
    rdfs:domain :人物 ;
    rdfs:range :戸 ;
    rdfs:label "在籍戸"@ja .

:戸主との続柄
    a owl:DatatypeProperty ;
    rdfs:domain :人物 ;
    rdfs:range xsd:string ;
    rdfs:label "戸主との続柄"@ja .

:実父
    a owl:ObjectProperty ;
    rdfs:domain :人物 ;
    rdfs:range :人物 ;
    rdfs:label "実父"@ja .

:実母
    a owl:ObjectProperty ;
    rdfs:domain :人物 ;
    rdfs:range :人物 ;
    rdfs:label "実母"@ja .

:養父
    a owl:ObjectProperty ;
    rdfs:domain :人物 ;
    rdfs:range :人物 ;
    rdfs:label "養父"@ja .

:養母
    a owl:ObjectProperty ;
    rdfs:domain :人物 ;
    rdfs:range :人物 ;
    rdfs:label "養母"@ja .

:謄本記載事由
    a owl:DatatypeProperty ;
    rdfs:domain :身分事項イベント ;
    rdfs:range xsd:string ;
    rdfs:subPropertyOf ic:説明 ;
    rdfs:label "謄本記載事由文"@ja .

:届出日
    a owl:ObjectProperty ;
    rdfs:domain :身分事項イベント ;
    rdfs:range ic:日付型 ;
    rdfs:subPropertyOf ic:日時 ;
    rdfs:label "届出日"@ja .

:前戸主
    a owl:ObjectProperty ;
    rdfs:domain :家督相続イベント ;
    rdfs:range :人物 ;
    rdfs:subPropertyOf ic:関係者 ;
    rdfs:label "前戸主"@ja .

:新戸主
    a owl:ObjectProperty ;
    rdfs:domain :家督相続イベント ;
    rdfs:range :人物 ;
    rdfs:subPropertyOf ic:主体 ;
    rdfs:label "新戸主"@ja .

:異動元戸
    a owl:ObjectProperty ;
    rdfs:domain :身分事項イベント ;
    rdfs:range :戸 ;
    rdfs:label "異動元戸"@ja .

:異動先戸
    a owl:ObjectProperty ;
    rdfs:domain :身分事項イベント ;
    rdfs:range :戸 ;
    rdfs:label "異動先戸"@ja .
```

#### `src/ggs/resources/shapes/koseki_shacl.ttl`
```turtle
@prefix :        [https://example.org/ns/koseki#](https://example.org/ns/koseki#) .
@prefix sh:      [http://www.w3.org/ns/shacl#](http://www.w3.org/ns/shacl#) .
@prefix ic:      [https://imi.go.jp/ns/core/rdf#](https://imi.go.jp/ns/core/rdf#) .
@prefix owl:     [http://www.w3.org/2002/07/owl#](http://www.w3.org/2002/07/owl#) .
@prefix rdf:     [http://www.w3.org/1999/02/22-rdf-syntax-ns#](http://www.w3.org/1999/02/22-rdf-syntax-ns#) .
@prefix rdfs:    [http://www.w3.org/2000/01/rdf-schema#](http://www.w3.org/2000/01/rdf-schema#) .
@prefix xsd:     [http://www.w3.org/2001/XMLSchema#](http://www.w3.org/2001/XMLSchema#) .

:PrefixDeclarations
    a owl:Ontology ;
    sh:declare [
        sh:prefix "k" ;
        sh:namespace "[https://example.org/ns/koseki#](https://example.org/ns/koseki#)"^^xsd:anyURI ;
    ] , [
        sh:prefix "ic" ;
        sh:namespace "[https://imi.go.jp/ns/core/rdf#](https://imi.go.jp/ns/core/rdf#)"^^xsd:anyURI ;
    ] , [
        sh:prefix "xsd" ;
        sh:namespace "[http://www.w3.org/2001/XMLSchema#](http://www.w3.org/2001/XMLSchema#)"^^xsd:anyURI ;
    ] .

:HouseholdShape
    a sh:NodeShape ;
    sh:targetClass :戸 ;
    sh:property [
        sh:path :本籍 ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:node :AddressShape ;
        sh:severity sh:Violation ;
        sh:message "「戸」には必ず1つの :本籍（ic:住所型）が定義されている必要があります。"@ja ;
    ] ;
    sh:property [
        sh:path :戸主 ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:class :人物 ;
        sh:severity sh:Violation ;
        sh:message "1つの「戸」における代表 :戸主（または :筆頭者）は必ず1名である必要があります（歴代の代替わりは :家督相続イベント で記述してください）。"@ja ;
    ] ;
    sh:property [
        sh:path :構成員 ;
        sh:minCount 1 ;
        sh:class :人物 ;
        sh:severity sh:Violation ;
        sh:message "「戸」には少なくとも1名の :構成員 が所属している必要があります。"@ja ;
    ] ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:prefixes :PrefixDeclarations ;
        sh:severity sh:Violation ;
        sh:message "指定された :戸主（{?koshu}）がその戸の :構成員（または逆方向の :在籍戸）に含まれていません。"@ja ;
        sh:select """
            SELECT $this ?koshu
            WHERE {
                $this k:戸主 ?koshu .
                FILTER NOT EXISTS {
                    { $this k:構成員 ?koshu } UNION { ?koshu k:在籍戸 $this }
                }
            }
        """ ;
    ] .

:PersonShape
    a sh:NodeShape ;
    sh:targetClass :人物 ;
    sh:property [
        sh:path ic:氏名 ;
        sh:minCount 1 ;
        sh:node :NameShape ;
        sh:severity sh:Violation ;
        sh:message "人物には少なくとも1つの ic:氏名 が必要です。"@ja ;
    ] ;
    sh:property [
        sh:path :実父 ;
        sh:maxCount 1 ;
        sh:class :人物 ;
        sh:severity sh:Violation ;
        sh:message "1人の人物に複数の :実父 を設定することはできません（養父は :養父 を使用してください）。"@ja ;
    ] ;
    sh:property [
        sh:path :実母 ;
        sh:maxCount 1 ;
        sh:class :人物 ;
        sh:severity sh:Violation ;
        sh:message "1人の人物に複数の :実母 を設定することはできません（養母は :養母 を使用してください）。"@ja ;
    ] ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:prefixes :PrefixDeclarations ;
        sh:severity sh:Violation ;
        sh:message "人物（{$this}）が自分自身の親（実親・養親）として参照されています。"@ja ;
        sh:select """
            SELECT $this
            WHERE {
                $this (k:実父\vert{}k:実母\vert{}k:養父\vert{}k:養母)+ $this .
            }
        """ ;
    ] ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:prefixes :PrefixDeclarations ;
        sh:severity sh:Violation ;
        sh:message "人物の生年月日（{?birth}）が死亡年月日（{?death}）より後の日付になっています。"@ja ;
        sh:select """
            SELECT $this ?birth ?death
            WHERE {
                $this ic:生年月日/ic:標準型日時 ?birth ;
                      ic:死亡年月日/ic:標準型日時 ?death .
                FILTER (STR(?birth) > STR(?death))
            }
        """ ;
    ] ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:prefixes :PrefixDeclarations ;
        sh:severity sh:Violation ;
        sh:message "実親（{?parent}: {?pBirth}生）の生年月日が、子（{$this}: {?cBirth}生）の生年月日以降になっています。"@ja ;
        sh:select """
            SELECT $this ?parent ?pBirth ?cBirth
            WHERE {
                $this (k:実父|k:実母) ?parent ;
                      ic:生年月日/ic:標準型日時 ?cBirth .
                ?parent ic:生年月日/ic:標準型日時 ?pBirth .
                FILTER (STR(?pBirth) >= STR(?cBirth))
            }
        """ ;
    ] ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:prefixes :PrefixDeclarations ;
        sh:severity sh:Warning ;
        sh:message "【警告】養親（{?adoptiveParent}: {?pBirth}生）が養子（{$this}: {?cBirth}生）と同年または年少です。謄本の記載または年号変換を確認してください。"@ja ;
        sh:select """
            SELECT $this ?adoptiveParent ?pBirth ?cBirth
            WHERE {
                $this (k:養父|k:養母) ?adoptiveParent ;
                      ic:生年月日/ic:標準型日時 ?cBirth .
                ?adoptiveParent ic:生年月日/ic:標準型日時 ?pBirth .
                FILTER (STR(?pBirth) >= STR(?cBirth))
            }
        """ ;
    ] .

:StatusEventShape
    a sh:NodeShape ;
    sh:targetClass :身分事項イベント ;
    sh:or (
        [ sh:path ic:日時 ; sh:minCount 1 ]
        [ sh:path :謄本記載事由 ; sh:minCount 1 ]
    ) ;
    sh:message "身分事項イベントには ic:日時 または :謄本記載事由 の少なくとも一方が記述されている必要があります。"@ja ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:prefixes :PrefixDeclarations ;
        sh:severity sh:Warning ;
        sh:message "【警告】人物（{?person}）のイベント発生日（{?evDate}）が生年月日（{?birth}）より前になっています。"@ja ;
        sh:select """
            SELECT $this ?person ?birth ?evDate
            WHERE {
                { ?person ic:イベント $this } UNION {$this ic:主体 ?person }
                $this ic:日時/ic:標準型日時 ?evDate .
                ?person ic:生年月日/ic:標準型日時 ?birth .
                FILTER (STR(?evDate) < STR(?birth))
            }
        """ ;
    ] .

:KatokuSozokuShape
    a sh:NodeShape ;
    sh:targetClass :家督相続イベント ;
    sh:property [
        sh:path :新戸主 ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:class :人物 ;
        sh:severity sh:Violation ;
        sh:message "家督相続イベントには :新戸主 が1名必須です。"@ja ;
    ] ;
    sh:property [
        sh:path :前戸主 ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:class :人物 ;
        sh:severity sh:Warning ;
        sh:message "【警告】家督相続イベントに :前戸主 が指定されていません。"@ja ;
    ] ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:prefixes :PrefixDeclarations ;
        sh:severity sh:Violation ;
        sh:message "家督相続イベントにおいて :前戸主 と :新戸主 に同一人物（{?head}）が指定されています。"@ja ;
        sh:select """
            SELECT $this ?head
            WHERE {
                $this k:新戸主 ?head ;
                      k:前戸主 ?head .
            }
        """ ;
    ] .

:NameShape
    a sh:NodeShape ;
    sh:targetClass ic:氏名型 ;
    sh:or (
        [ sh:path ic:表記 ; sh:minCount 1 ; sh:datatype xsd:string ]
        [ sh:path ic:姓 ; sh:minCount 1 ; sh:datatype xsd:string ]
        [ sh:path ic:名 ; sh:minCount 1 ; sh:datatype xsd:string ]
    ) ;
    sh:message "ic:氏名型 には ic:表記、ic:姓、ic:名 のいずれかが必要です。"@ja .

:DateShape
    a sh:NodeShape ;
    sh:targetClass ic:日付型 ;
    sh:property [
        sh:path ic:表記 ;
        sh:minCount 1 ;
        sh:datatype xsd:string ;
        sh:severity sh:Warning ;
        sh:message "【警告】ic:日付型 には謄本記載の和暦原文（ic:表記）を残すことを推奨します。"@ja ;
    ] ;
    sh:property [
        sh:path ic:標準型日時 ;
        sh:maxCount 1 ;
        sh:or (
            [ sh:datatype xsd:date ]
            [ sh:datatype xsd:gYearMonth ]
            [ sh:datatype xsd:gYear ]
        ) ;
        sh:severity sh:Violation ;
        sh:message "ic:標準型日時 は xsd:date (YYYY-MM-DD)、xsd:gYearMonth (YYYY-MM)、xsd:gYear (YYYY) のいずれかの型で記述してください。"@ja ;
    ] .

:AddressShape
    a sh:NodeShape ;
    sh:targetClass ic:住所型 ;
    sh:property [
        sh:path ic:表記 ;
        sh:minCount 1 ;
        sh:datatype xsd:string ;
        sh:severity sh:Violation ;
        sh:message "本籍や住所（ic:住所型）には謄本記載の文字列（ic:表記）が必須です。"@ja ;
    ] .
```
*(注: SPARQL 内で `xsd:date` と `xsd:gYearMonth` が混在比較されても型エラーでスキップされないよう、ISO 8601 辞書順比較 `STR(?a) > STR(?b)` を用いる設計としている)*

#### `src/ggs/resources/queries/heads.rq` および `adoptions.rq`
* 直前のチャット履歴で作成した `heads.rq`（歴代戸主・家督相続履歴抽出）および `adoptions.rq`（養子縁組・実親養親対照一覧）をそのまま配置する。

---

## 5. Antigravity で完了させる残タスク一覧

### Task 1: ファイル展開と初期セットアップ
1. 上記ディレクトリ構成に従い、作成済みのすべての実装ファイル（`config.py`, `validator.py`, `gramps_export.py`, `gramps_import.py`, `dot_export.py`, `diff.py`, `runner.py`, `prompt_builder.py`）、リソースファイル（`.ttl`, `.rq`）、およびテストファイル（`tests/test_*.py`）を配置する。
2. `src/ggs/__init__.py` に `__version__ = "0.1.0"` を定義する。

### Task 2: `src/ggs/cli.py` の完全実装
以下のサブコマンドを持つ Typer アプリケーションを実装し、全モジュールを接続する。
* `ggs init [DIR] [--name] [--base-uri]`:
  `GgsConfig` から `ggs.toml`、`data/`、`work/`、`docs/` ディレクトリとサンプル `.ttl` を生成する。
* `ggs validate [PATHS...] [--strict]`:
  対象パス（未指定時は `GgsConfig.resolved_data_dir`）の `.ttl` を読み込み、`run_validation()` を実行して `rich` で結果を表示。違反時は `raise typer.Exit(code=1)`。
* `ggs export [--to gramps|dot|ttl] [-o OUTPUT] [--compress/--no-compress]`:
  `GrampsExporter` または `DotExporter` を呼び出してファイル出力する。
* `ggs import <GRAMPS_FILE> [--target PATH] [--dry-run]`:
  既存 `data/` グラフをベースに `GrampsImporter` でマージし、`SemanticDiffer` で差分を表示。`--dry-run` でなければ結果をシリアライズ保存する。
* `ggs diff <SOURCE_A> <SOURCE_B>`:
  `SemanticDiffer.load_source()` で両者を読み込み、`render_diff_rich()` で差分を表示する。
* `ggs query [--preset NAME] [--file PATH] [--format table|json|csv]`:
  `QueryRunner` で SPARQL を実行し、指定フォーマットで標準出力する。
* `ggs prompt [-d DATA_PATHS] [-i INPUT_TEXT] [--include-existing/--no-existing]`:
  `PromptBuilder` で LLM 用システムプロンプトを組み立てて `typer.echo()` する。
* `ggs version`:
  `ggs (Genealogical Graph System) v0.1.0` を出力する。

### Task 3: `README.md` の作成
* パッケージ名 `ggs-genealogy`（コマンド名 `ggs`）のインストール方法（`pip install ggs-genealogy`）、設計思想（日本の戸籍モデルとGramps核家族モデルのブリッジ、IMIコア語彙2.4.2の採用）、CLIの各サブコマンドの使用例、エージェントを用いた謄本テキストからのデータ投入ワークフローを記載する。

### Task 4: 品質ゲート（Quality Gate）の通過確認
仮想環境で以下を実行し、すべてエラーゼロで通過することを確認する。
```bash
pip install -e ".[dev]"
ruff check .
mypy src
pytest
```