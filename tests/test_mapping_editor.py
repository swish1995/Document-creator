"""매핑 편집기 테스트

Phase 1: 필드 목록 인덱스 표시
Phase 2: 인라인 매핑 편집 + 데이터 시트 컬럼 하이라이트
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from PyQt6.QtWidgets import QApplication, QHeaderView, QComboBox
from PyQt6.QtCore import Qt

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


# ============================================================
# Phase 1: 필드 목록 인덱스 표시
# ============================================================


class TestFieldListIndexColumn:
    """T1.1: 인덱스 컬럼 존재 확인"""

    def test_field_tree_has_three_columns(self, editor):
        """필드 목록 트리에 3개 컬럼(#, 라벨, 엑셀 컬럼)이 존재해야 한다"""
        assert editor._field_tree.columnCount() == 3

    def test_field_tree_header_labels(self, editor):
        """트리 헤더 라벨이 'idx', '라벨', '엑셀 컬럼'이어야 한다"""
        header = editor._field_tree.headerItem()
        assert header.text(0) == "idx"
        assert header.text(1) == "라벨"
        assert header.text(2) == "엑셀 컬럼"


class TestFieldListIndexValue:
    """T1.2: 인덱스 값 표시"""

    def test_excel_index_displayed(self, editor):
        """excel_index 값이 # 컬럼에 표시되어야 한다"""
        fields = [
            {"id": "test", "label": "테스트", "excel_column": "A", "excel_index": 5}
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        item = editor._field_tree.topLevelItem(0)
        assert item.text(0) == "5"
        assert item.text(1) == "테스트"
        assert item.text(2) == "A"

    def test_multiple_fields_index(self, editor):
        """여러 필드의 인덱스가 각각 올바르게 표시되어야 한다"""
        fields = [
            {"id": "f1", "label": "이름", "excel_column": "A", "excel_index": 0},
            {"id": "f2", "label": "나이", "excel_column": "B", "excel_index": 3},
            {"id": "f3", "label": "점수", "excel_column": "C", "excel_index": 7},
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        assert editor._field_tree.topLevelItem(0).text(0) == "0"
        assert editor._field_tree.topLevelItem(1).text(0) == "3"
        assert editor._field_tree.topLevelItem(2).text(0) == "7"


class TestFieldListIndexMissing:
    """T1.3: 인덱스 없는 필드 처리"""

    def test_no_excel_index_shows_empty(self, editor):
        """excel_index가 없는 필드는 빈 문자열로 표시되어야 한다"""
        fields = [
            {"id": "test", "label": "테스트", "excel_column": "A"}
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        item = editor._field_tree.topLevelItem(0)
        assert item.text(0) == ""
        assert item.text(1) == "테스트"
        assert item.text(2) == "A"


class TestFieldListColumnWidth:
    """T1.3 추가: 컬럼 너비 설정 확인"""

    def test_index_column_width(self, editor):
        """# 컬럼 너비가 35px로 고정되어야 한다"""
        assert editor._field_tree.columnWidth(0) == 45

    def test_label_column_resize_mode(self, editor):
        """라벨 컬럼은 Interactive 모드여야 한다"""
        header = editor._field_tree.header()
        assert header.sectionResizeMode(1) == QHeaderView.ResizeMode.Interactive

    def test_excel_column_stretch(self, editor):
        """엑셀 컬럼은 Stretch(마지막 컬럼)여야 한다"""
        header = editor._field_tree.header()
        assert header.stretchLastSection() is True


# ============================================================
# Phase 2: 인라인 매핑 편집 + 데이터 시트 컬럼 하이라이트
# ============================================================


class TestSetExcelHeaders:
    """T2.1: 엑셀 헤더 설정"""

    def test_set_excel_headers(self, editor):
        """set_excel_headers()로 헤더 목록이 저장되어야 한다"""
        editor.set_excel_headers(["Name", "Age", "Score"])
        assert editor._excel_headers == ["Name", "Age", "Score"]

    def test_set_excel_headers_empty(self, editor):
        """빈 헤더 목록도 설정 가능해야 한다"""
        editor.set_excel_headers([])
        assert editor._excel_headers == []


class TestComboBoxCreation:
    """T2.2: ComboBox 생성"""

    def test_combobox_in_excel_column_cell(self, editor):
        """엑셀 헤더가 있을 때 '엑셀 컬럼' 셀에 QComboBox가 존재해야 한다"""
        editor.set_excel_headers(["Name", "Age", "Score"])
        fields = [
            {"id": "f1", "label": "이름", "excel_column": "Name", "excel_index": 0}
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        item = editor._field_tree.topLevelItem(0)
        widget = editor._field_tree.itemWidget(item, 2)  # 엑셀 컬럼 = 컬럼 2
        assert isinstance(widget, QComboBox)

    def test_combobox_items(self, editor):
        """ComboBox에 엑셀 헤더 목록이 아이템으로 들어가야 한다"""
        editor.set_excel_headers(["Name", "Age", "Score"])
        fields = [
            {"id": "f1", "label": "이름", "excel_column": "Name", "excel_index": 0}
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        item = editor._field_tree.topLevelItem(0)
        combo = editor._field_tree.itemWidget(item, 2)
        items = [combo.itemText(i) for i in range(combo.count())]
        assert items == ["Name", "Age", "Score"]

    def test_combobox_current_selection(self, editor):
        """ComboBox의 현재 선택이 매핑된 컬럼이어야 한다"""
        editor.set_excel_headers(["Name", "Age", "Score"])
        fields = [
            {"id": "f1", "label": "이름", "excel_column": "Age", "excel_index": 1}
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        item = editor._field_tree.topLevelItem(0)
        combo = editor._field_tree.itemWidget(item, 2)
        assert combo.currentText() == "Age"


class TestComboBoxDirtyFlag:
    """T2.3: ComboBox 변경 시 dirty 플래그"""

    def test_dirty_flag_on_change(self, editor):
        """ComboBox 변경 시 _dirty 플래그가 True가 되어야 한다"""
        editor.set_excel_headers(["Name", "Age", "Score"])
        fields = [
            {"id": "f1", "label": "이름", "excel_column": "Name", "excel_index": 0}
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        assert editor._dirty is False

        item = editor._field_tree.topLevelItem(0)
        combo = editor._field_tree.itemWidget(item, 2)
        combo.setCurrentText("Age")

        assert editor._dirty is True


class TestComboBoxDisabledWithoutHeaders:
    """T2.4: 엑셀 미로드 시 ComboBox 비활성화"""

    def test_no_combobox_without_headers(self, editor):
        """엑셀 헤더가 없으면 ComboBox 없이 텍스트만 표시되어야 한다"""
        editor.set_excel_headers([])
        fields = [
            {"id": "f1", "label": "이름", "excel_column": "Name", "excel_index": 0}
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        item = editor._field_tree.topLevelItem(0)
        widget = editor._field_tree.itemWidget(item, 2)
        assert widget is None  # ComboBox 없음
        assert item.text(2) == "Name"  # 텍스트로 표시


class TestColumnHighlightSignal:
    """T2.5~T2.7: 데이터 시트 컬럼 하이라이트 시그널"""

    def test_signal_exists(self, editor):
        """column_highlight_requested 시그널이 존재해야 한다"""
        assert hasattr(editor, 'column_highlight_requested')

    def test_field_click_emits_signal(self, editor):
        """필드 목록 행 클릭 시 column_highlight_requested 시그널이 emit되어야 한다"""
        mock = MagicMock()
        editor.column_highlight_requested.connect(mock)

        fields = [
            {"id": "f1", "label": "상박점수", "excel_column": "Base", "excel_index": 5}
        ]
        editor.set_excel_headers(["A", "B", "C", "D", "E", "Base"])
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        # 행 클릭 시뮬레이션
        item = editor._field_tree.topLevelItem(0)
        editor._on_field_clicked(item, 0)

        mock.assert_called_with(5)

    def test_combobox_change_emits_signal(self, editor):
        """ComboBox 변경 시 새 인덱스로 column_highlight_requested 시그널이 emit되어야 한다"""
        mock = MagicMock()
        editor.column_highlight_requested.connect(mock)

        headers = ["Name", "Age", "Score"]
        editor.set_excel_headers(headers)
        fields = [
            {"id": "f1", "label": "이름", "excel_column": "Name", "excel_index": 0}
        ]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)

        item = editor._field_tree.topLevelItem(0)
        combo = editor._field_tree.itemWidget(item, 2)
        combo.setCurrentText("Score")

        mock.assert_called_with(2)  # Score의 인덱스 = 2


# ============================================================
# Phase 3: 저장 UI 및 다이얼로그
# ============================================================


class TestSaveButtonBar:
    """T3.1~T3.3: 저장 버튼 바"""

    def test_save_buttons_exist(self, editor):
        """저장 버튼과 다른 이름으로 저장 버튼이 존재해야 한다"""
        assert hasattr(editor, '_btn_save')
        assert hasattr(editor, '_btn_save_as')

    def test_buttons_disabled_initially(self, editor):
        """초기 상태에서 두 버튼 모두 비활성화"""
        assert editor._btn_save.isEnabled() is False
        assert editor._btn_save_as.isEnabled() is False

    def test_builtin_save_disabled_on_dirty(self, editor):
        """빌트인 템플릿: 변경 후에도 '저장' 비활성화, '다른 이름으로 저장'만 활성화"""
        editor.set_excel_headers(["Name", "Age"])
        fields = [{"id": "f1", "label": "이름", "excel_column": "Name", "excel_index": 0}]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)
        editor._is_builtin = True

        # ComboBox 변경으로 dirty 만들기
        item = editor._field_tree.topLevelItem(0)
        combo = editor._field_tree.itemWidget(item, 2)
        combo.setCurrentText("Age")

        assert editor._btn_save.isEnabled() is False
        assert editor._btn_save_as.isEnabled() is True

    def test_user_template_both_enabled_on_dirty(self, editor):
        """사용자 템플릿: 변경 후 둘 다 활성화"""
        editor.set_excel_headers(["Name", "Age"])
        fields = [{"id": "f1", "label": "이름", "excel_column": "Name", "excel_index": 0}]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)
        editor._is_builtin = False

        item = editor._field_tree.topLevelItem(0)
        combo = editor._field_tree.itemWidget(item, 2)
        combo.setCurrentText("Age")

        assert editor._btn_save.isEnabled() is True
        assert editor._btn_save_as.isEnabled() is True

    def test_no_change_both_disabled(self, editor):
        """변경 없으면 둘 다 비활성화"""
        fields = [{"id": "f1", "label": "이름", "excel_column": "Name", "excel_index": 0}]
        editor.set_template("t", Path("/tmp/t.html"), "<html></html>", fields=fields)
        editor._is_builtin = False

        assert editor._btn_save.isEnabled() is False
        assert editor._btn_save_as.isEnabled() is False


class TestSaveAsDialog:
    """T3.4~T3.5: 다른 이름으로 저장 다이얼로그"""

    def test_save_as_dialog_exists(self):
        """SaveAsDialog 클래스가 존재해야 한다"""
        from src.ui.template_editor.save_as_dialog import SaveAsDialog
        assert SaveAsDialog is not None

    def test_dialog_default_name(self, app):
        """기본 이름이 '{원본이름}_복사본'이어야 한다"""
        from src.ui.template_editor.save_as_dialog import SaveAsDialog
        dialog = SaveAsDialog(
            original_name="RULA",
            categories=[{"id": "ergonomic", "name": "인체공학 평가"}],
            default_category="ergonomic",
        )
        assert dialog.get_name() == "RULA_복사본"

    def test_dialog_default_category(self, app):
        """기본 카테고리가 원본 카테고리여야 한다"""
        from src.ui.template_editor.save_as_dialog import SaveAsDialog
        dialog = SaveAsDialog(
            original_name="RULA",
            categories=[
                {"id": "ergonomic", "name": "인체공학 평가"},
                {"id": "inspection", "name": "점검"},
            ],
            default_category="ergonomic",
        )
        assert dialog.get_category() == "ergonomic"

    def test_dialog_duplicate_name_check(self, app):
        """중복 이름이면 is_valid()가 False여야 한다"""
        from src.ui.template_editor.save_as_dialog import SaveAsDialog
        dialog = SaveAsDialog(
            original_name="RULA",
            categories=[{"id": "ergonomic", "name": "인체공학 평가"}],
            default_category="ergonomic",
            existing_names=["RULA_TEST"],
        )
        dialog._name_input.setText("RULA_TEST")
        assert dialog.is_valid() is False

    def test_dialog_valid_name(self, app):
        """유효한 이름이면 is_valid()가 True여야 한다"""
        from src.ui.template_editor.save_as_dialog import SaveAsDialog
        dialog = SaveAsDialog(
            original_name="RULA",
            categories=[{"id": "ergonomic", "name": "인체공학 평가"}],
            default_category="ergonomic",
            existing_names=["RULA_TEST"],
        )
        assert dialog.is_valid() is True  # 기본 이름 "RULA_복사본"은 유효
