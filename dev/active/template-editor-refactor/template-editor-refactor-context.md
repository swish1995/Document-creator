# 템플릿 편집기 리팩토링 - 컨텍스트

> **최종 업데이트**: 2026-02-04

---

## 1. 주요 파일

### 1.1 수정 대상 파일

| 파일 | 역할 | 변경 내용 |
|------|------|-----------|
| `src/core/template_manager.py` | 템플릿 관리 | CRUD 기능 추가, 사용자 템플릿 지원 |
| `src/ui/main_window.py` | 메인 UI | 토글 레이아웃, 새 편집기 통합 |
| `src/ui/preview_widget.py` | 미리보기 | 전체화면 지원, 모드 전환 |
| `src/ui/excel_viewer.py` | 엑셀 뷰어 | 접기/펼치기 기능 |

### 1.2 신규 생성 파일

| 파일 | 역할 |
|------|------|
| `src/core/template_storage.py` | 템플릿 저장소 (기본/사용자 분리) |
| `src/ui/main_toolbar.py` | **[신규] 상단 메인 툴바** |
| `src/ui/template_editor/__init__.py` | 편집기 모듈 |
| `src/ui/template_editor/editor_widget.py` | 편집기 메인 위젯 |
| `src/ui/template_editor/wysiwyg_view.py` | 위지윅 뷰 |
| `src/ui/template_editor/mapping_overlay.py` | 매핑 오버레이 |
| `src/ui/template_editor/field_picker.py` | 필드 선택 팝업 |
| `src/ui/template_editor/template_manager_dialog.py` | 템플릿 관리 다이얼로그 |

### 1.3 관련 테스트 파일

| 파일 | 테스트 대상 |
|------|------------|
| `tests/test_template_storage.py` | TemplateStorage CRUD |
| `tests/test_template_manager_v2.py` | TemplateManager 확장 기능 |
| `tests/test_collapsible_panel.py` | CollapsiblePanel UI |
| `tests/test_editor_widget.py` | EditorWidget 모드 전환 |
| `tests/test_mapping_overlay.py` | MappingOverlay 클릭 처리 |

---

## 2. 주요 결정 사항

### 2.1 아키텍처 결정

| 결정 | 선택 | 이유 |
|------|------|------|
| HTML 편집 방식 | QTextEdit + 구문강조 | QWebEngineView는 편집 기능 제한적 |
| 미리보기 방식 | QWebEngineView (읽기전용) | HTML 렌더링 품질 |
| 템플릿 저장 위치 | `templates/_builtin/`, `templates/user/` | 기본/사용자 명확히 분리 |
| 매핑 방식 | 오버레이 + 클릭 | 위지윅 경험 제공 |

### 2.2 UI 결정

| 결정 | 선택 | 이유 |
|------|------|------|
| **툴바 구성** | 상단 메인 툴바 (기능별 그룹) | 스켈레톤 분석기 스타일, 버튼 집중 |
| **데이터 시트 토글** | 툴바 내 체크 버튼 | 별도 접기/펼치기 패널 대신 버튼으로 제어 |
| **그룹 분리** | QFrame separator | 기능별 시각적 구분 |
| 레이아웃 | 토글 + 전체화면 | 편집 영역 최대화 요구 |
| 모드 전환 | 라디오 버튼 (3가지) | 명확한 모드 구분 |
| 템플릿 선택 | 드롭다운 + 관리 다이얼로그 | 빠른 선택 + 상세 관리 |

### 2.3 데이터 결정

| 결정 | 선택 | 이유 |
|------|------|------|
| 템플릿 포맷 | HTML + mapping.json | 기존 포맷 유지 |
| 사용자 템플릿 ID | UUID 기반 폴더명 | 이름 충돌 방지 |
| 매핑 파일 | 템플릿 폴더 내 | 템플릿과 함께 관리 |

---

## 3. 의존성

### 3.1 내부 의존성

