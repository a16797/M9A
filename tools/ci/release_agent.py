import sys


def release_agent_child_exec(platform: str | None = None) -> str:
    platform_name = platform or sys.platform
    if platform_name.startswith("win"):
        return r"./python/python.exe"
    if platform_name.startswith("darwin"):
        return r"./python/bin/python3"
    if platform_name.startswith("linux"):
        return r"python3"
    raise RuntimeError(f"Unsupported release platform: {platform_name}")


def configure_release_agent(interface: dict, platform: str | None = None) -> None:
    agent = interface.get("agent")
    if not isinstance(agent, dict):
        raise RuntimeError("interface.json must contain an agent object")

    agent["child_exec"] = release_agent_child_exec(platform)
    agent["child_args"] = ["-u", r"./agent/main.py"]
    assert_release_agent_config(interface)


def assert_release_agent_config(interface: dict) -> None:
    agent = interface.get("agent")
    if not isinstance(agent, dict):
        raise RuntimeError("interface.json must contain an agent object")

    child_exec = agent.get("child_exec")
    child_args = agent.get("child_args", [])
    if child_exec == "uv" or (isinstance(child_args, list) and "uv" in child_args):
        raise RuntimeError("release interface.json must not launch Agent through uv")
