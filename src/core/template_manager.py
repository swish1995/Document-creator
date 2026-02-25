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


# 유효한 안전지표 목록 및 정렬 순서
SAFETY_INDICATORS = ["RULA", "REBA", "OWAS", "NLE", "SI"]


@dataclass
class Template:
    """템플릿 정보"""

    name: str
    version: str
    template_type: str  # "html" or "image"
    template_path: Path
    mapping_path: Path
    fields: List[Dict[str, Any]] = field(default_factory=list)
    safety_indicator: Optional[str] = None  # RULA, REBA, OWAS, NLE, SI
    category: Optional[str] = None  # 프리셋 카테고리 (ergonomic, inspection, ...)
    description: str = ""
    page_height_mm: float = 1000.0  # PDF 페이지 높이 (기본값: 충분히 큰 값)

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
        safety_indicator = data.get("safety_indicator")
        description = data.get("description", "")
        page_height_mm = data.get("page_height_mm", 1000.0)  # 기본값: 충분히 큰 값

        # 유효한 안전지표인지 확인
        if safety_indicator and safety_indicator not in SAFETY_INDICATORS:
            safety_indicator = None

        # category 필드 처리 (하위 호환: safety_indicator → category 자동 매핑)
        category = data.get("category")
        if category is None and safety_indicator:
            if safety_indicator in SAFETY_INDICATORS:
                category = "ergonomic"

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
            safety_indicator=safety_indicator,
            category=category,
            description=description,
            page_height_mm=page_height_mm,
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
    새로운 디렉토리 구조 지원:
        templates/_builtin/  - 기본 템플릿
        templates/user/      - 사용자 템플릿
    """

    BUILTIN_DIR = "_builtin"
    USER_DIR = "user"

    CATEGORIES_FILE = "_categories.json"

    def __init__(self, templates_dir: Path):
        """
        Args:
            templates_dir: 템플릿 디렉토리 경로

        Raises:
            TemplateError: 템플릿 로드 실패 시
        """
        self._templates_dir = Path(templates_dir)
        self._templates: Dict[str, Template] = {}
        self._categories: List[Dict[str, Any]] = []
        self._load_categories()
        self._scan_templates()

    def _load_categories(self) -> None:
        """카테고리 설정 파일 로드"""
        categories_path = self._templates_dir / self.BUILTIN_DIR / self.CATEGORIES_FILE
        if categories_path.exists():
            try:
                with open(categories_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._categories = data.get("categories", [])
            except (json.JSONDecodeError, Exception):
                self._categories = []
        else:
            self._categories = []

    @property
    def categories(self) -> List[Dict[str, Any]]:
        """카테고리 목록 반환"""
        return self._categories.copy()

    def _scan_templates(self) -> None:
        """템플릿 디렉토리 스캔 (새 구조 + 레거시 구조 지원)"""
        if not self._templates_dir.exists():
            return

        # 새 구조: _builtin/ 디렉토리
        builtin_dir = self._templates_dir / self.BUILTIN_DIR
        if builtin_dir.exists():
            self._scan_directory(builtin_dir)

        # 새 구조: user/ 디렉토리
        user_dir = self._templates_dir / self.USER_DIR
        if user_dir.exists():
            self._scan_directory(user_dir)

        # 레거시 구조: 루트 디렉토리의 템플릿 (하위 호환성)
        for template_dir in self._templates_dir.iterdir():
            if not template_dir.is_dir():
                continue
            # 특수 디렉토리 스킵
            if template_dir.name in (self.BUILTIN_DIR, self.USER_DIR, "sample"):
                continue
            if template_dir.name.startswith(".") or template_dir.name.startswith("_"):
                continue

            mapping_files = list(template_dir.glob("*.mapping.json"))
            if not mapping_files:
                continue

            try:
                template = Template.from_mapping_file(mapping_files[0])
                self._templates[template.name] = template
            except TemplateError:
                continue

    def _scan_directory(self, directory: Path) -> None:
        """특정 디렉토리의 템플릿 스캔"""
        for template_dir in directory.iterdir():
            if not template_dir.is_dir():
                continue
            if template_dir.name.startswith("."):
                continue

            # mapping.json 또는 *.mapping.json 찾기
            mapping_files = list(template_dir.glob("*.mapping.json"))
            if not mapping_files:
                mapping_files = list(template_dir.glob("mapping.json"))
            if not mapping_files:
                continue

            try:
                template = Template.from_mapping_file(mapping_files[0])
                self._templates[template.name] = template
            except TemplateError:
                continue

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
        """템플릿 이름 목록 (카테고리 순서 → 이름순 정렬)

        카테고리 설정이 있으면 sort_order 기반으로, 없으면 SAFETY_INDICATORS 순서로 정렬.
        """
        names = list(self._templates.keys())

        if self._categories:
            # 카테고리 sort_order 맵 생성
            category_order = {
                cat["id"]: cat.get("sort_order", 999)
                for cat in self._categories
            }
            max_order = max(category_order.values(), default=0) + 1

            def sort_key(name: str) -> tuple:
                template = self._templates.get(name)
                cat = template.category if template else None
                order = category_order.get(cat, max_order) if cat else max_order
                # 안전지표 순서 (RULA=0, REBA=1, OWAS=2, NLE=3, SI=4)
                si = template.safety_indicator if template else None
                si_order = len(SAFETY_INDICATORS)
                if si and si in SAFETY_INDICATORS:
                    si_order = SAFETY_INDICATORS.index(si)
                return (order, si_order, name)

            return sorted(names, key=sort_key)
        else:
            # 하위 호환: _categories.json 없으면 기존 SAFETY_INDICATORS 순서
            def sort_key_legacy(name: str) -> int:
                try:
                    return SAFETY_INDICATORS.index(name)
                except ValueError:
                    return len(SAFETY_INDICATORS)
            return sorted(names, key=sort_key_legacy)

    def refresh(self) -> None:
        """템플릿 목록 새로고침"""
        self._templates.clear()
        self._scan_templates()