```
template_editor/editor_widget.py
├── depends on: template_storage.py
├── depends on: wysiwyg_view.py
├── depends on: mapping_overlay.py
└── depends on: preview_widget.py

main_window.py
├── depends on: template_editor/editor_widget.py
├── depends on: collapsible_panel.py
└── depends on: excel_viewer.py

mapping_overlay.py
├── depends on: field_picker.py
└── depends on: template_storage.py (필드 목록)
```

### 3.2 외부 의존성

```python
# 기존 (유지)
PyQt6 >= 6.6.0
PyQt6-WebEngine >= 6.6.0
Jinja2 >= 3.1.0

# 신규 (검토)
QScintilla >= 2.14.0  # 선택: 구문 강조 에디터
# 또는
pygments >= 2.17.0    # 대안: 구문 강조 라이브러리
```

---

## 4. 데이터 구조

### 4.1 Template 클래스 (확장)

```python
@dataclass
class Template:
    id: str                    # UUID (사용자) 또는 이름 (기본)
    name: str                  # 표시 이름
    version: str
    template_type: str         # "html" | "image"
    template_path: Path
    mapping_path: Path
    fields: List[Dict]
    is_builtin: bool           # [신규] 기본 템플릿 여부
    is_readonly: bool          # [신규] 읽기 전용 여부
    created_at: datetime       # [신규]
    updated_at: datetime       # [신규]
```

### 4.2 TemplateStorage 인터페이스

```python
class TemplateStorage:
    def get_builtin_templates() -> List[Template]
    def get_user_templates() -> List[Template]
    def get_all_templates() -> List[Template]
    def get_template(id: str) -> Template
    def create_template(name: str, html: str, fields: List) -> Template
    def update_template(id: str, ...) -> Template
    def delete_template(id: str) -> bool
    def copy_template(src_id: str, new_name: str) -> Template
    def export_template(id: str, path: Path) -> bool
    def import_template(path: Path) -> Template
```

### 4.3 템플릿 폴더 구조

```
templates/
├── _builtin/
│   └── owas/
│       ├── owas.html
│       ├── owas.mapping.json
│       └── meta.json          # [신규] 메타데이터
└── user/
    └── a1b2c3d4/              # UUID
        ├── template.html
        ├── mapping.json
        └── meta.json
```

### 4.4 meta.json 구조

```json
{
  "id": "a1b2c3d4-...",
  "name": "내 OWAS 템플릿",
  "version": "1.0",
  "description": "회사 양식에 맞게 수정",
  "based_on": "owas",
  "created_at": "2026-02-03T10:00:00",
  "updated_at": "2026-02-03T15:30:00"
}
```

---

## 5. UI 컴포넌트 상세

### 5.1 MainToolbar (신규)

```python
class MainToolbar(QToolBar):
    """상단 메인 툴바 - 기능별 버튼 그룹"""

    Signals:
        file_open_requested = pyqtSignal()
        file_save_requested = pyqtSignal()
        data_sheet_toggled = pyqtSignal(bool)    # True=표시, False=숨김
        data_refresh_requested = pyqtSignal()
        template_selected = pyqtSignal(str)       # 템플릿 ID
        template_new_requested = pyqtSignal()
        template_manage_requested = pyqtSignal()
        mode_changed = pyqtSignal(int)            # 0=편집, 1=미리보기, 2=매핑
        zoom_changed = pyqtSignal(int)            # 줌 퍼센트
        fullscreen_toggled = pyqtSignal()

    Layout:
        ┌─ 파일 ─────┐ │ ┌─ 데이터 시트 ─┐ │ ┌─ 템플릿 ─────────┐ │ ┌─ 편집 모드 ─┐ │ ┌─ 뷰 ─────┐
        │ [열기][저장]│ │ │ [표시][새로고침]│ │ │ [▼선택][+][관리] │ │ │ [편][미][매] │ │ │ [줌][전체]│
        └────────────┘ │ └────────────────┘ │ └──────────────────┘ │ └─────────────┘ │ └──────────┘

    Methods:
        set_templates(templates: List[Template])   # 드롭다운 업데이트
        set_current_template(id: str)
        set_data_sheet_visible(visible: bool)      # 버튼 체크 상태
        set_mode(mode: int)
        set_zoom(percent: int)
```

