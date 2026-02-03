"""로깅 모듈

Document Creator의 로깅 시스템을 제공합니다.
- 2MB 파일 크기 제한
- 최대 10개 파일 로테이션
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# 로그 설정
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = "document_creator.log"
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
BACKUP_COUNT = 9  # 최대 10개 파일 (현재 + 백업 9개)
LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 전역 로거 저장소
_loggers: dict = {}
_initialized: bool = False


def _setup_logging():
    """로깅 시스템 초기화"""
    global _initialized
    if _initialized:
        return

    # 로그 디렉토리 생성
    LOG_DIR.mkdir(exist_ok=True)

    # 루트 로거 설정
    root_logger = logging.getLogger("document_creator")
    root_logger.setLevel(logging.DEBUG)

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 파일 핸들러 (로테이션)
    file_handler = RotatingFileHandler(
        LOG_DIR / LOG_FILE,
        maxBytes=MAX_FILE_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # 콘솔 핸들러 (개발용)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)

    _initialized = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """로거 인스턴스 반환

    Args:
        name: 로거 이름 (예: 'main_window', 'excel_viewer')
              None이면 루트 로거 반환

    Returns:
        logging.Logger: 로거 인스턴스
    """
    _setup_logging()

    if name is None:
        return logging.getLogger("document_creator")

    full_name = f"document_creator.{name}"
    if full_name not in _loggers:
        _loggers[full_name] = logging.getLogger(full_name)

    return _loggers[full_name]


def set_log_level(level: int):
    """전체 로그 레벨 설정

    Args:
        level: logging.DEBUG, logging.INFO, logging.WARNING 등
    """
    _setup_logging()
    logging.getLogger("document_creator").setLevel(level)


def set_console_level(level: int):
    """콘솔 출력 레벨 설정

    Args:
        level: logging.DEBUG, logging.INFO, logging.WARNING 등
    """
    _setup_logging()
    root_logger = logging.getLogger("document_creator")
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, RotatingFileHandler
        ):
            handler.setLevel(level)
