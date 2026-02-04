# 템플릿 편집기 리팩토링 - 테스트 명세

> **최종 업데이트**: 2026-02-04

---

## 1. 테스트 전략

### 1.1 TDD 원칙
- 테스트 먼저 작성 후 구현
- Red → Green → Refactor 사이클
- 각 기능별 최소 테스트 커버리지 80%

### 1.2 테스트 계층
```
테스트 피라미드:
        /\
       /  \  UI 테스트 (pytest-qt) - 적음
      /----\
     /      \  통합 테스트 - 중간
    /--------\
   /          \  단위 테스트 - 많음
  /------------\
```

---

## 2. 단위 테스트 명세

### 2.1 TemplateStorage 테스트

**파일**: `tests/test_template_storage.py`

```python
class TestTemplateStorage:
    """TemplateStorage CRUD 테스트"""

    # === 조회 테스트 ===

    def test_get_builtin_templates_returns_default_templates(self):
        """기본 템플릿 목록 조회"""
        # Given: TemplateStorage 인스턴스
        # When: get_builtin_templates() 호출
        # Then: OWAS, REBA, RULA 등 기본 템플릿 포함
        pass

    def test_get_user_templates_initially_empty(self):
        """초기 사용자 템플릿 빈 목록"""
        # Given: 새로운 TemplateStorage
        # When: get_user_templates() 호출
        # Then: 빈 리스트 반환
        pass

    def test_get_template_by_id_returns_correct_template(self):
        """ID로 템플릿 조회"""
        # Given: 존재하는 템플릿 ID
        # When: get_template(id) 호출
        # Then: 해당 템플릿 반환
        pass

    def test_get_template_by_invalid_id_raises_error(self):
        """존재하지 않는 ID 조회 시 에러"""
        # Given: 존재하지 않는 ID
        # When: get_template(invalid_id) 호출
        # Then: TemplateNotFoundError 발생
        pass

    # === 생성 테스트 ===

    def test_create_template_saves_files(self):
        """템플릿 생성 시 파일 저장"""
        # Given: 템플릿 이름, HTML, 필드 정보
        # When: create_template() 호출
        # Then: templates/user/ 에 폴더 및 파일 생성
        pass

    def test_create_template_with_duplicate_name_adds_suffix(self):
        """중복 이름 시 접미사 추가"""
        # Given: 이미 존재하는 이름
        # When: create_template(same_name) 호출
        # Then: "name (2)" 형태로 저장
        pass

    def test_create_template_generates_uuid_folder(self):
        """UUID 기반 폴더명 생성"""
        # Given: 새 템플릿 생성 요청
        # When: create_template() 호출
        # Then: UUID 형식의 폴더명 생성
        pass

    # === 수정 테스트 ===

    def test_update_template_modifies_content(self):
        """템플릿 내용 수정"""
        # Given: 기존 사용자 템플릿
        # When: update_template(id, new_html) 호출
        # Then: HTML 파일 업데이트
        pass

    def test_update_builtin_template_raises_error(self):
        """기본 템플릿 수정 시 에러"""
        # Given: 기본 템플릿 ID
        # When: update_template(builtin_id, ...) 호출
        # Then: ReadOnlyTemplateError 발생
        pass

    def test_update_template_updates_timestamp(self):
        """수정 시 타임스탬프 갱신"""
        # Given: 기존 템플릿
        # When: update_template() 호출
        # Then: meta.json의 updated_at 갱신
        pass

    # === 삭제 테스트 ===

    def test_delete_template_removes_folder(self):
        """템플릿 삭제 시 폴더 제거"""
        # Given: 사용자 템플릿
        # When: delete_template(id) 호출
        # Then: 해당 폴더 삭제됨
        pass

    def test_delete_builtin_template_raises_error(self):
        """기본 템플릿 삭제 시 에러"""
        # Given: 기본 템플릿 ID
        # When: delete_template(builtin_id) 호출
        # Then: ReadOnlyTemplateError 발생
        pass

    # === 복사 테스트 ===

    def test_copy_builtin_to_user(self):
        """기본 템플릿을 사용자 템플릿으로 복사"""
        # Given: 기본 템플릿 ID
        # When: copy_template(builtin_id, "My Copy") 호출
        # Then: 새 사용자 템플릿 생성, based_on 필드에 원본 ID
        pass

    def test_copy_user_template(self):
        """사용자 템플릿 복사"""
        # Given: 사용자 템플릿 ID
        # When: copy_template(user_id, "Copy") 호출
        # Then: 새 사용자 템플릿 생성
        pass
```

