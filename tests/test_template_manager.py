"""TemplateManager 단위 테스트"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def test_templates_dir(tmp_path):
    """테스트용 템플릿 디렉토리 생성"""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # RULA 템플릿 (HTML)
    rula_dir = templates_dir / "rula"
    rula_dir.mkdir()
    (rula_dir / "rula.html").write_text("<html><body>RULA Template</body></html>")
    (rula_dir / "rula.mapping.json").write_text(json.dumps({
        "name": "RULA",
        "version": "1.0",
        "type": "html",
        "fields": [
            {"id": "upper_arm", "label": "Upper Arm", "excel_column": "Upper Arm"},
            {"id": "score", "label": "Score", "excel_column": "Score"}
        ]
    }))

    # OWAS 템플릿 (이미지)
    owas_dir = templates_dir / "owas"
    owas_dir.mkdir()
    # 가짜 PNG 파일 생성
    (owas_dir / "owas.png").write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    (owas_dir / "owas.mapping.json").write_text(json.dumps({
        "name": "OWAS",
        "version": "1.0",
        "type": "image",
        "fields": [
            {"id": "back", "label": "Back", "excel_column": "Back", "position": {"x": 100, "y": 50}},
            {"id": "code", "label": "Code", "excel_column": "Code", "position": {"x": 200, "y": 100}}
        ]
    }))

    return templates_dir


@pytest.fixture
def invalid_mapping_dir(tmp_path):
    """잘못된 매핑 JSON이 있는 디렉토리"""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    bad_dir = templates_dir / "bad"
    bad_dir.mkdir()
    (bad_dir / "bad.html").write_text("<html></html>")
    (bad_dir / "bad.mapping.json").write_text("{ invalid json }")

    return templates_dir


class TestTemplateManager:
    """TemplateManager 단위 테스트"""

    def test_scan_templates_finds_all(self, test_templates_dir):
        """템플릿 디렉토리 스캔"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(test_templates_dir)
        templates = manager.get_all()

        assert len(templates) == 2
        names = [t.name for t in templates]
        assert "RULA" in names
        assert "OWAS" in names

    def test_get_template_by_name(self, test_templates_dir):
        """이름으로 템플릿 조회"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(test_templates_dir)
        template = manager.get("RULA")

        assert template is not None
        assert template.name == "RULA"
        assert template.template_type == "html"

    def test_get_nonexistent_template_returns_none(self, test_templates_dir):
        """존재하지 않는 템플릿 조회"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(test_templates_dir)
        template = manager.get("NONEXISTENT")

        assert template is None

    def test_parse_mapping_json(self, test_templates_dir):
        """mapping.json 파싱"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(test_templates_dir)
        template = manager.get("RULA")

        assert template.version == "1.0"
        assert len(template.fields) == 2
        assert template.fields[0]["id"] == "upper_arm"
        assert template.fields[0]["excel_column"] == "Upper Arm"

    def test_invalid_mapping_json_raises_error(self, invalid_mapping_dir):
        """잘못된 mapping.json 파싱 시 에러"""
        from src.core.template_manager import TemplateManager, TemplateError

        with pytest.raises(TemplateError):
            TemplateManager(invalid_mapping_dir)

    def test_template_types_html_and_image(self, test_templates_dir):
        """HTML과 이미지 템플릿 타입 구분"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(test_templates_dir)

        rula = manager.get("RULA")
        owas = manager.get("OWAS")

        assert rula.template_type == "html"
        assert owas.template_type == "image"

    def test_template_file_path(self, test_templates_dir):
        """템플릿 파일 경로 반환"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(test_templates_dir)
        rula = manager.get("RULA")

        assert rula.template_path.exists()
        assert rula.template_path.suffix == ".html"

    def test_empty_templates_directory(self, tmp_path):
        """빈 템플릿 디렉토리 처리"""
        from src.core.template_manager import TemplateManager

        empty_dir = tmp_path / "empty_templates"
        empty_dir.mkdir()

        manager = TemplateManager(empty_dir)
        templates = manager.get_all()

        assert len(templates) == 0

    def test_template_names_property(self, test_templates_dir):
        """템플릿 이름 목록 반환"""
        from src.core.template_manager import TemplateManager

        manager = TemplateManager(test_templates_dir)
        names = manager.template_names

        assert isinstance(names, list)
        assert "RULA" in names
        assert "OWAS" in names
