"""엑셀 데이터 뷰어 위젯

엑셀 데이터를 테이블 형태로 표시하고 행 선택 기능을 제공합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from PyQt6.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QPushButton,
    QSpinBox,
    QLabel,
    QHeaderView,
    QFileDialog,
)

from src.core.excel_loader import ExcelLoader, ExcelLoaderError


class ExcelTableModel(QAbstractTableModel):
    """엑셀 데이터 테이블 모델"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._headers: List[str] = []
        self._data: List[Dict[str, Any]] = []
        self._selected_rows: Set[int] = set()
        self._preview_row: int = 0

    def load_data(self, headers: List[str], data: List[Dict[str, Any]]):
        """데이터 로드"""
        self.beginResetModel()
        self._headers = headers
        self._data = data
        self._selected_rows.clear()
        self._preview_row = 0
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        # 체크박스 컬럼 + 데이터 컬럼
        return len(self._headers) + 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                # 체크박스 컬럼 - 텍스트 없음
                return None
            else:
                header = self._headers[col - 1]
                return str(self._data[row].get(header, ""))

        elif role == Qt.ItemDataRole.CheckStateRole:
            if col == 0:
                return Qt.CheckState.Checked if row in self._selected_rows else Qt.CheckState.Unchecked

        elif role == Qt.ItemDataRole.BackgroundRole:
            if row == self._preview_row:
                from PyQt6.QtGui import QColor
                return QColor(230, 240, 255)  # 미리보기 행 하이라이트

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 0:
                return "선택"
            elif section - 1 < len(self._headers):
                return self._headers[section - 1]
        elif orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return str(section + 1)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            row = index.row()
            if value == Qt.CheckState.Checked:
                self._selected_rows.add(row)
            else:
                self._selected_rows.discard(row)
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def get_selected_rows(self) -> List[int]:
        """선택된 행 인덱스 목록"""
        return sorted(list(self._selected_rows))

    def set_selected_rows(self, rows: Set[int]):
        """선택 행 설정"""
        self._selected_rows = rows
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
            [Qt.ItemDataRole.CheckStateRole]
        )

    def select_all(self):
        """모든 행 선택"""
        self._selected_rows = set(range(len(self._data)))
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
            [Qt.ItemDataRole.CheckStateRole]
        )

    def deselect_all(self):
        """모든 선택 해제"""
        self._selected_rows.clear()
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
            [Qt.ItemDataRole.CheckStateRole]
        )

    def toggle_row(self, row: int):
        """행 선택 토글"""
        if row in self._selected_rows:
            self._selected_rows.discard(row)
        else:
            self._selected_rows.add(row)
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])

    def set_preview_row(self, row: int):
        """미리보기 행 설정"""
        old_row = self._preview_row
        self._preview_row = row
        # 이전 행과 새 행 업데이트
        self.dataChanged.emit(
            self.index(old_row, 0),
            self.index(old_row, self.columnCount() - 1),
            [Qt.ItemDataRole.BackgroundRole]
        )
        self.dataChanged.emit(
            self.index(row, 0),
            self.index(row, self.columnCount() - 1),
            [Qt.ItemDataRole.BackgroundRole]
        )

    def get_preview_row(self) -> int:
        return self._preview_row


