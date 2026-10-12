from __future__ import annotations

import json
import os
import platform
import subprocess

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import hnswlib

from .embedders import get_device, make_embedder, EmbedderBase

@dataclass
class SearchConfig:
    k: int = 5
    open_top: int = 0
    prompt_template: Optional[str] = None

@dataclass
class SearchResult:
    rank: int
    similarity: float
    path: Path

class SearchEngine:
    def __init__(self, index_dir: Path, prompt_template: Optional[str] = None):
        self.index_dir = index_dir
         # -----------------------
        # 1. meta.json 불러오기
        # -----------------------

        meta_path = (
            self.index_dir
            / "meta.json"
        )

        if not meta_path.exists():
            raise FileNotFoundError(
                f"meta.json을 찾을 수 없습니다: {meta_path}"
            )

        self.meta = json.loads(
            meta_path.read_text(
                encoding="utf-8"
            )
        )

        # -----------------------
        # 2. 모델 정보
        # -----------------------

        backend = self.meta["backend"]
        model = self.meta["model"]

        pretrained = (
            self.meta.get("pretrained")
            or "openai"
        )

        if prompt_template is None:
            prompt_template = (
                self.meta.get(
                    "prompt_template"
                )
            )

        # -----------------------
        # 3. device
        # -----------------------

        self.device = get_device()

        # -----------------------
        # 4. Embedder 한 번만 로드
        # -----------------------

        self.embedder: EmbedderBase = (
            make_embedder(
                backend=backend,
                device=self.device,
                model=model,
                pretrained=pretrained,
                prompt_template=prompt_template,
            )
        )

        # -----------------------
        # 5. paths 로드
        # -----------------------

        self.paths = self._load_paths(
            self.index_dir
            / "paths.jsonl"
        )

        # -----------------------
        # 6. HNSW 로드
        # -----------------------

        self.index = hnswlib.Index(
            space=self.meta["hnsw"]["space"],
            dim=self.meta["dim"],
        )

        self.index.load_index(
            str(
                self.index_dir
                / "index_hnsw.bin"
            ),
            max_elements=self.meta[
                "max_elements"
            ],
        )

        self.index.set_ef(
            self.meta["hnsw"][
                "ef_search"
            ]
        )

    def _load_paths(self, paths_file: Path,) -> List[Path]:

        paths: List[Path] = []

        with paths_file.open(
            "r",
            encoding="utf-8",
        ) as f:

            for line in f:

                data = json.loads(line)

                paths.append(
                    Path(data["path"])
                )

        return paths


    def search(self, query: str, k: int = 10,) -> List[SearchResult]:

        if not query.strip():
            return []

        if not self.paths:
            return []

        # -----------------------
        # 텍스트 → 임베딩
        # -----------------------

        query_vector = (
            self.embedder.encode_texts(
                [query]
            )
        )

        # -----------------------
        # HNSW 검색
        # -----------------------

        labels, distances = (
            self.index.knn_query(
                query_vector,
                k=min(
                    k,
                    len(self.paths)
                ),
            )
        )

        # -----------------------
        # 결과 정리
        # -----------------------

        results: List[SearchResult] = []

        for rank, (
            image_id,
            distance,
        ) in enumerate(
            zip(
                labels[0],
                distances[0],
            ),
            start=1,
        ):

            similarity = (
                1.0
                - float(distance)
            )

            results.append(
                SearchResult(
                    rank=rank,
                    similarity=similarity,
                    path=self.paths[
                        int(image_id)
                    ],
                )
            )

        return results



'''
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
'''