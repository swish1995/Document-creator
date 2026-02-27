# Document Creator - 기술 스택

> 📅 마지막 갱신: 2026-02-06
> 🔍 소스: requirements.txt

## 프로덕션 의존성

### UI Framework
| 패키지 | 버전 | 용도 |
|--------|------|------|
| PyQt6 | >=6.6.0 | Qt6 기반 GUI 프레임워크 |
| PyQt6-WebEngine | >=6.6.0 | HTML 렌더링 (템플릿 미리보기) |

### Excel Processing
| 패키지 | 버전 | 용도 |
|--------|------|------|
| openpyxl | >=3.1.0 | Excel 파일 읽기/쓰기 + 내장 수식 평가 |

### Document Generation
| 패키지 | 버전 | 용도 |
|--------|------|------|
| PyMuPDF | >=1.24.0 | PDF 생성 및 조작 |
| Pillow | >=10.0.0 | 이미지 처리 |

### Template Engine
| 패키지 | 버전 | 용도 |
|--------|------|------|
| Jinja2 | >=3.1.0 | HTML 템플릿 렌더링 |

## 개발 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| pytest | >=8.0.0 | 테스트 프레임워크 |
| pytest-qt | >=4.2.0 | PyQt6 테스트 지원 |
| pytest-cov | >=4.1.0 | 테스트 커버리지 |
| ruff | >=0.5.0 | 코드 린팅 및 포매팅 |

## 주요 기술 선택 이유

### PyQt6
- **선택 이유**:
  - 크로스 플랫폼 지원 (Windows, macOS)
  - 풍부한 위젯 라이브러리
  - IMAS와 동일한 UI 스택 유지
- **대안**: PySide6, Tkinter, wxPython

### PyQt6-WebEngine
- **선택 이유**:
  - HTML/CSS 기반 템플릿 렌더링
  - 복잡한 문서 레이아웃 지원
  - Tailwind CSS 등 모던 스타일링 가능
- **대안**: QTextDocument (제한적인 HTML 지원)

### openpyxl + 내장 수식 평가기
- **선택 이유**:
  - 순수 Python 구현 (외부 의존성 없음)
  - Named Range + INDEX/IF/MIN/MAX 수식 지원
  - PyInstaller 완벽 호환 (동적 import 없음)
  - IMAS 출력 파일 호환
- **대안**: formulas (PyInstaller 비호환), xlcalculator (Named Range 미지원)

### PyMuPDF
- **선택 이유**:
  - 빠른 PDF 처리 속도
  - PDF 병합 기능
  - 이미지 추출 및 삽입
- **대안**: ReportLab (복잡한 API), WeasyPrint (무거움)

### Jinja2
- **선택 이유**:
  - Python 표준 템플릿 엔진
  - 풍부한 템플릿 문법
  - Django 템플릿과 유사한 친숙한 문법
- **대안**: Mako, Cheetah

## 시스템 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| 운영체제 | Windows 10, macOS 11 | Windows 11, macOS 12+ |
| Python | 3.9 | 3.11+ |
| RAM | 4GB | 8GB+ |
| 저장공간 | 200MB | 500MB+ |
| 디스플레이 | 1280x720 | 1920x1080+ |

## 빌드 및 배포

### PyInstaller 설정
- 단일 실행 파일 생성
- help/ 디렉토리 번들링
- templates/ 디렉토리 번들링

### 배포 대상
- Windows: .exe 실행 파일
- macOS: .app 번들
