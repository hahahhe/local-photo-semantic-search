26.10.09
1. library와 인덱스가 서로 맞는지 확인할 필요
    -> (new) index_status.py
    -> library 경로 비교 (인덱스가 최소한 현재 library를 대상으로 만들어진 인덱스인지 확인) - 인덱싱되지 않은 새로운 사진은 sql연동 후 개발
2. 검색어를 입력할때마다 searcher에서 모델을 로드하는 것 개선
    -> searcher.py 구조 개선
    현재 구조: 검색어 -> meta 읽고 -> siglip 로드 -> hnsw 로드 -> 검색 -> 검색어
    목표 구조: searchengine (siglip, hnsw, paths 로드) -> 검색어 -> 검색 -> 검색어
3. gui- 검색창, 결과창
    Mainwindow
    |
    | 검색창
    | 검색 버튼
    |
    | worker(search)
        |
        | searchengine
4. 검색 -> thread 필수
5. 신규/삭제 사진 관리 (sqlite)