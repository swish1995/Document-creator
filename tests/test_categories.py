"""카테고리 설정 파일 로드 테스트 (Phase 1.2)"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def templates_dir_with_categories(tmp_path):
    """_categories.json이 있는 templates 디렉토리"""
    templates_dir = tmp_path / "templates"
    builtin_dir = templates_dir / "_builtin"
    builtin_dir.mkdir(parents=True)

    # _categories.json 생성
    categories = {
        "categories": [
            {
                "id": "ergonomic",
                "name": "인체공학 평가",
                "description": "RULA, REBA, OWAS 등",
                "sort_order": 1,
            },
            {
                "id": "inspection",
                "name": "점검 보고서",
                "description": "일일/정기 안전 점검",
                "sort_order": 2,
            },
        ]
    }
    (builtin_dir / "_categories.json").write_text(
        json.dumps(categories, ensure_ascii=False)
    )

    # 템플릿 생성 (ergonomic 카테고리)
    for name in ["RULA", "REBA", "OWAS"]:
        tpl_dir = builtin_dir / name.lower()
        tpl_dir.mkdir()
        (tpl_dir / f"{name.lower()}.html").write_text("<html></html>")
        mapping = {
            "name": name,
            "version": "2.0",
            "type": "html",
            "category": "ergonomic",
            "safety_indicator": name,
            "fields": [],
        }
        (tpl_dir / f"{name.lower()}.mapping.json").write_text(json.dumps(mapping))

    # inspection 카테고리 템플릿
    insp_dir = builtin_dir / "daily-check"
    insp_dir.mkdir()
    (insp_dir / "daily-check.html").write_text("<html></html>")
    mapping = {
        "name": "Daily Check",
        "version": "1.0",
        "type": "html",
        "category": "inspection",
        "fields": [],
    }
    (insp_dir / "daily-check.mapping.json").write_text(json.dumps(mapping))

    return templates_dir


@pytest.fixture
def templates_dir_without_categories(tmp_path):
    """_categories.json이 없는 templates 디렉토리"""
    templates_dir = tmp_path / "templates"
    builtin_dir = templates_dir / "_builtin"
    builtin_dir.mkdir(parents=True)

    for name in ["RULA", "REBA"]:
        tpl_dir = builtin_dir / name.lower()
        tpl_dir.mkdir()
        (tpl_dir / f"{name.lower()}.html").write_text("<html></html>")
        mapping = {
            "name": name,
            "version": "2.0",
            "type": "html",
            "safety_indicator": name,
            "fields": [],
        }
        (tpl_dir / f"{name.lower()}.mapping.json").write_text(json.dumps(mapping))

    return templates_dir


class TestCategoriesConfig:
    """_categories.json 로드 테스트"""

    def test_load_categories_file(self, templates_dir_with_categories):
        """_categories.json 정상 로드"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(templates_dir_with_categories)
        categories = manager.categories

        assert len(categories) == 2
        assert categories[0]["id"] == "ergonomic"
        assert categories[1]["id"] == "inspection"

    def test_missing_categories_file_uses_defaults(self, templates_dir_without_categories):
        """_categories.json 없으면 에러 없이 동작"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(templates_dir_without_categories)

        # 에러 없이 동작하고 빈 카테고리 목록
        assert manager.categories == []
        # 템플릿은 정상 로드
        assert len(manager.get_all()) == 2

    def test_category_sort_order(self, templates_dir_with_categories):
        """카테고리 sort_order 기반 정렬"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(templates_dir_with_categories)
        names = manager.template_names

        # ergonomic(sort_order=1) 카테고리의 템플릿이 먼저
        ergonomic_names = {"RULA", "REBA", "OWAS"}
        inspection_names = {"Daily Check"}

        # ergonomic 템플릿들이 inspection 템플릿보다 먼저
        ergonomic_indices = [i for i, n in enumerate(names) if n in ergonomic_names]
        inspection_indices = [i for i, n in enumerate(names) if n in inspection_names]

        if ergonomic_indices and inspection_indices:
            assert max(ergonomic_indices) < min(inspection_indices)
