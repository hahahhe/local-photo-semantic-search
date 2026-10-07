from pathlib import Path

from src.searcher import (
    search,
    SearchConfig
)


cfg = SearchConfig(
    k=3,
    open_top=0
)

results = search(
    out_dir=Path("index_test"),
    query="울타리",
    cfg=cfg
)


for rank, similarity, path in results:
    print(
        rank,
        similarity,
        path
    )