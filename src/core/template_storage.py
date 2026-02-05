"""템플릿 저장소 모듈

기본(builtin) 템플릿과 사용자(user) 템플릿을 분리하여 관리합니다.
"""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .template_manager import Template, TemplateError


@dataclass
class TemplateMetadata:
    """템플릿 메타데이터"""

    id: str
    name: str
    version: str = "1.0"
    description: str = ""
    based_on: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "based_on": self.based_on,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateMetadata":
        """딕셔너리에서 생성"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown"),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            based_on=data.get("based_on"),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
        )


@dataclass
class ExtendedTemplate(Template):
    """확장 템플릿 (메타데이터 포함)"""

    id: str = ""
    is_builtin: bool = True
    is_readonly: bool = True
    metadata: Optional[TemplateMetadata] = None

    @classmethod
    def from_template(
        cls,
        template: Template,
        template_id: str,
        is_builtin: bool = True,
        metadata: Optional[TemplateMetadata] = None,
    ) -> "ExtendedTemplate":
        """기존 Template에서 ExtendedTemplate 생성"""
        return cls(
            name=template.name,
            version=template.version,
            template_type=template.template_type,
            template_path=template.template_path,
            mapping_path=template.mapping_path,
            fields=template.fields,
            safety_indicator=template.safety_indicator,
            description=template.description,
            id=template_id,
            is_builtin=is_builtin,
            is_readonly=is_builtin,
            metadata=metadata,
        )


class TemplateStorage:
    """템플릿 저장소

    기본 템플릿과 사용자 템플릿을 분리하여 관리합니다.

    디렉토리 구조:
        templates/
        ├── _builtin/          # 기본 템플릿 (읽기 전용)
        │   └── owas/
        │       ├── owas.html
        │       └── owas.mapping.json
        └── user/              # 사용자 템플릿
            └── {uuid}/
                ├── template.html
                ├── mapping.json
                └── meta.json
    """

    BUILTIN_DIR = "_builtin"
    USER_DIR = "user"

    def __init__(self, templates_dir: Path):
        """
        Args:
            templates_dir: 템플릿 루트 디렉토리 경로
        """
        self._root = Path(templates_dir)
        self._builtin_dir = self._root / self.BUILTIN_DIR
        self._user_dir = self._root / self.USER_DIR

        # 디렉토리 생성
        self._builtin_dir.mkdir(parents=True, exist_ok=True)
        self._user_dir.mkdir(parents=True, exist_ok=True)

        # 템플릿 캐시
        self._templates: Dict[str, ExtendedTemplate] = {}
        self._scan_all()

    def _scan_all(self) -> None:
        """모든 템플릿 스캔"""
        self._templates.clear()
        self._scan_builtin_templates()
        self._scan_user_templates()

    def _scan_builtin_templates(self) -> None:
        """기본 템플릿 스캔"""
        if not self._builtin_dir.exists():
            return

        for template_dir in self._builtin_dir.iterdir():
            if not template_dir.is_dir() or template_dir.name.startswith("."):
                continue

            mapping_files = list(template_dir.glob("*.mapping.json"))
            if not mapping_files:
                continue

            try:
                template = Template.from_mapping_file(mapping_files[0])
                template_id = template_dir.name  # 폴더명을 ID로 사용
                extended = ExtendedTemplate.from_template(
                    template, template_id, is_builtin=True
                )
                self._templates[template_id] = extended
            except TemplateError:
                continue

    def _scan_user_templates(self) -> None:
        """사용자 템플릿 스캔"""
        if not self._user_dir.exists():
            return

        for template_dir in self._user_dir.iterdir():
            if not template_dir.is_dir() or template_dir.name.startswith("."):
                continue

            mapping_path = template_dir / "mapping.json"
            meta_path = template_dir / "meta.json"

            if not mapping_path.exists():
                continue

            try:
                template = Template.from_mapping_file(mapping_path)
                template_id = template_dir.name

                # 메타데이터 로드
                metadata = None
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        metadata = TemplateMetadata.from_dict(json.load(f))

                extended = ExtendedTemplate.from_template(
                    template, template_id, is_builtin=False, metadata=metadata
                )
                extended.is_readonly = False
                self._templates[template_id] = extended
            except (TemplateError, json.JSONDecodeError):
                continue

    # ========== Read Operations ==========

    def get_builtin_templates(self) -> List[ExtendedTemplate]:
        """기본 템플릿 목록 반환"""
        return [t for t in self._templates.values() if t.is_builtin]

    def get_user_templates(self) -> List[ExtendedTemplate]:
        """사용자 템플릿 목록 반환"""
        return [t for t in self._templates.values() if not t.is_builtin]

    def get_all_templates(self) -> List[ExtendedTemplate]:
        """모든 템플릿 반환"""
        return list(self._templates.values())

    def get_template(self, template_id: str) -> Optional[ExtendedTemplate]:
        """ID로 템플릿 조회"""
        return self._templates.get(template_id)

    def get_template_by_name(self, name: str) -> Optional[ExtendedTemplate]:
        """이름으로 템플릿 조회 (첫 번째 매칭)"""
        for template in self._templates.values():
            if template.name == name:
                return template
        return None

    # ========== Create Operations ==========

    def create_template(
        self,
        name: str,
        html_content: str,
        fields: List[Dict[str, Any]],
        description: str = "",
        based_on: Optional[str] = None,
    ) -> ExtendedTemplate:
        """새 사용자 템플릿 생성

        Args:
            name: 템플릿 이름
            html_content: HTML 내용
            fields: 필드 정의 목록
            description: 설명
            based_on: 기반 템플릿 ID

        Returns:
            생성된 템플릿

        Raises:
            TemplateError: 생성 실패 시
        """
        template_id = str(uuid.uuid4())[:8]
        template_dir = self._user_dir / template_id
        template_dir.mkdir(parents=True, exist_ok=True)

        try:
            # HTML 파일 저장
            html_path = template_dir / "template.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # mapping.json 저장
            mapping_path = template_dir / "mapping.json"
            mapping_data = {
                "name": name,
                "version": "1.0",
                "type": "html",
                "description": description,
                "fields": fields,
            }
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping_data, f, ensure_ascii=False, indent=2)

            # meta.json 저장
            now = datetime.now()
            metadata = TemplateMetadata(
                id=template_id,
                name=name,
                version="1.0",
                description=description,
                based_on=based_on,
                created_at=now,
                updated_at=now,
            )
            meta_path = template_dir / "meta.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

            # 캐시에 추가
            template = Template.from_mapping_file(mapping_path)
            extended = ExtendedTemplate.from_template(
                template, template_id, is_builtin=False, metadata=metadata
            )
            extended.is_readonly = False
            self._templates[template_id] = extended

            return extended

        except Exception as e:
            # 실패 시 디렉토리 정리
            if template_dir.exists():
                shutil.rmtree(template_dir)
            raise TemplateError(f"템플릿 생성 실패: {e}")

    def copy_template(
        self, src_id: str, new_name: str, description: str = ""
    ) -> ExtendedTemplate:
        """템플릿 복사

        Args:
            src_id: 원본 템플릿 ID
            new_name: 새 템플릿 이름
            description: 설명

        Returns:
            복사된 템플릿

        Raises:
            TemplateError: 복사 실패 시
        """
        src_template = self.get_template(src_id)
        if src_template is None:
            raise TemplateError(f"템플릿을 찾을 수 없습니다: {src_id}")

        # HTML 내용 읽기
        with open(src_template.template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return self.create_template(
            name=new_name,
            html_content=html_content,
            fields=src_template.fields.copy(),
            description=description,
            based_on=src_id,
        )

    # ========== Update Operations ==========

    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        html_content: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
    ) -> ExtendedTemplate:
        """템플릿 업데이트

        Args:
            template_id: 템플릿 ID
            name: 새 이름 (None이면 유지)
            html_content: 새 HTML 내용 (None이면 유지)
            fields: 새 필드 정의 (None이면 유지)
            description: 새 설명 (None이면 유지)

        Returns:
            업데이트된 템플릿

        Raises:
            TemplateError: 업데이트 실패 시
        """
        template = self.get_template(template_id)
        if template is None:
            raise TemplateError(f"템플릿을 찾을 수 없습니다: {template_id}")

        if template.is_readonly:
            raise TemplateError("기본 템플릿은 수정할 수 없습니다.")

        template_dir = self._user_dir / template_id

        try:
            # HTML 업데이트
            if html_content is not None:
                with open(template.template_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

            # mapping.json 업데이트
            mapping_path = template_dir / "mapping.json"
            with open(mapping_path, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)

            if name is not None:
                mapping_data["name"] = name
            if fields is not None:
                mapping_data["fields"] = fields
            if description is not None:
                mapping_data["description"] = description

            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping_data, f, ensure_ascii=False, indent=2)

            # meta.json 업데이트
            meta_path = template_dir / "meta.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
            else:
                meta_data = {"id": template_id}

            if name is not None:
                meta_data["name"] = name
            if description is not None:
                meta_data["description"] = description
            meta_data["updated_at"] = datetime.now().isoformat()

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            # 캐시 갱신
            self._scan_user_templates()
            return self._templates[template_id]

        except Exception as e:
            raise TemplateError(f"템플릿 업데이트 실패: {e}")

    def update_template_name(self, template_id: str, name: str) -> None:
        """템플릿 이름 업데이트

        Args:
            template_id: 템플릿 ID
            name: 새 이름
        """
        self.update_template(template_id, name=name)

    def update_template_description(self, template_id: str, description: str) -> None:
        """템플릿 설명 업데이트

        Args:
            template_id: 템플릿 ID
            description: 새 설명
        """
        self.update_template(template_id, description=description)

    def update_template_active(self, template_id: str, is_active: bool) -> None:
        """템플릿 활성화 상태 업데이트

        Args:
            template_id: 템플릿 ID
            is_active: 활성화 여부
        """
        template = self.get_template(template_id)
        if template is None:
            raise TemplateError(f"템플릿을 찾을 수 없습니다: {template_id}")

        if template.is_readonly:
            raise TemplateError("기본 템플릿은 수정할 수 없습니다.")

        template_dir = self._user_dir / template_id
        meta_path = template_dir / "meta.json"

        try:
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
            else:
                meta_data = {"id": template_id}

            meta_data["is_active"] = is_active
            meta_data["updated_at"] = datetime.now().isoformat()

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            # 캐시 갱신
            self._scan_user_templates()

        except Exception as e:
            raise TemplateError(f"템플릿 활성화 상태 업데이트 실패: {e}")

    # ========== Delete Operations ==========

    def delete_template(self, template_id: str) -> bool:
        """템플릿 삭제

        Args:
            template_id: 템플릿 ID

        Returns:
            성공 여부

        Raises:
            TemplateError: 삭제 실패 시
        """
        template = self.get_template(template_id)
        if template is None:
            raise TemplateError(f"템플릿을 찾을 수 없습니다: {template_id}")

        if template.is_builtin:
            raise TemplateError("기본 템플릿은 삭제할 수 없습니다.")

        template_dir = self._user_dir / template_id
        if template_dir.exists():
            shutil.rmtree(template_dir)

        del self._templates[template_id]
        return True

    # ========== Export/Import Operations ==========

    def export_template(self, template_id: str, export_path: Path) -> bool:
        """템플릿 내보내기 (ZIP)

        Args:
            template_id: 템플릿 ID
            export_path: 내보낼 경로 (.zip)

        Returns:
            성공 여부
        """
        template = self.get_template(template_id)
        if template is None:
            raise TemplateError(f"템플릿을 찾을 수 없습니다: {template_id}")

        if template.is_builtin:
            template_dir = self._builtin_dir / template_id
        else:
            template_dir = self._user_dir / template_id

        # ZIP 생성
        export_path = Path(export_path)
        if export_path.suffix.lower() != ".zip":
            export_path = export_path.with_suffix(".zip")

        shutil.make_archive(
            str(export_path.with_suffix("")), "zip", template_dir.parent, template_dir.name
        )
        return True

    def import_template(self, import_path: Path, new_name: Optional[str] = None) -> ExtendedTemplate:
        """템플릿 가져오기 (ZIP)

        Args:
            import_path: 가져올 ZIP 파일 경로
            new_name: 새 이름 (None이면 원본 이름 사용)

        Returns:
            가져온 템플릿

        Raises:
            TemplateError: 가져오기 실패 시
        """
        import tempfile
        import zipfile

        if not import_path.exists():
            raise TemplateError(f"파일을 찾을 수 없습니다: {import_path}")

        # 임시 디렉토리에 압축 해제
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with zipfile.ZipFile(import_path, "r") as zf:
                zf.extractall(temp_path)

            # 압축 해제된 디렉토리 찾기
            extracted_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
            if not extracted_dirs:
                # 파일이 루트에 직접 있는 경우
                extracted_dir = temp_path
            else:
                extracted_dir = extracted_dirs[0]

            # mapping.json 찾기
            mapping_files = list(extracted_dir.glob("*.mapping.json")) + list(
                extracted_dir.glob("mapping.json")
            )
            if not mapping_files:
                raise TemplateError("유효한 템플릿이 아닙니다: mapping.json을 찾을 수 없습니다.")

            # HTML 파일 찾기
            html_files = list(extracted_dir.glob("*.html"))
            if not html_files:
                raise TemplateError("유효한 템플릿이 아닙니다: HTML 파일을 찾을 수 없습니다.")

            # 템플릿 생성
            with open(html_files[0], "r", encoding="utf-8") as f:
                html_content = f.read()

            with open(mapping_files[0], "r", encoding="utf-8") as f:
                mapping_data = json.load(f)

            name = new_name or mapping_data.get("name", "Imported Template")
            fields = mapping_data.get("fields", [])
            description = mapping_data.get("description", "")

            return self.create_template(
                name=name,
                html_content=html_content,
                fields=fields,
                description=description,
            )

    def refresh(self) -> None:
        """캐시 새로고침"""
        self._scan_all()
