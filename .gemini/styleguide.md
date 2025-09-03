# 팀 코드 컨벤션

💡 이 컨벤션은 절대 규칙이 아니라 협업을 위한 공통 기준입니다. 상황에 따라 예외가 있을 수 있습니다.

---

## 0. 주의사항

- 핵클 a/b테스트 종료 시 코드 정리
- 버전 분기 > 강업 시 코드 정리
- 매직넘버 제거 후 enum화

## 1. 코딩 스타일

- PEP8 기반
- Indentation: 4 space
- Line length: 120
- import 구문은 isort 적용
- pylint 권장
- 예외 처리 시 400, 404 외에는 Custom Exception class 사용
- Request: pydantic/marshmallow schema validate
- Response: pydantic/marshmallow serializer
- 추상화 메소드에는 `*args, **kwargs` 추가

## 2. 네이밍 규칙

- 변수/함수: snake_case
- 클래스: CamelCase
- 상수: UPPER_SNAKE_CASE
- private: `_single_leading_underscore`
- 함수명: create_xxx, update_xxx, delete_xxx
- 핵클 A/B 테스트 키: `{name}_variation`

## 3. 주석 및 문서화

- 서비스/리포지토리 메소드 docstring 필수
- 모델 필드 주석 필수
- 타입힌트 권장

## 4. 아키텍처 구조

- Layered Architecture (service, repository, view 등)

## 5. 폴더 구조

- common/enums.py, common/constants.py
- domain별 services, views, repositories, dtos, enums, serializers

## 6. 테스트 및 품질

- 모든 테스트 100% 성공 보장
- fixture 기반 E2E 테스트 필수
- 단위 테스트는 DI 기반
- sqlite in-memory DB로 독립 실행 가능해야 함

## 7. Refactoring 관리

- 지라 티켓으로 관리
- API Router별 담당자/상태 기록

## 8. Pull Request

- 모든 브랜치 전략에 PR 필수
- 코어: 데일리 스크럼 리뷰 필수
- 최소 1명 approve 필요

## 9. 회의록

- 노션 문서에 기록
