"""템플릿 패널 카테고리 그룹핑 테스트 (Phase 3.1, 3.2)"""

import json
import pytest
from unittest.mock import MagicMock

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QStandardItemModel


@pytest.fixture(scope="module")
def app():
    """QApplication 인스턴스"""
    _app = QApplication.instance()
    if _app is None:
        _app = QApplication([])
    yield _app


@pytest.fixture
def toolbar(app):
    """MainToolbar 인스턴스"""
    from src.ui.main_toolbar import MainToolbar
    return MainToolbar()


class TestDropdownCategoryGrouping:
    """드롭다운 카테고리 그룹핑 테스트"""

    def test_set_templates_with_categories(self, toolbar):
        """카테고리가 포함된 템플릿 목록으로 드롭다운 업데이트"""
        templates = [
            ("rula", "RULA", "ergonomic"),
            ("reba", "REBA", "ergonomic"),
            ("daily", "Daily Check", "inspection"),
        ]
        categories = [
            {"id": "ergonomic", "name": "인체공학 평가", "sort_order": 1},
            {"id": "inspection", "name": "점검 보고서", "sort_order": 2},
        ]
        toolbar.set_templates_grouped(templates, categories)

        # 카테고리 헤더 + 템플릿 아이템이 존재
        combo = toolbar.combo_template
        assert combo.count() > 3  # 카테고리 헤더 포함하면 3 + 헤더 수

    def test_category_header_not_selectable(self, toolbar):
        """카테고리 헤더 아이템은 선택 불가"""
        templates = [
            ("rula", "RULA", "ergonomic"),
            ("daily", "Daily Check", "inspection"),
        ]
        categories = [
            {"id": "ergonomic", "name": "인체공학 평가", "sort_order": 1},
            {"id": "inspection", "name": "점검 보고서", "sort_order": 2},
        ]
        toolbar.set_templates_grouped(templates, categories)

        combo = toolbar.combo_template
        model = combo.model()

        # 카테고리 헤더는 enabled=False
        header_found = False
        for i in range(combo.count()):
            item = model.item(i)
            if item and not item.isEnabled():
                header_found = True
                break
        assert header_found, "카테고리 헤더(disabled 아이템)가 있어야 함"

    def test_selectable_items_have_template_id(self, toolbar):
        """선택 가능한 아이템은 template_id 데이터를 가짐"""
        templates = [
            ("rula", "RULA", "ergonomic"),
        ]
        categories = [
            {"id": "ergonomic", "name": "인체공학 평가", "sort_order": 1},
        ]
        toolbar.set_templates_grouped(templates, categories)

        combo = toolbar.combo_template
        # template_id 데이터가 있는 아이템 찾기
        found = False
        for i in range(combo.count()):
            if combo.itemData(i) == "rula":
                found = True
                break
        assert found, "RULA 템플릿의 itemData가 'rula'여야 함"

    def test_templates_without_category_in_etc_group(self, toolbar):
        """카테고리 없는 템플릿은 '기타' 그룹"""
        templates = [
            ("rula", "RULA", "ergonomic"),
            ("custom", "Custom Report", None),
        ]
        categories = [
            {"id": "ergonomic", "name": "인체공학 평가", "sort_order": 1},
        ]
        toolbar.set_templates_grouped(templates, categories)

        combo = toolbar.combo_template
        # "기타" 그룹에 Custom Report가 있어야 함 (들여쓰기 포함)
        texts = [combo.itemText(i).strip() for i in range(combo.count())]
        assert "Custom Report" in texts


class TestCategoryFilter:
    """카테고리 필터 위젯 테스트"""

    def test_filter_combo_exists(self, toolbar):
        """카테고리 필터 콤보박스 존재"""
        assert hasattr(toolbar, "combo_category_filter")

    def test_filter_has_all_option(self, toolbar):
        """'전체' 옵션 존재"""
        templates = [
            ("rula", "RULA", "ergonomic"),
        ]
        categories = [
            {"id": "ergonomic", "name": "인체공학 평가", "sort_order": 1},
        ]
        toolbar.set_templates_grouped(templates, categories)

        combo = toolbar.combo_category_filter
        texts = [combo.itemText(i) for i in range(combo.count())]
        assert "전체" in texts

    def test_filter_has_category_options(self, toolbar):
        """카테고리 옵션들이 있음"""
        templates = [
            ("rula", "RULA", "ergonomic"),
            ("daily", "Daily Check", "inspection"),
        ]
        categories = [
            {"id": "ergonomic", "name": "인체공학 평가", "sort_order": 1},
            {"id": "inspection", "name": "점검 보고서", "sort_order": 2},
        ]
        toolbar.set_templates_grouped(templates, categories)

        combo = toolbar.combo_category_filter
        texts = [combo.itemText(i) for i in range(combo.count())]
        assert "인체공학 평가" in texts
        assert "점검 보고서" in texts
