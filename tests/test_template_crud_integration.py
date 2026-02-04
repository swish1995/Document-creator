"""TT5: 템플릿 CRUD 통합 테스트

템플릿 생성, 읽기, 업데이트, 삭제 워크플로우를 테스트합니다.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core.template_storage import TemplateStorage
from src.core.template_manager import TemplateManager, TemplateError


@pytest.fixture
def temp_templates_dir():
    """임시 템플릿 디렉토리"""
    temp_dir = tempfile.mkdtemp()

    # _builtin 디렉토리에 기본 템플릿 생성
    builtin_dir = Path(temp_dir) / "_builtin" / "sample"
    builtin_dir.mkdir(parents=True)

    html_path = builtin_dir / "sample.html"
    html_path.write_text("""<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ title }}</h1>
    <p>{{ content }}</p>
</body>
</html>""")

    mapping_path = builtin_dir / "sample.mapping.json"
    mapping_path.write_text("""{
        "name": "Sample Template",
        "version": "1.0",
        "type": "html",
        "description": "A sample template for testing",
        "fields": [
            {"id": "title", "label": "제목", "excel_column": "Title"},
            {"id": "content", "label": "내용", "excel_column": "Content"}
        ]
    }""")

    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage(temp_templates_dir):
    """TemplateStorage 인스턴스"""
    return TemplateStorage(temp_templates_dir)


@pytest.fixture
def manager(temp_templates_dir):
    """TemplateManager 인스턴스"""
    return TemplateManager(temp_templates_dir)


class TestManagerStorageSync:
    """TemplateManager와 TemplateStorage 동기화 테스트"""

    def test_manager_sees_builtin_templates(self, manager):
        """TemplateManager가 기본 템플릿을 인식"""
        templates = manager.get_all()
        assert len(templates) >= 1
        assert any(t.name == "Sample Template" for t in templates)

    def test_storage_sees_builtin_templates(self, storage):
        """TemplateStorage가 기본 템플릿을 인식"""
        templates = storage.get_builtin_templates()
        assert len(templates) >= 1
        assert any(t.name == "Sample Template" for t in templates)

    def test_both_see_same_builtin(self, manager, storage):
        """둘 다 같은 기본 템플릿 인식"""
        manager_names = {t.name for t in manager.get_all()}
        storage_names = {t.name for t in storage.get_builtin_templates()}

        assert "Sample Template" in manager_names
        assert "Sample Template" in storage_names


class TestCreateReadWorkflow:
    """생성-읽기 워크플로우 테스트"""

    def test_create_and_read_template(self, storage):
        """템플릿 생성 후 읽기"""
        # 생성
        created = storage.create_template(
            name="New Template",
            html_content="<html><body>{{ field1 }}</body></html>",
            fields=[{"id": "field1", "label": "Field 1", "excel_column": "Col1"}],
            description="A new template",
        )

        # ID로 읽기
        read = storage.get_template(created.id)

        assert read is not None
        assert read.name == "New Template"
        assert read.is_builtin is False

    def test_created_template_in_user_list(self, storage):
        """생성된 템플릿이 사용자 목록에 포함"""
        storage.create_template(
            name="User Template 1",
            html_content="<html></html>",
            fields=[],
        )

        user_templates = storage.get_user_templates()
        assert any(t.name == "User Template 1" for t in user_templates)

    def test_created_template_not_in_builtin_list(self, storage):
        """생성된 템플릿이 기본 목록에 미포함"""
        storage.create_template(
            name="User Template 2",
            html_content="<html></html>",
            fields=[],
        )

        builtin_templates = storage.get_builtin_templates()
        assert not any(t.name == "User Template 2" for t in builtin_templates)


class TestCopyWorkflow:
    """복사 워크플로우 테스트"""

    def test_copy_builtin_to_user(self, storage):
        """기본 템플릿을 사용자 템플릿으로 복사"""
        # 기본 템플릿 복사
        copied = storage.copy_template("sample", "My Custom Template")

        assert copied is not None
        assert copied.name == "My Custom Template"
        assert copied.is_builtin is False
        assert copied.is_readonly is False
        assert copied.metadata.based_on == "sample"

    def test_copy_preserves_html_content(self, storage):
        """복사 시 HTML 내용 보존"""
        original = storage.get_template("sample")
        copied = storage.copy_template("sample", "Copy of Sample")

        # HTML 내용 비교
        original_html = original.template_path.read_text()
        copied_html = copied.template_path.read_text()

        assert original_html == copied_html

    def test_copy_preserves_fields(self, storage):
        """복사 시 필드 정의 보존"""
        original = storage.get_template("sample")
        copied = storage.copy_template("sample", "Copy 2")

        assert len(copied.fields) == len(original.fields)


class TestUpdateWorkflow:
    """업데이트 워크플로우 테스트"""

    def test_update_user_template_name(self, storage):
        """사용자 템플릿 이름 업데이트"""
        template = storage.create_template(
            name="Original Name",
            html_content="<html></html>",
            fields=[],
        )

        updated = storage.update_template(template.id, name="Updated Name")

        assert updated.name == "Updated Name"

        # 다시 읽어도 업데이트됨
        reread = storage.get_template(template.id)
        assert reread.name == "Updated Name"

    def test_update_user_template_html(self, storage):
        """사용자 템플릿 HTML 업데이트"""
        template = storage.create_template(
            name="HTML Update Test",
            html_content="<html>Original</html>",
            fields=[],
        )

        storage.update_template(
            template.id, html_content="<html>Updated</html>"
        )

        # 파일 내용 확인
        updated = storage.get_template(template.id)
        content = updated.template_path.read_text()
        assert "Updated" in content

    def test_cannot_update_builtin(self, storage):
        """기본 템플릿 업데이트 불가"""
        with pytest.raises(TemplateError):
            storage.update_template("sample", name="Cannot Change")


class TestDeleteWorkflow:
    """삭제 워크플로우 테스트"""

    def test_delete_user_template(self, storage):
        """사용자 템플릿 삭제"""
        template = storage.create_template(
            name="To Delete",
            html_content="<html></html>",
            fields=[],
        )
        template_id = template.id

        # 삭제
        result = storage.delete_template(template_id)
        assert result is True

        # 더 이상 존재하지 않음
        assert storage.get_template(template_id) is None

    def test_cannot_delete_builtin(self, storage):
        """기본 템플릿 삭제 불가"""
        with pytest.raises(TemplateError):
            storage.delete_template("sample")

    def test_delete_removes_from_user_list(self, storage):
        """삭제 후 사용자 목록에서 제거"""
        template = storage.create_template(
            name="Temp",
            html_content="<html></html>",
            fields=[],
        )
        template_id = template.id

        # 삭제 전 확인
        assert any(t.id == template_id for t in storage.get_user_templates())

        storage.delete_template(template_id)

        # 삭제 후 확인
        assert not any(t.id == template_id for t in storage.get_user_templates())


class TestExportImportWorkflow:
    """내보내기/가져오기 워크플로우 테스트"""

    def test_export_import_roundtrip(self, storage, tmp_path):
        """내보내기 후 가져오기 왕복 테스트"""
        # 템플릿 생성
        original = storage.create_template(
            name="Export Test",
            html_content="<html><body>{{ data }}</body></html>",
            fields=[{"id": "data", "label": "데이터", "excel_column": "Data"}],
            description="Test export/import",
        )

        # 내보내기
        export_path = tmp_path / "export.zip"
        storage.export_template(original.id, export_path)
        assert export_path.exists()

        # 원본 삭제
        storage.delete_template(original.id)
        assert storage.get_template(original.id) is None

        # 가져오기
        imported = storage.import_template(export_path, "Imported Template")

        assert imported is not None
        assert imported.name == "Imported Template"
        assert len(imported.fields) == 1
        assert imported.fields[0]["id"] == "data"

    def test_export_builtin(self, storage, tmp_path):
        """기본 템플릿 내보내기"""
        export_path = tmp_path / "builtin_export.zip"
        result = storage.export_template("sample", export_path)

        assert result is True
        assert export_path.exists()


class TestRefreshWorkflow:
    """새로고침 워크플로우 테스트"""

    def test_refresh_after_external_change(self, storage, temp_templates_dir):
        """외부 변경 후 새로고침"""
        initial_count = len(storage.get_all_templates())

        # 외부에서 새 템플릿 디렉토리 생성
        new_template_dir = temp_templates_dir / "_builtin" / "external"
        new_template_dir.mkdir(parents=True)

        (new_template_dir / "external.html").write_text("<html></html>")
        (new_template_dir / "external.mapping.json").write_text("""{
            "name": "External Template",
            "version": "1.0",
            "type": "html",
            "fields": []
        }""")

        # 새로고침
        storage.refresh()

        # 새 템플릿 인식
        assert len(storage.get_all_templates()) == initial_count + 1
        assert any(t.name == "External Template" for t in storage.get_all_templates())
