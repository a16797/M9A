from pathlib import Path

import shutil
import sys
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from configure import configure_ocr_model
from generate_manifest_cache import generate_manifest_cache
from release_agent import configure_release_agent

working_dir = Path(__file__).parent.parent.parent
sys.path.append(str(working_dir))

from tools.source_layout import discover_source_layout

install_path = working_dir / Path("install")
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"
platform_tag = len(sys.argv) > 2 and sys.argv[2] or ""
source_layout = discover_source_layout(working_dir)


def install_deps(platform_tag: str):
    """安装 MaaFramework 依赖到对应架构路径

    Args:
        platform_tag: 平台标签，如 win-x64, linux-arm64, osx-arm64
    """
    if not platform_tag:
        raise ValueError("platform_tag is required")

    shutil.copytree(
        working_dir / "deps" / "bin",
        install_path / "runtimes" / platform_tag / "native",
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
            "plugins",
            "*.node",
            "*MaaPiCli*",
        ),
        dirs_exist_ok=True,
    )
    shutil.copytree(
        working_dir / "deps" / "share" / "MaaAgentBinary",
        install_path / "libs" / "MaaAgentBinary",
        dirs_exist_ok=True,
    )
    shutil.copytree(
        working_dir / "deps" / "bin" / "plugins",
        install_path / "plugins" / platform_tag,
        dirs_exist_ok=True,
    )


def install_resource():

    configure_ocr_model()

    shutil.copytree(
        source_layout.resource_dir,
        install_path / "resource",
        dirs_exist_ok=True,
    )
    shutil.copytree(
        source_layout.data_dir,
        install_path / "data",
        dirs_exist_ok=True,
    )
    shutil.copytree(
        source_layout.task_dir,
        install_path / "tasks",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        source_layout.interface_file,
        install_path,
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)

    interface["version"] = version
    interface["title"] = f"M9A {version} | 亿韭韭韭小助手"

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)


def install_chores():
    for file in ["README.md", "LICENSE", "CONTACT", "requirements.txt"]:
        shutil.copy2(
            working_dir / file,
            install_path,
        )
    # shutil.copytree(
    #     working_dir / "docs",
    #     install_path / "docs",
    #     dirs_exist_ok=True,
    #     ignore=shutil.ignore_patterns("*.yaml"),
    # )


def install_agent():
    shutil.copytree(
        working_dir / "agent",
        install_path / "agent",
        dirs_exist_ok=True,
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)

    configure_release_agent(interface)

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)


def install_manifest_cache():
    """生成初始 manifest 缓存，加速用户首次启动"""
    data_dir = install_path / "data"
    success = generate_manifest_cache(data_dir)
    if success:
        print("Manifest cache generated successfully.")
    else:
        print("Warning: Manifest cache generation failed, users will do full check on first run.")


if __name__ == "__main__":
    install_deps(platform_tag)
    install_resource()
    install_chores()
    install_agent()
    install_manifest_cache()

    print(f"Install to {install_path} successfully.")
