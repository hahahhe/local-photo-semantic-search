## Requirements

## Functional Requirements
- FR1. 지정 폴더에서 이미지 수집(재귀 옵션)
- FR2. 각 이미지를 임베딩(벡터)로 변환
- FR3. 벡터 인덱스를 로컬 파일로 저장/로드
- FR4. 텍스트 쿼리를 임베딩으로 변환
- FR5. 텍스트-이미지 유사도 기반으로 Top-K 결과 반환
- FR6. 결과를 파일 경로로 출력

## None-Functional Requirements
- NFR1. Privacy: 원본 사진은 로컬에만 존재
- NFR2. Reproducibility: 동일한 환경에서 동일한 인덱스의 재생성 가능
- NFR3. Speed: 수천~수만장 수준에서 인덱싱/검색 실사용
- NFR4. Maintainability: 모듈 구조(Embedder/Indexer/Search) 분리

## Constraints
- 개발 환경: Macbook M2, Python, 로컬 실행
- 데이터: 개인 사진
- Zero-shot, 필요 시 후처리(캡션/태그)로 품질 개선

## Acceptance Criteria (MVP)
- AC1. 1,000장 이상 폴더에서 인덱스 생성 완료
- AC2. 문장 검색 결과 Top-10 반환
- AC3. 검색 명령 3초이내 동작