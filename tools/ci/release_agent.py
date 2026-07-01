import sys
from typing import Any, cast


def release_agent_child_exec(platform: str | None = None) -> str:
    platform_name = platform or sys.platform
    if platform_name.startswith("win"):
        return r"./python/python.exe"
    if platform_name.startswith("darwin"):
        return r"./python/bin/python3"
    if platform_name.startswith("linux"):
        return r"python3"
    raise RuntimeError(f"Unsupported release platform: {platform_name}")


def iter_agent_configs(interface: dict[str, Any]) -> list[dict[str, Any]]:
    agent = interface.get("agent")
    if isinstance(agent, dict):
        return [cast(dict[str, Any], agent)]
    if isinstance(agent, list) and all(isinstance(item, dict) for item in agent):
        return cast(list[dict[str, Any]], agent)
    raise RuntimeError("interface.json must contain an agent object or object list")


def configure_release_agent(interface: dict[str, Any], platform: str | None = None) -> None:
    for agent in iter_agent_configs(interface):
        agent["child_exec"] = release_agent_child_exec(platform)
        agent["child_args"] = ["-u", r"./agent/bootstrap.py"]
    assert_release_agent_config(interface)


def assert_release_agent_config(interface: dict[str, Any]) -> None:
    for agent in iter_agent_configs(interface):
        child_exec = agent.get("child_exec")
        child_args = agent.get("child_args", [])
        if child_exec == "uv" or (isinstance(child_args, list) and "uv" in child_args):
            raise RuntimeError("release interface.json must not launch Agent through uv")
