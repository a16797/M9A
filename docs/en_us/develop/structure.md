---
order: 2
icon: hugeicons:structure-01
---
# Project Structure

```bash
.
|-- .github/                      # GitHub configuration
|   |-- ISSUE_TEMPLATE/           # Issue templates
|   |-- workflows/                # GitHub Actions workflows
|   `-- cliff.toml                # Changelog generation configuration
|-- .vscode/                      # VSCode editor configuration
|   |-- extensions.json           # Recommended extensions list
|   `-- settings.json             # Project settings
|-- agent/                        # Agent module
|   |-- custom/                   # Custom recognition and tasks
|   |-- utils/                    # Utility functions
|   |-- __init__.py               # Module initialization
|   `-- main.py                   # Main entry point
|-- MaaCommonAssets/              # MAA common resources (submodule)
|-- data/                         # Runtime data for activity, combat, and roguelike tasks
|-- resource/                     # Pipeline, image, model, and other project resources
|-- tasks/                        # MaaFramework task definitions
|-- deps/                         # MaaFramework dependency libraries, where schemas are stored
|-- docs/                         # Documentation directory
|   |-- en_us/                    # English documentation
|   |-- zh_cn/                    # Chinese documentation
|   `-- .markdownlint.yaml        # Markdown linting configuration
|-- tools/                        # Tool scripts directory
|   |-- activity_data/            # Activity data processing tools
|   |-- ci/                       # Continuous integration scripts
|   |-- image/                    # Drop item image processing tools
|   |-- optimize_templates/        # Template image optimization tools
|   |-- registry/                 # PC registry related tools
|   |-- migrate_pipeline_v5.py    # Pipeline v5 migration script
|   |-- minify_json.py            # JSON minification tool
|   `-- V1_upgrade.py             # Pipeline version upgrade script
|-- .editorconfig                 # Editor configuration
|-- .gitattributes                # Git attributes configuration
|-- .gitignore                    # Git ignore configuration
|-- .gitmodules                   # Git submodules configuration
|-- .node-version                 # Node.js version configuration
|-- .npmrc                        # Project-level pnpm/npm configuration
|-- .prettierignore               # Prettier ignore rules
|-- .prettierrc.mjs               # Code formatting configuration
|-- .python-version               # Python version configuration
|-- CONTACT                       # Contact information
|-- interface.json                # MaaFramework standardized project structure declaration
|-- LICENSE                       # License file
|-- README.md                     # Chinese documentation
|-- README_en.md                  # English documentation
|-- maatools.config.mts           # maa-tools check configuration
|-- package.json                  # Node.js project configuration
|-- pnpm-lock.yaml                # pnpm dependency lock file
|-- pnpm-workspace.yaml           # pnpm workspace configuration
|-- pyproject.toml                # Python project and tool configuration
|-- uv.lock                       # uv dependency lock file
`-- requirements.txt              # Python dependency list
```
