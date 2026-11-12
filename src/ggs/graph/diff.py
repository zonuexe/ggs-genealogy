"""Semantic difference engine for RDF graphs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rdflib import Graph
from rdflib.compare import graph_diff, isomorphic, to_isomorphic
from rich.console import Console
from rich.table import Table


@dataclass
class SemanticDiffResult:
    """Result of semantic diff between two RDF graphs."""

    is_identical: bool
    added_triples: list[tuple[Any, Any, Any]] = field(default_factory=list)
    removed_triples: list[tuple[Any, Any, Any]] = field(default_factory=list)
    common_triples_count: int = 0


class SemanticDiffer:
    """Engine for comparing two RDF sources semantically."""

    @staticmethod
    def load_source(source: str | Path | Graph) -> Graph:
        """Load an RDF graph from a file, turtle string, or existing Graph."""
        if isinstance(source, Graph):
            return source

        g = Graph()
        p = Path(source) if isinstance(source, str) else source
        if p.is_file():
            g.parse(location=str(p), format="turtle")
        elif p.is_dir():
            for ttl_file in p.rglob("*.ttl"):
                g.parse(location=str(ttl_file), format="turtle")
        else:
            # Attempt to parse as Turtle string
            g.parse(data=str(source), format="turtle")
        return g

    @classmethod
    def diff(cls, source_a: str | Path | Graph, source_b: str | Path | Graph) -> SemanticDiffResult:
        """Compute semantic difference between two RDF graphs."""
        g_a = cls.load_source(source_a)
        g_b = cls.load_source(source_b)

        iso_a = to_isomorphic(g_a)
        iso_b = to_isomorphic(g_b)

        if isomorphic(iso_a, iso_b):
            return SemanticDiffResult(
                is_identical=True,
                added_triples=[],
                removed_triples=[],
                common_triples_count=len(iso_a),
            )

        in_both, in_a, in_b = graph_diff(iso_a, iso_b)

        return SemanticDiffResult(
            is_identical=False,
            added_triples=sorted(in_b),
            removed_triples=sorted(in_a),
            common_triples_count=len(in_both),
        )


def _format_term(term: Any) -> str:
    """Format an RDF term for display."""
    s = str(term)
    # Simplify long URIs if convenient
    if s.startswith("https://example.org/ns/koseki#"):
        return "k:" + s[len("https://example.org/ns/koseki#") :]
    if s.startswith("https://imi.go.jp/ns/core/rdf#"):
        return "ic:" + s[len("https://imi.go.jp/ns/core/rdf#") :]
    if s.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"):
        return "a"
    return s


def render_diff_rich(
    diff_result: SemanticDiffResult,
    source_a_label: str = "Source A",
    source_b_label: str = "Source B",
    console: Console | None = None,
) -> None:
    """Render semantic diff using Rich console."""
    c = console or Console()

    if diff_result.is_identical:
        c.print(f"[bold green]✓ Identical:[/] {source_a_label} and {source_b_label} are semantically equivalent ({diff_result.common_triples_count} triples).")
        return

    c.print(
        f"[bold yellow]Semantic Diff:[/] {source_a_label} vs {source_b_label} "
        f"([green]+{len(diff_result.added_triples)} added[/], [red]-{len(diff_result.removed_triples)} removed[/], {diff_result.common_triples_count} shared)"
    )

    table = Table(title="Differences", show_lines=False)
    table.add_column("Type", width=4)
    table.add_column("Subject", style="cyan")
    table.add_column("Predicate", style="magenta")
    table.add_column("Object", style="white")

    for s, p, o in diff_result.removed_triples:
        table.add_row("[-]", _format_term(s), _format_term(p), _format_term(o), style="red")

    for s, p, o in diff_result.added_triples:
        table.add_row("[+]", _format_term(s), _format_term(p), _format_term(o), style="green")

    c.print(table)
