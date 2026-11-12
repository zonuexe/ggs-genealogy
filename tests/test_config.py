from pathlib import Path

from ggs_genealogy.config import GgsConfig, find_config_file, load_config


def test_default_config() -> None:
    config = GgsConfig()
    assert config.name == "ggs-project"
    assert config.base_uri == "https://example.org/koseki#"
    assert config.data_dir == Path("data")
    assert config.work_dir == Path("work")
    assert config.docs_dir == Path("docs")
    assert config.resolved_data_dir == (Path().resolve() / "data")


def test_config_write_and_load(tmp_path: Path) -> None:
    cfg = GgsConfig(
        name="test-family",
        base_uri="https://example.org/family#",
        data_dir=Path("my_data"),
        work_dir=Path("my_work"),
        docs_dir=Path("my_docs"),
        root_dir=tmp_path,
    )
    written_path = cfg.write_config(tmp_path / "ggs.toml")
    assert written_path.is_file()

    loaded = load_config(written_path)
    assert loaded.name == "test-family"
    assert loaded.base_uri == "https://example.org/family#"
    assert loaded.data_dir == Path("my_data")
    assert loaded.resolved_data_dir == (tmp_path / "my_data").resolve()


def test_find_config_file(tmp_path: Path) -> None:
    toml_path = tmp_path / "ggs.toml"
    toml_path.write_text('[project]\nname = "found"\n', encoding="utf-8")

    sub_dir = tmp_path / "sub" / "deep"
    sub_dir.mkdir(parents=True)

    found = find_config_file(sub_dir)
    assert found == toml_path
