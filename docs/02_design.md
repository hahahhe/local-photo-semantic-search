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

### Structure
utils.py
|
| collect_images()
|
사진 목록
|

embedders.py
|
| 이미지 -> vector
| 텍스트 -> vector
|
임베딩 (dim 768)
|

indexer.py
|
| 이미지 vector 저장
|
HNSW index
|

searcher.py
|
| query vector
| nearest neighbor search
|
검색 결과



### GUI Architecture
프로그램 실행
|
사진 폴더 선택
|
폴더 선택 창
|
사진 분석 / 인덱싱 - 스레드 필수
|
검색창 활성화
|
"query"
|
검색 결과(사진 썸네일)
|
사진 열기