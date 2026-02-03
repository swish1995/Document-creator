"""Mapper 파일 I/O 테스트"""

import json
from pathlib import Path

import pytest

from src.core.mapper import Mapper


@pytest.fixture
def sample_template_fields():
    """샘플 템플릿 필드"""
    return [
        {"id": "frame", "label": "프레임", "excel_column": "Frame"},
        {"id": "time", "label": "시간", "excel_column": "Time"},
        {"id": "upper_arm", "label": "상완", "excel_column": "Upper Arm"},
        {"id": "lower_arm", "label": "전완", "excel_column": "Lower Arm"},
        {"id": "score", "label": "점수", "excel_column": "Score"},
    ]


@pytest.fixture
def sample_excel_headers():
    """샘플 엑셀 헤더"""
    return ["Frame", "Time", "Upper Arm", "Lower Arm", "Wrist", "Score", "Risk"]


@pytest.fixture
def sample_mapper(sample_template_fields, sample_excel_headers):
    """샘플 Mapper 인스턴스"""
    return Mapper(sample_template_fields, sample_excel_headers)


class TestSaveToFile:
    """save_to_file() 메서드 테스트"""

    def test_save_to_file_creates_valid_json(
        self, sample_mapper, sample_template_fields, tmp_path
    ):
        """파일 저장 시 유효한 JSON 파일 생성"""
        file_path = tmp_path / "test.xlsx.rula.mapping"
        excel_file = "test.xlsx"
        template_name = "RULA"

        sample_mapper.save_to_file(str(file_path), template_name, excel_file)

        assert file_path.exists()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 필수 필드 확인
        assert "version" in data
        assert "template_name" in data
        assert "excel_file" in data
        assert "mappings" in data
        assert "created_at" in data
        assert "updated_at" in data

        # 값 확인
        assert data["version"] == "1.0"
        assert data["template_name"] == template_name
        assert data["excel_file"] == excel_file
        assert isinstance(data["mappings"], dict)

    def test_save_includes_manual_mappings(self, sample_mapper, tmp_path):
        """수동 매핑이 저장됨"""
        file_path = tmp_path / "test.mapping"

        # 수동 매핑 설정
        sample_mapper.set_mapping("upper_arm", "Arm Upper")
        sample_mapper.save_to_file(str(file_path), "RULA", "test.xlsx")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["mappings"]["upper_arm"] == "Arm Upper"

    def test_save_includes_auto_mappings(self, sample_mapper, tmp_path):
        """자동 매핑이 저장됨"""
        file_path = tmp_path / "test.mapping"

        sample_mapper.save_to_file(str(file_path), "RULA", "test.xlsx")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 자동 매핑된 필드 확인
        assert data["mappings"]["frame"] == "Frame"
        assert data["mappings"]["time"] == "Time"

    def test_save_with_unmapped_fields(
        self, sample_template_fields, sample_excel_headers, tmp_path
    ):
        """미매핑 필드는 null로 저장"""
        # "wrist" 필드가 없는 상황
        fields_with_missing = sample_template_fields + [
            {"id": "wrist", "label": "손목", "excel_column": "Wrist Missing"}
        ]

        mapper = Mapper(fields_with_missing, sample_excel_headers)
        file_path = tmp_path / "test.mapping"

        mapper.save_to_file(str(file_path), "RULA", "test.xlsx")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["mappings"]["wrist"] is None


class TestLoadFromFile:
    """load_from_file() 메서드 테스트"""

    def test_load_from_file_restores_mappings(
        self, sample_mapper, sample_template_fields, tmp_path
    ):
        """파일에서 매핑 복원"""
        file_path = tmp_path / "test.mapping"

        # 저장
        sample_mapper.set_mapping("upper_arm", "Custom Upper Arm")
        sample_mapper.save_to_file(str(file_path), "RULA", "test.xlsx")

        # 새 매퍼 생성 후 로드
        new_mapper = Mapper(sample_template_fields, sample_mapper._excel_headers)
        new_mapper.load_from_file(str(file_path))

        mapping = new_mapper.get_mapping()
        assert mapping["upper_arm"] == "Custom Upper Arm"

    def test_load_nonexistent_file_raises_error(self, sample_mapper):
        """존재하지 않는 파일 로드 시 에러"""
        with pytest.raises(FileNotFoundError):
            sample_mapper.load_from_file("/nonexistent/file.mapping")

    def test_load_invalid_json_raises_error(self, sample_mapper, tmp_path):
        """잘못된 JSON 파일 로드 시 에러"""
        file_path = tmp_path / "invalid.mapping"
        file_path.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            sample_mapper.load_from_file(str(file_path))

    def test_load_missing_version_raises_error(self, sample_mapper, tmp_path):
        """버전 정보 없는 파일 로드 시 에러"""
        file_path = tmp_path / "no_version.mapping"
        data = {
            "template_name": "RULA",
            "excel_file": "test.xlsx",
            "mappings": {},
        }
        file_path.write_text(json.dumps(data))

        with pytest.raises(ValueError, match="version"):
            sample_mapper.load_from_file(str(file_path))

    def test_load_incompatible_version_raises_error(self, sample_mapper, tmp_path):
        """호환되지 않는 버전 로드 시 에러"""
        file_path = tmp_path / "future_version.mapping"
        data = {
            "version": "99.0",
            "template_name": "RULA",
            "excel_file": "test.xlsx",
            "mappings": {},
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }
        file_path.write_text(json.dumps(data))

        with pytest.raises(ValueError, match="version"):
            sample_mapper.load_from_file(str(file_path))


