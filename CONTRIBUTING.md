# Contributing to M9A

感谢你帮助改进 M9A。请让每次改动保持聚焦，清楚说明用户可见影响，并提供可复现的验证信息，方便维护者 review。

## 开发环境

首次配置建议在仓库根目录运行：

```bash
pnpm install
pnpm install:py
python ./tools/ci/configure.py
```

本项目使用 `uv` 管理 Python 开发环境，虚拟环境位于 `.venv`。

## 本地检查

提交 PR 前请尽量运行：

```bash
pnpm check
```

如果只改了资源或 Project Interface 相关文件，至少运行：

```bash
pnpm check:schema
pnpm check:maa
```

如果只改了 Python：

```bash
pnpm check:py
```

## Pull Request

- 一个 PR 只解决一个明确问题，避免混入无关格式化或重构。
- PR 描述应写清楚需求来源、变更摘要、验证命令和结果。
- 涉及识别、点击、ROI、模板图片、Pipeline 或 GUI 流程时，请提供截图、日志、资源路径或 Actions 链接。
- 新增或修改 Custom Recognition 时，同步维护 `deps/tools/custom.recognition.schema.json`。
- 不要提交本地缓存、构建产物、调试日志、下载的 runtime 文件或临时测试脚本。

推荐使用约定式提交：

```text
feat(scope): short description
fix(scope): short description
docs: short description
```
