"""내보내기 다이얼로그 모듈

내보내기 옵션을 설정하는 다이얼로그입니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QDialogButtonBox,
)


class ExportDialog(QDialog):
    """내보내기 설정 다이얼로그"""

    def __init__(
        self,
        row_count: int,
        template_names: List[str],
        parent=None
    ):
        super().__init__(parent)
        self._row_count = row_count
        self._template_names = template_names
        self._output_dir: Optional[Path] = None

        self.setWindowTitle("내보내기")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 요약 정보
        summary_group = QGroupBox("내보내기 요약")
        summary_layout = QFormLayout(summary_group)

        self._row_label = QLabel(f"{self._row_count}행")
        summary_layout.addRow("선택된 행:", self._row_label)

        self._template_label = QLabel(f"{len(self._template_names)}개 ({', '.join(self._template_names)})")
        summary_layout.addRow("템플릿:", self._template_label)

        total = self._row_count * len(self._template_names)
        self._total_label = QLabel(f"<b>{total}개 파일</b>")
        summary_layout.addRow("생성 파일 수:", self._total_label)

        layout.addWidget(summary_group)

        # 출력 옵션
        options_group = QGroupBox("출력 옵션")
        options_layout = QFormLayout(options_group)

        # 출력 형식
        self._format_combo = QComboBox()
        self._format_combo.addItems(["HTML", "PDF (준비 중)", "PNG (준비 중)"])
        options_layout.addRow("출력 형식:", self._format_combo)

        # 폴더 구조
        self._structure_combo = QComboBox()
        self._structure_combo.addItems([
            "단일 폴더 (모든 파일)",
            "템플릿별 폴더",
            "행별 폴더"
        ])
        options_layout.addRow("폴더 구조:", self._structure_combo)

        # 파일명 패턴
        self._pattern_edit = QLineEdit("{template}_{row:03d}.html")
        options_layout.addRow("파일명 패턴:", self._pattern_edit)

        layout.addWidget(options_group)

        # 저장 경로
        path_group = QGroupBox("저장 위치")
        path_layout = QHBoxLayout(path_group)

        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText("저장 폴더를 선택하세요...")
        path_layout.addWidget(self._path_edit)

        browse_button = QPushButton("찾아보기...")
        browse_button.clicked.connect(self._on_browse)
        path_layout.addWidget(browse_button)

        layout.addWidget(path_group)

        # 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        self._ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setText("내보내기")
        self._ok_button.setEnabled(False)

        layout.addWidget(button_box)

    def _on_browse(self):
        """폴더 선택"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "저장 폴더 선택",
            str(Path.home())
        )
        if dir_path:
            self._output_dir = Path(dir_path)
            self._path_edit.setText(dir_path)
            self._ok_button.setEnabled(True)

    def _on_accept(self):
        """확인 버튼"""
        if self._output_dir:
            self.accept()

    def get_settings(self) -> dict:
        """설정값 반환"""
        structure_map = {
            0: "flat",
            1: "by_template",
            2: "by_row"
        }

        return {
            "output_dir": self._output_dir,
            "format": self._format_combo.currentText().split()[0].lower(),
            "structure": structure_map.get(self._structure_combo.currentIndex(), "flat"),
            "filename_pattern": self._pattern_edit.text(),
        }
