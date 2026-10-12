from PIL import Image
import os
import platform
import subprocess
from pathlib import Path

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()

except ImportError:
    pass

def open_image(path: Path) -> None:

    system = platform.system()

    if system == "Windows":

        os.startfile(str(path))

    elif system == "Darwin":

        subprocess.run(
            ["open", str(path)],
            check=False,
        )

    else:

        subprocess.run(
            ["xdg-open", str(path)],
            check=False,
        )