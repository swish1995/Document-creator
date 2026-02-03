"""엑셀 파일 로더 모듈

Skeleton Analyzer에서 생성된 엑셀 파일을 로드하고 데이터를 제공합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, List, Dict, Union

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException


class ExcelLoaderError(Exception):
    """ExcelLoader 관련 에러"""

    pass


class ExcelLoader:
    """엑셀 파일 로더

    Skeleton Analyzer 출력 엑셀 파일의 Capture Data 시트를 로드합니다.
    """

    DEFAULT_SHEET_NAME = "Capture Data"

    def __init__(self):
        self._workbook = None
        self._sheet = None
        self._headers: list[str] = []
        self._data: list[dict[str, Any]] = []
        self._file_path: Path | None = None

    @property
    def is_loaded(self) -> bool:
        """데이터가 로드되었는지 여부"""
        return self._workbook is not None

    @property
    def file_path(self) -> Path | None:
        """로드된 파일 경로"""
        return self._file_path

    @property
    def row_count(self) -> int:
        """전체 행 수"""
        self._ensure_loaded()
        return len(self._data)

    def load(self, file_path: Path | str) -> None:
        """엑셀 파일 로드

        Args:
            file_path: 엑셀 파일 경로

        Raises:
            ExcelLoaderError: 파일을 찾을 수 없거나 형식이 잘못된 경우
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ExcelLoaderError(f"파일을 찾을 수 없습니다: {file_path}")

        try:
            self._workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        except InvalidFileException as e:
            raise ExcelLoaderError(f"잘못된 엑셀 파일 형식입니다: {e}")
        except Exception as e:
            raise ExcelLoaderError(f"파일 로드 실패: {e}")

        self._file_path = file_path
        self._load_sheet()

    def _load_sheet(self) -> None:
        """시트 데이터 로드"""
        # Capture Data 시트 또는 첫 번째 시트 선택
        if self.DEFAULT_SHEET_NAME in self._workbook.sheetnames:
            self._sheet = self._workbook[self.DEFAULT_SHEET_NAME]
        else:
            self._sheet = self._workbook.active

        # 헤더 읽기 (첫 번째 행)
        rows = list(self._sheet.iter_rows(values_only=True))
        if not rows:
            self._headers = []
            self._data = []
            return

        self._headers = [str(cell) if cell is not None else "" for cell in rows[0]]

        # 데이터 행 읽기
        self._data = []
        for row in rows[1:]:
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(self._headers):
                    row_dict[self._headers[i]] = value
            self._data.append(row_dict)

    def _ensure_loaded(self) -> None:
        """데이터가 로드되었는지 확인"""
        if not self.is_loaded:
            raise ExcelLoaderError("먼저 load()를 호출하여 파일을 로드해야 합니다")

    def get_headers(self) -> list[str]:
        """헤더 목록 반환

        Returns:
            컬럼 이름 목록
        """
        self._ensure_loaded()
        return self._headers.copy()

    def get_row(self, index: int) -> dict[str, Any]:
        """특정 행 데이터 반환

        Args:
            index: 행 인덱스 (0부터 시작)

        Returns:
            {컬럼명: 값} 딕셔너리

        Raises:
            ExcelLoaderError: 잘못된 인덱스인 경우
        """
        self._ensure_loaded()

        if index < 0 or index >= len(self._data):
            raise ExcelLoaderError(f"잘못된 행 인덱스입니다: {index} (범위: 0-{len(self._data) - 1})")

        return self._data[index].copy()

    def get_rows(self, indices: list[int]) -> list[dict[str, Any]]:
        """다중 행 데이터 반환

        Args:
            indices: 행 인덱스 목록

        Returns:
            딕셔너리 목록
        """
        return [self.get_row(i) for i in indices]

    def get_all_rows(self) -> list[dict[str, Any]]:
        """전체 행 데이터 반환

        Returns:
            모든 행의 딕셔너리 목록
        """
        self._ensure_loaded()
        return [row.copy() for row in self._data]
