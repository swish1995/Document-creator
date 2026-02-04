"""TT6: 편집→미리보기→저장 워크플로우 통합 테스트

EditorWidget의 편집, 미리보기, 저장 워크플로우를 테스트합니다.
"""

import pytest
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from src.ui.template_editor.editor_widget import EditorWidget


@pytest.fixture(scope="module")
def app():
    """QApplication 인스턴스"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def editor(app):
    """EditorWidget 인스턴스"""
    return EditorWidget()


@pytest.fixture
def temp_template_file():
    """임시 템플릿 파일"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write("""<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ title }}</h1>
    <p>{{ content }}</p>
</body>
</html>""")
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()


class TestEditModeWorkflow:
    """편집 모드 워크플로우 테스트"""

    def test_load_edit_workflow(self, editor, temp_template_file):
        """템플릿 로드 → 편집 워크플로우"""
        # 1. 템플릿 로드
        editor.load_template_from_path(temp_template_file)
        assert "{{ title }}" in editor.get_html_content()
        assert editor.is_modified() is False

        # 2. 편집 모드 확인
        assert editor.get_current_mode() == EditorWidget.MODE_EDIT

        # 3. 편집
        original = editor.get_html_content()
        new_content = original.replace("{{ content }}", "{{ body }}")
        editor._html_editor.setPlainText(new_content)

        # 4. 수정됨 상태 확인
        assert editor.is_modified() is True
        assert "{{ body }}" in editor.get_html_content()

    def test_edit_updates_internal_state(self, editor, temp_template_file):
        """편집이 내부 상태를 업데이트"""
        editor.load_template_from_path(temp_template_file)

        # 편집 전
        before_edit = editor.get_html_content()

        # 편집
        editor._html_editor.setPlainText("<html>Completely new content</html>")

        # 편집 후
        after_edit = editor.get_html_content()

        assert before_edit != after_edit
        assert "Completely new content" in after_edit


class TestPreviewModeWorkflow:
    """미리보기 모드 워크플로우 테스트"""

    def test_switch_to_preview_mode(self, editor, temp_template_file):
        """미리보기 모드로 전환"""
        editor.load_template_from_path(temp_template_file)

        # 미리보기 모드로 전환
        editor.set_mode(EditorWidget.MODE_PREVIEW)

        assert editor.get_current_mode() == EditorWidget.MODE_PREVIEW

    def test_preview_with_data(self, editor, temp_template_file):
        """데이터와 함께 미리보기"""
        editor.load_template_from_path(temp_template_file)

        # 데이터 설정
        preview_data = {
            "title": "Test Title",
            "content": "Test Content",
        }
        editor.set_preview_data(preview_data)

        # 미리보기 모드로 전환
        editor.set_mode(EditorWidget.MODE_PREVIEW)

        # 내부 데이터 확인
        assert editor._preview_data["title"] == "Test Title"

    def test_edit_preview_roundtrip(self, editor, temp_template_file):
        """편집 → 미리보기 → 편집 왕복"""
        editor.load_template_from_path(temp_template_file)

        # 편집 모드에서 수정
        editor._html_editor.setPlainText("<html>{{ modified }}</html>")
        assert editor.is_modified() is True

        # 미리보기 모드로 전환
        editor.set_mode(EditorWidget.MODE_PREVIEW)
        assert editor.get_current_mode() == EditorWidget.MODE_PREVIEW

        # 다시 편집 모드로
        editor.set_mode(EditorWidget.MODE_EDIT)
        assert editor.get_current_mode() == EditorWidget.MODE_EDIT

        # 수정 내용 유지
        assert "{{ modified }}" in editor.get_html_content()
        assert editor.is_modified() is True


class TestSaveWorkflow:
    """저장 워크플로우 테스트"""

    def test_save_after_edit(self, editor, temp_template_file):
        """편집 후 저장"""
        editor.load_template_from_path(temp_template_file)

        # 편집
        editor._html_editor.setPlainText("<html>Saved Content</html>")
        assert editor.is_modified() is True

        # 저장
        result = editor.save_template()

        assert result is True
        assert editor.is_modified() is False

        # 파일 내용 확인
        saved = temp_template_file.read_text()
        assert "Saved Content" in saved

    def test_save_preserves_content(self, editor, temp_template_file):
        """저장이 내용을 보존"""
        editor.load_template_from_path(temp_template_file)

        new_content = """<!DOCTYPE html>
<html>
<head><title>New Title</title></head>
<body>
    <h1>{{ header }}</h1>
    <div>{{ body }}</div>
