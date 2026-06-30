import hashlib
import importlib.metadata
import json
import os
import re
import runpy
import subprocess
import sys
from pathlib import Path

try:
    from utils import logger
    from utils.runtime_paths import configure_runtime_paths, get_runtime_paths
except ImportError:
    from .utils import logger
    from .utils.runtime_paths import configure_runtime_paths, get_runtime_paths

VENV_NAME = ".venv"
REQUIREMENTS_MARKER_NAME = ".m9a-requirements.sha256"
ENV_PROJECT_ROOT = "M9A_AGENT_PROJECT_ROOT"
ENV_WORK_ROOT = "M9A_AGENT_WORK_ROOT"
ENV_DEV_MODE = "M9A_AGENT_DEV_MODE"
REQUIREMENT_NAME_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(?:==\s*v?([^;\s]+))?"
)


def configure_initial_runtime_paths(project_root_dir: str | Path):
    return configure_runtime_paths(
        project_root=project_root_dir,
        work_root=project_root_dir,
    )


def _venv_dir() -> Path:
    return get_runtime_paths().project_root / VENV_NAME


def _is_running_in_our_venv():
    """检查脚本是否在虚拟环境中运行。"""
    # 使用 sys.prefix 和 sys.base_prefix 来判断是否在虚拟环境中
    in_venv = sys.prefix != sys.base_prefix

    if in_venv:
        logger.debug(f"当前在虚拟环境中运行: {sys.prefix}")
    else:
        logger.debug(f"当前不在虚拟环境中，使用系统Python: {sys.prefix}")

    return in_venv


def ensure_venv_and_relaunch_if_needed(current_file_path: str):
    """
    确保venv存在，并且如果尚未在脚本管理的venv中运行，
    则在其中重新启动脚本。支持Linux和Windows系统。
    """
    venv_dir = _venv_dir()
    logger.info(f"检测到系统: {sys.platform}。当前Python解释器: {sys.executable}")

    if _is_running_in_our_venv():
        logger.info(f"已在目标虚拟环境 ({venv_dir}) 中运行。")
        return

    if not venv_dir.exists():
        logger.info(f"正在 {venv_dir} 创建虚拟环境...")
        try:
            # 使用当前运行此脚本的Python（系统/外部Python）
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
            )
            logger.info("创建成功")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"创建失败: {e.stderr.decode(errors='ignore') if e.stderr else e.stdout.decode(errors='ignore')}"
            )
            logger.error("正在退出")
            sys.exit(1)
        except FileNotFoundError:
            logger.error(
                f"命令 '{sys.executable} -m venv' 未找到。请确保 'venv' 模块可用。"
            )
            logger.error("无法在没有虚拟环境的情况下继续。正在退出。")
            sys.exit(1)

    if sys.platform.startswith("win"):
        python_in_venv = venv_dir / "Scripts" / "python.exe"
    else:
        python3_path = venv_dir / "bin" / "python3"
        python_path = venv_dir / "bin" / "python"
        if python3_path.exists():
            python_in_venv = python3_path
        elif python_path.exists():
            python_in_venv = python_path
        else:
            python_in_venv = python3_path  # 默认使用python3，让后续错误处理捕获

    if not python_in_venv.exists():
        logger.error(f"在虚拟环境 {python_in_venv} 中未找到Python解释器。")
        logger.error("虚拟环境创建可能失败或虚拟环境结构异常。")
        sys.exit(1)

    logger.info("正在使用虚拟环境Python重新启动")

    try:
        # Use the absolute bootstrap path when relaunching inside the venv.
        # sys.argv[0] may be relative to assets/ and resolve differently after
        # cwd changes.
        script_abs = current_file_path
        args = sys.argv[1:]
        cmd = [str(python_in_venv), str(script_abs)] + args
        logger.info(f"执行命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            env=os.environ.copy(),
            check=False,  # 不在非零退出码时抛出异常
        )
        # 退出时使用子进程的退出码
        sys.exit(result.returncode)

    except Exception as e:
        logger.exception(f"在虚拟环境中重新启动脚本失败: {e}")
        sys.exit(1)


def read_config(config_name: str, default_config: dict) -> dict:
    """
    通用配置文件读取函数

    Args:
        config_name: 配置文件名（不含.json后缀）
        default_config: 默认配置字典

    Returns:
        配置字典
    """
    config_dir = get_runtime_paths().config_dir
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / f"{config_name}.json"

    if not config_path.exists():
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
        except Exception:
            logger.debug(f"无法写入 {config_name}.json，使用默认配置")
        return default_config

    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception(f"读取 {config_name}.json 失败，使用默认配置")
        return default_config