### 2.2 MainToolbar 테스트

**파일**: `tests/test_main_toolbar.py`

```python
class TestMainToolbar:
    """MainToolbar 테스트"""

    # === 초기화 테스트 ===

    def test_initial_state(self):
        """초기 상태 확인"""
        # Given: MainToolbar 생성
        # When: 초기화 완료
        # Then: 데이터 시트 버튼 체크됨, 편집 모드 선택됨
        pass

    def test_button_groups_separated(self):
        """버튼 그룹 분리 확인"""
        # Given: MainToolbar 생성
        # Then: 5개 그룹이 separator로 분리됨
        pass

    # === 파일 그룹 테스트 ===

    def test_open_button_emits_signal(self):
        """열기 버튼 시그널"""
        # When: btn_open 클릭
        # Then: file_open_requested 시그널 발생
        pass

    def test_save_button_emits_signal(self):
        """저장 버튼 시그널"""
        # When: btn_save 클릭
        # Then: file_save_requested 시그널 발생
        pass

    # === 데이터 시트 그룹 테스트 ===

    def test_data_toggle_button_is_checkable(self):
        """토글 버튼 체크 가능 여부"""
        # Given: btn_data_toggle
        # Then: isCheckable() == True
        pass

    def test_data_toggle_emits_signal_with_state(self):
        """토글 시 상태와 함께 시그널 발생"""
        # Given: 체크된 상태
        # When: 클릭
        # Then: data_sheet_toggled(False) 시그널 발생
        pass

    def test_refresh_button_emits_signal(self):
        """새로고침 버튼 시그널"""
        # When: btn_refresh 클릭
        # Then: data_refresh_requested 시그널 발생
        pass

    # === 템플릿 그룹 테스트 ===

    def test_template_dropdown_populated(self):
        """템플릿 드롭다운 목록"""
        # Given: templates = [OWAS, REBA, RULA]
        # When: set_templates(templates)
        # Then: combo_template.count() == 3
        pass

    def test_template_selection_emits_signal(self):
        """템플릿 선택 시그널"""
        # When: 드롭다운에서 선택
        # Then: template_selected(id) 시그널 발생
        pass

    def test_new_template_button_emits_signal(self):
        """새 템플릿 버튼 시그널"""
        # When: btn_new_template 클릭
        # Then: template_new_requested 시그널 발생
        pass

    # === 편집 모드 그룹 테스트 ===

    def test_mode_buttons_exclusive(self):
        """모드 버튼 배타적 선택"""
        # Given: mode_group (QButtonGroup)
        # When: btn_mode_preview 클릭
        # Then: btn_mode_edit 체크 해제됨
        pass

    def test_mode_change_emits_signal(self):
        """모드 변경 시그널"""
        # When: btn_mode_mapping 클릭
        # Then: mode_changed(2) 시그널 발생
        pass

    # === 뷰 그룹 테스트 ===

    def test_zoom_dropdown_options(self):
        """줌 드롭다운 옵션"""
        # Then: combo_zoom에 50%, 75%, 100%, 125%, 150%, 200% 포함
        pass

    def test_zoom_change_emits_signal(self):
        """줌 변경 시그널"""
        # When: combo_zoom에서 150% 선택
        # Then: zoom_changed(150) 시그널 발생
        pass

    def test_fullscreen_button_emits_signal(self):
        """전체화면 버튼 시그널"""
        # When: btn_fullscreen 클릭
        # Then: fullscreen_toggled 시그널 발생
        pass

    # === 단축키 테스트 ===

    def test_shortcut_ctrl_o(self):
        """Ctrl+O 단축키"""
        # When: Ctrl+O 입력
        # Then: file_open_requested 시그널 발생
        pass

    def test_shortcut_ctrl_d(self):
        """Ctrl+D 단축키"""
        # When: Ctrl+D 입력
        # Then: data_sheet_toggled 시그널 발생
        pass

    def test_shortcut_f11(self):
        """F11 단축키"""
        # When: F11 입력
        # Then: fullscreen_toggled 시그널 발생
        pass
```

