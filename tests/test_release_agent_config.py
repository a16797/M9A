import json
from pathlib import Path

import pytest

from tools.ci.release_agent import configure_release_agent
from tools.source_layout import discover_source_layout


def read_source_interface() -> dict:
    interface_file = discover_source_layout(Path.cwd()).interface_file
    return json.loads(interface_file.read_text(encoding="utf-8"))


def test_source_agent_uses_uv_for_development() -> None:
    agent = read_source_interface()["agent"][0]

    assert agent["child_exec"] == "uv"
    assert agent["child_args"] == ["run", "python", "agent/bootstrap.py"]
    assert agent["identifier"] == "m9a.agent"


@pytest.mark.parametrize(
    ("platform", "expected_child_exec"),
    [
        ("win32", r"./python/python.exe"),
        ("darwin", r"./python/bin/python3"),
        ("linux", "python3"),
    ],
)
def test_release_agent_config_rewrites_uv_entry(platform: str, expected_child_exec: str) -> None:
    interface = read_source_interface()

    configure_release_agent(interface, platform)

    agent = interface["agent"][0]
    assert agent["child_exec"] == expected_child_exec
    assert agent["child_args"] == ["-u", r"./agent/bootstrap.py"]