### 5.2 MainToolbar 버튼 그룹 상세

```python
# 파일 그룹
self.btn_open = QToolButton(icon="📂", tooltip="파일 열기 (Ctrl+O)")
self.btn_save = QToolButton(icon="💾", tooltip="저장 (Ctrl+S)")

# 데이터 시트 그룹
self.btn_data_toggle = QToolButton(icon="📊", tooltip="데이터 시트 표시/숨김 (Ctrl+D)")
self.btn_data_toggle.setCheckable(True)  # 체크 가능 버튼
self.btn_data_toggle.setChecked(True)    # 기본값: 표시
self.btn_refresh = QToolButton(icon="🔄", tooltip="새로고침 (F5)")

# 템플릿 그룹
self.combo_template = QComboBox()        # 템플릿 선택 드롭다운
self.btn_new_template = QToolButton(icon="➕", tooltip="새 템플릿")
self.btn_manage_template = QToolButton(icon="📋", tooltip="템플릿 관리")

# 편집 모드 그룹 (라디오 버튼 스타일)
self.mode_group = QButtonGroup()
self.btn_mode_edit = QToolButton(text="편집", checkable=True)
self.btn_mode_preview = QToolButton(text="미리보기", checkable=True)
self.btn_mode_mapping = QToolButton(text="매핑", checkable=True)

# 뷰 그룹
self.combo_zoom = QComboBox()            # 50%, 75%, 100%, 125%, 150%, 200%
self.btn_fullscreen = QToolButton(icon="⛶", tooltip="전체화면 (F11)")

# 분리자 추가
def _add_separator():
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    return separator
```

### 5.2 EditorWidget

```python
class EditorWidget(QWidget):
    """템플릿 편집기 메인 위젯"""

    Signals:
        template_changed = pyqtSignal(str)    # 템플릿 ID
        content_modified = pyqtSignal()

    Mode:
        EDIT = 0       # HTML 편집
        PREVIEW = 1    # 미리보기
        MAPPING = 2    # 매핑 모드

    Methods:
        set_template(id: str)
        set_mode(mode: Mode)
        set_preview_data(data: dict)
        save_template()
        toggle_fullscreen()
```

### 5.3 MappingOverlay

```python
class MappingOverlay(QWidget):
    """매핑 모드 오버레이"""

    Signals:
        placeholder_inserted = pyqtSignal(str, int)  # field_id, position

    Methods:
        show_field_picker(position: QPoint)
        highlight_placeholders()
        get_placeholder_positions() -> List[Tuple[str, int, int]]
```

---

## 6. 이전 결정 로그

| 날짜 | 결정 | 배경 |
|------|------|------|
| 2026-02-03 | 프로젝트 시작 | 사용자 요구사항 정의 |
| 2026-02-04 | 상단 툴바 구조로 변경 | 스켈레톤 분석기 스타일, 버튼 집중화 요청 |
| 2026-02-04 | 데이터 시트 토글을 툴바 버튼으로 | 별도 패널 대신 토글 버튼 방식 |
| 2026-02-04 | 기능별 그룹 분리 (separator) | 파일/데이터시트/템플릿/모드/뷰 5개 그룹 |

---

## 7. 참고 자료

- 기존 코드: `src/ui/mapping_dialog.py` (현재 매핑 UI)
- 기존 코드: `src/core/template_manager.py` (현재 템플릿 관리)
- 샘플 템플릿: `templates/sample/OWAS_Sample.html`
- PyQt6 문서: https://www.riverbankcomputing.com/static/Docs/PyQt6/