</body>
</html>"""
        editor._html_editor.setPlainText(new_content)
        editor.save_template()

        # 다시 로드
        editor.load_template_from_path(temp_template_file)

        assert "{{ header }}" in editor.get_html_content()
        assert "{{ body }}" in editor.get_html_content()

    def test_modified_flag_after_save(self, editor, temp_template_file):
        """저장 후 수정 플래그"""
        editor.load_template_from_path(temp_template_file)
        editor._html_editor.setPlainText("<html>Modified</html>")

        # 저장 전: 수정됨
        assert editor.is_modified() is True

        editor.save_template()

        # 저장 후: 수정 안됨
        assert editor.is_modified() is False

        # 다시 수정
        editor._html_editor.setPlainText("<html>Modified Again</html>")

        # 다시 수정됨
        assert editor.is_modified() is True


class TestFullWorkflow:
    """전체 워크플로우 테스트"""

    def test_complete_edit_preview_save_workflow(self, editor, temp_template_file):
        """완전한 편집 → 미리보기 → 저장 워크플로우"""
        # 1. 템플릿 로드
        editor.load_template_from_path(temp_template_file)
        assert editor.is_modified() is False

        # 2. 편집 모드에서 수정
        editor.set_mode(EditorWidget.MODE_EDIT)
        new_html = """<!DOCTYPE html>
<html>
<head><title>{{ page_title }}</title></head>
<body>
    <header>{{ header }}</header>
    <main>{{ main_content }}</main>
    <footer>{{ footer }}</footer>
</body>
</html>"""
        editor._html_editor.setPlainText(new_html)
        assert editor.is_modified() is True

        # 3. 미리보기 모드로 전환하여 확인
        editor.set_mode(EditorWidget.MODE_PREVIEW)
        editor.set_preview_data({
            "page_title": "Test Page",
            "header": "Header Text",
            "main_content": "Main Content",
            "footer": "Footer Text",
        })

        # 4. 다시 편집 모드로
        editor.set_mode(EditorWidget.MODE_EDIT)

        # 5. 저장
        result = editor.save_template()
        assert result is True
        assert editor.is_modified() is False

        # 6. 파일 내용 확인
        saved = temp_template_file.read_text()
        assert "{{ page_title }}" in saved
        assert "{{ header }}" in saved
        assert "{{ main_content }}" in saved
        assert "{{ footer }}" in saved


class TestZoomWorkflow:
    """줌 워크플로우 테스트"""

    def test_zoom_in_preview_mode(self, editor, temp_template_file):
        """미리보기 모드에서 줌"""
        editor.load_template_from_path(temp_template_file)
        editor.set_mode(EditorWidget.MODE_PREVIEW)

        # 줌 변경
        editor.set_zoom(150)

        assert editor._zoom_level == 150

    def test_zoom_persists_across_modes(self, editor, temp_template_file):
        """줌이 모드 전환 시 유지"""
        editor.load_template_from_path(temp_template_file)

        editor.set_zoom(125)
        editor.set_mode(EditorWidget.MODE_PREVIEW)
        editor.set_mode(EditorWidget.MODE_EDIT)
        editor.set_mode(EditorWidget.MODE_PREVIEW)

        assert editor._zoom_level == 125


class TestModifiedStateTracking:
    """수정 상태 추적 테스트"""

    def test_modified_after_each_edit(self, editor, temp_template_file):
        """각 편집 후 수정 상태"""
        editor.load_template_from_path(temp_template_file)

        # 초기: 수정 안됨
        assert editor.is_modified() is False

        # 첫 번째 편집
        editor._html_editor.setPlainText("Edit 1")
        assert editor.is_modified() is True

        # 저장
        editor.save_template()
        assert editor.is_modified() is False

        # 두 번째 편집
        editor._html_editor.setPlainText("Edit 2")
        assert editor.is_modified() is True

    def test_modified_state_with_mode_switch(self, editor, temp_template_file):
        """모드 전환 시 수정 상태 유지"""
        editor.load_template_from_path(temp_template_file)
        editor._html_editor.setPlainText("Modified content")

        assert editor.is_modified() is True

        # 모드 전환
        editor.set_mode(EditorWidget.MODE_PREVIEW)
        assert editor.is_modified() is True

        editor.set_mode(EditorWidget.MODE_MAPPING)
        assert editor.is_modified() is True

        editor.set_mode(EditorWidget.MODE_EDIT)
        assert editor.is_modified() is True
