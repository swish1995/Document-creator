"""데이터 매퍼 모듈

엑셀 컬럼과 템플릿 필드 간의 매핑을 관리합니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


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

    def apply(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """매핑을 적용하여 데이터 변환

        Args:
            row_data: 엑셀 행 데이터 {column: value}

        Returns:
            변환된 데이터 {field_id: value}
        """
        mapping = self.get_mapping()
        result = {}

        for field_id, excel_column in mapping.items():
            if excel_column is not None and excel_column in row_data:
                result[field_id] = row_data[excel_column]
            else:
                result[field_id] = None

        return result

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