### 2.3 EditorWidget 테스트

**파일**: `tests/test_editor_widget.py`

```python
class TestEditorWidget:
    """EditorWidget 테스트"""

    # === 모드 전환 테스트 ===

    def test_initial_mode_is_edit(self):
        """초기 모드는 편집 모드"""
        pass

    def test_set_mode_to_preview(self):
        """미리보기 모드 전환"""
        pass

    def test_set_mode_to_mapping(self):
        """매핑 모드 전환"""
        pass

    def test_mode_change_updates_ui(self):
        """모드 변경 시 UI 업데이트"""
        pass

    # === 템플릿 로드 테스트 ===

    def test_set_template_loads_content(self):
        """템플릿 설정 시 내용 로드"""
        pass

    def test_set_template_updates_dropdown(self):
        """템플릿 설정 시 드롭다운 업데이트"""
        pass

    def test_template_changed_signal_emitted(self):
        """템플릿 변경 시 시그널 발생"""
        pass

    # === 저장 테스트 ===

    def test_save_template_persists_changes(self):
        """저장 시 변경 내용 유지"""
        pass

    def test_save_prompts_for_name_if_new(self):
        """새 템플릿 저장 시 이름 요청"""
        pass

    def test_unsaved_changes_warning_on_switch(self):
        """저장하지 않고 전환 시 경고"""
        pass

    # === 전체화면 테스트 ===

    def test_toggle_fullscreen_on(self):
        """전체화면 진입"""
        pass

    def test_toggle_fullscreen_off(self):
        """전체화면 해제"""
        pass

    def test_escape_exits_fullscreen(self):
        """ESC 키로 전체화면 해제"""
        pass
```

### 2.4 MappingOverlay 테스트

**파일**: `tests/test_mapping_overlay.py`

```python
class TestMappingOverlay:
    """MappingOverlay 테스트"""

    # === 클릭 처리 테스트 ===

    def test_click_shows_field_picker(self):
        """클릭 시 필드 선택 팝업 표시"""
        pass

    def test_click_position_accurate(self):
        """클릭 위치 정확히 캡처"""
        pass

    # === 플레이스홀더 하이라이트 테스트 ===

    def test_highlight_existing_placeholders(self):
        """기존 플레이스홀더 하이라이트"""
        pass

    def test_highlight_updates_on_template_change(self):
        """템플릿 변경 시 하이라이트 업데이트"""
        pass

    def test_hover_shows_tooltip(self):
        """호버 시 툴팁 표시"""
        pass

    # === 플레이스홀더 삽입 테스트 ===

    def test_insert_placeholder_at_position(self):
        """위치에 플레이스홀더 삽입"""
        pass

    def test_insert_placeholder_emits_signal(self):
        """삽입 시 시그널 발생"""
        pass

    def test_insert_updates_mapping_json(self):
        """삽입 시 mapping.json 업데이트"""
        pass
```

---

## 3. 통합 테스트 명세

### 3.1 템플릿 CRUD 워크플로우

**파일**: `tests/integration/test_template_crud.py`

