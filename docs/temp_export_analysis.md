# 내보내기 기능 구현 계획서

> 작성일: 2026-02-06
> 상태: 구현 완료

---

## 1. 개요

내보내기 기능을 전면 개편하여 QWebEngine 기반 PDF 변환, PyMuPDF 이미지 변환, ZIP 아카이브 제공 방식으로 변경한다.

---

## 2. 핵심 변경사항

| 항목 | 현재 | 변경 후 |
|------|------|---------|
| PDF 변환 | 미구현 | QWebEngine 사용 |
| 이미지 변환 | 미구현 | PDF → PNG (PyMuPDF) |
| 파일 제공 | 폴더에 직접 저장 | ZIP 아카이브 또는 단일 PDF |
| 저장 위치 | 미리 선택 | 완료 후 저장 다이얼로그 |
| 임시 파일 | 없음 | `worked/` 디렉토리 사용 후 삭제 |

---

## 3. 작업 흐름

```
[내보내기 버튼 클릭]
    ↓
[ExportDialog] - 형식(PDF/PNG), 통합파일 여부, 파일명 설정
    ↓
[전체 창 흐리게 + 진행 오버레이 표시]
    ↓
[worked/ 디렉토리 생성/초기화]
    ↓
[엑셀 행 순차 처리] ← 진행 상태: "3/24 처리 중..."
    │
    ├─ 1. 해당 행 데이터로 템플릿 매핑 (미리보기에 반영)
    ├─ 2. QWebEngine으로 HTML → PDF 변환
    ├─ 3. (PNG 선택 시) PyMuPDF로 PDF → PNG 변환
    └─ 4. 다음 행으로 이동
    ↓
[후처리]
    ├─ PDF 통합 옵션 선택 시: PyMuPDF로 PDF 병합
    ├─ 단일 PDF 파일: 그대로 제공
    └─ 여러 파일: ZIP 아카이브 생성
    ↓
[QFileDialog.getSaveFileName()] - 저장 위치 선택
    ↓
[파일 저장 + worked/ 디렉토리 정리]
    ↓
[완료]
```

---

## 4. 파일 제공 규칙

| 조건 | 출력 형식 |
|------|----------|
| PDF + 통합파일 체크 | 단일 `.pdf` 파일 |
| PDF + 통합파일 미체크 + 파일 1개 | 단일 `.pdf` 파일 |
| PDF + 통합파일 미체크 + 파일 2개 이상 | `.zip` 아카이브 |
| PNG + 파일 1개 | 단일 `.png` 파일 |
| PNG + 파일 2개 이상 | `.zip` 아카이브 |

---

## 5. 작업 디렉토리 관리

### 5.1 디렉토리 구조
```
document-creator/
├── worked/              ← 임시 작업 디렉토리 (gitignore)
│   ├── temp_001.pdf
│   ├── temp_002.pdf
│   └── ...
└── .gitignore           ← worked/ 추가
```

### 5.2 생명주기
1. **프로그램 시작 시**: `worked/` 존재하면 내용물 전체 삭제 (고아 파일 방지)
2. **내보내기 시작**: `worked/` 디렉토리 생성
3. **내보내기 진행**: 임시 PDF/PNG 파일 저장
4. **내보내기 완료**: 최종 파일 저장 후 `worked/` 내용물 삭제

---

## 6. UI 변경사항

### 6.1 ExportDialog 수정
- **제거**: 저장 위치 그룹 (path_group) 전체 삭제
- **제거**: 찾아보기 버튼 관련 로직
- **제거**: 폴더 구조 옵션 (ZIP으로 통합되므로 불필요)
- **변경**: 내보내기 버튼 항상 활성화 (저장 위치 조건 제거)

### 6.2 진행 표시 변경
- **제거**: ExportProgressDialog (별도 다이얼로그)
- **추가**: MainWindow 오버레이 방식
  - 전체 창 흐리게 (반투명 오버레이)
  - 중앙에 진행 상태 표시
  - 현재 처리 중인 행이 미리보기에 표시됨

### 6.3 진행 상태 표시
```
┌─────────────────────────────────┐
│      (흐린 메인 윈도우 배경)      │
│                                 │
│    ┌───────────────────────┐    │
│    │   내보내기 진행 중...   │    │
│    │                       │    │
│    │   ████████░░░░  12/24 │    │
│    │   OWAS_row003.pdf     │    │
│    │                       │    │
│    │      [ 취소 ]         │    │
│    └───────────────────────┘    │
│                                 │
└─────────────────────────────────┘
```

---

## 7. 기술 구현 상세

### 7.1 QWebEngine PDF 변환
```python
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage

# 방법: QWebEnginePage.printToPdf()
page.printToPdf(output_path, page_layout)
```

### 7.2 PyMuPDF 이미지 변환
```python
import fitz  # PyMuPDF

doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x 해상도
pix.save(png_path)
```

### 7.3 PyMuPDF PDF 병합
```python
import fitz

merged = fitz.open()
for pdf_path in pdf_files:
    doc = fitz.open(pdf_path)
    merged.insert_pdf(doc)
merged.save(output_path)
```

### 7.4 ZIP 아카이브 생성
```python
import zipfile

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for file_path in files:
        zf.write(file_path, file_path.name)
```

---

## 8. 변경 대상 파일

### 8.1 수정
| 파일 | 변경 내용 |
|------|----------|
| `src/ui/export_dialog.py` | 저장 위치 UI 제거, 폴더 구조 옵션 제거 |
| `src/ui/main_window.py` | 오버레이 진행 표시, 완료 후 저장 다이얼로그 |
| `src/core/document_generator.py` | PDF/PNG 생성 로직 추가 |
| `.gitignore` | `worked/` 추가 |

### 8.2 신규
| 파일 | 역할 |
|------|------|
| `src/core/pdf_converter.py` | QWebEngine PDF 변환 래퍼 |
| `src/core/export_manager.py` | 내보내기 전체 프로세스 관리 |
| `src/ui/export_overlay.py` | 진행 오버레이 위젯 |

### 8.3 삭제
| 파일 | 사유 |
|------|------|
| `src/ui/export_progress_dialog.py` | 오버레이 방식으로 대체 |

---

## 9. 의존성 추가

```txt
# requirements.txt
PyMuPDF>=1.24.0   # PDF→이미지, PDF 병합
```

> QWebEngine은 PyQt6에 포함 (PyQt6-WebEngine)

---

## 10. 구현 순서

### Phase 1: 기반 작업
1. `.gitignore`에 `worked/` 추가
2. 프로그램 시작 시 `worked/` 정리 로직 추가
3. `requirements.txt`에 PyMuPDF 추가

### Phase 2: 핵심 모듈
4. `pdf_converter.py` - QWebEngine PDF 변환
5. `export_manager.py` - 전체 프로세스 관리

### Phase 3: UI 수정
6. `export_dialog.py` - 저장 위치/폴더 구조 옵션 제거
7. `export_overlay.py` - 진행 오버레이 위젯
8. `main_window.py` - 오버레이 통합, 완료 후 저장 다이얼로그

### Phase 4: 정리
9. `export_progress_dialog.py` 삭제
10. 테스트 및 검증

---

## 11. 파일명 규칙

```
개별 파일: {사용자입력}_{템플릿명}_{행번호:03d}.pdf
통합 PDF:  {사용자입력}.pdf
ZIP 파일:  {사용자입력}.zip
```

예시 (사용자 입력: "안전문서_20260206"):
- 개별: `안전문서_20260206_OWAS_001.pdf`
- 통합: `안전문서_20260206.pdf`
- ZIP: `안전문서_20260206.zip`
