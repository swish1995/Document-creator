"""내보내기 다이얼로그 모듈

내보내기 옵션을 설정하는 다이얼로그입니다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QFrame,
    QWidget,
)


class ExportDialog(QDialog):
    """내보내기 설정 다이얼로그"""

    # 버튼별 색상 정의 (기본색, 어두운색, 밝은색)
    BUTTON_COLORS = {
        'export': ('#5ab87a', '#4aa86a', '#6ac88a'),   # 초록색 (내보내기)
        'cancel': ('#7a7a7a', '#6a6a6a', '#8a8a8a'),   # 회색 (취소)
        'browse': ('#5a7ab8', '#4a6aa8', '#6a8ac8'),   # 파란색 (찾아보기)
    }

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
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        self._setup_style()
        self._setup_ui()
        self._connect_signals()

    def _get_icon_path(self, icon_name: str) -> str:
        """아이콘 경로 반환"""
        return str(Path(__file__).parent.parent / "resources" / "icons" / f"{icon_name}.svg")

    def _get_button_style(self, color_key: str) -> str:
        """버튼 스타일 생성 (그라데이션)"""
        colors = self.BUTTON_COLORS.get(color_key, self.BUTTON_COLORS['cancel'])
        base, dark, light = colors

        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {base}, stop:1 {dark});
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {light}, stop:1 {base});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {dark}, stop:1 {base});
            }}
            QPushButton:disabled {{
                background: #444444;
                color: #666666;
            }}
        """

    def _setup_style(self):
        """다이얼로그 스타일 설정"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QGroupBox {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 6px;
                margin-top: 12px;
                padding: 16px;
                font-size: 12px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 12px;
                background-color: #333333;
                border-radius: 4px;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
                background-color: transparent;
            }
            QLabel[class="key"] {
                color: #999999;
                font-weight: normal;
                background-color: transparent;
            }
            QLabel[class="value"] {
                color: #ffffff;
                font-weight: bold;
                background-color: transparent;
            }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
                min-width: 150px;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 1px solid #666666;
                background-color: #4a4a4a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                selection-background-color: #0d47a1;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:hover {
                border: 1px solid #666666;
            }
            QLineEdit:focus {
                border: 1px solid #5a7ab8;
            }
            QLineEdit:read-only {
                background-color: #333333;
                color: #999999;
            }
            QCheckBox {
                color: #cccccc;
                font-size: 12px;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #555555;
                background-color: #3a3a3a;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #666666;
                background-color: #4a4a4a;
            }
            QCheckBox::indicator:checked {
                background-color: #5ab87a;
                border: 1px solid #4aa86a;
            }
            QCheckBox:disabled {
                color: #666666;
            }
            QCheckBox::indicator:disabled {
                background-color: #333333;
                border: 1px solid #444444;
            }
            /* 찾아보기 버튼 - 파란색 */
            QPushButton#browseButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a7ab8, stop:1 #4a6aa8);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#browseButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a8ac8, stop:1 #5a7ab8);
            }
            QPushButton#browseButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6aa8, stop:1 #5a7ab8);
            }
            /* 취소 버튼 - 회색 */
            QPushButton#cancelButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a7a7a, stop:1 #6a6a6a);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#cancelButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a8a8a, stop:1 #7a7a7a);
            }
            QPushButton#cancelButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a6a6a, stop:1 #7a7a7a);
            }
            /* 내보내기 버튼 - 초록색 */
            QPushButton#exportButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5ab87a, stop:1 #4aa86a);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#exportButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ac88a, stop:1 #5ab87a);
            }
            QPushButton#exportButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4aa86a, stop:1 #5ab87a);
            }
            QPushButton#exportButton:disabled {
                background: #444444;
                color: #666666;
            }
        """)

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # 요약 정보
        summary_group = QGroupBox("내보내기 요약")
        summary_layout = QGridLayout(summary_group)
        summary_layout.setSpacing(12)
        summary_layout.setColumnStretch(1, 1)

        # 선택된 행
        row_key = QLabel("선택된 행")
        row_key.setProperty("class", "key")
        self._row_label = QLabel(f"{self._row_count}행")
        self._row_label.setProperty("class", "value")
        summary_layout.addWidget(row_key, 0, 0, Qt.AlignmentFlag.AlignLeft)
        summary_layout.addWidget(self._row_label, 0, 1, Qt.AlignmentFlag.AlignLeft)

        # 템플릿
        template_key = QLabel("템플릿")
        template_key.setProperty("class", "key")
        self._template_label = QLabel(f"{len(self._template_names)}개 ({', '.join(self._template_names)})")
        self._template_label.setProperty("class", "value")
        self._template_label.setWordWrap(True)
        self._template_label.setMinimumWidth(400)
        summary_layout.addWidget(template_key, 1, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        summary_layout.addWidget(self._template_label, 1, 1, Qt.AlignmentFlag.AlignLeft)

        # 생성 파일 수
        total = self._row_count * len(self._template_names)
        total_key = QLabel("생성 파일 수")
        total_key.setProperty("class", "key")
        self._total_label = QLabel(f"{total}개 파일")
        self._total_label.setProperty("class", "value")
        self._total_label.setStyleSheet("color: #5ab87a; font-weight: bold;")
        summary_layout.addWidget(total_key, 2, 0, Qt.AlignmentFlag.AlignLeft)
        summary_layout.addWidget(self._total_label, 2, 1, Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(summary_group)

        # 출력 옵션
        options_group = QGroupBox("출력 옵션")
        options_layout = QGridLayout(options_group)
        options_layout.setSpacing(12)
        options_layout.setColumnStretch(1, 1)

        # 출력 형식
        format_key = QLabel("출력 형식")
        format_key.setProperty("class", "key")
        self._format_combo = QComboBox()
        self._format_combo.addItems(["PDF", "PNG"])
        options_layout.addWidget(format_key, 0, 0, Qt.AlignmentFlag.AlignLeft)
        options_layout.addWidget(self._format_combo, 0, 1, Qt.AlignmentFlag.AlignLeft)

        # 단일 파일 옵션 (PDF일 때만)
        self._single_file_check = QCheckBox("단일 파일로 병합 (PDF만 해당)")
        self._single_file_check.setEnabled(True)  # PDF가 기본 선택이므로 활성화
        options_layout.addWidget(self._single_file_check, 1, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)

        # 폴더 구조
        structure_key = QLabel("폴더 구조")
        structure_key.setProperty("class", "key")
        self._structure_combo = QComboBox()
        self._structure_combo.addItems([
            "단일 폴더 (모든 파일)",
            "템플릿별 폴더",
            "행별 폴더"
        ])
        options_layout.addWidget(structure_key, 2, 0, Qt.AlignmentFlag.AlignLeft)
        options_layout.addWidget(self._structure_combo, 2, 1, Qt.AlignmentFlag.AlignLeft)

        # 파일 이름
        filename_key = QLabel("파일 이름")
        filename_key.setProperty("class", "key")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._filename_edit = QLineEdit(f"안전문서_{timestamp}")
        self._filename_edit.setMinimumWidth(250)
        options_layout.addWidget(filename_key, 3, 0, Qt.AlignmentFlag.AlignLeft)
        options_layout.addWidget(self._filename_edit, 3, 1, Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(options_group)

        # 저장 경로
        path_group = QGroupBox("저장 위치")
        path_layout = QHBoxLayout(path_group)
        path_layout.setSpacing(12)

        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText("저장 폴더를 선택하세요...")
        path_layout.addWidget(self._path_edit)

        self._browse_button = QPushButton(" 찾아보기")
        self._browse_button.setObjectName("browseButton")
        self._browse_button.setIcon(QIcon(self._get_icon_path("load")))
        self._browse_button.clicked.connect(self._on_browse)
        path_layout.addWidget(self._browse_button)

        layout.addWidget(path_group)

        # 스페이서
        layout.addStretch()

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        # 취소 버튼
        self._cancel_button = QPushButton(" 취소")
        self._cancel_button.setObjectName("cancelButton")
        self._cancel_button.setIcon(QIcon(self._get_icon_path("cancel")))
        self._cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_button)

        # 내보내기 버튼
        self._export_button = QPushButton(" 내보내기")
        self._export_button.setObjectName("exportButton")
        self._export_button.setIcon(QIcon(self._get_icon_path("export")))
        self._export_button.setEnabled(False)  # 저장 위치가 없으면 비활성화
        self._export_button.clicked.connect(self._on_accept)
        button_layout.addWidget(self._export_button)

        layout.addLayout(button_layout)

    def _connect_signals(self):
        """시그널 연결"""
        # 출력 형식 변경 시 단일 파일 옵션 활성화/비활성화
        self._format_combo.currentTextChanged.connect(self._on_format_changed)

    def _on_format_changed(self, text: str):
        """출력 형식 변경"""
        is_pdf = text == "PDF"
        self._single_file_check.setEnabled(is_pdf)
        if not is_pdf:
            self._single_file_check.setChecked(False)

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
            self._export_button.setEnabled(True)

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
            "format": self._format_combo.currentText().lower(),
            "single_file": self._single_file_check.isChecked(),
            "structure": structure_map.get(self._structure_combo.currentIndex(), "flat"),
            "filename": self._filename_edit.text(),
        }
