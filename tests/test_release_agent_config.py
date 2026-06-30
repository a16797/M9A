import json
from pathlib import Path

import pytest

from tools.ci.release_agent import configure_release_agent


def read_source_interface() -> dict:
    return json.loads(Path("assets/interface.json").read_text(encoding="utf-8"))


def test_source_agent_uses_uv_for_development() -> None:
    agent = read_source_interface()["agent"]

    assert agent["child_exec"] == "uv"
    assert agent["child_args"][:3] == ["run", "--frozen", "python"]
    assert agent["child_args"][-1] == "./../agent/bootstrap.py"


@pytest.mark.parametrize(
    ("platform", "expected_child_exec"),
    [
        ("win32", r"./python/python.exe"),
        ("darwin", r"./python/bin/python3"),
        ("linux", "python3"),
    ],
)
def test_release_agent_config_rewrites_uv_entry(
    platform: str, expected_child_exec: str
) -> None:
    interface = read_source_interface()

    configure_release_agent(interface, platform)

    assert interface["agent"]["child_exec"] == expected_child_exec
    assert interface["agent"]["child_args"] == ["-u", r"./agent/bootstrap.py"]