```python
class TestTemplateCRUDWorkflow:
    """템플릿 CRUD 전체 워크플로우 테스트"""

    def test_create_edit_save_workflow(self):
        """생성 → 편집 → 저장 워크플로우"""
        # 1. 새 템플릿 생성
        # 2. HTML 편집
        # 3. 저장
        # 4. 다시 로드하여 확인
        pass

    def test_copy_modify_delete_workflow(self):
        """복사 → 수정 → 삭제 워크플로우"""
        # 1. 기본 템플릿 복사
        # 2. 복사본 수정
        # 3. 복사본 삭제
        # 4. 원본 변경 없음 확인
        pass

    def test_export_import_roundtrip(self):
        """내보내기 → 가져오기 왕복 테스트"""
        # 1. 템플릿 내보내기
        # 2. 원본 삭제
        # 3. 가져오기
        # 4. 내용 동일 확인
        pass
```

### 3.2 편집기 워크플로우

**파일**: `tests/integration/test_editor_workflow.py`

```python
class TestEditorWorkflow:
    """편집기 전체 워크플로우 테스트"""

    def test_edit_preview_save_workflow(self):
        """편집 → 미리보기 → 저장 워크플로우"""
        pass

    def test_mapping_mode_workflow(self):
        """매핑 모드 전체 워크플로우"""
        # 1. 매핑 모드 진입
        # 2. 클릭하여 필드 선택
        # 3. 플레이스홀더 삽입
        # 4. 미리보기에서 확인
        pass

    def test_unsaved_changes_protection(self):
        """저장하지 않은 변경 보호"""
        # 1. 템플릿 편집
        # 2. 저장 없이 다른 템플릿 선택
        # 3. 경고 다이얼로그 확인
        # 4. 취소 시 원래 템플릿 유지
        pass
```

---

## 4. UI 테스트 명세 (pytest-qt)

### 4.1 CollapsiblePanel UI 테스트

```python
class TestCollapsiblePanelUI:
    """CollapsiblePanel UI 상호작용 테스트"""

    def test_click_toggle_button(self, qtbot):
        """토글 버튼 클릭"""
        pass

    def test_animation_completes(self, qtbot):
        """애니메이션 완료 확인"""
        pass
```

### 4.2 EditorWidget UI 테스트

```python
class TestEditorWidgetUI:
    """EditorWidget UI 상호작용 테스트"""

    def test_mode_radio_button_click(self, qtbot):
        """모드 라디오 버튼 클릭"""
        pass

    def test_template_dropdown_selection(self, qtbot):
        """템플릿 드롭다운 선택"""
        pass

    def test_save_button_click(self, qtbot):
        """저장 버튼 클릭"""
        pass
```

---

## 5. 테스트 진행 상황

| 카테고리 | 작성 | 통과 | 실패 | 스킵 |
|----------|------|------|------|------|
| TemplateStorage | 0 | 0 | 0 | 0 |
| CollapsiblePanel | 0 | 0 | 0 | 0 |
| EditorWidget | 0 | 0 | 0 | 0 |
| MappingOverlay | 0 | 0 | 0 | 0 |
| 통합 테스트 | 0 | 0 | 0 | 0 |
| UI 테스트 | 0 | 0 | 0 | 0 |
| **합계** | **0** | **0** | **0** | **0** |

---

## 6. 테스트 실행 명령

```bash
# 전체 테스트
pytest

# 특정 모듈 테스트
pytest tests/test_template_storage.py

# 커버리지 포함
pytest --cov=src --cov-report=html

# UI 테스트만
pytest tests/test_*_ui.py

# 통합 테스트만
pytest tests/integration/
```

---

## 7. 테스트 픽스처

**파일**: `tests/conftest.py`

```python
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def temp_templates_dir():
    """임시 템플릿 디렉토리"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def template_storage(temp_templates_dir):
    """TemplateStorage 인스턴스"""
    from src.core.template_storage import TemplateStorage
    return TemplateStorage(temp_templates_dir)

@pytest.fixture
def sample_html():
    """샘플 HTML 템플릿"""
    return """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>{{ title }}</h1>
        <p>Score: {{ score }}</p>
    </body>
    </html>
    """

@pytest.fixture
def sample_fields():
    """샘플 필드 정의"""
    return [
        {"id": "title", "label": "제목", "excel_column": "Title"},
        {"id": "score", "label": "점수", "excel_column": "Score"},
    ]
```