class ExcelViewer(QWidget):
    """엑셀 데이터 뷰어 위젯"""

    # 시그널
    preview_row_changed = pyqtSignal(int)  # 미리보기 행 변경
    selection_changed = pyqtSignal(list)   # 선택 변경 (행 인덱스 리스트)
    file_loaded = pyqtSignal(str, int)     # 파일 로드 완료 (파일명, 행 수)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loader: Optional[ExcelLoader] = None
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 상단 툴바
        toolbar = QHBoxLayout()

        # 파일 열기 버튼
        self._open_button = QPushButton("📂 파일 열기")
        self._open_button.clicked.connect(self._on_open_clicked)
        toolbar.addWidget(self._open_button)

        toolbar.addStretch()

        # 전체 선택 / 해제 버튼
        self._select_all_button = QPushButton("☑ 전체 선택")
        self._select_all_button.clicked.connect(self.select_all)
        self._select_all_button.setEnabled(False)
        toolbar.addWidget(self._select_all_button)

        self._deselect_all_button = QPushButton("☐ 선택 해제")
        self._deselect_all_button.clicked.connect(self.deselect_all)
        self._deselect_all_button.setEnabled(False)
        toolbar.addWidget(self._deselect_all_button)

        toolbar.addSpacing(20)

        # 미리보기 행 선택
        toolbar.addWidget(QLabel("미리보기 행:"))
        self._preview_row_spinbox = QSpinBox()
        self._preview_row_spinbox.setMinimum(1)
        self._preview_row_spinbox.setMaximum(1)
        self._preview_row_spinbox.setEnabled(False)
        self._preview_row_spinbox.valueChanged.connect(self._on_preview_row_changed)
        toolbar.addWidget(self._preview_row_spinbox)

        self._row_count_label = QLabel("/ 0")
        toolbar.addWidget(self._row_count_label)

        layout.addLayout(toolbar)

        # 테이블 뷰
        self._table_view = QTableView()
        self._model = ExcelTableModel(self)
        self._table_view.setModel(self._model)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.clicked.connect(self._on_table_clicked)

        # 모델 데이터 변경 시 선택 상태 업데이트
        self._model.dataChanged.connect(self._on_model_data_changed)

        layout.addWidget(self._table_view)

        # 하단 상태바
        status_bar = QHBoxLayout()
        self._selection_count_label = QLabel("선택됨: 0행")
        status_bar.addWidget(self._selection_count_label)
        status_bar.addStretch()

        layout.addLayout(status_bar)

    def _on_open_clicked(self):
        """파일 열기 버튼 클릭"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "엑셀 파일 열기",
            str(Path.home()),
            "Excel Files (*.xlsx *.xls);;All Files (*)",
        )
        if file_path:
            self.load_file(Path(file_path))

    def load_file(self, file_path: Path):
        """파일 로드"""
        self._loader = ExcelLoader()
        self._loader.load(file_path)

        headers = self._loader.get_headers()
        data = self._loader.get_all_rows()

        self._model.load_data(headers, data)

        # UI 업데이트
        self._select_all_button.setEnabled(True)
        self._deselect_all_button.setEnabled(True)
        self._preview_row_spinbox.setEnabled(True)
        self._preview_row_spinbox.setMaximum(len(data))
        self._preview_row_spinbox.setValue(1)
        self._row_count_label.setText(f"/ {len(data)}")
        self._update_selection_count()

        # 첫 번째 컬럼 너비 조정
        self._table_view.setColumnWidth(0, 50)

        self.file_loaded.emit(file_path.name, len(data))

    def _on_preview_row_changed(self, value: int):
        """미리보기 행 스핀박스 변경"""
        row_index = value - 1  # 1-based to 0-based
        self._model.set_preview_row(row_index)
        self.preview_row_changed.emit(row_index)

    def _on_table_clicked(self, index: QModelIndex):
        """테이블 클릭"""
        if index.column() == 0:
            # 체크박스 클릭 - 모델에서 처리됨
            pass
        else:
            # 데이터 컬럼 클릭 - 미리보기 행 변경
            row = index.row()
            self._preview_row_spinbox.setValue(row + 1)

    def _on_model_data_changed(self, topLeft, bottomRight, roles):
        """모델 데이터 변경"""
        if Qt.ItemDataRole.CheckStateRole in roles:
            self._update_selection_count()
            self.selection_changed.emit(self.get_selected_rows())

    def _update_selection_count(self):
        """선택 행 수 업데이트"""
        count = len(self._model.get_selected_rows())
        self._selection_count_label.setText(f"선택됨: {count}행")

    def select_all(self):
        """모든 행 선택"""
        self._model.select_all()

    def deselect_all(self):
        """모든 선택 해제"""
        self._model.deselect_all()

    def toggle_row_selection(self, row: int):
        """행 선택 토글"""
        self._model.toggle_row(row)

    def get_selected_rows(self) -> List[int]:
        """선택된 행 인덱스 목록"""
        return self._model.get_selected_rows()

    def set_preview_row(self, row: int):
        """미리보기 행 설정"""
        self._preview_row_spinbox.setValue(row + 1)

    def get_preview_row(self) -> int:
        """현재 미리보기 행 반환"""
        return self._model.get_preview_row()

    @property
    def row_count(self) -> int:
        """전체 행 수"""
        return self._model.rowCount()

    def get_row_data(self, row: int) -> Optional[Dict[str, Any]]:
        """특정 행 데이터 반환"""
        if self._loader:
            return self._loader.get_row(row)
        return None

    def get_selected_data(self) -> List[Dict[str, Any]]:
        """선택된 행 데이터 목록"""
        if self._loader:
            return self._loader.get_rows(self.get_selected_rows())
        return []
