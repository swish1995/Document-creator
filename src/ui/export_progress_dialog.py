"""내보내기 진행 다이얼로그 모듈

내보내기 진행 상황을 표시하는 다이얼로그입니다.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
)


class ExportWorker(QThread):
    """내보내기 작업 스레드"""

    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(list)  # generated files
    error = pyqtSignal(str)  # error message

    def __init__(
        self,
        generator,
        template_names: List[str],
        rows_data: List[Dict[str, Any]],
        output_dir: Path,
        settings: dict,
        excel_headers: Optional[List[str]] = None,
    ):
        super().__init__()
        self._generator = generator
        self._template_names = template_names
        self._rows_data = rows_data
        self._output_dir = output_dir
        self._settings = settings
        self._excel_headers = excel_headers

    def run(self):
        """작업 실행"""
        try:
            files = self._generator.batch_generate_all(
                template_names=self._template_names,
                rows_data=self._rows_data,
                output_dir=self._output_dir,
                filename_pattern=self._settings.get("filename_pattern", "{template}_{row:03d}.html"),
                structure=self._settings.get("structure", "flat"),
                excel_headers=self._excel_headers,
                progress_callback=self._on_progress,
            )
            self.finished.emit(files)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, current: int, total: int, filename: str):
        """진행 상황 콜백"""
        self.progress.emit(current, total, filename)

    def cancel(self):
        """취소"""
        self._generator.cancel()


class ExportProgressDialog(QDialog):
    """내보내기 진행 다이얼로그"""

    def __init__(
        self,
        generator,
        template_names: List[str],
        rows_data: List[Dict[str, Any]],
        output_dir: Path,
        settings: dict,
        excel_headers: Optional[List[str]] = None,
        parent=None
    ):
        super().__init__(parent)
        self._generator = generator
        self._template_names = template_names
        self._rows_data = rows_data
        self._output_dir = output_dir
        self._settings = settings
        self._excel_headers = excel_headers

        self._worker: Optional[ExportWorker] = None
        self._generated_files: List[Path] = []
        self._start_time = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)

        self.setWindowTitle("내보내기 중...")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 진행률
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        total = len(self._template_names) * len(self._rows_data)
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # 상태 정보
        info_layout = QHBoxLayout()

        self._status_label = QLabel("준비 중...")
        info_layout.addWidget(self._status_label)

        info_layout.addStretch()

        self._time_label = QLabel("경과: 0:00")
        info_layout.addWidget(self._time_label)

        layout.addLayout(info_layout)

        # 현재 파일
        self._current_file_label = QLabel("")
        self._current_file_label.setStyleSheet("color: #666;")
        layout.addWidget(self._current_file_label)

        # 로그
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(100)
        layout.addWidget(self._log_text)

        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_button = QPushButton("취소")
        self._cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_button)

        self._open_folder_button = QPushButton("폴더 열기")
        self._open_folder_button.clicked.connect(self._on_open_folder)
        self._open_folder_button.setEnabled(False)
        self._open_folder_button.setVisible(False)
        button_layout.addWidget(self._open_folder_button)

        self._close_button = QPushButton("닫기")
        self._close_button.clicked.connect(self.accept)
        self._close_button.setEnabled(False)
        self._close_button.setVisible(False)
        button_layout.addWidget(self._close_button)

        layout.addLayout(button_layout)

    def showEvent(self, event):
        """다이얼로그 표시 시 작업 시작"""
        super().showEvent(event)
        QTimer.singleShot(100, self._start_export)

    def _start_export(self):
        """내보내기 시작"""
        self._start_time = time.time()
        self._timer.start(1000)

        self._worker = ExportWorker(
            generator=self._generator,
            template_names=self._template_names,
            rows_data=self._rows_data,
            output_dir=self._output_dir,
            settings=self._settings,
            excel_headers=self._excel_headers,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

        self._log("내보내기 시작...")

    def _on_progress(self, current: int, total: int, filename: str):
        """진행 상황 업데이트"""
        self._progress_bar.setValue(current)
        self._status_label.setText(f"{current} / {total}")
        self._current_file_label.setText(f"생성 중: {filename}")

    def _on_finished(self, files: List[Path]):
        """완료"""
        self._timer.stop()
        self._generated_files = files

        elapsed = time.time() - self._start_time
        self._status_label.setText(f"완료! {len(files)}개 파일 생성됨")
        self._current_file_label.setText("")
        self._log(f"완료: {len(files)}개 파일 생성 ({elapsed:.1f}초)")

        self._cancel_button.setVisible(False)
        self._open_folder_button.setEnabled(True)
        self._open_folder_button.setVisible(True)
        self._close_button.setEnabled(True)
        self._close_button.setVisible(True)

    def _on_error(self, message: str):
        """에러"""
        self._timer.stop()
        self._status_label.setText("오류 발생!")
        self._status_label.setStyleSheet("color: red;")
        self._log(f"오류: {message}")

        self._cancel_button.setVisible(False)
        self._close_button.setEnabled(True)
        self._close_button.setVisible(True)

    def _on_cancel(self):
        """취소"""
        if self._worker:
            self._worker.cancel()
            self._log("취소됨")
            self._status_label.setText("취소됨")

    def _on_open_folder(self):
        """폴더 열기"""
        import subprocess
        import sys

        if sys.platform == "darwin":
            subprocess.run(["open", str(self._output_dir)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", str(self._output_dir)])
        else:
            subprocess.run(["xdg-open", str(self._output_dir)])

    def _update_time(self):
        """경과 시간 업데이트"""
        elapsed = int(time.time() - self._start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self._time_label.setText(f"경과: {minutes}:{seconds:02d}")

    def _log(self, message: str):
        """로그 추가"""
        self._log_text.append(message)

    def get_generated_files(self) -> List[Path]:
        """생성된 파일 목록"""
        return self._generated_files
