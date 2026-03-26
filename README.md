# local-photo-semantic-search

로컬 사진 폴더를 대상으로 **문장 검색(semantic search)**를 제공하는 프로젝트
이미지마다 임베딩(벡터)을 생성해 로컬 인덱스를 저장하고, 사용자가 입력한 문장을 같은 모델로 임베딩하여 **유사한 사진 Top-K** 반환

- **Privacy-first**
- **Zero-shot**



## What this project solves

일반적인 폴더/파일명 기반의 검색은 "공항에서 찍은 야경"과 같은 **기억 기반 문장**에 대한 검색이 부정확함
본 프로젝트는 사진을 "의미(semantic)"로 인덱싱하여 **어떤 문장이 들어와도 가장 유사한 사진을 찾는 경험ㅁ**을 목표로 함



## Features

- 폴더(재귀) 스캔 -> 이미지 임베딩 생성
- 로컬 벡터 인덱스(HNSW) 저장 및 로드
- 문장 쿼리 -> Top-K 결과 출력
- (추가) 증분 인덱싱(새 파일만 업데이트)
- (추가) 태그/캡션 메타데이터(하이브리드 검색)
- (추가) 테스트 UI(Streamlit)



## Repository Structure
```text
local-photo-semantic-search/
├─ docs/
│  ├─ 00_overview.md
│  ├─ 01_requirements.md
│  ├─ 02_design.md
├─ src/
│  ├─ cli.py
│  ├─ indexer.py
│  ├─ searcher.py
│  ├─ embedders.py
│  └─ utils.py
├─ scripts/
├─ data/
│  ├─ samples/
│  └─ .gitkeep
├─ outputs/
├─ requirements.txt
├─ README.md
└─ LICENSE
```
