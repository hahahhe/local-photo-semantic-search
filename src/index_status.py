import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class IndexStatus:
    exists: bool # 인덱스 파일 존재 여부
    valid: bool # 현재 library와 맞는지
    indexed_count: int # 몇장이 인덱싱 되었는지
    message: str # GUI에 띄울 설명

def check_index_status(library_root: Path, index_dir: Path,) -> IndexStatus:
    """
    검색이 가능한지 판별
    -> meta, index_hnsw, paths 모두 있어야 검색 가능
    """
    meta_path = index_dir / "meta.json"
    index_path = index_dir / "index_hnsw.bin"
    paths_path = index_dir / "paths.jsonl"

    # ---------------------------------
    # 1. 인덱스 파일 존재 여부
    # ---------------------------------

    required_files = [
        meta_path,
        index_path,
        paths_path,
    ]

    if not all(
        path.exists()
        for path in required_files
    ):
        return IndexStatus(
            exists=False,
            valid=False,
            indexed_count=0,
            message="검색 인덱스가 없습니다.",
        )

    # ---------------------------------
    # 2. meta.json 읽기
    # ---------------------------------

    try:
        meta = json.loads(
            meta_path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return IndexStatus(
            exists=True,
            valid=False,
            indexed_count=0,
            message="검색 인덱스 정보를 읽을 수 없습니다.",
        )

    # ---------------------------------
    # 3. Library 경로 비교
    # ---------------------------------

    indexed_library = meta.get(
        "library_root"
    )

    if not indexed_library:

        return IndexStatus(
            exists=True,
            valid=False,
            indexed_count=0,
            message="인덱스에 Library 정보가 없습니다.",
        )

    current_library = str(
        library_root.resolve()
    )

    indexed_library = str(
        Path(indexed_library).resolve()
    )

    if indexed_library != current_library:

        return IndexStatus(
            exists=True,
            valid=False,
            indexed_count=0,
            message="현재 Library와 다른 인덱스입니다.",
        )

    # ---------------------------------
    # 4. 인덱싱 개수
    # ---------------------------------

    indexed_count = meta.get(
        "num_indexed",
        0
    )

    return IndexStatus(
        exists=True,
        valid=True,
        indexed_count=indexed_count,
        message="검색 가능",
    )