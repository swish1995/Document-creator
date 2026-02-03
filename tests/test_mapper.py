"""Mapper 단위 테스트"""

import pytest


@pytest.fixture
def template_fields():
    """테스트용 템플릿 필드"""
    return [
        {"id": "upper_arm", "label": "Upper Arm", "excel_column": "Upper Arm"},
        {"id": "lower_arm", "label": "Lower Arm", "excel_column": "Lower Arm"},
        {"id": "score", "label": "Score", "excel_column": "Score"},
        {"id": "risk", "label": "Risk Level", "excel_column": "Risk"},
    ]


@pytest.fixture
def excel_headers():
    """테스트용 엑셀 헤더"""
    return ["Frame", "Time", "Upper Arm", "Lower Arm", "Score", "Risk", "Extra Column"]


@pytest.fixture
def row_data():
    """테스트용 행 데이터"""
    return {
        "Frame": 1,
        "Time": "00:01.50",
        "Upper Arm": 3,
        "Lower Arm": 2,
        "Score": 5,
        "Risk": "Medium",
        "Extra Column": "ignored",
    }


class TestMapper:
    """Mapper 단위 테스트"""

    def test_auto_map_matching_columns(self, template_fields, excel_headers):
        """일치하는 컬럼 자동 매핑"""
        from src.core.mapper import Mapper

        mapper = Mapper(template_fields, excel_headers)

        # 자동 매핑 결과 확인
        mapping = mapper.get_mapping()

        assert mapping["upper_arm"] == "Upper Arm"
        assert mapping["lower_arm"] == "Lower Arm"
        assert mapping["score"] == "Score"
        assert mapping["risk"] == "Risk"

    def test_auto_map_case_insensitive(self, excel_headers):
        """대소문자 무시 매핑"""
        from src.core.mapper import Mapper

        # 대소문자가 다른 필드
        fields = [
            {"id": "upper_arm", "label": "Upper Arm", "excel_column": "upper arm"},
            {"id": "score", "label": "Score", "excel_column": "SCORE"},
        ]

        mapper = Mapper(fields, excel_headers)
        mapping = mapper.get_mapping()

        assert mapping["upper_arm"] == "Upper Arm"
        assert mapping["score"] == "Score"

    def test_manual_override(self, template_fields, excel_headers):
        """수동 매핑 오버라이드"""
        from src.core.mapper import Mapper

        mapper = Mapper(template_fields, excel_headers)

        # 수동으로 다른 컬럼 매핑
        mapper.set_mapping("upper_arm", "Extra Column")

        mapping = mapper.get_mapping()
        assert mapping["upper_arm"] == "Extra Column"

    def test_apply_mapping_returns_dict(self, template_fields, excel_headers, row_data):
        """매핑 적용 결과 dict 반환"""
        from src.core.mapper import Mapper

        mapper = Mapper(template_fields, excel_headers)
        result = mapper.apply(row_data)

        assert isinstance(result, dict)
        assert result["upper_arm"] == 3
        assert result["lower_arm"] == 2
        assert result["score"] == 5
        assert result["risk"] == "Medium"

    def test_unmapped_fields_return_none(self, excel_headers, row_data):
        """매핑되지 않은 필드는 None"""
        from src.core.mapper import Mapper

        # 엑셀에 없는 컬럼을 참조하는 필드
        fields = [
            {"id": "upper_arm", "label": "Upper Arm", "excel_column": "Upper Arm"},
            {"id": "nonexistent", "label": "Nonexistent", "excel_column": "Does Not Exist"},
        ]

        mapper = Mapper(fields, excel_headers)
        result = mapper.apply(row_data)

        assert result["upper_arm"] == 3
        assert result["nonexistent"] is None

    def test_get_unmapped_fields(self, excel_headers):
        """매핑되지 않은 필드 목록"""
        from src.core.mapper import Mapper

        fields = [
            {"id": "upper_arm", "label": "Upper Arm", "excel_column": "Upper Arm"},
            {"id": "nonexistent", "label": "Nonexistent", "excel_column": "Does Not Exist"},
            {"id": "another_missing", "label": "Missing", "excel_column": "Missing Column"},
        ]

        mapper = Mapper(fields, excel_headers)
        unmapped = mapper.get_unmapped_fields()

        assert "nonexistent" in unmapped
        assert "another_missing" in unmapped
        assert "upper_arm" not in unmapped

    def test_clear_mapping(self, template_fields, excel_headers):
        """매핑 초기화"""
        from src.core.mapper import Mapper

        mapper = Mapper(template_fields, excel_headers)
        mapper.set_mapping("upper_arm", "Extra Column")
        mapper.clear_mapping("upper_arm")

        # 자동 매핑으로 복원
        mapping = mapper.get_mapping()
        assert mapping["upper_arm"] == "Upper Arm"

    def test_is_fully_mapped(self, template_fields, excel_headers):
        """모든 필드 매핑 여부 확인"""
        from src.core.mapper import Mapper

        mapper = Mapper(template_fields, excel_headers)

        assert mapper.is_fully_mapped

    def test_is_not_fully_mapped(self, excel_headers):
        """일부 필드 미매핑 확인"""
        from src.core.mapper import Mapper

        fields = [
            {"id": "upper_arm", "label": "Upper Arm", "excel_column": "Upper Arm"},
            {"id": "missing", "label": "Missing", "excel_column": "Nonexistent"},
        ]

        mapper = Mapper(fields, excel_headers)

        assert not mapper.is_fully_mapped

    def test_apply_batch(self, template_fields, excel_headers):
        """다중 행 일괄 매핑"""
        from src.core.mapper import Mapper

        rows = [
            {"Frame": 1, "Upper Arm": 3, "Lower Arm": 2, "Score": 5, "Risk": "Low"},
            {"Frame": 2, "Upper Arm": 4, "Lower Arm": 3, "Score": 6, "Risk": "Medium"},
            {"Frame": 3, "Upper Arm": 5, "Lower Arm": 4, "Score": 7, "Risk": "High"},
        ]

        mapper = Mapper(template_fields, excel_headers)
        results = mapper.apply_batch(rows)

        assert len(results) == 3
        assert results[0]["upper_arm"] == 3
        assert results[1]["upper_arm"] == 4
        assert results[2]["upper_arm"] == 5
