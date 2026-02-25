"""매핑 편집기 테스트

Phase 1: 필드 목록 인덱스 표시
"""

import pytest
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QHeaderView
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
