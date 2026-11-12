# ggs-genealogy: Genealogical Graph System (GGS)

[![CI](https://github.com/zonuexe/ggs-genealogy/actions/workflows/ci.yml/badge.svg)](https://github.com/zonuexe/ggs-genealogy/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Genealogical Graph System (GGS)** は、日本の戸籍制度（明治民法下の旧戸籍・改製原戸籍・除籍謄本から現行民法下の現行戸籍まで）に記録された系譜・身分事項データを、情報欠落なくセマンティックWeb標準（RDF/Turtle / OWL / SHACL）で管理し、系譜ソフトウェア **Gramps**（Gramps XML 1.7.1）および **Graphviz (DOT)** と双方向・非破壊で相互運用するためのPythonパッケージおよびCLIツールです。

---

## 1. 背景と設計思想

### 日本の戸籍モデルと西欧核家族モデル（GEDCOM）のギャップ
GEDCOMや一般的な系図ソフトウェア（Grampsなど）は西欧の核家族モデル（父・母・子）を前提として設計されています。しかし、日本の明治民法下の戸籍制度は以下の固有な特徴を持っています：

* **「家（戸）」公簿単位**: 単一の代表者（戸主・筆頭者）と、本籍地、戸に属する構成員で構成される。
* **家督相続**: 代替わりに伴う戸主の地位承継履歴。
* **養子縁組と実親・養親の併記**: 1人の人物に実父・実母と養父・養母が併存する複線的親子関係。
* **身分事項変動の時系列記録**: 出生、婚姻、養子縁組、離縁、家督相続、分家、転籍、死亡などの身分変動事由が履歴として残る。

GGSは **IMIコア語彙 2.4.2**（情報共有基盤 共通語彙基盤）を基盤に拡張した戸籍OWLオントロジー（`koseki.ttl`）と、論理整合性を検証するSHACLルール（`koseki_shacl.ttl`）を採用し、RDF/Turtleを**単一の情報源（SSOT: Single Source of Truth）**として位置付けます。

### 非破壊往復（Lossless Round-trip）
Gramps XML への出力時には URI アンカリング（`<attribute type="ggs:uri" value="...">`）と元のRDFグラフの埋め込みを行い、Gramps側での編集を取り込みつつ、元のRDFグラフとの間で `rdflib.compare.isomorphic` による同型性（Lossless Round-trip）を維持します。また、Gramps XML 1.7.1のDTD要件（トップレベル要素の厳密な順序：`header` → `tags` → `events` → `people` → `families` → `citations` → `sources` → `places` → `notes`）に完全準拠します。

---

## 2. インストール

```bash
# pip を使用する場合
pip install ggs-genealogy

# uv を使用する場合
uv add ggs-genealogy
```

---

## 3. CLI コマンド仕様

`ggs` コマンドで各種機能を利用できます。

```bash
ggs --help
```

### 3.1 プロジェクトの初期化 (`ggs init`)
作業ワークスペースに設定ファイル `ggs.toml`、データ格納ディレクトリ（`data/`）、作業ディレクトリ（`work/`）、ドキュメントディレクトリ（`docs/`）、およびサンプルTurtleファイルを生成します。

```bash
ggs init my-family --name "Yamada Family Genealogy" --base-uri "https://example.org/yamada#"
```

### 3.2 SHACL制約検証 (`ggs validate`)
指定したディレクトリまたは `data/` 配下の `.ttl` ファイルに対し、戸籍オントロジーおよびSHACL論理制約（実親の生年月日が子の生年月日より前であるか、1つの戸に戸主が1名存在し構成員に含まれているか等）を検証します。

```bash
# 通常検証
ggs validate data/

# 警告も含めて終了コード1とする厳格モード
ggs validate data/ --strict
```

### 3.3 データのエクスポート (`ggs export`)
RDFグラフから Gramps XML、Graphviz DOT、または Turtle ファイルを出力します。

```bash
# Gramps XML への出力（非圧縮 .xml）
ggs export --to gramps -o work/family.xml

# Gramps XML への出力（gzip圧縮 .gramps）
ggs export --to gramps -o work/family.gramps --compress

# Graphviz DOT ファイルへの出力
ggs export --to dot -o work/family.dot

# Turtle シリアライズ
ggs export --to ttl -o work/backup.ttl
```

### 3.4 Grampsデータのインポートとマージ (`ggs import`)
Grampsで編集したXMLファイル（または `.gramps` 圧縮ファイル）を取り込み、既存のRDFグラフとマージします。

```bash
# 差分のプレビュー（反映なし）
ggs import work/family.gramps --dry-run

# 既存データにマージして保存
ggs import work/family.gramps --target data/merged.ttl
```

### 3.5 グラフ間の意味論的差分比較 (`ggs diff`)
2つのRDFソース（ファイルまたはディレクトリ）を読み込み、グラフ間の意味的差分（追加・削除されたトリプル）をリッチに表示します。

```bash
ggs diff data/before.ttl data/after.ttl
```

### 3.6 SPARQLクエリ実行 (`ggs query`)
組み込みのプリセットクエリまたは任意のSPARQLクエリファイルを実行し、テーブル、JSON、またはCSV形式で出力します。

```bash
# 歴代戸主・家督相続履歴の抽出（プリセット）
ggs query --preset heads --format table

# 養子縁組・実親養親対照一覧の抽出（JSON出力）
ggs query --preset adoptions --format json

# カスタムSPARQLクエリファイルの実行（CSV出力）
ggs query --file custom.rq --format csv
```

### 3.7 LLMプロンプト生成 (`ggs prompt`)
古い戸籍謄本（除籍謄本・改製原戸籍など）のOCRテキストや翻刻テキストから、オントロジー・SHACL制約に準拠したTurtleデータを抽出・生成するためのLLM向けシステムプロンプトを構築します。

```bash
ggs prompt --input "大正四年三月拾五日...戸主 田中太郎 養子縁組届出..."
```

### 3.8 バージョン表示 (`ggs version`)
```bash
ggs version
```

---

## 4. LLMエージェントを用いた謄本データ投入ワークフロー

1. **謄本テキストの準備**: 除籍謄本や改製原戸籍の記載事項（戸主欄、身分事項欄）をテキスト化します。
2. **システムプロンプトの取得**:
   ```bash
   ggs prompt -i transcript.txt > prompt.txt
   ```
3. **LLMによるTurtle生成**: LLM（Claude / Gemini 等）に `prompt.txt` を入力し、RDF Turtle を生成させます。
4. **制約検証**:
   ```bash
   ggs validate data/
   ```
   エラーや警告（生年月日の順序不整合、戸主の指定漏れなど）があれば、指摘内容をもとに修正します。
5. **系譜可視化と確認**:
   ```bash
   ggs export --to dot -o work/tree.dot
   dot -Tpng work/tree.dot -o work/tree.png
   ```

---

## 5. ライセンス
 
GNU General Public License v3.0 (GPL-3.0)
