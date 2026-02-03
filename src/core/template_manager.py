"""템플릿 관리자 모듈

템플릿 파일을 스캔하고 관리합니다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


class TemplateError(Exception):
    """템플릿 관련 에러"""

    pass


@dataclass
class Template:
    """템플릿 정보"""

    name: str
    version: str
    template_type: str  # "html" or "image"
    template_path: Path
    mapping_path: Path
    fields: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_mapping_file(cls, mapping_path: Path) -> "Template":
        """매핑 파일에서 템플릿 생성

        Args:
            mapping_path: mapping.json 파일 경로

        Returns:
            Template 인스턴스

        Raises:
            TemplateError: 매핑 파일 파싱 실패 시
        """
        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise TemplateError(f"매핑 파일 파싱 실패: {mapping_path} - {e}")
        except Exception as e:
            raise TemplateError(f"매핑 파일 읽기 실패: {mapping_path} - {e}")

        name = data.get("name", "Unknown")
        version = data.get("version", "1.0")
        template_type = data.get("type", "html")
        fields = data.get("fields", [])

        # 템플릿 파일 경로 찾기
        template_dir = mapping_path.parent
        if template_type == "html":
            template_path = cls._find_file(template_dir, [".html", ".htm"])
        else:  # image
            template_path = cls._find_file(template_dir, [".png", ".jpg", ".jpeg"])

        if template_path is None:
            raise TemplateError(f"템플릿 파일을 찾을 수 없습니다: {template_dir}")

        return cls(
            name=name,
            version=version,
            template_type=template_type,
            template_path=template_path,
            mapping_path=mapping_path,
            fields=fields,
        )

    @staticmethod
    def _find_file(directory: Path, extensions: List[str]) -> Optional[Path]:
        """디렉토리에서 특정 확장자 파일 찾기"""
        for ext in extensions:
            for file in directory.glob(f"*{ext}"):
                if not file.name.endswith(".mapping.json"):
                    return file
        return None


class TemplateManager:
    """템플릿 관리자

    템플릿 디렉토리를 스캔하고 템플릿을 관리합니다.
    """

    def __init__(self, templates_dir: Path):
        """
        Args:
            templates_dir: 템플릿 디렉토리 경로

        Raises:
            TemplateError: 템플릿 로드 실패 시
        """
        self._templates_dir = Path(templates_dir)
        self._templates: Dict[str, Template] = {}
        self._scan_templates()

    def _scan_templates(self) -> None:
        """템플릿 디렉토리 스캔"""
        if not self._templates_dir.exists():
            return

        for template_dir in self._templates_dir.iterdir():
            if not template_dir.is_dir():
                continue

            # mapping.json 파일 찾기
            mapping_files = list(template_dir.glob("*.mapping.json"))
            if not mapping_files:
                continue

            mapping_path = mapping_files[0]
            template = Template.from_mapping_file(mapping_path)
            self._templates[template.name] = template

    def get(self, name: str) -> Optional[Template]:
        """이름으로 템플릿 조회

        Args:
            name: 템플릿 이름

        Returns:
            Template 또는 None
        """
        return self._templates.get(name)

    def get_all(self) -> List[Template]:
        """모든 템플릿 반환

        Returns:
            템플릿 목록
        """
        return list(self._templates.values())

    @property
    def template_names(self) -> List[str]:
        """템플릿 이름 목록"""
        return list(self._templates.keys())
