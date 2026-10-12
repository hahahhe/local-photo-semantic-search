import json
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def get_app_data_dir() -> Path:
    app_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)

    path = Path(app_data_dir)

    path.mkdir(parents=True, exist_ok=True)

    return path


def get_settings_path() -> Path:

    return (get_app_data_dir() / "settings.json")


def get_index_dir() -> Path:

    index_dir = (get_app_data_dir() / "index")

    index_dir.mkdir(parents=True, exist_ok=True)

    return index_dir


def save_library_root(library_root: Path) -> None:
    settings_path = get_settings_path()

    data = {"library_root": str(library_root)}

    settings_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def load_library_root() -> Path | None:
    settings_path = get_settings_path()

    if not settings_path.exists():
        return None

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))

        library_root = data.get("library_root")

        if not library_root:
            return None

        return Path(library_root)

    except (json.JSONDecodeError, OSError):
        return None

