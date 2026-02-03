"""MainWindow UI 테스트"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


@pytest.fixture(scope="session")
def qapp():
    """PyQt6 애플리케이션 인스턴스"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp):
    """MainWindow 인스턴스"""
    from src.ui.main_window import MainWindow

    window = MainWindow()
    yield window
    window.close()


class TestMainWindow:
    """MainWindow UI 테스트"""

    def test_window_opens(self, main_window):
        """윈도우 열기"""
        main_window.show()
        assert main_window.isVisible()

    def test_window_title(self, main_window):
        """윈도우 타이틀"""
        assert "Document Creator" in main_window.windowTitle()

    def test_window_minimum_size(self, main_window):
        """윈도우 최소 크기"""
        assert main_window.minimumWidth() >= 1000
        assert main_window.minimumHeight() >= 700

    def test_menu_bar_exists(self, main_window):
        """메뉴바 존재"""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None

    def test_file_menu_exists(self, main_window):
        """파일 메뉴 존재"""
        menu_bar = main_window.menuBar()
        actions = menu_bar.actions()
        menu_titles = [a.text() for a in actions]

        # 파일 메뉴 확인 (한글 또는 영어)
        assert any("파일" in t or "File" in t for t in menu_titles)

    def test_file_menu_has_open_action(self, main_window):
        """파일 메뉴에 열기 액션"""
        file_menu = main_window._file_menu
        action_texts = [a.text() for a in file_menu.actions()]

        assert any("열기" in t or "Open" in t for t in action_texts)

    def test_file_menu_has_exit_action(self, main_window):
        """파일 메뉴에 종료 액션"""
        file_menu = main_window._file_menu
        action_texts = [a.text() for a in file_menu.actions()]

        assert any("종료" in t or "Exit" in t or "Quit" in t for t in action_texts)

    def test_central_widget_exists(self, main_window):
        """중앙 위젯 존재"""
        assert main_window.centralWidget() is not None

    def test_splitter_layout(self, main_window):
        """상단/하단 분할 레이아웃"""
        from PyQt6.QtWidgets import QSplitter

        central = main_window.centralWidget()
        # 중앙 위젯 내에 스플리터가 있어야 함
        splitter = central.findChild(QSplitter)
        assert splitter is not None

    def test_status_bar_exists(self, main_window):
        """상태바 존재"""
        status_bar = main_window.statusBar()
        assert status_bar is not None

    def test_export_button_exists(self, main_window):
        """내보내기 버튼 존재"""
        assert hasattr(main_window, "_export_button")
        assert main_window._export_button is not None

    def test_export_button_initially_disabled(self, main_window):
        """내보내기 버튼 초기 비활성화"""
        assert not main_window._export_button.isEnabled()
