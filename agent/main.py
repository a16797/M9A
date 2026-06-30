import os
import sys
from contextlib import suppress
from pathlib import Path

with suppress(AttributeError):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ENV_PROJECT_ROOT = "M9A_AGENT_PROJECT_ROOT"
ENV_WORK_ROOT = "M9A_AGENT_WORK_ROOT"
ENV_DEV_MODE = "M9A_AGENT_DEV_MODE"


def _agent_dir() -> Path:
    return Path(__file__).resolve().parent


def _project_root() -> Path:
    env_project_root = os.getenv(ENV_PROJECT_ROOT)
    if env_project_root:
        return Path(env_project_root).resolve()
    return _agent_dir().parent


def _is_dev_mode(project_root: Path) -> bool:
    env_dev_mode = os.getenv(ENV_DEV_MODE)
    if env_dev_mode is not None:
        return env_dev_mode == "1"
    return (
        not (project_root / "interface.json").exists()
        and (project_root / "assets" / "interface.json").exists()
    )


def _work_root(project_root: Path, is_dev_mode: bool) -> Path:
    env_work_root = os.getenv(ENV_WORK_ROOT)
    if env_work_root:
        return Path(env_work_root).resolve()
    if is_dev_mode:
        return (project_root / "assets").resolve()
    return project_root.resolve()


def _prepare_process(work_root: Path) -> None:
    if Path.cwd().resolve() != work_root:
        os.chdir(work_root)

    agent_dir = str(_agent_dir())
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)


def main() -> int:
    project_root = _project_root()
    is_dev_mode = _is_dev_mode(project_root)
    work_root = _work_root(project_root, is_dev_mode)
    _prepare_process(work_root)

    from agent_runtime import run_agent  # noqa: E402

    result = run_agent(project_root_dir=str(project_root), is_dev_mode=is_dev_mode)
    return int(result or 0)


if __name__ == "__main__":
    sys.exit(main())
