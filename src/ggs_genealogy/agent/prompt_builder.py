"""Prompt builder for LLM agents to convert koseki transcripts to RDF Turtle."""

from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import TYPE_CHECKING

from rdflib import Graph

if TYPE_CHECKING:
    from collections.abc import Sequence


class PromptBuilder:
    """Builds system prompt and context for LLM to extract koseki RDF."""

    def __init__(
        self,
        base_uri: str = "https://example.org/koseki#",
        data_paths: Sequence[Path | str] | None = None,
        include_existing: bool = True,
        input_text: str | None = None,
    ):
        self.base_uri = base_uri
        self.data_paths = data_paths or []
        self.include_existing = include_existing
        self.input_text = input_text

    def get_ontology_content(self) -> str:
        """Load bundled koseki.ttl ontology string."""
        ont_path = importlib.resources.files("ggs_genealogy.resources.ontology").joinpath("koseki.ttl")
        return ont_path.read_text(encoding="utf-8")

    def get_existing_turtle(self) -> str:
        """Load existing data files into a single Turtle snippet."""
        if not self.include_existing or not self.data_paths:
            return ""

        g = Graph()
        for p in self.data_paths:
            path = Path(p)
            if path.is_dir():
                for ttl_file in path.rglob("*.ttl"):
                    g.parse(location=str(ttl_file), format="turtle")
            elif path.is_file():
                g.parse(location=str(path), format="turtle")

        if len(g) == 0:
            return ""
        return g.serialize(format="turtle")

    def build(self) -> str:
        """Generate the complete system prompt for the LLM agent."""
        ontology_ttl = self.get_ontology_content()
        existing_ttl = self.get_existing_turtle()

        sections = [
            "# Role & Objective",
            (
                "You are an expert genealogical archivist and Semantic Web engineer specializing in "
                "Japanese Koseki (family registers from the Meiji Civil Code to modern civil registers). "
                "Your task is to analyze historical transcript text (謄本・改製原戸籍・除籍謄本) and extract "
                "all individuals, households, relationships, and status events into RDF/Turtle format strictly "
                "conforming to the Japanese Koseki Ontology and SHACL validation constraints."
            ),
            "",
            "# Core Directives & Constraints",
            "1. **Prefixes**:",
            f"   - Default/Subject Prefix: `@prefix : <{self.base_uri}> .`",
            "   - Koseki Ontology: `@prefix k: <https://example.org/ns/koseki#> .`",
            "   - IMI Core Vocabulary 2.4.2: `@prefix ic: <https://imi.go.jp/ns/core/rdf#> .`",
            "   - XSD Datatypes: `@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .`",
            "   - RDFS: `@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .`",
            "2. **Strict Integrity Rules**:",
            "   - Each household (`k:戸`) must have exactly one head (`k:戸主`), one address (`k:本籍`), and members (`k:構成員`).",
            "   - The head (`k:戸主`) must be included in the household members (`k:構成員`).",
            "   - Each person (`k:人物`) can have at most one biological father (`k:実父`) and one biological mother (`k:実母`). Adoptive parents use `k:養父` and `k:養母`.",
            "   - Parent birth dates must precede child birth dates.",
            "   - Standard dates (`ic:標準型日時`) must be formatted as `xsd:date` (YYYY-MM-DD), `xsd:gYearMonth` (YYYY-MM), or `xsd:gYear` (YYYY).",
            "   - Preserve original Japanese era dates (e.g. '明治15年3月1日') in `ic:表記`.",
            "",
            "# Reference Ontology (koseki.ttl)",
            "```turtle",
            ontology_ttl.strip(),
            "```",
        ]

        if existing_ttl:
            sections.extend([
                "",
                "# Existing Knowledge Graph (Context)",
                "```turtle",
                existing_ttl.strip(),
                "```",
            ])

        if self.input_text:
            sections.extend([
                "",
                "# Input Transcript Text to Process",
                "```text",
                self.input_text.strip(),
                "```",
            ])

        sections.extend([
            "",
            "# Output Format",
            "Output only valid RDF Turtle enclosed in a ````turtle ... ```` block.",
        ])

        return "\n".join(sections) + "\n"
