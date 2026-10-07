from pathlib import Path
from src.indexer import build_index, IndexConfig

cfg = IndexConfig(
    backend="siglip",
    model="google/siglip-base-patch16-224",
    recursive=True,
    batch_size=8,
)

build_index(Path("data/samples"), Path("./index_test"), cfg)