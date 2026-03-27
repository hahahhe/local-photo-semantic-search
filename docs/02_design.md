## Design

## Architecture

```text
[Local Photo Folder]
        |
        v
    (Indexer)
  - scan files
  - load image (PIL)
  - embed image (SigLIP/CLIP)
  - add to vector index (HNSW)
        |
        v
[Local Index Storage]
  - index_hnsw.bin
  - paths.json
  - meta.json
        ^
        |
    (Searcher)
  - embed query text
  - ANN search (cosine)
  - return top-k paths
```

