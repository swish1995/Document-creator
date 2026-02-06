# Document Creator - 시스템 아키텍처

> 📅 마지막 갱신: 2026-02-06
> 🔍 소스: 코드베이스 분석

## 개요

Document Creator는 Skeleton Analyzer에서 분석한 인체공학 평가 결과를 바탕으로 전문적인 안전문서를 자동으로 생성하는 PyQt6 기반 데스크톱 애플리케이션입니다.

## 기술 스택

### Core
| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.9+ | 런타임 |
| PyQt6 | 6.6.0+ | UI 프레임워크 |
| PyQt6-WebEngine | 6.6.0+ | HTML 템플릿 렌더링 |

### Data Processing
| 기술 | 버전 | 용도 |
|------|------|------|
| openpyxl | 3.1.0+ | Excel 파일 읽기/쓰기 |
| formulas | 1.3.0+ | 엑셀 수식 평가 |
| Jinja2 | 3.1.0+ | HTML 템플릿 엔진 |

### Document Generation
| 기술 | 버전 | 용도 |
|------|------|------|
| PyMuPDF | 1.24.0+ | PDF 생성 및 처리 |
| Pillow | 10.0.0+ | 이미지 처리 |

### Development
| 기술 | 버전 | 용도 |
|------|------|------|
| pytest | 8.0.0+ | 테스트 프레임워크 |
| pytest-qt | 4.2.0+ | PyQt6 테스트 지원 |
| ruff | 0.5.0+ | 코드 린팅 |

## 아키텍처 패턴

### 레이어 구조

```
┌─────────────────────────────────────────────────────┐
│                    UI Layer (src/ui/)               │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │ MainWindow  │ │ ExcelViewer │ │TemplatePanel │  │
│  └─────────────┘ └─────────────┘ └──────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │ MainToolbar │ │ HelpDialog  │ │ ExportDialog │  │
│  └─────────────┘ └─────────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────┤
│                  Core Layer (src/core/)             │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │ExcelLoader  │ │TemplateManager│ │   Mapper    │  │
│  └─────────────┘ └─────────────┘ └──────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │ExportManager│ │DocGenerator │ │PDFConverter  │  │
│  └─────────────┘ └─────────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────┤
│                License Layer (src/license/)         │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │LicenseManager│ │LicenseValidator│ │HardwareID │  │
│  └─────────────┘ └─────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 디렉토리 구조

```
document-creator/
├── main.py                    # 애플리케이션 엔트리 포인트
├── requirements.txt           # Python 의존성
├── src/
│   ├── __init__.py
│   ├── core/                  # 비즈니스 로직
│   │   ├── document_generator.py  # 문서 생성
│   │   ├── excel_loader.py        # Excel 파일 로드
│   │   ├── export_manager.py      # 내보내기 관리
│   │   ├── logger.py              # 로깅
│   │   ├── mapper.py              # 필드 매핑
│   │   ├── pdf_converter.py       # PDF 변환
│   │   ├── template_manager.py    # 템플릿 관리
│   │   └── template_storage.py    # 템플릿 저장소
│   ├── license/               # 라이센스 시스템
│   │   ├── hardware_id.py         # 하드웨어 ID 생성
│   │   ├── license_dialog.py      # 라이센스 등록 UI
│   │   ├── license_manager.py     # 라이센스 상태 관리
│   │   └── license_validator.py   # 라이센스 키 검증
│   ├── ui/                    # 사용자 인터페이스
│   │   ├── main_window.py         # 메인 윈도우
│   │   ├── main_toolbar.py        # 툴바
│   │   ├── excel_viewer.py        # Excel 데이터 뷰어
│   │   ├── template_panel.py      # 템플릿 미리보기 패널
│   │   ├── export_dialog.py       # 내보내기 다이얼로그
│   │   ├── help_dialog.py         # 도움말 다이얼로그
│   │   └── template_editor/       # 템플릿 편집기
│   │       ├── editor_widget.py
│   │       └── ...
│   ├── resources/             # 리소스 파일
│   │   └── help/                  # 도움말 HTML
│   │       ├── about.html
│   │       └── usage.html
│   └── utils/                 # 유틸리티
├── templates/                 # 문서 템플릿
│   ├── _builtin/                  # 내장 템플릿
│   │   ├── rula/
│   │   ├── reba/
│   │   ├── owas/
│   │   ├── nle/
│   │   └── si/
│   └── sample/                    # 샘플 템플릿
├── tests/                     # 테스트 코드
├── docs/                      # 문서
└── worked/                    # 작업 임시 디렉토리
```

## 주요 컴포넌트

### MainWindow (`src/ui/main_window.py`)
- **역할**: 애플리케이션의 메인 윈도우
- **기능**:
  - UI 레이아웃 관리
  - 메뉴 및 툴바 설정
  - 컴포넌트 간 이벤트 조정

### ExcelLoader (`src/core/excel_loader.py`)
- **역할**: Excel 파일 로드 및 파싱
- **기능**:
  - .xlsx, .xls 파일 읽기
  - 수식 평가 (formulas 라이브러리)
  - 데이터 정규화

### TemplateManager (`src/core/template_manager.py`)
- **역할**: HTML 템플릿 관리
- **기능**:
  - 템플릿 목록 조회
  - 템플릿 로드 및 렌더링
  - 매핑 정보 관리

### DocumentGenerator (`src/core/document_generator.py`)
- **역할**: 최종 문서 생성
- **기능**:
  - HTML 템플릿에 데이터 바인딩
  - PDF/PNG 출력
  - 배치 처리

### LicenseManager (`src/license/license_manager.py`)
- **역할**: 라이센스 상태 관리 (Singleton)
- **기능**:
  - 라이센스 등록/검증
  - 기능 제한 관리
  - Skeleton Analyzer와 라이센스 공유

## 데이터 흐름

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Excel File  │ ──► │ ExcelLoader  │ ──► │   Mapper     │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Output File  │ ◄── │ DocGenerator │ ◄── │TemplateManager│
│  (PDF/PNG)   │     └──────────────┘     └──────────────┘
└──────────────┘
```

## 라이센스 시스템

### 공유 라이센스
- Skeleton Analyzer와 동일한 라이센스 파일 사용
- 경로: `~/.config/SkeletonAnalyzer/license.json`
- 한 번 등록으로 두 앱 모두 활성화

### 기능 제한
| 기능 | 무료 | 라이센스 |
|------|------|----------|
| Excel 로드 | ✅ | ✅ |
| 템플릿 미리보기 | ✅ | ✅ |
| 문서 생성 | ❌ | ✅ |

## 설정 저장

- QSettings를 사용하여 사용자 설정 저장
- 조직: "SafetyDoc"
- 애플리케이션: "DocumentCreator"
- 저장 항목: 윈도우 크기/위치, 최근 파일, 매핑 설정
