"""Template 클래스의 category 필드 테스트 (Phase 1.1)"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def mapping_with_category(tmp_path):
    """category 필드가 있는 mapping.json"""
    template_dir = tmp_path / "test_template"
    template_dir.mkdir()
    (template_dir / "template.html").write_text("<html></html>")

    mapping = {
        "name": "TestTemplate",
        "version": "3.0",
        "type": "html",
        "category": "ergonomic",
        "fields": [],
    }
    mapping_path = template_dir / "test.mapping.json"
    mapping_path.write_text(json.dumps(mapping))
    return mapping_path


@pytest.fixture
def mapping_with_safety_indicator(tmp_path):
    """safety_indicator만 있는 기존 mapping.json"""
    template_dir = tmp_path / "rula_legacy"
    template_dir.mkdir()
    (template_dir / "rula.html").write_text("<html></html>")

    mapping = {
        "name": "RULA",
        "version": "2.0",
        "type": "html",
        "safety_indicator": "RULA",
        "fields": [],
    }
    mapping_path = template_dir / "rula.mapping.json"
    mapping_path.write_text(json.dumps(mapping))
    return mapping_path


@pytest.fixture
def mapping_without_category_or_indicator(tmp_path):
    """category도 safety_indicator도 없는 mapping.json"""
    template_dir = tmp_path / "plain"
    template_dir.mkdir()
    (template_dir / "template.html").write_text("<html></html>")

    mapping = {
        "name": "PlainTemplate",
        "version": "1.0",
        "type": "html",
        "fields": [],
    }
    mapping_path = template_dir / "plain.mapping.json"
    mapping_path.write_text(json.dumps(mapping))
    return mapping_path


@pytest.fixture
def mapping_with_both(tmp_path):
    """category와 safety_indicator 모두 있는 mapping.json"""
    template_dir = tmp_path / "both"
    template_dir.mkdir()
    (template_dir / "template.html").write_text("<html></html>")

    mapping = {
        "name": "BothTemplate",
        "version": "2.0",
        "type": "html",
        "category": "custom_category",
        "safety_indicator": "RULA",
        "fields": [],
    }
    mapping_path = template_dir / "both.mapping.json"
    mapping_path.write_text(json.dumps(mapping))
    return mapping_path


class TestTemplateCategoryField:
    """Template 클래스의 category 필드 테스트"""

    def test_mapping_with_category_field(self, mapping_with_category):
        """category 필드가 있는 mapping.json 정상 로드"""
        from src.core.template_manager import Template

        template = Template.from_mapping_file(mapping_with_category)
        assert template.category == "ergonomic"

    def test_mapping_with_safety_indicator_fallback(self, mapping_with_safety_indicator):
        """safety_indicator만 있는 기존 mapping.json → category 자동 변환"""
        from src.core.template_manager import Template

        template = Template.from_mapping_file(mapping_with_safety_indicator)
        assert template.category == "ergonomic"

    def test_mapping_without_category_or_indicator(self, mapping_without_category_or_indicator):
        """category도 safety_indicator도 없는 경우 → None"""
        from src.core.template_manager import Template

        template = Template.from_mapping_file(mapping_without_category_or_indicator)
        assert template.category is None

    def test_category_takes_precedence_over_indicator(self, mapping_with_both):
        """category와 safety_indicator 모두 있으면 category 우선"""
        from src.core.template_manager import Template

        template = Template.from_mapping_file(mapping_with_both)
        assert template.category == "custom_category"

    def test_safety_indicator_still_available(self, mapping_with_safety_indicator):
        """하위 호환: safety_indicator 필드도 여전히 접근 가능"""
        from src.core.template_manager import Template

        template = Template.from_mapping_file(mapping_with_safety_indicator)
        assert template.safety_indicator == "RULA"
