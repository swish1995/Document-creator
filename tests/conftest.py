"""pytest fixtures for Document Creator tests"""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """테스트 fixtures 디렉토리 경로"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_xlsx(fixtures_dir):
    """샘플 엑셀 파일 경로"""
    return fixtures_dir / "sample.xlsx"


@pytest.fixture
def templates_dir(fixtures_dir):
    """테스트 템플릿 디렉토리"""
    return fixtures_dir / "templates"
