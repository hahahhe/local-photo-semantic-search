from __future__ import annotations

import json
import os
import platform
import subprocess

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import hnswlib

from .embedders import get_device, make_embedder

@dataclass
class SearchConfig:
    k: int = 5
    open_top: int = 0
    prompt_template: Optional[str] = None

def load_paths(paths_file: Path) -> List[str]:
    """
    paths.jsonl 참고해서 이미지 경로 리스트로 변환
    """

    paths: List[str] = []
    with paths_file.open("r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            paths.append(data["path"])
    return paths

def open_images(path: str) -> None:
    """
    운영체제의 기본 이미지 프로그램으로 파일 오픈
    """

    system = platform.system()

    if system == "Windows":
        os.startfile(path)

    elif system == "Darwin":
        subprocess.run(["open", path], check=False)

    else:
        subprocess.run(["xdg-open", path], check=False)

def search(out_dir: Path, query: str, cfg: SearchConfig) -> List[Tuple[int, float, str]]:
    # 1. meta 읽기
    meta_path = out_dir / "meta.json"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    # 2. 인덱싱 모델 정보 가져오기
    backend = meta["backend"]
    model = meta["model"]
    pretrained = meta.get("pretrained") or "openai"

    prompt_template = (
        cfg.prompt_template
        if cfg.prompt_template is not None
        else meta.get("prompt_template")
    )

    # 3. 임베딩 모델 준비
    device = get_device()

    embedder = make_embedder(
        backend=backend,
        device=device,
        model=model,
        pretrained=pretrained,
        prompt_template=prompt_template,
    )

    # 4. ID로 이미지 경로 목록 불러오기
    paths = load_paths(out_dir / "paths.jsonl")

    # 5. HNSW 인덱스 생성
    index = hnswlib.Index(
        space="cosine",
        dim=meta["dim"]
    )

    # 6. 인덱스 불러오기
    index.load_index(
        str(out_dir / "index_hnsw.bin"),
        max_elements=meta["max_elements"]
    )

    # 검색 범위
    index.set_ef(meta["hnsw"]["ef_search"])

    # 7. 검색어 -> 벡터
    query_vector = embedder.encode_texts([query])

    # 8. knn 이미지 검색
    labels, distances = index.knn_query(
        query_vector,
        k=min(cfg.k, len(paths))
    )

    # 9. 결과
    results: List[Tuple[int, float, str]] = []

    for rank, (image_id, distances) in enumerate(zip(labels[0], distances[0]), start=1):
        similarity = 1.0 - float(distances)

        image_path = paths[image_id]

        results.append((rank, similarity, image_path))

    # 10. 상위 이미지 오픈
    for _, _, image_path in results[:cfg.open_top]:
        open_images(image_path)

    return results