def read_interface_version(interface_file_name="./interface.json") -> str:
    paths = get_runtime_paths()
    interface_path = paths.project_root / interface_file_name
    assets_interface_path = paths.assets_dir / interface_file_name

    target_path = None
    if interface_path.exists():
        target_path = interface_path
    elif assets_interface_path.exists():
        return "DEBUG"

    if target_path is None:
        logger.warning("未找到interface.json")
        return "unknown"

    try:
        with open(target_path, encoding="utf-8") as f:
            interface_data = json.load(f)
            return interface_data.get("version", "unknown")
    except Exception:
        logger.exception(f"读取interface.json版本失败，文件路径：{target_path}")
        return "unknown"


def read_pip_config() -> dict:
    default_config = {
        "enable_pip_install": True,
        "mirror": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "backup_mirror": "https://mirrors.ustc.edu.cn/pypi/simple",
    }
    return read_config("pip_config", default_config)


def read_hot_update_config() -> dict:
    """
    读取热更配置
    """
    default_config = {"enable_hot_update": True}
    return read_config("hot_update", default_config)


def find_local_wheels_dir():
    """查找本地deps目录中的whl文件"""
    deps_dir = get_runtime_paths().deps_dir

    if deps_dir.exists() and any(deps_dir.glob("*.whl")):
        whl_count = len(list(deps_dir.glob("*.whl")))
        logger.debug(f"发现本地deps目录包含 {whl_count} 个 whl 文件")
        return deps_dir

    logger.debug("未找到deps目录或目录中无 whl 文件")
    return None


def _requirements_digest(req_path: Path) -> str:
    return hashlib.sha256(req_path.read_bytes()).hexdigest()


def _requirements_marker_path() -> Path:
    if _is_running_in_our_venv():
        return _venv_dir() / REQUIREMENTS_MARKER_NAME
    return get_runtime_paths().debug_dir / REQUIREMENTS_MARKER_NAME


def _is_package_installed(package_name: str) -> bool:
    try:
        importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def _normalize_version(version: str) -> str:
    return version.strip().lower().removeprefix("v")


def _iter_runtime_requirements(req_path: Path):
    for line in req_path.read_text(encoding="utf-8").splitlines():
        requirement = line.split("#", 1)[0].strip()
        if not requirement:
            continue
        match = REQUIREMENT_NAME_PATTERN.match(requirement)
        if match:
            yield match.group(1), match.group(2)


def _runtime_requirements_installed(req_path: Path) -> bool:
    missing = []
    mismatched = []
    for package_name, expected_version in _iter_runtime_requirements(req_path):
        try:
            installed_version = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(package_name)
            continue

        if expected_version and _normalize_version(
            installed_version
        ) != _normalize_version(expected_version):
            mismatched.append(
                f"{package_name}=={installed_version} (need {expected_version})"
            )

    if missing:
        logger.debug(f"缺少运行时依赖: {', '.join(missing)}")
    if mismatched:
        logger.debug(f"运行时依赖版本不匹配: {', '.join(mismatched)}")
    return not missing and not mismatched


def _requirements_are_current(digest: str, req_path: Path) -> bool:
    if _runtime_requirements_installed(req_path):
        marker_path = _requirements_marker_path()
        marker_digest = None
        if marker_path.exists():
            try:
                marker_digest = marker_path.read_text(encoding="utf-8").strip()
            except OSError:
                logger.debug(f"无法读取依赖安装标记: {marker_path}")

        if marker_digest != digest:
            logger.info("运行时依赖已满足，更新 requirements 安装标记")
            _write_requirements_marker(digest)
        else:
            logger.info("requirements.txt 未变化且依赖已安装，跳过 pip 安装")
        return True

    marker_path = _requirements_marker_path()
    if not marker_path.exists():
        return False

    try:
        marker_digest = marker_path.read_text(encoding="utf-8").strip()
    except OSError:
        logger.debug(f"无法读取依赖安装标记: {marker_path}")
        return False

    if marker_digest != digest:
        logger.debug("requirements.txt 已变化，需要重新安装依赖")
        return False

    logger.debug("依赖安装标记存在，但运行时依赖不完整，需要重新安装依赖")
    return False


def _write_requirements_marker(digest: str) -> None:
    marker_path = _requirements_marker_path()
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(f"{digest}\n", encoding="utf-8")
        logger.debug(f"写入依赖安装标记: {marker_path}")
    except OSError:
        logger.exception(f"写入依赖安装标记失败: {marker_path}")


def _run_pip_command(cmd_args: list, operation_name: str) -> bool:
    try:
        logger.info(f"开始 {operation_name}")
        logger.debug(f"执行命令: {' '.join(cmd_args)}")

        # 使用subprocess.Popen进行实时输出
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,  # 行缓冲
            universal_newlines=True,
        )

        # 收集所有输出用于日志记录
        all_output = []

        # 实时读取并显示输出
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                line = line.rstrip("\n\r")
                if line.strip():  # 只显示非空行
                    all_output.append(line)  # 收集到列表中

        # 等待进程结束
        return_code = process.wait()

        # 记录完整输出到日志
        if all_output:
            full_output = "\n".join(all_output)
            logger.debug(f"{operation_name} 输出:\n{full_output}")

        if return_code == 0:
            logger.info(f"{operation_name} 完成")
            return True
        else:
            logger.error(f"{operation_name} 时出错。返回码: {return_code}")
            return False

    except Exception as e:
        logger.exception(f"{operation_name} 时发生未知异常: {e}")
        return False


