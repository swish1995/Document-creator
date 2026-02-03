"""ExcelViewer UI 테스트"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QModelIndex


@pytest.fixture(scope="session")
def qapp():
    """PyQt6 애플리케이션 인스턴스"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def excel_viewer(qapp):
    """ExcelViewer 인스턴스"""
    from src.ui.excel_viewer import ExcelViewer

    viewer = ExcelViewer()
    yield viewer
    viewer.close()


@pytest.fixture
def excel_viewer_with_data(qapp, sample_xlsx):
    """데이터가 로드된 ExcelViewer"""
    from src.ui.excel_viewer import ExcelViewer

    viewer = ExcelViewer()
    viewer.load_file(sample_xlsx)
    yield viewer
    viewer.close()


class TestExcelViewer:
    """ExcelViewer UI 테스트"""

    def test_widget_creation(self, excel_viewer):
        """위젯 생성"""
        assert excel_viewer is not None

    def test_open_file_button_exists(self, excel_viewer):
        """파일 열기 버튼 존재"""
        assert hasattr(excel_viewer, "_open_button")
        assert excel_viewer._open_button is not None

    def test_table_view_exists(self, excel_viewer):
        """테이블 뷰 존재"""
        from PyQt6.QtWidgets import QTableView

        assert hasattr(excel_viewer, "_table_view")
        assert isinstance(excel_viewer._table_view, QTableView)

    def test_load_file_displays_data(self, excel_viewer_with_data):
        """파일 로드 시 데이터 표시"""
        model = excel_viewer_with_data._table_view.model()
        assert model is not None
        assert model.rowCount() > 0
        assert model.columnCount() > 0

    def test_select_all_button_exists(self, excel_viewer):
        """전체 선택 버튼 존재"""
        assert hasattr(excel_viewer, "_select_all_button")

    def test_deselect_all_button_exists(self, excel_viewer):
        """선택 해제 버튼 존재"""
        assert hasattr(excel_viewer, "_deselect_all_button")

    def test_preview_row_dropdown_exists(self, excel_viewer):
        """미리보기 행 드롭다운 존재"""
        from PyQt6.QtWidgets import QSpinBox

        assert hasattr(excel_viewer, "_preview_row_spinbox")
        assert isinstance(excel_viewer._preview_row_spinbox, QSpinBox)

    def test_selection_count_label_exists(self, excel_viewer):
        """선택된 행 수 레이블 존재"""
        assert hasattr(excel_viewer, "_selection_count_label")

    def test_checkbox_column_exists(self, excel_viewer_with_data):
        """체크박스 컬럼 존재"""
        model = excel_viewer_with_data._table_view.model()
        # 첫 번째 컬럼이 체크박스용
        assert model.columnCount() > 1

    def test_initial_selection_empty(self, excel_viewer_with_data):
        """초기 선택 비어있음"""
        selected = excel_viewer_with_data.get_selected_rows()
        assert isinstance(selected, list)
        assert len(selected) == 0

    def test_select_all_selects_all_rows(self, excel_viewer_with_data):
        """전체 선택 시 모든 행 선택"""
        excel_viewer_with_data.select_all()
        selected = excel_viewer_with_data.get_selected_rows()
        assert len(selected) == excel_viewer_with_data.row_count

    def test_deselect_all_clears_selection(self, excel_viewer_with_data):
        """선택 해제 시 선택 초기화"""
        excel_viewer_with_data.select_all()
        excel_viewer_with_data.deselect_all()
        selected = excel_viewer_with_data.get_selected_rows()
        assert len(selected) == 0

    def test_toggle_row_selection(self, excel_viewer_with_data):
        """행 선택 토글"""
        excel_viewer_with_data.toggle_row_selection(0)
        selected = excel_viewer_with_data.get_selected_rows()
        assert 0 in selected

        excel_viewer_with_data.toggle_row_selection(0)
        selected = excel_viewer_with_data.get_selected_rows()
        assert 0 not in selected

    def test_preview_row_changed_signal(self, excel_viewer_with_data, qtbot):
        """미리보기 행 변경 시그널"""
        from PyQt6.QtCore import QSignalBlocker

        with qtbot.waitSignal(excel_viewer_with_data.preview_row_changed, timeout=1000):
            excel_viewer_with_data.set_preview_row(1)

    def test_selection_changed_signal(self, excel_viewer_with_data, qtbot):
        """선택 변경 시그널"""
        with qtbot.waitSignal(excel_viewer_with_data.selection_changed, timeout=1000):
            excel_viewer_with_data.toggle_row_selection(0)

    def test_row_count_property(self, excel_viewer_with_data):
        """행 수 속성"""
        assert excel_viewer_with_data.row_count > 0

    def test_get_preview_row(self, excel_viewer_with_data):
        """미리보기 행 가져오기"""
        excel_viewer_with_data.set_preview_row(0)
        assert excel_viewer_with_data.get_preview_row() == 0

    def test_file_loaded_signal(self, excel_viewer, sample_xlsx, qtbot):
        """파일 로드 완료 시그널"""
        with qtbot.waitSignal(excel_viewer.file_loaded, timeout=1000):
            excel_viewer.load_file(sample_xlsx)

    def test_selection_count_updates(self, excel_viewer_with_data):
        """선택 행 수 업데이트"""
        excel_viewer_with_data.select_all()
        label_text = excel_viewer_with_data._selection_count_label.text()
        assert str(excel_viewer_with_data.row_count) in label_text
