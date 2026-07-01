# M9A 模板化重构迁移方案

本文记录本轮将 M9A 迁移到 `create-maa-project` 标准 Python Agent 项目骨架的方案和验收点。目标是先生成一份全 add-ons 空白模板，再把 M9A 的真实资源、任务、Python Agent、CI 和发布流程迁移到对应位置，而不是继续在旧目录上叠补丁。

## 参考基线

- 模板来源：`Windsland52/create-maa-project`
- 模板 commit：`d1597d1969adc117421e7cc3c78059a581b62d5d`
- 本地对照模板：`D:\02code\_template_refs\m9a-full-agent-addons`
- 模板类型：`agent`
- add-ons：`dev-tools`、`github`、`resource-pack extra`、`git-cliff`、`auto-format`、`optimize-images`、`community`、`dependabot`、`schema-sync`
- 参考类型配置：`Windsland52/ArknightsAutoOperator` 的 strict pyright 策略

## 目标结构

```text
M9A/
├── interface.json
├── logo.png
├── MaaCommonAssets/
├── agent/
├── config/
├── data/
├── resource/
├── tasks/
├── tools/
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

关键变化：

- `interface.json`、`logo.png`、`resource/`、`tasks/`、`data/` 全部位于项目根目录。
- `MaaCommonAssets` 子模块移动到根目录，OCR 模型配置脚本从根目录读取。
- 源码态 `interface.json` 的 `agent` 字段使用模板同款数组形态：`uv run python agent/bootstrap.py`。
- 发布包仍由打包脚本重写为平台 Python，release artifact 不要求用户安装 `uv`。
- 不引入 `maa-project.json`、`maa-project.lock.json` 或 `maa-project..lock.json`，暂不通过脚手架托管后续更新。

## 迁移决策

1. Python Agent 入口对齐模板，但保留 M9A 自有 bootstrap 流程：热更新、manifest cache、依赖 marker、本地 wheels 优先、日志和 PI 环境快照继续保留。
2. Windows/macOS 发布包在 CI 中把 `requirements.txt` 安装进内置 Python；用户启动发布包时检测到内置 Python 后跳过运行时 pip 安装。
3. `pyproject.toml` 将 `typeCheckingMode` 切到 `strict`，并显式关闭当前历史代码和 maafw 第三方库缺存根造成的大面积噪声。后续可按规则逐项收紧。
4. M9A 仓库只负责 MFAA 和 MXU 包。CLI 包迁到 `MAA1999/m9a-cli` 独立仓库生成；M9A 发版后通过 `repository_dispatch` 通知该仓库同步打包发版。
5. `tools/source_layout.py` 只接受模板根布局，不再 fallback 到旧 `assets/` 布局，避免迁移错误被兼容层吞掉。

## CI 与发布

M9A 本仓库：

- `install.yml` 监听 `interface.json`、`logo.png`、`MaaCommonAssets/**`、`resource/**`、`data/**`、`tasks/**`、Python 依赖和脚本变化。
- Windows/macOS job 在 `Download drop_core module` 后安装 Python 依赖到 `install/python`。
- MFAA 包由 `tools/ci/install.py` 生成。
- MXU 包由 `tools/ci/install_mxu.py` 生成。
- release job 打包 MFAA/MXU artifacts，并向 `MAA1999/m9a-cli` 发送 `m9a-release` dispatch。

`MAA1999/m9a-cli`：

- 仓库地址：`https://github.com/MAA1999/m9a-cli`
- 以 `MAA1999/M9A` 作为 `M9A` 子仓库。
- 接收 `m9a-release` dispatch。
- 使用 payload 中的 `tag`、`source_repo`、`source_ref`、`source_sha`、`source_run_id`、`maa_framework_version` 与 M9A 同步生成 CLI release。

## 验收清单

- `npm run check`
- `node tools/run-uv.mjs run --frozen python tools/validate_schema.py`
- `npm exec -- @nekosu/maa-tools check`
- `python tools/ci/install.py v0.0.0-ci.template-test win-x64`
- `python tools/ci/install_mxu.py v0.0.0-ci.template-test`
- `python D:\02code\m9a-cli\tools\ci\install_cli.py --source-dir D:\02code\M9A --deps-dir D:\02code\M9A\deps --output-dir D:\02code\m9a-cli\install-cli-smoke --version v0.0.0-local --platform win32`
- 检查 release 包内 `interface.json` 的 `agent.child_exec` 不为 `uv`
- 检查仓库根目录不存在 `maa-project.json`、`maa-project.lock.json`、`maa-project..lock.json`
- 检查运行时代码不再引用旧 `assets/interface.json` 或 `assets/resource`

## 对抗式审查问题

- 源码态是否还依赖旧 `assets` 层级？
- `tasks/` 和 `data/` 移到根目录后，Custom 与 CI 是否都读新路径？
- 发布包是否误带 `uv`、`.venv`、`node_modules` 或开发态启动命令？
- Windows/macOS 内置 Python 是否已在 CI 阶段安装运行依赖？
- MXU 与 MFAA 是否都包含 `agent/bootstrap.py`、`resource/`、`tasks/`、`data/`？
- CLI 是否已从 M9A release artifacts 中移除，并改由 `m9a-cli` 仓库接收 dispatch？
