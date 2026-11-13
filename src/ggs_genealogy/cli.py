"""Command Line Interface for Genealogical Graph System (GGS)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rdflib import Graph
from rich.console import Console

from ggs_genealogy import __version__
from ggs_genealogy.agent.prompt_builder import PromptBuilder
from ggs_genealogy.config import SAMPLE_TURTLE_TEMPLATE, GgsConfig, load_config
from ggs_genealogy.converters.dot_export import DotExporter
from ggs_genealogy.converters.gramps_export import GrampsExporter
from ggs_genealogy.converters.gramps_import import GrampsImporter
from ggs_genealogy.graph.diff import SemanticDiffer, render_diff_rich
from ggs_genealogy.query.runner import QueryRunner
from ggs_genealogy.validation.validator import render_validation_rich, run_validation

app = typer.Typer(
    name="ggs",
    help="Genealogical Graph System (GGS) - Japanese Koseki RDF & Gramps Bridge CLI",
    no_args_is_help=True,
)
console = Console()


def _load_graph_from_source(source: Path | None, config: GgsConfig) -> Graph:
    """Load RDF graph from specified source path or resolved data_dir."""
    target = source or config.resolved_data_dir
    g = Graph()
    if target.is_dir():
        for ttl_path in sorted(target.rglob("*.ttl")):
            g.parse(location=str(ttl_path), format="turtle")
    elif target.is_file():
        g.parse(location=str(target), format="turtle")
    return g


@app.command()
def init(
    directory: Annotated[
        Path,
        typer.Argument(help="Target directory to initialize GGS project"),
    ] = Path(),
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="Project name"),
    ] = "ggs-project",
    base_uri: Annotated[
        str,
        typer.Option("--base-uri", "-b", help="Base URI for genealogical RDF entities"),
    ] = "https://example.org/koseki#",
) -> None:
    """Initialize a new GGS workspace with ggs.toml, data, work, docs directories."""
    target_dir = directory.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    config = GgsConfig(
        name=name,
        base_uri=base_uri,
        data_dir=Path("data"),
        work_dir=Path("work"),
        docs_dir=Path("docs"),
        root_dir=target_dir,
    )
    config_file = config.write_config(target_dir / "ggs.toml")

    # Create directories
    data_dir = target_dir / "data"
    work_dir = target_dir / "work"
    docs_dir = target_dir / "docs"

    data_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Generate sample.ttl if data directory is empty
    sample_file = data_dir / "sample.ttl"
    if not sample_file.exists():
        sample_file.write_text(
            SAMPLE_TURTLE_TEMPLATE.format(base_uri=base_uri),
            encoding="utf-8",
        )

    console.print(f"[bold green]Initialized GGS project in:[/] {target_dir}")
    console.print(f"  - Config: {config_file.name}")
    console.print("  - Directories: data/, work/, docs/")
    console.print(f"  - Sample RDF: data/{sample_file.name}")


@app.command()
def validate(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(
            help="RDF files or directories to validate. Defaults to data_dir."
        ),
    ] = None,
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Treat warnings as violations (strict mode)"),
    ] = False,
) -> None:
    """Validate RDF Turtle data against Japanese Koseki SHACL rules."""
    config = load_config()
    target_paths: list[Path] = paths if paths else [config.resolved_data_dir]

    report = run_validation(target_paths, strict=strict)
    render_validation_rich(report, console=console)

    if not report.conforms:
        raise typer.Exit(code=1)


@app.command()
def export(
    to: Annotated[
        str,
        typer.Option("--to", "-t", help="Target format: gramps, dot, or ttl"),
    ] = "gramps",
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    compress: Annotated[
        bool,
        typer.Option(
            "--compress/--no-compress", help="Compress output with gzip (for Gramps)"
        ),
    ] = False,
    source: Annotated[
        Path | None,
        typer.Option("--source", "-s", help="Source RDF path (defaults to data_dir)"),
    ] = None,
) -> None:
    """Export RDF graph to Gramps XML, Graphviz DOT, or Turtle."""
    config = load_config()
    graph = _load_graph_from_source(source, config)

    if len(graph) == 0:
        console.print("[yellow]Warning: Source RDF graph is empty.[/]")

    fmt = to.lower()
    work_dir = config.resolved_work_dir
    work_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "gramps":
        default_name = "export.gramps" if compress else "export.xml"
        out_path = output or (work_dir / default_name)
        exporter = GrampsExporter(graph)
        written = exporter.export_to_file(out_path, compress=compress)
        console.print(f"[bold green]Exported Gramps XML:[/] {written}")
    elif fmt == "dot":
        out_path = output or (work_dir / "genealogy.dot")
        dot_exporter = DotExporter(graph)
        written = dot_exporter.export_to_file(out_path, title=config.name)
        console.print(f"[bold green]Exported Graphviz DOT:[/] {written}")
    elif fmt == "ttl":
        out_path = output or (work_dir / "export.ttl")
        out_path.write_text(graph.serialize(format="turtle"), encoding="utf-8")
        console.print(f"[bold green]Exported Turtle:[/] {out_path}")
    else:
        console.print(
            f"[bold red]Error:[/] Unknown export format '{to}'. Choose from gramps, dot, ttl."
        )
        raise typer.Exit(code=1)


@app.command(name="import")
def import_gramps(
    gramps_file: Annotated[
        Path,
        typer.Argument(help="Path to Gramps XML or .gramps file to import"),
    ],
    target: Annotated[
        Path | None,
        typer.Option("--target", "-t", help="Target Turtle file to save merged graph"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Display semantic diff without writing to disk"),
    ] = False,
) -> None:
    """Import Gramps XML / .gramps file and merge with existing RDF data."""
    if not gramps_file.is_file():
        console.print(f"[bold red]Error:[/] Gramps file not found: {gramps_file}")
        raise typer.Exit(code=1)

    config = load_config()
    base_graph = _load_graph_from_source(None, config)

    importer = GrampsImporter.from_file(gramps_file)
    imported_graph = importer.to_rdf_graph()

    # Merge graphs
    merged_graph = Graph()
    for t in base_graph:
        merged_graph.add(t)
    for t in imported_graph:
        merged_graph.add(t)

    # Compute diff between base and merged
    diff_result = SemanticDiffer.diff(base_graph, merged_graph)
    render_diff_rich(
        diff_result,
        source_a_label="Existing RDF",
        source_b_label="Imported Gramps",
        console=console,
    )

    if dry_run:
        console.print("[yellow]Dry-run mode:[/] No files were modified.")
        return

    out_file = target or (config.resolved_data_dir / "imported.ttl")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(merged_graph.serialize(format="turtle"), encoding="utf-8")
    console.print(f"[bold green]Saved merged RDF data to:[/] {out_file}")


@app.command()
def diff(
    source_a: Annotated[
        Path,
        typer.Argument(help="First RDF file or directory"),
    ],
    source_b: Annotated[
        Path,
        typer.Argument(help="Second RDF file or directory"),
    ],
) -> None:
    """Show semantic differences between two RDF graphs."""
    result = SemanticDiffer.diff(source_a, source_b)
    render_diff_rich(result, str(source_a), str(source_b), console=console)


@app.command()
def query(
    preset: Annotated[
        str | None,
        typer.Option(
            "--preset", "-p", help="Preset query name (e.g. heads, adoptions)"
        ),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option("--file", "-f", help="Path to custom SPARQL query file"),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: table, json, or csv"),
    ] = "table",
    source: Annotated[
        Path | None,
        typer.Option("--source", "-s", help="Source RDF data directory or file"),
    ] = None,
) -> None:
    """Execute SPARQL queries against RDF data with table, JSON, or CSV output."""
    if preset is None and file is None:
        console.print(
            "[bold yellow]Specify --preset or --file.[/]\nAvailable presets: "
            + ", ".join(QueryRunner.list_presets())
        )
        raise typer.Exit(code=1)

    if preset is not None:
        try:
            query_str = QueryRunner.load_preset_query(preset)
        except ValueError as err:
            console.print(f"[bold red]Error:[/] {err}")
            raise typer.Exit(code=1) from err
    else:
        assert file is not None
        if not file.is_file():
            console.print(f"[bold red]Error:[/] SPARQL file not found: {file}")
            raise typer.Exit(code=1)
        query_str = file.read_text(encoding="utf-8")

    config = load_config()
    graph = _load_graph_from_source(source, config)

    runner = QueryRunner(graph)
    res = runner.execute(query_str)
    output_text = runner.format_output(res, output_format=output_format)
    typer.echo(output_text)


@app.command()
def prompt(
    data_paths: Annotated[
        list[Path] | None,
        typer.Option(
            "--data", "-d", help="Paths to existing RDF data to provide as context"
        ),
    ] = None,
    input_text: Annotated[
        str | None,
        typer.Option("--input", "-i", help="Raw Japanese transcript text"),
    ] = None,
    include_existing: Annotated[
        bool,
        typer.Option(
            "--include-existing/--no-existing",
            help="Include existing data graph in prompt",
        ),
    ] = True,
) -> None:
    """Generate LLM system prompt and context to extract koseki transcripts into RDF."""
    config = load_config()
    paths = data_paths if data_paths is not None else [config.resolved_data_dir]

    builder = PromptBuilder(
        base_uri=config.base_uri,
        data_paths=paths,
        include_existing=include_existing,
        input_text=input_text,
    )
    typer.echo(builder.build())


@app.command()
def version() -> None:
    """Display GGS version."""
    typer.echo(f"ggs (Genealogical Graph System) v{__version__}")


if __name__ == "__main__":
    app()
