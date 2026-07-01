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

install_path = working_dir / Path("install-mxu")
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"
source_layout = discover_source_layout(working_dir)


def install_deps():
    """安装 MaaFramework 依赖到 maafw 目录（MXU 要求的目录结构）

    MXU 要求将 MaaFramework 的 bin 文件夹内容解压到 maafw 文件夹中。
    参考: https://github.com/MistEO/MXU#依赖文件
    """

    # MaaFramework 运行库 → maafw/
    shutil.copytree(
        working_dir / "deps" / "bin",
        install_path / "maafw",
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
            "*.node",
            "*MaaPiCli*",
        ),
        dirs_exist_ok=True,
    )
    shutil.copytree(
        working_dir / "deps" / "share" / "MaaAgentBinary",
        install_path / "maafw" / "MaaAgentBinary",
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
    interface["mirrorchyan_rid"] = "M9A-MXU"

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)


def install_chores():
    for file in ["README.md", "LICENSE", "CONTACT", "requirements.txt"]:
        shutil.copy2(
            working_dir / file,
            install_path,
        )


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
    install_deps()
    install_resource()
    install_chores()
    install_agent()
    install_manifest_cache()

    print(f"Install MXU to {install_path} successfully.")
