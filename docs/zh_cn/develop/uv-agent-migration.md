---
order: 12
icon: mdi:tools
---

# uv 与 Agent 运行时改造方案

本文档记录 M9A 开发环境迁移到 `uv` 后的运行边界和维护规则。

## 结论

M9A 可以改成 `uv` 启动开发环境，但不应把发布包运行时绑定到 `uv`。推荐边界是：

- 开发态使用 `uv sync` / `uv run` 管理 Python 环境与工具。
- 源码态 `assets/interface.json` 可改为通过 `uv run` 启动 Agent。
- 发布包继续使用内置 Python 或系统 Python 启动 Agent，不要求用户安装 `uv`。
- `requirements.txt` 保留为发布包依赖清单；`pyproject.toml` 与 `uv.lock` 作为开发和 CI 的锁定入口。
- 打包脚本必须继续重写发布包内的 `agent.child_exec` 和 `agent.child_args`，避免把源码态的 `uv` 命令带进 release。

## 当前事实

M9A 当前的源码态 Agent 配置在 `assets/interface.json` 中：

```json
"agent": {
    "child_exec": "python",
    "child_args": [
        "-u",
        "./../agent/main.py"
    ]
}
```

发布包打包脚本已经会改写该配置：

- Windows: `./python/python.exe`
- macOS: `./python/bin/python3`
- Linux: `python3`
- 参数统一为 `["-u", "./agent/main.py"]`

因此，迁移时可以把源码态改为 `uv run`，但必须保留打包脚本的 release 改写逻辑。

当前 Python 版本约束保持一致：

- `pyproject.toml` 中 ruff/pyright 目标为 Python 3.12。
- CI 使用 Python 3.12。
- `tools/ci/setup_embed_python.py` 的嵌入式 Python 版本为 3.12.10。

本方案不包含升级到 Python 3.13。

## 参考项目边界

