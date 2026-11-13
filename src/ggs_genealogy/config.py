"""Configuration management for Genealogical Graph System (GGS)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class GgsConfig(BaseModel):
    """Configuration model for a GGS project (ggs.toml)."""

    name: str = Field(default="ggs-project", description="Project name")
    base_uri: str = Field(
        default="https://example.org/koseki#",
        description="Base URI for RDF subjects",
    )
    data_dir: Path = Field(
        default=Path("data"), description="Path to RDF data directory"
    )
    work_dir: Path = Field(
        default=Path("work"), description="Path to working/export directory"
    )
    docs_dir: Path = Field(
        default=Path("docs"), description="Path to documentation directory"
    )
    root_dir: Path = Field(default=Path(), description="Project root directory")

    @property
    def resolved_data_dir(self) -> Path:
        """Absolute or resolved path to data directory."""
        if self.data_dir.is_absolute():
            return self.data_dir
        return (self.root_dir / self.data_dir).resolve()

    @property
    def resolved_work_dir(self) -> Path:
        """Absolute or resolved path to work directory."""
        if self.work_dir.is_absolute():
            return self.work_dir
        return (self.root_dir / self.work_dir).resolve()

    @property
    def resolved_docs_dir(self) -> Path:
        """Absolute or resolved path to docs directory."""
        if self.docs_dir.is_absolute():
            return self.docs_dir
        return (self.root_dir / self.docs_dir).resolve()

    def to_toml_dict(self) -> dict[str, Any]:
        """Convert config to dictionary suitable for TOML serialization."""
        return {
            "project": {
                "name": self.name,
                "base_uri": self.base_uri,
            },
            "paths": {
                "data_dir": str(self.data_dir),
                "work_dir": str(self.work_dir),
                "docs_dir": str(self.docs_dir),
            },
        }

    def to_toml(self) -> str:
        """Serialize configuration to TOML format string."""
        return (
            f"[project]\n"
            f'name = "{self.name}"\n'
            f'base_uri = "{self.base_uri}"\n\n'
            f"[paths]\n"
            f'data_dir = "{self.data_dir}"\n'
            f'work_dir = "{self.work_dir}"\n'
            f'docs_dir = "{self.docs_dir}"\n'
        )

    def write_config(self, target_path: Path | None = None) -> Path:
        """Write ggs.toml to the specified path or project root."""
        out_path = target_path or (self.root_dir / "ggs.toml")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(self.to_toml(), encoding="utf-8")
        return out_path


def find_config_file(start_path: Path | None = None) -> Path | None:
    """Search for ggs.toml in start_path and its parents."""
    current = (start_path or Path.cwd()).resolve()
    if current.is_file():
        if current.name == "ggs.toml":
            return current
        current = current.parent

    for candidate in [current, *current.parents]:
        toml_path = candidate / "ggs.toml"
        if toml_path.is_file():
            return toml_path
    return None


def load_config(config_path: Path | str | None = None) -> GgsConfig:
    """Load GgsConfig from a path or find ggs.toml in parent directories."""
    target: Path | None = None
    if config_path is not None:
        p = Path(config_path).resolve()
        target = p / "ggs.toml" if p.is_dir() else p
    else:
        target = find_config_file()

    if target is None or not target.is_file():
        return GgsConfig()

    root_dir = target.parent
    try:
        with target.open("rb") as f:
            data = tomllib.load(f)
    except Exception:
        return GgsConfig(root_dir=root_dir)

    project_section = data.get("project", {})
    paths_section = data.get("paths", {})

    return GgsConfig(
        name=project_section.get("name", "ggs-project"),
        base_uri=project_section.get("base_uri", "https://example.org/koseki#"),
        data_dir=Path(paths_section.get("data_dir", "data")),
        work_dir=Path(paths_section.get("work_dir", "work")),
        docs_dir=Path(paths_section.get("docs_dir", "docs")),
        root_dir=root_dir,
    )


SAMPLE_TURTLE_TEMPLATE = """@prefix : <{base_uri}> .
@prefix k: <https://example.org/ns/koseki#> .
@prefix ic: <https://imi.go.jp/ns/core/rdf#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:household_001
    a k:戸 ;
    rdfs:label "東京府豊島郡巣鴨村 田中家"@ja ;
    k:本籍 [
        a ic:住所型 ;
        ic:表記 "東京府豊島郡巣鴨村一丁目二番地"
    ] ;
    k:戸主 :person_taro ;
    k:構成員 :person_taro , :person_hanako .

:person_taro
    a k:人物 ;
    ic:氏名 [
        a ic:氏名型 ;
        ic:表記 "田中 太郎" ;
        ic:姓 "田中" ;
        ic:名 "太郎"
    ] ;
    k:在籍戸 :household_001 ;
    k:戸主との続柄 "戸主" ;
    ic:生年月日 [
        a ic:日付型 ;
        ic:表記 "明治15年3月1日" ;
        ic:標準型日時 "1882-03-01"^^xsd:date
    ] .

:person_hanako
    a k:人物 ;
    ic:氏名 [
        a ic:氏名型 ;
        ic:表記 "田中 花子" ;
        ic:姓 "田中" ;
        ic:名 "花子"
    ] ;
    k:在籍戸 :household_001 ;
    k:戸主との続柄 "妻" ;
    ic:生年月日 [
        a ic:日付型 ;
        ic:表記 "明治18年7月15日" ;
        ic:標準型日時 "1885-07-15"^^xsd:date
    ] .
"""