class TestExportImportConfig:
    """export_config() / import_config() 테스트"""

    def test_export_config_returns_dict(self, sample_mapper):
        """현재 매핑을 딕셔너리로 변환"""
        config = sample_mapper.export_config()

        assert isinstance(config, dict)
        assert "frame" in config
        assert "time" in config
        assert config["frame"] == "Frame"

    def test_export_prefers_manual_over_auto(self, sample_mapper):
        """수동 매핑이 우선 적용됨"""
        sample_mapper.set_mapping("frame", "Custom Frame")
        config = sample_mapper.export_config()

        assert config["frame"] == "Custom Frame"

    def test_import_config_sets_manual_mappings(
        self, sample_mapper, sample_template_fields
    ):
        """import 시 수동 매핑으로 설정"""
        config = {
            "frame": "New Frame",
            "time": "New Time",
            "upper_arm": "New Upper Arm",
        }

        sample_mapper.import_config(config)

        mapping = sample_mapper.get_mapping()
        assert mapping["frame"] == "New Frame"
        assert mapping["time"] == "New Time"
        assert mapping["upper_arm"] == "New Upper Arm"

    def test_export_import_roundtrip(self, sample_mapper, sample_template_fields):
        """export → import 왕복 테스트"""
        # 수동 매핑 설정
        sample_mapper.set_mapping("upper_arm", "Custom Arm")

        # export
        config = sample_mapper.export_config()

        # 새 매퍼 생성 후 import
        new_mapper = Mapper(sample_template_fields, sample_mapper._excel_headers)
        new_mapper.import_config(config)

        # 매핑 비교
        original_mapping = sample_mapper.get_mapping()
        new_mapping = new_mapper.get_mapping()

        assert original_mapping == new_mapping


class TestResetToAuto:
    """reset_to_auto() 메서드 테스트"""

    def test_reset_clears_all_manual_mappings(self, sample_mapper):
        """모든 수동 매핑 제거"""
        # 수동 매핑 설정
        sample_mapper.set_mapping("frame", "Custom Frame")
        sample_mapper.set_mapping("time", "Custom Time")

        sample_mapper.reset_to_auto()

        # 자동 매핑으로 복원되었는지 확인
        mapping = sample_mapper.get_mapping()
        assert mapping["frame"] == "Frame"  # 원래 자동 매핑
        assert mapping["time"] == "Time"  # 원래 자동 매핑

    def test_reset_preserves_auto_mappings(self, sample_mapper):
        """자동 매핑은 유지됨"""
        original_auto = sample_mapper._auto_mappings.copy()

        sample_mapper.set_mapping("frame", "Custom")
        sample_mapper.reset_to_auto()

        assert sample_mapper._auto_mappings == original_auto


class TestGetMappingStatus:
    """get_mapping_status() 메서드 테스트"""

    def test_status_shows_auto_mapped_fields(self, sample_mapper):
        """자동 매핑된 필드는 'auto'"""
        status = sample_mapper.get_mapping_status()

        assert status["frame"] == "auto"
        assert status["time"] == "auto"

    def test_status_shows_manual_mapped_fields(self, sample_mapper):
        """수동 매핑된 필드는 'manual'"""
        sample_mapper.set_mapping("frame", "Custom Frame")
        status = sample_mapper.get_mapping_status()

        assert status["frame"] == "manual"

    def test_status_shows_unmapped_fields(
        self, sample_template_fields, sample_excel_headers
    ):
        """미매핑 필드는 'unmapped'"""
        fields_with_missing = sample_template_fields + [
            {"id": "missing", "label": "없음", "excel_column": "Not Exists"}
        ]

        mapper = Mapper(fields_with_missing, sample_excel_headers)
        status = mapper.get_mapping_status()

        assert status["missing"] == "unmapped"

    def test_status_includes_all_fields(self, sample_mapper, sample_template_fields):
        """모든 필드의 상태 포함"""
        status = sample_mapper.get_mapping_status()

        for field in sample_template_fields:
            assert field["id"] in status


class TestGetMappingFilePath:
    """get_mapping_file_path() 유틸리티 함수 테스트"""

    def test_path_format(self):
        """경로 포맷 확인"""
        from src.core.mapper import get_mapping_file_path

        path = get_mapping_file_path("/data/sample.xlsx", "RULA")
        assert path == "/data/sample.xlsx.rula.mapping"

    def test_path_with_different_extension(self):
        """다양한 확장자 처리"""
        from src.core.mapper import get_mapping_file_path

        path = get_mapping_file_path("/data/test.xlsm", "REBA")
        assert path == "/data/test.xlsm.reba.mapping"

    def test_path_lowercase_template(self):
        """템플릿명은 소문자 변환"""
        from src.core.mapper import get_mapping_file_path

        path = get_mapping_file_path("/data/test.xlsx", "OWAS")
        assert path == "/data/test.xlsx.owas.mapping"

    def test_path_with_spaces(self):
        """공백 포함 경로 처리"""
        from src.core.mapper import get_mapping_file_path

        path = get_mapping_file_path("/data/my file.xlsx", "NLE")
        assert path == "/data/my file.xlsx.nle.mapping"