[Windsland52/create-maa-project](https://github.com/Windsland52/create-maa-project) 的 Agent 模板采用了较清晰的双态设计：

- 开发态默认命令为 `uv run python agent/bootstrap.py`。
- `pyproject.toml` / `uv.lock` 管理开发环境。
- 发布构建时将 Agent 启动命令改写为平台 Python。
- 运行时同步仍保留 `requirements.txt`，并用 pip/uv pip 把依赖安装进目标 Python。
- `bootstrap.py` 使用 requirements sha256 marker 避免每次启动重复安装依赖。

[Windsland52/ArknightsAutoOperator](https://github.com/Windsland52/ArknightsAutoOperator) 是 Win32-only 项目，源码态直接在 `interface.json` 中使用：

```json
"agent": {
    "child_exec": "uv",
    "child_args": [
        "run",
        "python",
        "-u",
        "-m",
        "custom.agent"
    ]
}
```

它证明 Win-only 开发项目可以直接让 MaaFramework 启动 `uv run`。但 M9A 有正式发布包、内置 Python、多平台依赖和用户侧免配置要求，因此只能参考它的开发态写法，不能照搬为发布态方案。

## 目标形态

### Python 项目元数据

将现有 `pyproject.toml` 从仅包含工具配置，扩展为完整项目元数据：

```toml
[project]
name = "m9a"
requires-python = ">=3.12,<3.13"
dependencies = [
    "maafw==v5.10.4",
    "loguru",
    "pillow",
    "pytz",
    "requests",
]

[dependency-groups]
dev = [
    "black",
    "ruff",
    "pytest",
    "pyright",
    "jsonschema==4.26.0",
    "referencing==0.37.0",
]

[tool.uv]
package = false
```

同时新增：

- `.python-version`：固定为 `3.12`
- `uv.lock`：由 `uv lock` 生成并提交

### 依赖清单职责

保留 `requirements.txt`，它仍然是发布包和 bootstrap 的运行时依赖契约。迁移后职责如下：

| 文件                   | 作用                                                         |
| ---------------------- | ------------------------------------------------------------ |
| `pyproject.toml`       | 开发环境、工具配置、依赖声明                                 |
| `uv.lock`              | 开发与 CI 的可复现锁定                                       |
| `requirements.txt`     | 发布包依赖清单、bootstrap 安装入口                           |
| `requirements-dev.txt` | 可在第一阶段保留，等 CI 全部切到 uv 后再删除或降级为兼容入口 |

`[tool.uv] package = false` 表示 M9A 不在 `uv sync` 时安装自身包，只把仓库当作运行型项目使用。这能避免为了 uv 迁移而引入不必要的 wheel 构建配置。

### 源码态 Agent 启动

源码态可改为：

```json
"agent": {
    "child_exec": "uv",
    "child_args": [
        "run",
        "--frozen",
        "python",
        "-u",
        "./../agent/main.py"
    ]
}
```

这里的 `--frozen` 用来保证启动时不会隐式改动 `uv.lock`。如果开发体验中发现首次启动不够友好，可以只在 CI 和脚本中使用 `--frozen`，源码态 Maa 启动保留无 `--frozen`，但需要在 PR 中明确取舍。

### 发布包 Agent 启动

发布包仍应由打包脚本重写为平台 Python：

```json
"agent": {
    "child_exec": "./python/python.exe",
    "child_args": [
        "-u",
        "./agent/main.py"
    ]
}
```

macOS 与 Linux 分别继续使用 `./python/bin/python3` 和 `python3`。发布包内不应包含 `.venv`、`uv.lock`、`.python-version` 作为运行时依赖，也不应要求用户安装 `uv`。

## 实施状态

### 第一阶段：开发环境 uv 化

状态：已实施。开发者可以用 `uv sync` 和 `uv run` 完成当前 Python 检查。

改动范围：

- 新增 `[project]`、`[dependency-groups] dev`、`.python-version`、`uv.lock`。
- 保留 `requirements.txt` 和 `requirements-dev.txt`。
- 将 `package.json` 的 Python 脚本切到 `uv run --frozen`。Windows 下 pnpm 直接包装 `uv.exe` 可能残留进程，因此脚本通过 `tools/run-uv.mjs` 调用 uv：

```json
{
    "install:py": "node tools/run-uv.mjs sync --frozen --group dev",
    "format:py": "node tools/run-uv.mjs run --frozen black .",
    "lint:py": "node tools/run-uv.mjs run --frozen ruff check .",
    "typecheck": "node tools/run-uv.mjs run --frozen pyright",
    "test": "node tools/run-uv.mjs run --frozen pytest"
}
```

- GitHub Actions 使用 `astral-sh/setup-uv` 的完整版本标签，并继续安装 Python 3.12。

验收：

```bash
uv sync --frozen --group dev
pnpm lint:py
pnpm typecheck
pnpm test
python tools/validate_schema.py --schema-dir deps/tools --resource-dirs assets/resource --exclude-dirs assets/resource/announcement assets/resource/data assets/resource/tasks --interface-files assets/interface.json --task-dirs assets/resource/tasks
```

### 第二阶段：源码态 Agent 改为 uv 启动

状态：已实施。开发时由 MaaFramework 直接通过 `uv run` 启动 Agent。

改动范围：

- 修改源码态 `assets/interface.json` 的 `agent` 字段。
- 保持 `tools/ci/install.py`、`tools/ci/install_cli.py`、`tools/ci/install_mxu.py` 的发布包改写逻辑。
- 增加 release 改写 smoke check，确认打包产物中没有 `uv` 启动命令。

验收：

```bash
python tools/ci/install.py v0.0.0 win-x64
python - <<'PY'
import json

with open("install/interface.json", encoding="utf-8") as file:
    print(json.load(file)["agent"])
PY
```

Windows PowerShell 可用：

```powershell
@'
import json

with open("install/interface.json", encoding="utf-8") as file:
    print(json.load(file)["agent"])
'@ | python -
```

预期结果：输出的 `child_exec` 是发布包 Python，而不是 `uv`。

### 第三阶段：优化 bootstrap

状态：已实施。Agent 会根据 `requirements.txt` 的 sha256 marker 跳过重复 pip 安装。

改动范围：

- 计算 `requirements.txt` 的 sha256。
- 安装成功后写入 marker，例如 `debug/.m9a-requirements.sha256` 或 venv 内 marker。
- 下次启动时，如果 marker 匹配且 `maafw` 已安装，跳过安装。
- 保留当前本地 whl 优先、镜像源 fallback 的安装顺序。

验收：

- 首次启动会安装依赖并写入 marker。
- 第二次启动不会重复安装依赖。
- 修改 `requirements.txt` 后会重新安装。
- 发布包和开发态行为一致。

## 不做的事

- 不把 `download_deps.py` 改成 `uv`，它需要处理跨平台 wheel 下载，当前 pip 参数更明确。
- 不删除 `requirements.txt`。
- 不在第一轮迁移中删除 `requirements-dev.txt`。
- 不升级 Python 3.13。
- 不引入 `maa-project.json` / `maa-project.lock.json`。
- 不改 Pipeline 业务逻辑、资源路径或任务入口。

## 风险与应对

| 风险                                             | 应对                                                                                                  |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| 用户运行发布包时没有 `uv`                        | 发布包 `interface.json` 必须被重写为平台 Python                                                       |
| CI 与本地 Python 版本漂移                        | `.python-version`、CI Python 3.12、pyright/ruff 目标统一为 3.12                                       |
| `uv.lock` 与 `requirements.txt` 漂移             | 迁移 PR 中明确双清单职责；运行时依赖变更必须同时更新两处                                              |
| 首次 Maa 启动时 `uv run --frozen` 因缺少环境失败 | 文档要求先执行 `uv sync --frozen --group dev`；必要时源码态不加 `--frozen`                            |
| 打包产物误带开发文件                             | release smoke check 中检查 `.venv`、`.python-version`、`uv.lock`、`package.json` 等不进入运行时根目录 |

## 参考链接

- [MaaFramework Project Interface V2](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/en_us/3.3-ProjectInterfaceV2.md)
- [create-maa-project Agent pyproject 模板](https://github.com/Windsland52/create-maa-project/blob/d1597d1969adc117421e7cc3c78059a581b62d5d/templates/agent/pyproject.toml)
- [create-maa-project Agent bootstrap 模板](https://github.com/Windsland52/create-maa-project/blob/d1597d1969adc117421e7cc3c78059a581b62d5d/templates/agent/agent/bootstrap.py)
- [create-maa-project release 构建脚本模板](https://github.com/Windsland52/create-maa-project/blob/d1597d1969adc117421e7cc3c78059a581b62d5d/templates/addons/github/tools/build-release.mjs)
- [create-maa-project runtime 同步脚本模板](https://github.com/Windsland52/create-maa-project/blob/d1597d1969adc117421e7cc3c78059a581b62d5d/templates/addons/github/tools/sync-runtime.mjs)
- [ArknightsAutoOperator interface.json](https://github.com/Windsland52/ArknightsAutoOperator/blob/9fa29f0626dd5e89f3ee2bf5f05bc22abda42eca/interface.json)
