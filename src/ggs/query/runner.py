"""SPARQL query runner and preset manager for GGS."""

from __future__ import annotations

import csv
import importlib.resources
import io
import json
from typing import TYPE_CHECKING, Any, ClassVar

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from rdflib import Graph
    from rdflib.query import Result


class QueryRunner:
    """Executes SPARQL queries against RDF graphs and formats results."""

    PRESETS: ClassVar[dict[str, str]] = {
        "heads": "heads.rq",
        "adoptions": "adoptions.rq",
    }

    def __init__(self, graph: Graph):
        self.graph = graph

    @classmethod
    def list_presets(cls) -> list[str]:
        """List available preset query names."""
        return sorted(cls.PRESETS.keys())

    @classmethod
    def load_preset_query(cls, name: str) -> str:
        """Load SPARQL text for a named preset."""
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown query preset: {name}. Available: {', '.join(cls.list_presets())}")
        file_name = cls.PRESETS[name]
        q_path = importlib.resources.files("ggs.resources.queries").joinpath(file_name)
        return q_path.read_text(encoding="utf-8")

    def execute(self, sparql: str) -> Result:
        """Execute a SPARQL query string."""
        return self.graph.query(sparql)

    @staticmethod
    def to_dict_list(result: Result) -> list[dict[str, str]]:
        """Convert SPARQL query result to a list of dicts."""
        rows: list[dict[str, str]] = []
        vars_ = [str(v) for v in result.vars] if result.vars else []
        for row in result:
            row_dict: dict[str, str] = {}
            r_any: Any = row
            for v in vars_:
                try:
                    val = r_any[v]
                except Exception:
                    val = None
                row_dict[v] = str(val) if val is not None else ""
            rows.append(row_dict)
        return rows

    def format_output(self, result: Result, output_format: str = "table") -> str:
        """Format SPARQL result as table, json, or csv."""
        rows = self.to_dict_list(result)
        vars_ = [str(v) for v in result.vars] if result.vars else []

        fmt = output_format.lower()
        if fmt == "json":
            return json.dumps(rows, ensure_ascii=False, indent=2)

        if fmt == "csv":
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=vars_)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
            return out.getvalue()

        # table format
        if not rows:
            return "No results found."

        col_width = max(160, len(vars_) * 30)
        console = Console(record=True, color_system=None, width=col_width)
        table = Table(show_header=True, header_style="bold", expand=False)
        for v in vars_:
            table.add_column(v, overflow="fold")

        for r in rows:
            table.add_row(*(r.get(v, "") for v in vars_))

        console.print(table)
        return console.export_text()
