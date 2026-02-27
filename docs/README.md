# Document Creator 문서

## 문서 구조

```
docs/
├── README.md                      # 이 파일
├── architecture/
│   ├── overview.md                # 시스템 아키텍처 개요
│   └── tech-stack.md              # 기술 스택 상세
└── temp_export_analysis.md        # 내보내기 분석 (임시)
```

## 빠른 링크

- [시스템 아키텍처](./architecture/overview.md)
- [기술 스택](./architecture/tech-stack.md)

## 관련 프로젝트

- **IMAS**: 영상 기반 인체공학 자세 분석 도구
  - 동일한 라이센스 시스템 공유
  - Document Creator의 입력 데이터 생성

## 도움말 리소스

앱 내 도움말은 다음 위치에 있습니다:
- `src/resources/help/about.html` - 프로그램 정보
- `src/resources/help/usage.html` - 사용 방법

## 문서 갱신

문서는 코드 변경 시 `/docs-sync` 명령으로 자동 갱신됩니다.
