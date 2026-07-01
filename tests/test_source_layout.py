from pathlib import Path

import pytest

from tools.source_layout import discover_source_layout


def test_discovers_template_root_layout(tmp_path: Path) -> None:
    resource = tmp_path / "resource"
    data = tmp_path / "data"
    tasks = tmp_path / "tasks"
    schema = tmp_path / "tools" / "schema"
    resource.mkdir()
    data.mkdir()
    tasks.mkdir()
    schema.mkdir(parents=True)
    (tmp_path / "interface.json").write_text("{}", encoding="utf-8")

    layout = discover_source_layout(tmp_path)

    assert layout.interface_file == tmp_path / "interface.json"
    assert layout.resource_dir == resource
    assert layout.data_dir == data
    assert layout.task_dir == tasks
    assert layout.schema_dir == schema
    assert data not in layout.pipeline_exclude_dirs
    assert tasks not in layout.pipeline_exclude_dirs


def test_rejects_legacy_assets_layout(tmp_path: Path) -> None:
    assets_resource = tmp_path / "assets" / "resource"
    assets_resource.mkdir(parents=True)
    (tmp_path / "assets" / "interface.json").write_text("{}", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        discover_source_layout(tmp_path)
