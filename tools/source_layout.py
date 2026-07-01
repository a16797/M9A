from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceLayout:
    root: Path
    interface_file: Path
    resource_dir: Path
    data_dir: Path
    task_dir: Path
    schema_dir: Path

    @property
    def pipeline_exclude_dirs(self) -> list[Path]:
        return [
            self.resource_dir / "announcement",
        ]


def discover_source_layout(root: str | Path | None = None) -> SourceLayout:
    project_root = Path(root or Path.cwd()).resolve()

    root_interface = project_root / "interface.json"
    root_resource = project_root / "resource"
    root_data = project_root / "data"
    root_tasks = project_root / "tasks"

    if not root_interface.exists() or not root_resource.exists():
        raise FileNotFoundError(
            "Expected create-maa-project style root layout with interface.json and resource/"
        )

    return SourceLayout(
        root=project_root,
        interface_file=root_interface,
        resource_dir=root_resource,
        data_dir=root_data,
        task_dir=root_tasks,
        schema_dir=_schema_dir(project_root),
    )


def _schema_dir(project_root: Path) -> Path:
    deps_schema = project_root / "deps" / "tools"
    if deps_schema.exists():
        return deps_schema
    return project_root / "tools" / "schema"
