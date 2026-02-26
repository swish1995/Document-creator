"""다른 이름으로 저장 다이얼로그"""

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
)


class SaveAsDialog(QDialog):
    """다른 이름으로 저장 다이얼로그

    Args:
        original_name: 원본 템플릿 이름
        categories: 카테고리 목록 [{"id": ..., "name": ...}, ...]
        default_category: 기본 카테고리 ID
        existing_names: 기존 사용자 템플릿 이름 목록 (중복 검사용)
    """

    def __init__(
        self,
        original_name: str = "",
        categories: Optional[List[Dict[str, Any]]] = None,
        default_category: str = "",
        existing_names: Optional[List[str]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._existing_names = existing_names or []
        self._categories = categories or []

        self.setWindowTitle("다른 이름으로 저장")
        self.setMinimumWidth(350)
        self._setup_style()

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 이름 입력
        layout.addWidget(QLabel("템플릿 이름:"))
        self._name_input = QLineEdit()
        self._name_input.setText(f"{original_name}_복사본")
        self._name_input.selectAll()
        self._name_input.textChanged.connect(self._validate)
        layout.addWidget(self._name_input)

        # 경고 라벨
        self._warning_label = QLabel()
        self._warning_label.setObjectName("warningLabel")
        self._warning_label.setVisible(False)
        layout.addWidget(self._warning_label)

        # 카테고리 선택
        layout.addWidget(QLabel("카테고리:"))
        self._category_combo = QComboBox()
        for cat in self._categories:
            self._category_combo.addItem(cat.get("name", ""), cat.get("id", ""))
        # 기본 카테고리 선택
        for i in range(self._category_combo.count()):
            if self._category_combo.itemData(i) == default_category:
                self._category_combo.setCurrentIndex(i)
                break
        layout.addWidget(self._category_combo)

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._btn_cancel = QPushButton("취소")
        self._btn_cancel.setObjectName("cancelButton")
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)

        self._btn_ok = QPushButton("저장")
        self._btn_ok.setObjectName("okButton")
        self._btn_ok.setDefault(True)
        self._btn_ok.clicked.connect(self._on_ok)
        btn_layout.addWidget(self._btn_ok)

        layout.addLayout(btn_layout)

    def _setup_style(self):
        """다크 테마 스타일 설정"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
            QLabel#warningLabel {
                color: #ff6b6b;
                font-size: 11px;
            }
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #0d47a1;
            }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
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
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                selection-background-color: #0d47a1;
                color: #ffffff;
            }
            QPushButton#cancelButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a7a7a, stop:1 #6a6a6a);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton#cancelButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a8a8a, stop:1 #7a7a7a);
            }
            QPushButton#cancelButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a6a6a, stop:1 #7a7a7a);
            }
            QPushButton#okButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5ab87a, stop:1 #4aa86a);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton#okButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ac88a, stop:1 #5ab87a);
            }
            QPushButton#okButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4aa86a, stop:1 #5ab87a);
            }
            QPushButton#okButton:disabled {
                background: #3a3a3a;
                color: #666666;
            }
        """)

    def get_name(self) -> str:
        """입력된 이름 반환"""
        return self._name_input.text().strip()

    def get_category(self) -> str:
        """선택된 카테고리 ID 반환"""
        return self._category_combo.currentData() or ""

    def is_valid(self) -> bool:
        """입력값 유효성 검사"""
        name = self.get_name()
        if not name:
            return False
        if name in self._existing_names:
            return False
        return True

    def _validate(self):
        """입력값 실시간 검증"""
        name = self.get_name()
        if not name:
            self._warning_label.setText("이름을 입력해주세요.")
            self._warning_label.setVisible(True)
            self._btn_ok.setEnabled(False)
        elif name in self._existing_names:
            self._warning_label.setText(f"'{name}'은(는) 이미 존재하는 이름입니다.")
            self._warning_label.setVisible(True)
            self._btn_ok.setEnabled(False)
        else:
            self._warning_label.setVisible(False)
            self._btn_ok.setEnabled(True)

    def _on_ok(self):
        """확인 버튼 클릭"""
        if self.is_valid():
            self.accept()
