
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from ggs_genealogy import __version__
from ggs_genealogy.cli import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"ggs (Genealogical Graph System) v{__version__}" in result.stdout


def test_cli_init_and_validate(tmp_path: Path) -> None:
    project_dir = tmp_path / "my_project"
    init_res = runner.invoke(app, ["init", str(project_dir), "--name", "test-project"])
    assert init_res.exit_code == 0
    assert (project_dir / "ggs.toml").is_file()
    assert (project_dir / "data" / "sample.ttl").is_file()

    # Validate the generated sample.ttl
    val_res = runner.invoke(app, ["validate", str(project_dir / "data")])
    assert val_res.exit_code == 0
    assert "Validation Passed" in val_res.stdout


def test_cli_diff(tmp_path: Path) -> None:
    f1 = tmp_path / "a.ttl"
    f2 = tmp_path / "b.ttl"
    f1.write_text(
        '@prefix : <https://example.org/k#> .\n:p a <https://example.org/ns/koseki#人物> .\n',
        encoding="utf-8",
    )
    f2.write_text(
        '@prefix : <https://example.org/k#> .\n:p a <https://example.org/ns/koseki#人物> .\n',
        encoding="utf-8",
    )

    diff_res = runner.invoke(app, ["diff", str(f1), str(f2)])
    assert diff_res.exit_code == 0
    assert "Identical" in diff_res.stdout


def test_cli_prompt() -> None:
    res = runner.invoke(app, ["prompt", "--no-existing", "-i", "昭和初期の戸籍"])
    assert res.exit_code == 0
    assert "昭和初期の戸籍" in res.stdout
    assert "koseki.ttl" in res.stdout
