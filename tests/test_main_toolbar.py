"""TT2: MainToolbar 단위 테스트

MainToolbar 시그널 및 버튼 기능을 테스트합니다.
"""

import pytest
from unittest.mock import MagicMock

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.ui.main_toolbar import MainToolbar


@pytest.fixture(scope="module")
def app():
    """QApplication 인스턴스"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def toolbar(app):
    """MainToolbar 인스턴스"""
    return MainToolbar()


class TestMainToolbarInit:
    """MainToolbar 초기화 테스트"""

    def test_toolbar_created(self, toolbar):
        """툴바 생성 확인"""
        assert toolbar is not None
        assert toolbar.objectName() == "mainToolbar"

    def test_not_movable(self, toolbar):
        """이동 불가 확인"""
        assert toolbar.isMovable() is False

    def test_not_floatable(self, toolbar):
        """분리 불가 확인"""
        assert toolbar.isFloatable() is False


class TestFileGroup:
    """파일 그룹 버튼 테스트"""

    def test_open_button_exists(self, toolbar):
        """열기 버튼 존재"""
        assert toolbar.btn_open is not None

    def test_save_button_exists(self, toolbar):
        """저장 버튼 존재"""
        assert toolbar.btn_save is not None

    def test_save_button_disabled_by_default(self, toolbar):
        """저장 버튼 기본 비활성화"""
        assert toolbar.btn_save.isEnabled() is False

    def test_open_signal(self, toolbar):
        """열기 시그널 발생"""
        mock = MagicMock()
        toolbar.file_open_requested.connect(mock)

        toolbar.btn_open.click()

        mock.assert_called_once()

    def test_save_signal(self, toolbar):
        """저장 시그널 발생"""
        mock = MagicMock()
        toolbar.file_save_requested.connect(mock)
        toolbar.btn_save.setEnabled(True)

        toolbar.btn_save.click()

        mock.assert_called_once()


class TestDataSheetGroup:
    """데이터 시트 그룹 버튼 테스트"""

    def test_toggle_button_exists(self, toolbar):
        """토글 버튼 존재"""
        assert toolbar.btn_data_toggle is not None

    def test_toggle_button_checkable(self, toolbar):
        """토글 버튼 체크 가능"""
        assert toolbar.btn_data_toggle.isCheckable() is True

    def test_toggle_button_checked_by_default(self, toolbar):
        """토글 버튼 기본 체크됨"""
        assert toolbar.btn_data_toggle.isChecked() is True

    def test_refresh_button_exists(self, toolbar):
        """새로고침 버튼 존재"""
        assert toolbar.btn_refresh is not None

    def test_toggle_signal(self, toolbar):
        """토글 시그널 발생"""
        mock = MagicMock()
        toolbar.data_sheet_toggled.connect(mock)

        toolbar.btn_data_toggle.setChecked(False)

        mock.assert_called_with(False)

    def test_refresh_signal(self, toolbar):
        """새로고침 시그널 발생"""
        mock = MagicMock()
        toolbar.data_refresh_requested.connect(mock)

        toolbar.btn_refresh.click()

        mock.assert_called_once()


class TestTemplateGroup:
    """템플릿 그룹 테스트"""

    def test_combo_exists(self, toolbar):
        """콤보박스 존재"""
        assert toolbar.combo_template is not None

    def test_new_button_exists(self, toolbar):
        """새로 만들기 버튼 존재"""
        assert toolbar.btn_new_template is not None

    def test_manage_button_exists(self, toolbar):
        """관리 버튼 존재"""
        assert toolbar.btn_manage_template is not None

    def test_set_templates(self, toolbar):
        """템플릿 목록 설정"""
        templates = [
            ("id1", "Template 1"),
            ("id2", "Template 2"),
        ]
        toolbar.set_templates(templates)

        assert toolbar.combo_template.count() == 2
        assert toolbar.combo_template.itemText(0) == "Template 1"
        assert toolbar.combo_template.itemData(0) == "id1"

    def test_set_current_template(self, toolbar):
        """현재 템플릿 설정"""
        templates = [("id1", "T1"), ("id2", "T2"), ("id3", "T3")]
        toolbar.set_templates(templates)

        toolbar.set_current_template("id2")

        assert toolbar.combo_template.currentText() == "T2"

    def test_new_template_signal(self, toolbar):
        """새 템플릿 시그널"""
        mock = MagicMock()
        toolbar.template_new_requested.connect(mock)

        toolbar.btn_new_template.click()

        mock.assert_called_once()

    def test_manage_template_signal(self, toolbar):
        """템플릿 관리 시그널"""
        mock = MagicMock()
        toolbar.template_manage_requested.connect(mock)

        toolbar.btn_manage_template.click()

        mock.assert_called_once()


class TestModeGroup:
    """편집 모드 그룹 테스트"""

    def test_mode_buttons_exist(self, toolbar):
        """모드 버튼 존재"""
        assert toolbar.btn_mode_edit is not None
        assert toolbar.btn_mode_preview is not None
        assert toolbar.btn_mode_mapping is not None

    def test_mode_buttons_checkable(self, toolbar):
        """모드 버튼 체크 가능"""
        assert toolbar.btn_mode_edit.isCheckable() is True
        assert toolbar.btn_mode_preview.isCheckable() is True
        assert toolbar.btn_mode_mapping.isCheckable() is True

    def test_edit_mode_default(self, toolbar):
        """편집 모드 기본 선택"""
        assert toolbar.btn_mode_edit.isChecked() is True

    def test_mode_group_exclusive(self, toolbar):
        """모드 그룹 배타적"""
        toolbar.btn_mode_preview.setChecked(True)

        assert toolbar.btn_mode_edit.isChecked() is False
        assert toolbar.btn_mode_preview.isChecked() is True
        assert toolbar.btn_mode_mapping.isChecked() is False

    def test_mode_changed_signal(self, toolbar):
        """모드 변경 시그널"""
        mock = MagicMock()
        toolbar.mode_changed.connect(mock)

        toolbar.btn_mode_preview.click()

        mock.assert_called_with(MainToolbar.MODE_PREVIEW)

    def test_set_mode(self, toolbar):
        """모드 설정"""
        toolbar.set_mode(MainToolbar.MODE_MAPPING)

        assert toolbar.btn_mode_mapping.isChecked() is True

    def test_get_current_mode(self, toolbar):
        """현재 모드 반환"""
        toolbar.set_mode(MainToolbar.MODE_EDIT)
        assert toolbar.get_current_mode() == MainToolbar.MODE_EDIT

        toolbar.set_mode(MainToolbar.MODE_PREVIEW)
        assert toolbar.get_current_mode() == MainToolbar.MODE_PREVIEW


class TestViewGroup:
    """뷰 그룹 테스트"""

    def test_zoom_combo_exists(self, toolbar):
        """줌 콤보박스 존재"""
        assert toolbar.combo_zoom is not None

    def test_fullscreen_button_exists(self, toolbar):
        """전체화면 버튼 존재"""
        assert toolbar.btn_fullscreen is not None

    def test_zoom_default_100(self, toolbar):
        """줌 기본값 100%"""
        assert toolbar.combo_zoom.currentText() == "100%"

    def test_zoom_options(self, toolbar):
        """줌 옵션"""
        options = [toolbar.combo_zoom.itemText(i) for i in range(toolbar.combo_zoom.count())]
        assert "50%" in options
        assert "100%" in options
        assert "200%" in options

    def test_zoom_changed_signal(self, toolbar):
        """줌 변경 시그널"""
        mock = MagicMock()
        toolbar.zoom_changed.connect(mock)

        toolbar.combo_zoom.setCurrentText("150%")

        mock.assert_called_with(150)

    def test_set_zoom(self, toolbar):
        """줌 설정"""
        toolbar.set_zoom(75)
        assert toolbar.combo_zoom.currentText() == "75%"

    def test_get_current_zoom(self, toolbar):
        """현재 줌 반환"""
        toolbar.set_zoom(125)
        assert toolbar.get_current_zoom() == 125

    def test_fullscreen_signal(self, toolbar):
        """전체화면 시그널"""
        mock = MagicMock()
        toolbar.fullscreen_toggled.connect(mock)

        toolbar.btn_fullscreen.click()

        mock.assert_called_once()


class TestHelperMethods:
    """헬퍼 메서드 테스트"""

    def test_set_data_sheet_visible(self, toolbar):
        """데이터 시트 표시 상태 설정"""
        toolbar.set_data_sheet_visible(False)
        assert toolbar.btn_data_toggle.isChecked() is False

        toolbar.set_data_sheet_visible(True)
        assert toolbar.btn_data_toggle.isChecked() is True

    def test_is_data_sheet_visible(self, toolbar):
        """데이터 시트 표시 여부"""
        toolbar.btn_data_toggle.setChecked(True)
        assert toolbar.is_data_sheet_visible() is True

        toolbar.btn_data_toggle.setChecked(False)
        assert toolbar.is_data_sheet_visible() is False

    def test_set_save_enabled(self, toolbar):
        """저장 버튼 활성화/비활성화"""
        toolbar.set_save_enabled(True)
        assert toolbar.btn_save.isEnabled() is True

        toolbar.set_save_enabled(False)
        assert toolbar.btn_save.isEnabled() is False
