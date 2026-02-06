"""데이터 매퍼 모듈

엑셀 컬럼과 템플릿 필드 간의 매핑을 관리합니다.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.logger import get_logger

logger = get_logger("mapper")


class MapperError(Exception):
    """Mapper 관련 에러"""

    pass


class Mapper:
    """데이터 매퍼

    엑셀 컬럼과 템플릿 필드 간의 매핑을 관리하고 데이터를 변환합니다.
    """

    def __init__(self, template_fields: List[Dict[str, Any]], excel_headers: List[str]):
        """
        Args:
            template_fields: 템플릿 필드 목록 [{"id": str, "excel_column": str, ...}, ...]
            excel_headers: 엑셀 헤더 목록
        """
        self._template_fields = template_fields
        self._excel_headers = excel_headers
        self._excel_headers_lower = {h.lower(): h for h in excel_headers}
        self._manual_mappings: Dict[str, str] = {}
        self._auto_mappings: Dict[str, Optional[str]] = {}
        self._auto_map()

    def _auto_map(self) -> None:
        """자동 매핑 수행"""
        for field in self._template_fields:
            field_id = field["id"]
            excel_column = field.get("excel_column", "")

            # 대소문자 무시하고 매칭
            excel_column_lower = excel_column.lower()
            if excel_column_lower in self._excel_headers_lower:
                self._auto_mappings[field_id] = self._excel_headers_lower[excel_column_lower]
            else:
                self._auto_mappings[field_id] = None

    def get_mapping(self) -> Dict[str, Optional[str]]:
        """현재 매핑 반환

        수동 매핑이 있으면 우선 적용, 없으면 자동 매핑 사용

        Returns:
            {field_id: excel_column} 딕셔너리
        """
        result = {}
        for field in self._template_fields:
            field_id = field["id"]
            if field_id in self._manual_mappings:
                result[field_id] = self._manual_mappings[field_id]
            else:
                result[field_id] = self._auto_mappings.get(field_id)
        return result

    def set_mapping(self, field_id: str, excel_column: str) -> None:
        """수동 매핑 설정

        Args:
            field_id: 템플릿 필드 ID
            excel_column: 엑셀 컬럼명
        """
        self._manual_mappings[field_id] = excel_column

    def clear_mapping(self, field_id: str) -> None:
        """수동 매핑 제거 (자동 매핑으로 복원)

        Args:
            field_id: 템플릿 필드 ID
        """
        self._manual_mappings.pop(field_id, None)

    def apply(self, row_data: Dict[str, Any], row_data_by_index: List[Any] = None) -> Dict[str, Any]:
        """매핑을 적용하여 데이터 변환

        Args:
            row_data: 엑셀 행 데이터 {column: value}
            row_data_by_index: 인덱스 기반 행 데이터 [value, ...] (중복 헤더 지원)

        Returns:
            변환된 데이터 {field_id: value}
        """
        mapping = self.get_mapping()
        result = {}

        for field in self._template_fields:
            field_id = field["id"]
            excel_column = mapping.get(field_id)
            excel_index = field.get("excel_index")
            field_type = field.get("type", "text")

            # 인덱스 기반 데이터가 있고, excel_index가 정의된 경우 우선 사용 (중복 헤더 문제 해결)
            if row_data_by_index is not None and excel_index is not None:
                if 0 <= excel_index < len(row_data_by_index):
                    value = row_data_by_index[excel_index]
                else:
                    value = None
            elif excel_column is not None and excel_column in row_data:
                value = row_data[excel_column]
            else:
                value = None

            # 이미지 타입인 경우 img 태그로 변환
            if field_type == "image" and value is not None:
                value = self._convert_image_to_img_tag(value)

            result[field_id] = value

        return result

    def _convert_image_to_img_tag(self, image_path) -> str:
        """이미지 경로를 완전한 img 태그로 변환

        Args:
            image_path: 이미지 파일 경로 (Path 또는 str)

        Returns:
            <img src="data:..."> 형식의 HTML 태그, 실패시 빈 문자열
        """
        data_url = self._convert_image_to_data_url(image_path)
        if data_url:
            return f'<img src="{data_url}" style="width:100%;height:100%;object-fit:contain;">'
        return ""

    def _convert_image_to_data_url(self, image_path) -> str:
        """이미지 경로를 Base64 data URL로 변환

        Args:
            image_path: 이미지 파일 경로 (Path 또는 str)

        Returns:
            data:image/png;base64,... 형식의 문자열, 실패시 빈 문자열
        """
        try:
            path = Path(image_path) if not isinstance(image_path, Path) else image_path
            if not path.exists():
                return ""

            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")

            # 확장자로 MIME 타입 결정
            suffix = path.suffix.lower()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_types.get(suffix, "image/png")

            return f"data:{mime_type};base64,{data}"
        except Exception:
            return ""

    def apply_batch(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """다중 행에 매핑 적용

        Args:
            rows: 엑셀 행 데이터 목록

        Returns:
            변환된 데이터 목록
        """
        return [self.apply(row) for row in rows]

    def get_unmapped_fields(self) -> List[str]:
        """매핑되지 않은 필드 목록 반환

        Returns:
            매핑되지 않은 필드 ID 목록
        """
        mapping = self.get_mapping()
        return [field_id for field_id, column in mapping.items() if column is None]

    @property
    def is_fully_mapped(self) -> bool:
        """모든 필드가 매핑되었는지 여부"""
        return len(self.get_unmapped_fields()) == 0

    def save_to_file(
        self, file_path: str, template_name: str, excel_file: str
    ) -> None:
        """현재 매핑을 파일로 저장

        Args:
            file_path: 저장할 파일 경로
            template_name: 템플릿 이름
            excel_file: 엑셀 파일명
        """
        mapping = self.get_mapping()
        now = datetime.now().isoformat()

        data = {
            "version": "1.0",
            "template_name": template_name,
            "excel_file": excel_file,
            "mappings": mapping,
            "created_at": now,
            "updated_at": now,
        }

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, file_path: str) -> None:
        """파일에서 매핑 로드

        Args:
            file_path: 로드할 파일 경로

        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            json.JSONDecodeError: 잘못된 JSON 형식
            ValueError: 필수 필드 누락 또는 버전 불일치
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"매핑 파일을 찾을 수 없습니다: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 버전 확인
        if "version" not in data:
            raise ValueError("version 정보가 없습니다")

        version = data["version"]
        if version != "1.0":
            raise ValueError(f"version 불일치: {version}")

        # 매핑 로드
        if "mappings" in data:
            self.import_config(data["mappings"])

    def export_config(self) -> Dict[str, Optional[str]]:
        """현재 매핑을 딕셔너리로 변환

        Returns:
            {field_id: excel_column} 딕셔너리
        """
        return self.get_mapping()

    def import_config(self, config: Dict[str, Optional[str]]) -> None:
        """딕셔너리에서 매핑 가져오기

        수동 매핑으로 설정됨

        Args:
            config: {field_id: excel_column} 딕셔너리
        """
        for field_id, excel_column in config.items():
            if excel_column is not None:
                self._manual_mappings[field_id] = excel_column

    def reset_to_auto(self) -> None:
        """모든 수동 매핑 제거 (자동 매핑으로 복원)"""
        self._manual_mappings.clear()

    def get_mapping_status(self) -> Dict[str, str]:
        """각 필드의 매핑 상태 반환

        Returns:
            {field_id: status} 딕셔너리
            status: "auto", "manual", "unmapped"
        """
        result = {}
        mapping = self.get_mapping()

        for field in self._template_fields:
            field_id = field["id"]

            if field_id in self._manual_mappings:
                result[field_id] = "manual"
            elif mapping.get(field_id) is not None:
                result[field_id] = "auto"
            else:
                result[field_id] = "unmapped"

        return result


def get_mapping_file_path(excel_path: str, template_name: str) -> str:
    """매핑 파일 경로 생성

    Args:
        excel_path: 엑셀 파일 경로
        template_name: 템플릿 이름

    Returns:
        매핑 파일 경로 (예: /data/sample.xlsx.rula.mapping)
    """
    template_lower = template_name.lower()
    return f"{excel_path}.{template_lower}.mapping"
