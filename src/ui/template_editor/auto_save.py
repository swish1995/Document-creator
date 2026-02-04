"""자동 저장 및 백업 모듈

템플릿 편집 중 자동 저장 및 버전 백업을 관리합니다.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class AutoSaveManager(QObject):
    """자동 저장 관리자

    일정 간격으로 자동 저장하고, 백업 파일을 관리합니다.
    """

    # 시그널
    auto_saved = pyqtSignal(str)  # 저장된 파일 경로
    backup_created = pyqtSignal(str)  # 백업 파일 경로
    error_occurred = pyqtSignal(str)  # 에러 메시지

    # 기본 설정
    DEFAULT_INTERVAL = 60000  # 60초
    DEFAULT_MAX_BACKUPS = 5

    def __init__(
        self,
        parent: Optional[QObject] = None,
        interval_ms: int = DEFAULT_INTERVAL,
        max_backups: int = DEFAULT_MAX_BACKUPS,
    ):
        super().__init__(parent)
        self._interval = interval_ms
        self._max_backups = max_backups
        self._enabled = False
        self._modified = False
        self._current_path: Optional[Path] = None
        self._content_getter: Optional[callable] = None
        self._backup_dir: Optional[Path] = None

        # 타이머 설정
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)

    def set_content_getter(self, getter: callable):
        """콘텐츠 가져오기 함수 설정

        Args:
            getter: 현재 편집 중인 콘텐츠를 반환하는 함수
        """
        self._content_getter = getter

    def set_file_path(self, path: Path):
        """현재 파일 경로 설정"""
        self._current_path = Path(path)
        self._backup_dir = self._current_path.parent / ".backup"

    def set_interval(self, interval_ms: int):
        """자동 저장 간격 설정 (밀리초)"""
        self._interval = interval_ms
        if self._enabled:
            self._timer.setInterval(interval_ms)

    def set_max_backups(self, max_backups: int):
        """최대 백업 수 설정"""
        self._max_backups = max_backups

    def set_modified(self, modified: bool):
        """수정 상태 설정"""
        self._modified = modified

    def start(self):
        """자동 저장 시작"""
        if not self._enabled:
            self._enabled = True
            self._timer.start(self._interval)

    def stop(self):
        """자동 저장 중지"""
        self._enabled = False
        self._timer.stop()

    def is_enabled(self) -> bool:
        """활성화 여부"""
        return self._enabled

    def _on_timer(self):
        """타이머 콜백"""
        if self._modified and self._current_path and self._content_getter:
            self.save_now()

    def save_now(self) -> bool:
        """즉시 저장

        Returns:
            성공 여부
        """
        if not self._current_path or not self._content_getter:
            return False

        try:
            content = self._content_getter()

            # 임시 파일에 먼저 저장
            temp_path = self._current_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

            # 기존 파일을 백업
            if self._current_path.exists():
                self._create_backup()

            # 임시 파일을 실제 파일로 이동
            shutil.move(str(temp_path), str(self._current_path))

            self._modified = False
            self.auto_saved.emit(str(self._current_path))
            return True

        except Exception as e:
            self.error_occurred.emit(f"자동 저장 실패: {e}")
            return False

    def _create_backup(self):
        """백업 파일 생성"""
        if not self._backup_dir or not self._current_path:
            return

        try:
            # 백업 디렉토리 생성
            self._backup_dir.mkdir(parents=True, exist_ok=True)

            # 백업 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self._current_path.stem}_{timestamp}{self._current_path.suffix}"
            backup_path = self._backup_dir / backup_name

            # 백업 복사
            shutil.copy2(self._current_path, backup_path)
            self.backup_created.emit(str(backup_path))

            # 오래된 백업 정리
            self._cleanup_old_backups()

        except Exception as e:
            self.error_occurred.emit(f"백업 생성 실패: {e}")

    def _cleanup_old_backups(self):
        """오래된 백업 파일 정리"""
        if not self._backup_dir or not self._backup_dir.exists():
            return

        if not self._current_path:
            return

        # 현재 파일의 백업들만 찾기
        pattern = f"{self._current_path.stem}_*{self._current_path.suffix}"
        backups = sorted(self._backup_dir.glob(pattern), reverse=True)

        # 최대 개수 초과 시 삭제
        for backup in backups[self._max_backups:]:
            try:
                backup.unlink()
            except Exception:
                pass

    def get_backups(self) -> List[Path]:
        """백업 파일 목록 반환 (최신순)"""
        if not self._backup_dir or not self._backup_dir.exists():
            return []

        if not self._current_path:
            return []

        pattern = f"{self._current_path.stem}_*{self._current_path.suffix}"
        return sorted(self._backup_dir.glob(pattern), reverse=True)

    def restore_backup(self, backup_path: Path) -> bool:
        """백업에서 복구

        Args:
            backup_path: 복구할 백업 파일 경로

        Returns:
            성공 여부
        """
        if not backup_path.exists():
            self.error_occurred.emit(f"백업 파일을 찾을 수 없습니다: {backup_path}")
            return False

        if not self._current_path:
            self.error_occurred.emit("현재 파일 경로가 설정되지 않았습니다.")
            return False

        try:
            # 현재 파일을 백업
            self._create_backup()

            # 백업 파일로 복구
            shutil.copy2(backup_path, self._current_path)
            return True

        except Exception as e:
            self.error_occurred.emit(f"복구 실패: {e}")
            return False


class BackupInfo:
    """백업 파일 정보"""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.size = path.stat().st_size if path.exists() else 0
        self.modified = datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else None

    @property
    def timestamp_str(self) -> str:
        """타임스탬프 문자열"""
        if self.modified:
            return self.modified.strftime("%Y-%m-%d %H:%M:%S")
        return "알 수 없음"

    @property
    def size_str(self) -> str:
        """파일 크기 문자열"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"


def get_backup_info_list(backup_dir: Path, file_stem: str, file_suffix: str) -> List[BackupInfo]:
    """백업 정보 목록 반환"""
    if not backup_dir.exists():
        return []

    pattern = f"{file_stem}_*{file_suffix}"
    backups = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return [BackupInfo(p) for p in backups]
