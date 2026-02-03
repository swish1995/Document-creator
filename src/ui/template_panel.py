"""템플릿 패널 위젯 모듈

단일 템플릿을 선택하고 미리보기를 표시하는 패널입니다.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QFrame,
)

from src.core.template_manager import TemplateManager, Template
from src.core.mapper import Mapper
from src.ui.preview_widget import PreviewWidget


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
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)

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
        self._template_combo.currentTextChanged.connect(self._on_template_changed)
        toolbar.addWidget(self._template_combo, 1)

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
