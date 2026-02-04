"""TT3: EditorWidget 단위 테스트

EditorWidget 모드 전환 및 편집 기능을 테스트합니다.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

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
def temp_template():
    """임시 템플릿 파일"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write("<html><body>{{ title }}</body></html>")
        return Path(f.name)


class TestEditorWidgetInit:
    """EditorWidget 초기화 테스트"""

    def test_editor_created(self, editor):
        """에디터 생성 확인"""
        assert editor is not None

    def test_default_mode_is_edit(self, editor):
        """기본 모드는 편집"""
        assert editor.get_current_mode() == EditorWidget.MODE_EDIT

    def test_not_modified_initially(self, editor):
        """초기 상태는 수정되지 않음"""
        assert editor.is_modified() is False

    def test_empty_html_initially(self, editor):
        """초기 HTML은 비어있음"""
        assert editor.get_html_content() == ""


class TestModeSwitch:
    """모드 전환 테스트"""

    def test_switch_to_edit_mode(self, editor):
        """편집 모드로 전환"""
        editor.set_mode(EditorWidget.MODE_EDIT)
        assert editor.get_current_mode() == EditorWidget.MODE_EDIT

    def test_switch_to_preview_mode(self, editor):
        """미리보기 모드로 전환"""
        editor.set_mode(EditorWidget.MODE_PREVIEW)
        assert editor.get_current_mode() == EditorWidget.MODE_PREVIEW

    def test_switch_to_mapping_mode(self, editor):
        """매핑 모드로 전환"""
        editor.set_mode(EditorWidget.MODE_MAPPING)
        assert editor.get_current_mode() == EditorWidget.MODE_MAPPING

    def test_invalid_mode_ignored(self, editor):
        """유효하지 않은 모드는 무시"""
        editor.set_mode(EditorWidget.MODE_EDIT)
        editor.set_mode(999)  # 유효하지 않은 모드
        assert editor.get_current_mode() == EditorWidget.MODE_EDIT


class TestTemplateLoading:
    """템플릿 로딩 테스트"""

    def test_set_template(self, editor):
        """템플릿 설정"""
        html = "<html><body>Test</body></html>"
        editor.set_template("test-id", Path("/tmp/test.html"), html)

        assert editor.get_html_content() == html
        assert editor.is_modified() is False

    def test_load_template_from_path(self, editor, temp_template):
        """파일에서 템플릿 로드"""
        editor.load_template_from_path(temp_template)

        assert "{{ title }}" in editor.get_html_content()

    def test_template_changed_signal(self, editor):
        """템플릿 변경 시그널"""
        mock = MagicMock()
        editor.template_changed.connect(mock)

        editor.set_template("new-id", Path("/tmp/test.html"), "<html></html>")

        mock.assert_called_with("new-id")


class TestEditing:
    """편집 기능 테스트"""

    def test_content_modified_signal(self, editor):
        """내용 수정 시그널"""
        mock = MagicMock()
        editor.content_modified.connect(mock)

        # HTML 설정 후 텍스트 변경
        editor.set_template("id", Path("/tmp/test.html"), "original")
        editor._html_editor.setPlainText("modified")

        mock.assert_called()

    def test_is_modified_after_edit(self, editor):
        """편집 후 수정됨 상태"""
        editor.set_template("id", Path("/tmp/test.html"), "original")
        editor._html_editor.setPlainText("modified")

        assert editor.is_modified() is True

    def test_get_html_content_returns_current(self, editor):
        """현재 HTML 내용 반환"""
        editor.set_template("id", Path("/tmp/test.html"), "original")
        editor._html_editor.setPlainText("new content")

        assert editor.get_html_content() == "new content"


class TestPreviewData:
    """미리보기 데이터 테스트"""

    def test_set_preview_data(self, editor):
        """미리보기 데이터 설정"""
        data = {"title": "Test Title", "content": "Test Content"}
        editor.set_preview_data(data)

        assert editor._preview_data == data


class TestZoom:
    """줌 기능 테스트"""

    def test_set_zoom(self, editor):
        """줌 설정"""
        editor.set_zoom(150)
        assert editor._zoom_level == 150

    def test_default_zoom_is_100(self, editor):
        """기본 줌은 100%"""
        assert editor._zoom_level == 100


class TestSaving:
    """저장 기능 테스트"""

    def test_save_template_no_path(self, editor):
        """경로 없이 저장 실패"""
        result = editor.save_template()
        assert result is False

    def test_save_template_success(self, editor, temp_template):
        """저장 성공"""
        editor.set_template("id", temp_template, "<html>Saved</html>")
        result = editor.save_template()

        assert result is True
        assert editor.is_modified() is False

        # 파일 내용 확인
        saved_content = temp_template.read_text()
        assert saved_content == "<html>Saved</html>"


class TestUndoRedo:
    """실행 취소/다시 실행 테스트"""

    def test_can_undo_initially_false(self, editor):
        """초기 상태에서 실행 취소 불가"""
        assert editor.can_undo() is False

    def test_can_redo_initially_false(self, editor):
        """초기 상태에서 다시 실행 불가"""
        assert editor.can_redo() is False

    def test_get_undo_manager(self, editor):
        """UndoManager 반환"""
        undo_manager = editor.get_undo_manager()
        assert undo_manager is not None


class TestAutoSave:
    """자동 저장 테스트"""

    def test_get_auto_save_manager(self, editor):
        """AutoSaveManager 반환"""
        auto_save = editor.get_auto_save_manager()
        assert auto_save is not None

    def test_enable_auto_save(self, editor):
        """자동 저장 활성화"""
        editor.enable_auto_save(True, 30000)
        assert editor._auto_save.is_enabled() is True

    def test_disable_auto_save(self, editor):
        """자동 저장 비활성화"""
        editor.enable_auto_save(True)
        editor.enable_auto_save(False)
        assert editor._auto_save.is_enabled() is False
