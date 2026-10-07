from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

import json
import hnswlib
import numpy as np
from PIL import Image
from tqdm import tqdm

from .embedders import get_device, make_embedder
from .utils import collect_images, cpu_thread

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

def build_index(img_dir: Path, out_dir: Path, cfg: IndexConfig) -> None:
    """
    1. 이미지 경로 수집
    2. 이미지 임베딩 생성
    3. HNSW 추가
    4. index_hnsw / path.json / meta.json
    """
    img_dir = img_dir.expanduser()
    out_dir = out_dir.expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 이미지 경로 수집
    image_paths = collect_images(img_dir, recrusive=cfg.recursive)
    if not image_paths:
        raise RuntimeError(f"이미지 파일 검색 실패: {img_dir}")
    
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

        vecs = embedder.encode_images(batch_imgs) # (8, 0) float32
        if vecs.ndim !=2 or vecs.shape[1] != dim:
            raise RuntimeError(f"임베딩 차원 불일치: got {vecs.shape}, expected (*, {dim})")

        ids = np.arange(next_id, next_id + vecs.shape[0], dtype=np.int64)
        index.add_items(vecs, ids)

        ok_paths.extend(str(p) for p in batch_paths)
        next_id += vecs.shape[0]

        batch_imgs.clear()
        batch_paths.clear()

    # 4. 이미지 로드 -> 배치로 임베딩 -> 인덱스에 추가
    for p in tqdm(image_paths, desc="Indexing images"):
        try:
            with Image.open(p) as im:
                img = im.convert("RGB")
            batch_imgs.append(img)
            batch_paths.append(p)
        except Exception:
            skipped += 1
            continue

        if len(batch_imgs) >= cfg.batch_size:
            flush_batch()

    flush_batch()

    # 5. 저장: index / paths / meta
    index_path = out_dir / "index_hnsw.bin"
    paths_path = out_dir / "paths.jsonl"
    meta_path = out_dir / "meta.json"

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
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n✅ Index build complete")
    print(f"- img_dir      : {img_dir}")
    print(f"- out_dir      : {out_dir}")
    print(f"- indexed      : {len(ok_paths)}")
    print(f"- skipped      : {skipped}")
    print(f"- dim          : {dim}")
    print(f"- index file   : {index_path}")
    print(f"- paths file   : {paths_path}")
    print(f"- meta file    : {meta_path}")