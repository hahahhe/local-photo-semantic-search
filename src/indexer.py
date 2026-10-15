from dataclasses import dataclass
from typing import Optional, List, Callable
from pathlib import Path

import json
import hnswlib
import numpy as np
from PIL import Image
from tqdm import tqdm

from .embedders import get_device, make_embedder
from .utils import collect_images, cpu_thread
from . import image_io

@dataclass
class IndexConfig:
    # 모델 선택
    backend: str = "siglip"
    model: str = "google/siglip2-so400m-patch16-256"
    prompt_template: Optional[str] = None

    # 입력 폴더 서치/배치
    recursive: bool = True
    batch_size: int = 16

    # HNSW 파라미터 설정
    ef_construction: int = 200 # 초기 탐색 크기
    M: int = 16 # 노드의 최대 연결선
    ef_search: int = 64 # 검색시 탐색 크기

class IndexCancelled(Exception):
    """인덱싱 취소 시"""
    pass

@dataclass(frozen=True)
class IndexBuildResult:
    indexed: int
    skipped: int
    dim: int

def build_index(
        img_dir: Path, 
        out_dir: Path, 
        cfg: IndexConfig, 
        progress_callback: Callable[[int, int], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None, ) -> IndexBuildResult:
    """
    1. 이미지 경로 수집
    2. 이미지 임베딩 생성
    3. HNSW 추가
    4. index_hnsw / path.json / meta.json
    """

    skip_log_path = out_dir / "skipped_files.jsonl"
    skip_log_path.write_text(
        "",
        encoding="utf-8"
    )

    def log_skipped_file(
        path: Path,
        error: Exception
    ) -> None:

        try:
            file_size = path.stat().st_size
        except OSError:
            file_size = None

        try:
            with path.open("rb") as f:
                header = f.read(16).hex(" ")
        except OSError:
            header = None

        record = {
            "path": str(path),
            "error_type": type(error).__name__,
            "reason": str(error),
        }

        with skip_log_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

    def check_cancelled() -> None:
        if should_cancel is not None and should_cancel():
            raise IndexCancelled()
    def notify_status(message: str) -> None:
        if status_callback is not None:
            status_callback(message)
    def notify_progress(current: int, total: int) -> None:
        if progress_callback is not None:
            progress_callback(current, total)

    img_dir = img_dir.expanduser()
    out_dir = out_dir.expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    notify_status("사진 목록 확인중..")

    # 1. 이미지 경로 수집
    image_paths = collect_images(img_dir, recrusive=cfg.recursive)
    if not image_paths:
        raise RuntimeError(f"이미지 파일 검색 실패: {img_dir}")

    total = len(image_paths)
    check_cancelled()

    notify_status("AI 모델 불러오는 중..")
    
    # 2. 이미지 임베딩 생성
    device = get_device()
    embedder = make_embedder(
        backend=cfg.backend,
        device=device,
        model=cfg.model,
        prompt_template=cfg.prompt_template,
    )
    dim = embedder.dim

    # 3. HNSW 인덱스 초기화
    index = hnswlib.Index(space="cosine", dim=dim)
    index.init_index(
        max_elements=len(image_paths),
        ef_construction=cfg.ef_construction,
        M=cfg.M,
    )
    index.set_ef(cfg.ef_search)
    index.set_num_threads(cpu_thread())

    ok_paths: List[str] = []
    batch_imgs: List[Image.Image] = []
    batch_paths: List[Path] = []

    next_id = 0
    skipped = 0

    def flush_batch() -> None:
        nonlocal next_id, batch_imgs, batch_paths, ok_paths
        if not batch_imgs:
            return

        check_cancelled()
        vecs = embedder.encode_images(batch_imgs) # (8, 0) float32
        check_cancelled()

        if vecs.ndim !=2 or vecs.shape[1] != dim:
            raise RuntimeError(f"임베딩 차원 불일치: got {vecs.shape}, expected (*, {dim})")

        ids = np.arange(next_id, next_id + vecs.shape[0], dtype=np.int64)
        index.add_items(vecs, ids)

        ok_paths.extend(str(p) for p in batch_paths)
        next_id += vecs.shape[0]

        notify_progress(next_id + skipped, total)

        batch_imgs.clear()
        batch_paths.clear()

    notify_status("사진 분석중..")

    # 4. 이미지 로드 -> 배치로 임베딩 -> 인덱스에 추가
    for p in tqdm(image_paths, desc="Indexing images"):
        check_cancelled()
        try:
            with Image.open(p) as im:
                img = im.convert("RGB")

            batch_imgs.append(img)
            batch_paths.append(p)

        except Exception as e:
            skipped += 1

            log_skipped_file(p, e)

            notify_progress(next_id + skipped, total)
            continue

        if len(batch_imgs) >= cfg.batch_size:
            flush_batch()

    flush_batch()

    check_cancelled()

    # 5. 저장: index / paths / meta
    index_path = out_dir / "index_hnsw.bin"
    paths_path = out_dir / "paths.jsonl"
    meta_path = out_dir / "meta.json"

    check_cancelled()

    notify_status("검색 인덱스 저장중..")

    index.save_index(str(index_path))

    with paths_path.open("w", encoding="utf-8") as f:
        for s in ok_paths:
            f.write(json.dumps({"path": s}, ensure_ascii=False) + "\n")

    meta = {
        "backend": cfg.backend,
        "model": cfg.model,
        "pretrained": cfg.pretrained if cfg.backend == "clip" else None,
        "prompt_template": cfg.prompt_template if cfg.backend == "siglip" else None,
        "device": str(device),
        "dim": dim,
        "max_elements": len(image_paths),
        "num_indexed": len(ok_paths),
        "skipped": skipped,
        "hnsw": {
            "space": "cosine",
            "ef_construction": cfg.ef_construction,
            "M": cfg.M,
            "ef_search": cfg.ef_search,
        },
        "library_root": str(img_dir.resolve()),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    notify_progress(total, total)

    notify_status("사진 분석 완료")

    return IndexBuildResult(
        indexed=len(ok_paths),
        skipped=skipped,
        dim=dim
    )

    '''
    print("\n✅ Index build complete")
    print(f"- img_dir      : {img_dir}")
    print(f"- out_dir      : {out_dir}")
    print(f"- indexed      : {len(ok_paths)}")
    print(f"- skipped      : {skipped}")
    print(f"- dim          : {dim}")
    print(f"- index file   : {index_path}")
    print(f"- paths file   : {paths_path}")
    print(f"- meta file    : {meta_path}")
    '''