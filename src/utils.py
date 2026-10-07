from typing import Iterable, List, Set
from pathlib import Path
import os

# 확장자
IMG_EXTS: Set[str] = {
    ".jpg", ".jpeg", ".png",
    ".webp", ".bmp", ".tif", ".tiff",
    ".heic", ".heif",
}

# 지정된 폴더에서 이미지 파일 경로 수집
def collect_images(img_dir: Path, recrusive: bool = True) -> List[Path]:
    img_dir = img_dir.expanduser()

    if not img_dir.exists():
        raise FileNotFoundError(f"Not found: {img_dir}")
    if not img_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {img_dir}")

    paths_pre: Iterable[Path] = img_dir.rglob("*") if recrusive else img_dir.glob("*")

    paths: List[Path] = []
    for p in paths_pre:
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMG_EXTS:
            continue
        paths.append(p)
    
    paths.sort()

    return paths

# hnsw 사용할 스레드 함수
def cpu_thread(default: int=4) -> int:
    return os.cpu_count() or default