def install_requirements(
    req_file="requirements.txt", pip_config: dict | None = None
) -> bool:
    req_path = get_runtime_paths().project_root / req_file  # 确保相对于项目根目录
    if not req_path.exists():
        logger.error(f"{req_file} 文件不存在于 {req_path.resolve()}")
        return False

    requirements_digest = _requirements_digest(req_path)
    logger.debug(f"{req_file} sha256: {requirements_digest}")

    if _requirements_are_current(requirements_digest, req_path):
        return True

    # 查找本地deps目录
    deps_dir = find_local_wheels_dir()
    if deps_dir:
        logger.debug(f"使用本地 whl 文件安装，目录: {deps_dir}")

        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "-r",
            str(req_path),
            "--no-warn-script-location",
            "--break-system-packages",
            "--find-links",
            str(deps_dir),  # pip会优先使用这里的文件
            "--no-index",  # 禁止在线索引
        ]

        if _run_pip_command(cmd, "从本地deps安装依赖"):
            _write_requirements_marker(requirements_digest)
            return True
        else:
            logger.warning("本地deps安装失败，回退到纯在线安装")

    # 回退到在线安装
    primary_mirror = pip_config.get("mirror", "") if pip_config else ""
    backup_mirror = pip_config.get("backup_mirror", "") if pip_config else ""

    if primary_mirror:
        # 使用主镜像源，只添加一个备用源避免冲突
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "-r",
            str(req_path),
            "--no-warn-script-location",
            "--break-system-packages",
            "-i",
            primary_mirror,
        ]

        # 只添加一个备用源
        if backup_mirror:
            cmd.extend(["--extra-index-url", backup_mirror])
            logger.info(f"使用主源 {primary_mirror} 和备用源 {backup_mirror} 安装依赖")
        else:
            logger.info(f"使用主源 {primary_mirror} 安装依赖")

        if _run_pip_command(cmd, f"从 {req_path.name} 安装依赖"):
            _write_requirements_marker(requirements_digest)
            return True
        else:
            logger.error("在线安装失败")
            return False
    else:
        # 如果没有配置主镜像源，使用pip的本地全局配置
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "-r",
            str(req_path),
            "--no-warn-script-location",
            "--break-system-packages",
        ]

        if _run_pip_command(cmd, f"从 {req_path.name} 安装依赖 (本地全局配置)"):
            _write_requirements_marker(requirements_digest)
            return True
        else:
            logger.error("使用pip本地全局配置安装失败")
            return False


def check_and_install_dependencies():
    """检查并安装项目依赖"""
    pip_config = read_pip_config()
    enable_pip_install = pip_config.get("enable_pip_install", True)

    logger.debug(f"启用 pip 安装依赖: {enable_pip_install}")

    if enable_pip_install:
        logger.info("开始安装/更新依赖")
        if install_requirements(pip_config=pip_config):
            logger.info("依赖检查和安装完成")
        else:
            logger.warning("依赖安装失败，程序可能无法正常运行")
    else:
        logger.info("Pip 依赖安装已禁用，跳过依赖安装")


def switch_to_dev_work_root(project_root_dir: str | Path):
    paths = configure_runtime_paths(
        project_root=project_root_dir,
        work_root=get_runtime_paths().assets_dir,
    )
    os.chdir(paths.work_root)
    logger.info(f"set cwd: {os.getcwd()}")
    return paths


def switch_to_release_work_root(project_root_dir: str | Path):
    paths = configure_runtime_paths(
        project_root=project_root_dir,
        work_root=project_root_dir,
    )
    if Path.cwd().resolve() != paths.work_root:
        os.chdir(paths.work_root)
        logger.info(f"set cwd: {os.getcwd()}")
    return paths


def prepare_and_run_main(current_file_path: str | Path) -> None:
    current_file = Path(current_file_path).resolve()
    project_root_dir = current_file.parent.parent

    configure_initial_runtime_paths(project_root_dir)
    current_version = read_interface_version()
    is_dev_mode = current_version == "DEBUG"

    if sys.platform.startswith("linux") or is_dev_mode:
        ensure_venv_and_relaunch_if_needed(str(current_file))

    check_and_install_dependencies()

    if is_dev_mode:
        paths = switch_to_dev_work_root(project_root_dir)
    else:
        paths = switch_to_release_work_root(project_root_dir)

    os.environ[ENV_PROJECT_ROOT] = str(paths.project_root)
    os.environ[ENV_WORK_ROOT] = str(paths.work_root)
    os.environ[ENV_DEV_MODE] = "1" if is_dev_mode else "0"

    runpy.run_path(str(current_file.with_name("main.py")), run_name="__main__")


def main() -> None:
    prepare_and_run_main(Path(__file__).resolve())


if __name__ == "__main__":
    main()
