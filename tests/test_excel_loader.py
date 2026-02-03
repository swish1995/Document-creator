"""ExcelLoader 단위 테스트"""

import pytest
from pathlib import Path


class TestExcelLoader:
    """ExcelLoader 단위 테스트"""

    def test_load_valid_excel_file(self, sample_xlsx):
        """유효한 엑셀 파일 로드 성공"""
        from src.core.excel_loader import ExcelLoader

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        assert loader.is_loaded
        assert loader.row_count > 0

    def test_load_nonexistent_file_raises_error(self):
        """존재하지 않는 파일 로드 시 에러"""
        from src.core.excel_loader import ExcelLoader, ExcelLoaderError

        loader = ExcelLoader()

        with pytest.raises(ExcelLoaderError):
            loader.load(Path("/nonexistent/file.xlsx"))

    def test_load_invalid_format_raises_error(self, tmp_path):
        """잘못된 형식 파일 로드 시 에러"""
        from src.core.excel_loader import ExcelLoader, ExcelLoaderError

        # 잘못된 형식의 파일 생성
        invalid_file = tmp_path / "invalid.xlsx"
        invalid_file.write_text("not an excel file")

        loader = ExcelLoader()

        with pytest.raises(ExcelLoaderError):
            loader.load(invalid_file)

    def test_get_headers_returns_column_names(self, sample_xlsx):
        """헤더 목록 반환"""
        from src.core.excel_loader import ExcelLoader

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        headers = loader.get_headers()

        assert isinstance(headers, list)
        assert len(headers) > 0
        assert "Frame" in headers or "frame" in [h.lower() for h in headers]

    def test_get_row_returns_dict(self, sample_xlsx):
        """특정 행 데이터 dict 반환"""
        from src.core.excel_loader import ExcelLoader

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        row = loader.get_row(0)

        assert isinstance(row, dict)
        assert len(row) > 0

    def test_get_row_invalid_index_raises_error(self, sample_xlsx):
        """잘못된 인덱스로 행 조회 시 에러"""
        from src.core.excel_loader import ExcelLoader, ExcelLoaderError

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        with pytest.raises(ExcelLoaderError):
            loader.get_row(-1)

        with pytest.raises(ExcelLoaderError):
            loader.get_row(999999)

    def test_get_rows_returns_list_of_dicts(self, sample_xlsx):
        """다중 행 데이터 반환"""
        from src.core.excel_loader import ExcelLoader

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        # 실제 데이터 행 수에 맞게 인덱스 조정
        row_count = loader.row_count
        if row_count >= 3:
            indices = [0, 1, 2]
        else:
            indices = list(range(row_count))

        rows = loader.get_rows(indices)

        assert isinstance(rows, list)
        assert len(rows) == len(indices)
        assert all(isinstance(r, dict) for r in rows)

    def test_get_all_rows_returns_complete_data(self, sample_xlsx):
        """전체 행 데이터 반환"""
        from src.core.excel_loader import ExcelLoader

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        all_rows = loader.get_all_rows()

        assert isinstance(all_rows, list)
        assert len(all_rows) == loader.row_count
        assert all(isinstance(r, dict) for r in all_rows)

    def test_row_count_property(self, sample_xlsx):
        """전체 행 수 반환"""
        from src.core.excel_loader import ExcelLoader

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        assert isinstance(loader.row_count, int)
        assert loader.row_count > 0

    def test_capture_data_sheet_loaded_by_default(self, sample_xlsx):
        """Capture Data 시트가 기본 로드됨"""
        from src.core.excel_loader import ExcelLoader

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        # Capture Data 시트의 특징적인 컬럼 확인
        headers = loader.get_headers()
        # Frame 또는 Time 같은 기본 컬럼이 있어야 함
        header_lower = [h.lower() for h in headers]
        assert "frame" in header_lower or "time" in header_lower

    def test_not_loaded_before_load_call(self):
        """load() 호출 전에는 데이터 접근 불가"""
        from src.core.excel_loader import ExcelLoader, ExcelLoaderError

        loader = ExcelLoader()

        assert not loader.is_loaded

        with pytest.raises(ExcelLoaderError):
            _ = loader.row_count

        with pytest.raises(ExcelLoaderError):
            loader.get_headers()

        with pytest.raises(ExcelLoaderError):
            loader.get_row(0)

    def test_file_path_property(self, sample_xlsx):
        """로드된 파일 경로 반환"""
        from src.core.excel_loader import ExcelLoader

        loader = ExcelLoader()
        loader.load(sample_xlsx)

        assert loader.file_path == sample_xlsx
