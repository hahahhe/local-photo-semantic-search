import json
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def get_settings_path() -> Path:
    app_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)

    settings_dir = Path(app_data_dir)

    settings_dir.mkdir(parents=True, exist_ok=True)

    return settings_dir / "settings.json"


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