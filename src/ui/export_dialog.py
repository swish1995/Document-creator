"""내보내기 다이얼로그 모듈

내보내기 옵션을 설정하는 다이얼로그입니다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

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
    QPushButton,
    QCheckBox,
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

        self.setWindowTitle("내보내기")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self._setup_style()
        self._setup_ui()
        self._connect_signals()

    def _get_icon_path(self, icon_name: str) -> str:
        """아이콘 경로 반환"""
        return str(Path(__file__).parent.parent / "resources" / "icons" / f"{icon_name}.svg")

    def _setup_style(self):
        """다이얼로그 스타일 설정"""
        check_icon_path = self._get_icon_path("confirm").replace("\\", "/")
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
                image: url(__CHECK_ICON__);
            }
            QCheckBox::indicator:checked:disabled {
                background-color: #4a6a5a;
                border: 1px solid #3a5a4a;
                image: url(__CHECK_ICON__);
            }
            QCheckBox:disabled {
                color: #666666;
            }
            QCheckBox::indicator:disabled {
                background-color: #333333;
                border: 1px solid #444444;
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
        """.replace("__CHECK_ICON__", check_icon_path))

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
        self._template_label.setMinimumWidth(350)
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
        self._single_file_check.setChecked(True)  # 기본값: 체크
        options_layout.addWidget(self._single_file_check, 1, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)

        # 템플릿별 묶음 옵션
        self._group_by_template_check = QCheckBox("템플릿별로 묶음")
        self._group_by_template_check.setChecked(False)  # 기본값: 체크 해제 (행별로 출력)
        self._group_by_template_check.setToolTip(
            "체크 해제: 행별로 출력 (행1의 모든 템플릿 → 행2의 모든 템플릿)\n"
            "체크: 템플릿별로 출력 (템플릿1의 모든 행 → 템플릿2의 모든 행)"
        )
        options_layout.addWidget(self._group_by_template_check, 2, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(options_group)

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
        self._export_button.clicked.connect(self.accept)
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
        # PNG로 변경해도 체크 상태 유지 (비활성화만)

    def get_settings(self) -> dict:
        """설정값 반환"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_format = self._format_combo.currentText().lower()

        # PNG일 때는 단일 파일 옵션 무시
        single_file = self._single_file_check.isChecked() if output_format == "pdf" else False

        return {
            "format": output_format,
            "single_file": single_file,
            "group_by_template": self._group_by_template_check.isChecked(),
            "filename": f"안전문서_{timestamp}",
        }
