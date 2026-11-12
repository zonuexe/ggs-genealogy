"""Validation engine for Japanese Koseki RDF using SHACL rules."""

from __future__ import annotations

import importlib.resources
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pyshacl
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF
from rich.console import Console
from rich.table import Table

SH = Namespace("http://www.w3.org/ns/shacl#")


@dataclass
class ValidationIssue:
    """An individual SHACL validation issue."""

    severity: str
    message: str
    focus_node: str | None = None
    source_shape: str | None = None
    result_path: str | None = None


@dataclass
class ValidationReport:
    """Result of running SHACL validation."""

    conforms: bool
    results_graph: Graph
    results_text: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def violations(self) -> list[ValidationIssue]:
        return [i for i in self.issues if "violation" in i.severity.lower()]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if "warning" in i.severity.lower()]

    @property
    def infos(self) -> list[ValidationIssue]:
        return [i for i in self.issues if "info" in i.severity.lower()]


def get_builtin_ontology_graph() -> Graph:
    """Load default koseki OWL ontology bundled with the package."""
    g = Graph()
    ont_path = importlib.resources.files("ggs.resources.ontology").joinpath("koseki.ttl")
    g.parse(data=ont_path.read_text(encoding="utf-8"), format="turtle")
    return g


def get_builtin_shapes_graph() -> Graph:
    """Load default koseki SHACL shapes bundled with the package."""
    g = Graph()
    shacl_path = importlib.resources.files("ggs.resources.shapes").joinpath("koseki_shacl.ttl")
    g.parse(data=shacl_path.read_text(encoding="utf-8"), format="turtle")
    return g


def _coerce_to_graph(source: Graph | Path | str | Sequence[Path | str]) -> Graph:
    if isinstance(source, Graph):
        return source

    g = Graph()
    if isinstance(source, (Path, str)):
        p = Path(source)
        if p.is_dir():
            for ttl_file in p.rglob("*.ttl"):
                g.parse(location=str(ttl_file), format="turtle")
        elif p.is_file():
            g.parse(location=str(p), format="turtle")
        else:
            # Try parsing as turtle string
            g.parse(data=str(source), format="turtle")
    elif isinstance(source, Sequence):
        for item in source:
            p = Path(item)
            if p.is_dir():
                for ttl_file in p.rglob("*.ttl"):
                    g.parse(location=str(ttl_file), format="turtle")
            elif p.is_file():
                g.parse(location=str(p), format="turtle")
    return g


def extract_issues(results_graph: Graph) -> list[ValidationIssue]:
    """Parse SHACL ValidationResult nodes from the results graph."""
    issues: list[ValidationIssue] = []

    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        severity_uri = results_graph.value(result, SH.resultSeverity)
        severity = severity_uri.split("#")[-1] if isinstance(severity_uri, URIRef) else "Violation"

        msg_val = results_graph.value(result, SH.resultMessage)
        message = str(msg_val) if msg_val else "Validation constraint violated"

        focus_val = results_graph.value(result, SH.focusNode)
        focus_node = str(focus_val) if focus_val else None

        shape_val = results_graph.value(result, SH.sourceShape)
        source_shape = str(shape_val) if shape_val else None

        path_val = results_graph.value(result, SH.resultPath)
        result_path = str(path_val) if path_val else None

        issues.append(
            ValidationIssue(
                severity=severity,
                message=message,
                focus_node=focus_node,
                source_shape=source_shape,
                result_path=result_path,
            )
        )

    return issues


def run_validation(
    data_source: Graph | Path | str | Sequence[Path | str],
    shapes_source: Graph | Path | str | None = None,
    ont_source: Graph | Path | str | None = None,
    strict: bool = False,
) -> ValidationReport:
    """Run SHACL validation against koseki RDF data.

    If strict is True, any warning or violation will cause conforms=False.
    """
    data_graph = _coerce_to_graph(data_source)
    shapes_graph = (
        _coerce_to_graph(shapes_source) if shapes_source is not None else get_builtin_shapes_graph()
    )
    ont_graph = (
        _coerce_to_graph(ont_source) if ont_source is not None else get_builtin_ontology_graph()
    )

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        ont_graph=ont_graph,
        advanced=True,
        inference="rdfs",
        abort_on_first=False,
    )

    res_g: Graph = results_graph if isinstance(results_graph, Graph) else Graph()
    issues = extract_issues(res_g)

    if strict and (len(issues) > 0 or not conforms):
        final_conforms = False
    else:
        final_conforms = bool(conforms)

    return ValidationReport(
        conforms=final_conforms,
        results_graph=res_g,
        results_text=str(results_text),
        issues=issues,
    )


def render_validation_rich(report: ValidationReport, console: Console | None = None) -> None:
    """Render validation report using Rich console."""
    c = console or Console()

    if report.conforms and not report.issues:
        c.print("[bold green]✓ Validation Passed:[/] All SHACL constraints satisfied.")
        return

    status = (
        "[bold green]✓ Conforms (with warnings)[/]"
        if report.conforms
        else "[bold red]✗ Validation Failed[/]"
    )
    c.print(f"{status} - Total issues found: {len(report.issues)}")

    table = Table(title="SHACL Validation Details", show_lines=True)
    table.add_column("Severity", style="bold", width=12)
    table.add_column("Focus Node", style="cyan", width=30)
    table.add_column("Message", style="white")

    for issue in report.issues:
        sev = issue.severity.lower()
        if "violation" in sev:
            sev_styled = "[bold red]VIOLATION[/]"
        elif "warning" in sev:
            sev_styled = "[bold yellow]WARNING[/]"
        else:
            sev_styled = "[bold blue]INFO[/]"

        table.add_row(
            sev_styled,
            issue.focus_node or "-",
            issue.message,
        )

    c.print(table)
