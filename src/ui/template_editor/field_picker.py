"""필드 선택 팝업 모듈

엑셀 컬럼 목록에서 필드를 선택하는 팝업입니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QFrame,
)


class FieldPicker(QFrame):
    """필드 선택 팝업

    엑셀 컬럼 목록에서 필드를 선택하여 플레이스홀더로 삽입합니다.
    """

    # 시그널
    field_selected = pyqtSignal(str, str)  # field_id, field_label
    canceled = pyqtSignal()

    def __init__(
        self,
        fields: List[Dict[str, Any]],
        position: QPoint,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._fields = fields
        self._filtered_fields = fields.copy()

        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._setup_ui()
        self._load_fields()

        # 위치 설정
        self.move(position)
        self.setFixedSize(250, 300)

    def _setup_ui(self):
        """UI 초기화"""
        self.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 8px;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #0d47a1;
            }
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton#insertBtn {
                background-color: #0d47a1;
                border: none;
            }
            QPushButton#insertBtn:hover {
                background-color: #1565c0;
            }
            QLabel {
                color: #888888;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 헤더
        header = QLabel("📋 필드 선택")
        header.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        # 검색 입력
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("🔍 검색...")
        self._search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self._search_edit)

        # 필드 목록
        self._field_list = QListWidget()
        self._field_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._field_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._field_list, 1)

        # 선택된 필드 정보
        self._info_label = QLabel("필드를 선택하세요")
        layout.addWidget(self._info_label)

        # 버튼
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)

        self._insert_btn = QPushButton("삽입")
        self._insert_btn.setObjectName("insertBtn")
        self._insert_btn.setEnabled(False)
        self._insert_btn.clicked.connect(self._on_insert)
        button_layout.addWidget(self._insert_btn)

        layout.addLayout(button_layout)

        # 포커스 설정
        self._search_edit.setFocus()

    def _load_fields(self):
        """필드 목록 로드"""
        self._field_list.clear()

        for field in self._filtered_fields:
            field_id = field.get("id", "")
            label = field.get("label", field_id)
            excel_col = field.get("excel_column", "")

            item = QListWidgetItem()
            if excel_col:
                item.setText(f"{label}\n  → {excel_col}")
            else:
                item.setText(label)

            item.setData(Qt.ItemDataRole.UserRole, field)
            self._field_list.addItem(item)

    def _on_search(self, text: str):
        """검색어 변경"""
        text = text.lower().strip()

        if not text:
            self._filtered_fields = self._fields.copy()
        else:
            self._filtered_fields = [
                f
                for f in self._fields
                if text in f.get("id", "").lower()
                or text in f.get("label", "").lower()
                or text in f.get("excel_column", "").lower()
            ]

        self._load_fields()

    def _on_selection_changed(self):
        """선택 변경"""
        items = self._field_list.selectedItems()
        if items:
            field = items[0].data(Qt.ItemDataRole.UserRole)
            self._info_label.setText(
                f"{{ {field.get('id', '')} }} → {field.get('excel_column', '')}"
            )
            self._insert_btn.setEnabled(True)
        else:
            self._info_label.setText("필드를 선택하세요")
            self._insert_btn.setEnabled(False)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """아이템 더블 클릭"""
        self._on_insert()

    def _on_insert(self):
        """삽입 버튼 클릭"""
        items = self._field_list.selectedItems()
        if not items:
            return

        field = items[0].data(Qt.ItemDataRole.UserRole)
        field_id = field.get("id", "")
        field_label = field.get("label", field_id)

        self.field_selected.emit(field_id, field_label)
        self.close()

    def _on_cancel(self):
        """취소 버튼 클릭"""
        self.canceled.emit()
        self.close()

    def keyPressEvent(self, event):
        """키 입력 이벤트"""
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self._on_insert()
        else:
            super().keyPressEvent(event)


class FieldListWidget(QWidget):
    """필드 목록 위젯 (매핑 뷰 왼쪽 패널용)"""

    # 시그널
    field_selected = pyqtSignal(dict)  # field 정보
    field_drag_started = pyqtSignal(dict)  # field 정보

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._fields: List[Dict[str, Any]] = []
        self._mapped_fields: set = set()

        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        self.setStyleSheet("""
            QWidget {
                background-color: #333333;
            }
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 검색
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("🔍 필드 검색...")
        self._search_edit.textChanged.connect(self._filter_fields)
        layout.addWidget(self._search_edit)

        # 필드 목록
        self._list = QListWidget()
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list, 1)

        # 통계
        self._stats_label = QLabel("0/0 매핑됨")
        self._stats_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self._stats_label)

    def set_fields(self, fields: List[Dict[str, Any]]):
        """필드 목록 설정"""
        self._fields = fields
        self._refresh_list()

    def set_mapped_fields(self, mapped_ids: set):
        """매핑된 필드 ID 설정"""
        self._mapped_fields = mapped_ids
        self._refresh_list()

    def _refresh_list(self):
        """목록 새로고침"""
        self._list.clear()
        search_text = self._search_edit.text().lower()

        for field in self._fields:
            field_id = field.get("id", "")
            label = field.get("label", field_id)

            # 검색 필터
            if search_text and search_text not in label.lower() and search_text not in field_id.lower():
                continue

            is_mapped = field_id in self._mapped_fields
            status = "✓" if is_mapped else "○"

            item = QListWidgetItem(f"{status} {label}")
            item.setData(Qt.ItemDataRole.UserRole, field)

            if is_mapped:
                item.setForeground(Qt.GlobalColor.green)

            self._list.addItem(item)

        # 통계 업데이트
        mapped_count = len(self._mapped_fields)
        total_count = len(self._fields)
        self._stats_label.setText(f"{mapped_count}/{total_count} 매핑됨")

    def _filter_fields(self):
        """필드 필터링"""
        self._refresh_list()

    def _on_item_clicked(self, item: QListWidgetItem):
        """아이템 클릭"""
        field = item.data(Qt.ItemDataRole.UserRole)
        if field:
            self.field_selected.emit(field)
