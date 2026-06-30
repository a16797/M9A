from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from agent import bootstrap
from agent import main as agent_main


def test_bootstrap_prepares_dev_runtime_before_main(
    monkeypatch, tmp_path: Path
) -> None:
    current_file = tmp_path / "agent" / "bootstrap.py"
    work_root = tmp_path / "assets"
    current_file.parent.mkdir()
    work_root.mkdir()

    paths = SimpleNamespace(project_root=tmp_path, work_root=work_root)
    run_path = Mock()

    monkeypatch.setattr(bootstrap, "configure_initial_runtime_paths", Mock())
    monkeypatch.setattr(bootstrap, "read_interface_version", Mock(return_value="DEBUG"))
    monkeypatch.setattr(bootstrap, "ensure_venv_and_relaunch_if_needed", Mock())
    monkeypatch.setattr(bootstrap, "check_and_install_dependencies", Mock())
    monkeypatch.setattr(bootstrap, "switch_to_dev_work_root", Mock(return_value=paths))
    monkeypatch.setattr(bootstrap, "switch_to_release_work_root", Mock())
    monkeypatch.setattr(bootstrap.runpy, "run_path", run_path)
    monkeypatch.delenv(bootstrap.ENV_PROJECT_ROOT, raising=False)
    monkeypatch.delenv(bootstrap.ENV_WORK_ROOT, raising=False)
    monkeypatch.delenv(bootstrap.ENV_DEV_MODE, raising=False)

    bootstrap.prepare_and_run_main(current_file)

    assert bootstrap.ENV_PROJECT_ROOT in bootstrap.os.environ
    assert bootstrap.os.environ[bootstrap.ENV_PROJECT_ROOT] == str(tmp_path)
    assert bootstrap.os.environ[bootstrap.ENV_WORK_ROOT] == str(work_root)
    assert bootstrap.os.environ[bootstrap.ENV_DEV_MODE] == "1"
    bootstrap.switch_to_dev_work_root.assert_called_once_with(tmp_path)
    bootstrap.switch_to_release_work_root.assert_not_called()
    run_path.assert_called_once_with(
        str(current_file.with_name("main.py").resolve()),
        run_name="__main__",
    )


def test_main_infers_source_tree_dev_work_root(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path / "m9a"
    assets_dir = project_root / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "interface.json").write_text('{"version":"DEBUG"}', encoding="utf-8")

    monkeypatch.delenv(agent_main.ENV_PROJECT_ROOT, raising=False)
    monkeypatch.delenv(agent_main.ENV_WORK_ROOT, raising=False)
    monkeypatch.delenv(agent_main.ENV_DEV_MODE, raising=False)

    assert agent_main._is_dev_mode(project_root)
    assert agent_main._work_root(project_root, True) == assets_dir.resolve()
