"""템플릿 패널 위젯 모듈

단일 템플릿을 선택하고 미리보기를 표시하는 패널입니다.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QFrame,
    QLabel,
)

from src.core.template_manager import TemplateManager, Template
from src.core.mapper import Mapper, get_mapping_file_path
from src.ui.preview_widget import PreviewWidget
from src.ui.mapping_dialog import MappingDialog

logger = logging.getLogger(__name__)


class TemplatePanel(QFrame):
    """템플릿 패널 위젯

    템플릿 선택과 미리보기를 담당하는 개별 패널입니다.
    """

    # 시그널
    template_changed = pyqtSignal(str)  # 템플릿 변경 (템플릿 이름)
    close_requested = pyqtSignal()       # 패널 닫기 요청

    def __init__(self, template_manager: TemplateManager, parent=None):
        super().__init__(parent)
        self._template_manager = template_manager
        self._current_template: Optional[Template] = None
        self._mapper: Optional[Mapper] = None
        self._excel_headers: list = []
        self._excel_file_path: Optional[str] = None
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444444;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 상단 툴바
        toolbar = QHBoxLayout()

        # 템플릿 선택 드롭다운
        self._template_combo = QComboBox()
        self._template_combo.addItem("템플릿 선택...")
        for name in self._template_manager.template_names:
            self._template_combo.addItem(name)
        self._template_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #666666;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #888888;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #ffffff;
                selection-background-color: #0d47a1;
                border: 1px solid #555555;
            }
        """)
        self._template_combo.currentTextChanged.connect(self._on_template_changed)
        toolbar.addWidget(self._template_combo, 1)

        # 매핑 버튼
        self._mapping_button = QPushButton("🔧 매핑")
        self._mapping_button.setEnabled(False)
        self._mapping_button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 12px;
                min-height: 20px;
            }
            QPushButton:hover:enabled {
                background-color: #4a4a4a;
                border-color: #666666;
            }
            QPushButton:disabled {
                color: #666666;
            }
        """)
        self._mapping_button.clicked.connect(self._on_mapping_clicked)
        toolbar.addWidget(self._mapping_button)

        # 닫기 버튼
        self._close_button = QPushButton("×")
        self._close_button.setFixedSize(24, 24)
        self._close_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: #666;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
                color: white;
                border-radius: 12px;
            }
        """)
        self._close_button.clicked.connect(self.close_requested.emit)
        toolbar.addWidget(self._close_button)

        layout.addLayout(toolbar)

        # 매핑 상태 라벨
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("""
            QLabel {
                color: #bbbbbb;
                font-size: 11px;
                padding: 2px 5px;
            }
        """)
        layout.addWidget(self._status_label)

        # 미리보기 영역
        self._preview_widget = PreviewWidget()
        self._preview_widget.setMinimumHeight(150)
        layout.addWidget(self._preview_widget, 1)

    def _on_template_changed(self, text: str):
        """템플릿 선택 변경"""
        if text == "템플릿 선택...":
            self._current_template = None
            self._mapper = None
            self._preview_widget.clear()
            return

        template = self._template_manager.get(text)
        if template:
            self._current_template = template
            self._preview_widget.set_template(template)

            # 매퍼 생성 (엑셀 헤더가 있는 경우)
            if self._excel_headers:
                self._mapper = Mapper(template.fields, self._excel_headers)
                self._auto_detect_mapping()
                self._update_mapping_status()
                self._mapping_button.setEnabled(True)

            self.template_changed.emit(text)

    def set_template(self, name: str):
        """템플릿 설정"""
        index = self._template_combo.findText(name)
        if index >= 0:
            self._template_combo.setCurrentIndex(index)

    def set_excel_headers(self, headers: list):
        """엑셀 헤더 설정"""
        self._excel_headers = headers
        if self._current_template:
            self._mapper = Mapper(self._current_template.fields, headers)
            self._auto_detect_mapping()
            self._update_mapping_status()
            self._mapping_button.setEnabled(True)

    def set_excel_file_path(self, file_path: str):
        """엑셀 파일 경로 설정"""
        self._excel_file_path = file_path

    def update_preview(self, row_data: Dict[str, Any]):
        """미리보기 업데이트"""
        if self._mapper:
            mapped_data = self._mapper.apply(row_data)
            self._preview_widget.update_data(mapped_data)
        else:
            self._preview_widget.update_data(row_data)

    @property
    def current_template_name(self) -> Optional[str]:
        """현재 선택된 템플릿 이름"""
        if self._current_template:
            return self._current_template.name
        return None

    @property
    def is_active(self) -> bool:
        """템플릿이 선택되어 있는지 여부"""
        return self._current_template is not None

    def get_template(self) -> Optional[Template]:
        """현재 템플릿 반환"""
        return self._current_template

    def get_mapper(self) -> Optional[Mapper]:
        """현재 매퍼 반환"""
        return self._mapper

    def _auto_detect_mapping(self):
        """매핑 파일 자동 탐지 및 로드"""
        if not self._excel_file_path or not self._current_template or not self._mapper:
            return

        mapping_path = get_mapping_file_path(
            self._excel_file_path, self._current_template.name
        )

        if Path(mapping_path).exists():
            try:
                self._mapper.load_from_file(mapping_path)
                logger.debug(f"매핑 파일 자동 로드: {mapping_path}")
            except Exception as e:
                logger.warning(f"매핑 파일 로드 실패: {e}")

    def _update_mapping_status(self):
        """매핑 상태 업데이트"""
        if not self._mapper:
            self._status_label.setText("")
            return

        unmapped = self._mapper.get_unmapped_fields()
        total = len(self._mapper._template_fields)
        mapped = total - len(unmapped)

        if len(unmapped) == 0:
            self._status_label.setText(f"매핑: 완료")
            self._status_label.setStyleSheet("""
                QLabel {
                    color: #4caf50;
                    font-size: 11px;
                    padding: 2px 5px;
                }
            """)
        else:
            self._status_label.setText(f"매핑: {mapped}/{total}")
            self._status_label.setStyleSheet("""
                QLabel {
                    color: #ff9800;
                    font-size: 11px;
                    padding: 2px 5px;
                }
            """)

    def _on_mapping_clicked(self):
        """매핑 버튼 클릭"""
        if not self._mapper or not self._current_template:
            return

        excel_file = Path(self._excel_file_path).name if self._excel_file_path else ""

        dialog = MappingDialog(
            self._mapper, self._current_template.name, excel_file, self
        )
        dialog.mapping_changed.connect(self._on_mapping_changed)

        if dialog.exec():
            self._update_mapping_status()

    def _on_mapping_changed(self, mapping: Dict[str, str]):
        """매핑 변경 시"""
        logger.debug(f"매핑 변경: {mapping}")
        self._update_mapping_status()
