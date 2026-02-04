"""TT1: TemplateStorage 단위 테스트

TemplateStorage CRUD 기능을 테스트합니다.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core.template_storage import (
    TemplateStorage,
    TemplateMetadata,
    ExtendedTemplate,
)
from src.core.template_manager import TemplateError


@pytest.fixture
def temp_templates_dir():
    """임시 템플릿 디렉토리"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage_with_builtin(temp_templates_dir):
    """기본 템플릿이 있는 저장소"""
    # _builtin 디렉토리 생성
    builtin_dir = temp_templates_dir / "_builtin" / "test_template"
    builtin_dir.mkdir(parents=True)

    # HTML 파일 생성
    html_path = builtin_dir / "test.html"
    html_path.write_text("<html><body>{{ title }}</body></html>")

    # mapping.json 생성
    mapping_path = builtin_dir / "test.mapping.json"
    mapping_path.write_text("""{
        "name": "Test Template",
        "version": "1.0",
        "type": "html",
        "fields": [{"id": "title", "label": "제목", "excel_column": "Title"}]
    }""")

    return TemplateStorage(temp_templates_dir)


class TestTemplateMetadata:
    """TemplateMetadata 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        meta = TemplateMetadata(
            id="test-id",
            name="Test",
            version="1.0",
            description="Test description",
        )
        data = meta.to_dict()

        assert data["id"] == "test-id"
        assert data["name"] == "Test"
        assert data["version"] == "1.0"
        assert data["description"] == "Test description"
        assert "created_at" in data
        assert "updated_at" in data

    def test_from_dict(self):
        """딕셔너리에서 생성 테스트"""
        data = {
            "id": "test-id",
            "name": "Test",
            "version": "2.0",
            "description": "From dict",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-02T00:00:00",
        }
        meta = TemplateMetadata.from_dict(data)

        assert meta.id == "test-id"
        assert meta.name == "Test"
        assert meta.version == "2.0"
        assert meta.description == "From dict"


class TestTemplateStorageInit:
    """TemplateStorage 초기화 테스트"""

    def test_creates_directories(self, temp_templates_dir):
        """디렉토리 자동 생성 테스트"""
        storage = TemplateStorage(temp_templates_dir)

        assert (temp_templates_dir / "_builtin").exists()
        assert (temp_templates_dir / "user").exists()

    def test_scans_builtin_templates(self, storage_with_builtin):
        """기본 템플릿 스캔 테스트"""
        templates = storage_with_builtin.get_builtin_templates()

        assert len(templates) == 1
        assert templates[0].name == "Test Template"
        assert templates[0].is_builtin is True
        assert templates[0].is_readonly is True


class TestTemplateStorageRead:
    """TemplateStorage 읽기 테스트"""

    def test_get_all_templates(self, storage_with_builtin):
        """전체 템플릿 조회"""
        templates = storage_with_builtin.get_all_templates()
        assert len(templates) >= 1

    def test_get_builtin_templates(self, storage_with_builtin):
        """기본 템플릿 조회"""
        templates = storage_with_builtin.get_builtin_templates()
        assert all(t.is_builtin for t in templates)

    def test_get_user_templates_empty(self, storage_with_builtin):
        """사용자 템플릿 조회 (초기 상태)"""
        templates = storage_with_builtin.get_user_templates()
        assert len(templates) == 0

    def test_get_template_by_id(self, storage_with_builtin):
        """ID로 템플릿 조회"""
        template = storage_with_builtin.get_template("test_template")
        assert template is not None
        assert template.name == "Test Template"

    def test_get_template_not_found(self, storage_with_builtin):
        """존재하지 않는 템플릿 조회"""
        template = storage_with_builtin.get_template("nonexistent")
        assert template is None

    def test_get_template_by_name(self, storage_with_builtin):
        """이름으로 템플릿 조회"""
        template = storage_with_builtin.get_template_by_name("Test Template")
        assert template is not None
        assert template.id == "test_template"


class TestTemplateStorageCreate:
    """TemplateStorage 생성 테스트"""

    def test_create_template(self, storage_with_builtin):
        """템플릿 생성"""
        new_template = storage_with_builtin.create_template(
            name="New Template",
            html_content="<html><body>{{ content }}</body></html>",
            fields=[{"id": "content", "label": "내용", "excel_column": "Content"}],
            description="A new template",
        )

        assert new_template is not None
        assert new_template.name == "New Template"
        assert new_template.is_builtin is False
        assert new_template.is_readonly is False
        assert len(new_template.id) == 8  # UUID의 처음 8자

    def test_create_template_appears_in_user_list(self, storage_with_builtin):
        """생성된 템플릿이 사용자 목록에 나타남"""
        storage_with_builtin.create_template(
            name="User Template",
            html_content="<html></html>",
            fields=[],
        )

        user_templates = storage_with_builtin.get_user_templates()
        assert len(user_templates) == 1
        assert user_templates[0].name == "User Template"


class TestTemplateStorageCopy:
    """TemplateStorage 복사 테스트"""

    def test_copy_builtin_template(self, storage_with_builtin):
        """기본 템플릿 복사"""
        copied = storage_with_builtin.copy_template(
            "test_template", "Copied Template"
        )

        assert copied is not None
        assert copied.name == "Copied Template"
        assert copied.is_builtin is False
        assert copied.metadata.based_on == "test_template"

    def test_copy_nonexistent_template(self, storage_with_builtin):
        """존재하지 않는 템플릿 복사"""
        with pytest.raises(TemplateError):
            storage_with_builtin.copy_template("nonexistent", "Copy")


class TestTemplateStorageUpdate:
    """TemplateStorage 업데이트 테스트"""

    def test_update_user_template(self, storage_with_builtin):
        """사용자 템플릿 업데이트"""
        # 먼저 템플릿 생성
        template = storage_with_builtin.create_template(
            name="Original",
            html_content="<html></html>",
            fields=[],
        )

        # 업데이트
        updated = storage_with_builtin.update_template(
            template.id,
            name="Updated Name",
            description="Updated description",
        )

        assert updated.name == "Updated Name"

    def test_update_builtin_template_fails(self, storage_with_builtin):
        """기본 템플릿 업데이트 실패"""
        with pytest.raises(TemplateError):
            storage_with_builtin.update_template(
                "test_template", name="New Name"
            )


class TestTemplateStorageDelete:
    """TemplateStorage 삭제 테스트"""

    def test_delete_user_template(self, storage_with_builtin):
        """사용자 템플릿 삭제"""
        template = storage_with_builtin.create_template(
            name="To Delete",
            html_content="<html></html>",
            fields=[],
        )

        result = storage_with_builtin.delete_template(template.id)
        assert result is True

        # 삭제 확인
        assert storage_with_builtin.get_template(template.id) is None

    def test_delete_builtin_template_fails(self, storage_with_builtin):
        """기본 템플릿 삭제 실패"""
        with pytest.raises(TemplateError):
            storage_with_builtin.delete_template("test_template")

    def test_delete_nonexistent_template(self, storage_with_builtin):
        """존재하지 않는 템플릿 삭제"""
        with pytest.raises(TemplateError):
            storage_with_builtin.delete_template("nonexistent")


class TestTemplateStorageExportImport:
    """TemplateStorage 내보내기/가져오기 테스트"""

    def test_export_template(self, storage_with_builtin, tmp_path):
        """템플릿 내보내기"""
        export_path = tmp_path / "exported.zip"
        result = storage_with_builtin.export_template("test_template", export_path)

        assert result is True
        assert export_path.exists()

    def test_import_template(self, storage_with_builtin, tmp_path):
        """템플릿 가져오기"""
        # 먼저 내보내기
        export_path = tmp_path / "to_import.zip"
        storage_with_builtin.export_template("test_template", export_path)

        # 가져오기
        imported = storage_with_builtin.import_template(export_path, "Imported")

        assert imported is not None
        assert imported.name == "Imported"
        assert imported.is_builtin is False


class TestTemplateStorageRefresh:
    """TemplateStorage 새로고침 테스트"""

    def test_refresh(self, storage_with_builtin):
        """새로고침 테스트"""
        initial_count = len(storage_with_builtin.get_all_templates())

        storage_with_builtin.refresh()

        assert len(storage_with_builtin.get_all_templates()) == initial_count
