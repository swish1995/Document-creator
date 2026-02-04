"""매핑 설정 다이얼로그"""

from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.mapper import Mapper


# 버튼별 색상 정의 (기본색, 어두운색, 밝은색)
BUTTON_COLORS = {
    'load': ('#b8a25a', '#a8924a', '#c8b26a'),      # 골드 (불러오기)
    'save': ('#5ab87a', '#4aa86a', '#6ac88a'),      # 초록색 (저장)
    'auto': ('#5a8ab8', '#4a7aa8', '#6a9ac8'),      # 하늘색 (자동 매핑)
    'reset': ('#b8825a', '#a8724a', '#c8926a'),     # 주황색 (초기화)
    'cancel': ('#7a7a7a', '#6a6a6a', '#8a8a8a'),    # 회색 (취소)
    'confirm': ('#5ab87a', '#4aa86a', '#6ac88a'),   # 초록색 (확인)
}


def _get_icon_path(icon_name: str) -> str:
    """아이콘 경로 반환"""
    return str(Path(__file__).parent.parent / "resources" / "icons" / f"{icon_name}.svg")


def _get_button_style(color_key: str) -> str:
    """버튼 스타일 생성 (그라데이션)"""
    colors = BUTTON_COLORS.get(color_key, BUTTON_COLORS['cancel'])
    base, dark, light = colors

    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {base}, stop:1 {dark});
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
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


class MappingDialog(QDialog):
    """매핑 설정 다이얼로그"""

    mapping_changed = pyqtSignal(dict)  # {field_id: excel_column}

    def __init__(
        self,
        mapper: Mapper,
        template_name: str,
        excel_file: str,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._mapper = mapper
        self._template_name = template_name
        self._excel_file = excel_file
        self._field_combos: Dict[str, QComboBox] = {}

        self._init_ui()
        self._load_current_mappings()
        self._apply_styles()

    def _init_ui(self) -> None:
        """UI 초기화"""
        self.setWindowTitle(f"매핑 설정: {self._template_name}")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # 헤더
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"파일: {self._excel_file}"))
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 버튼 툴바
        toolbar_layout = QHBoxLayout()

        self._load_btn = QPushButton(" 불러오기")
        self._load_btn.setIcon(QIcon(_get_icon_path("load")))
        self._load_btn.setIconSize(QSize(14, 14))
        self._load_btn.setFixedHeight(28)
        self._load_btn.setStyleSheet(_get_button_style('load'))
        self._load_btn.clicked.connect(self._on_load_clicked)
        toolbar_layout.addWidget(self._load_btn)

        self._save_btn = QPushButton(" 저장")
        self._save_btn.setIcon(QIcon(_get_icon_path("save")))
        self._save_btn.setIconSize(QSize(14, 14))
        self._save_btn.setFixedHeight(28)
        self._save_btn.setStyleSheet(_get_button_style('save'))
        self._save_btn.clicked.connect(self._on_save_clicked)
        toolbar_layout.addWidget(self._save_btn)

        self._auto_map_btn = QPushButton(" 자동 매핑")
        self._auto_map_btn.setIcon(QIcon(_get_icon_path("auto")))
        self._auto_map_btn.setIconSize(QSize(14, 14))
        self._auto_map_btn.setFixedHeight(28)
        self._auto_map_btn.setStyleSheet(_get_button_style('auto'))
        self._auto_map_btn.clicked.connect(self._on_auto_map_clicked)
        toolbar_layout.addWidget(self._auto_map_btn)

        self._reset_btn = QPushButton(" 초기화")
        self._reset_btn.setIcon(QIcon(_get_icon_path("reset")))
        self._reset_btn.setIconSize(QSize(14, 14))
        self._reset_btn.setFixedHeight(28)
        self._reset_btn.setStyleSheet(_get_button_style('reset'))
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        toolbar_layout.addWidget(self._reset_btn)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # 매핑 테이블
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["템플릿 필드", "엑셀 컬럼", "상태", "타입"])

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self._populate_table()
        layout.addWidget(self._table)

        # 상태 라벨
        self._status_label = QLabel()
        self._update_status()
        layout.addWidget(self._status_label)

        # 하단 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton(" 취소")
        cancel_btn.setIcon(QIcon(_get_icon_path("cancel")))
        cancel_btn.setIconSize(QSize(14, 14))
        cancel_btn.setFixedHeight(28)
        cancel_btn.setStyleSheet(_get_button_style('cancel'))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(" 확인")
        confirm_btn.setIcon(QIcon(_get_icon_path("confirm")))
        confirm_btn.setIconSize(QSize(14, 14))
        confirm_btn.setFixedHeight(28)
        confirm_btn.setStyleSheet(_get_button_style('confirm'))
        confirm_btn.clicked.connect(self._on_confirm_clicked)
        button_layout.addWidget(confirm_btn)

        layout.addLayout(button_layout)

    def _populate_table(self) -> None:
        """테이블 채우기"""
        fields = self._mapper._template_fields
        self._table.setRowCount(len(fields))

        excel_headers = ["선택하세요..."] + self._mapper._excel_headers

        for row, field in enumerate(fields):
            field_id = field["id"]
            field_label = field.get("label", field_id)

            # 필드명
            field_item = QTableWidgetItem(f"{field_id}\n({field_label})")
            field_item.setFlags(field_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, field_item)

            # 엑셀 컬럼 콤보박스
            combo = QComboBox()
            combo.addItems(excel_headers)
            combo.currentTextChanged.connect(
                lambda text, fid=field_id: self._on_column_changed(fid, text)
            )
            self._field_combos[field_id] = combo
            self._table.setCellWidget(row, 1, combo)

            # 상태
            status_item = QTableWidgetItem()
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 2, status_item)

            # 타입
            type_item = QTableWidgetItem("str")
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 3, type_item)

    def _load_current_mappings(self) -> None:
        """현재 매핑 로드"""
        mapping = self._mapper.get_mapping()
        status = self._mapper.get_mapping_status()

        for field_id, excel_column in mapping.items():
            if field_id in self._field_combos:
                combo = self._field_combos[field_id]
                if excel_column:
                    index = combo.findText(excel_column)
                    if index >= 0:
                        combo.setCurrentIndex(index)

        self._update_all_status()

    def _on_column_changed(self, field_id: str, column_text: str) -> None:
        """컬럼 선택 변경"""
        if column_text == "선택하세요...":
            self._mapper.clear_mapping(field_id)
        else:
            self._mapper.set_mapping(field_id, column_text)

        self._update_field_status(field_id)
        self._update_status()

    def _update_field_status(self, field_id: str) -> None:
        """필드 상태 업데이트"""
        status = self._mapper.get_mapping_status()
        field_status = status.get(field_id, "unmapped")

        row = self._get_field_row(field_id)
        if row >= 0:
            status_item = self._table.item(row, 2)
            if field_status == "auto":
                status_item.setText("✓ 자동")
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif field_status == "manual":
                status_item.setText("✓ 수동")
                status_item.setForeground(Qt.GlobalColor.darkBlue)
            else:
                status_item.setText("✗ 미매핑")
                status_item.setForeground(Qt.GlobalColor.darkRed)

    def _update_all_status(self) -> None:
        """모든 필드 상태 업데이트"""
        for field_id in self._field_combos.keys():
            self._update_field_status(field_id)

    def _update_status(self) -> None:
        """하단 상태 메시지 업데이트"""
        unmapped = self._mapper.get_unmapped_fields()
        total = len(self._mapper._template_fields)
        mapped = total - len(unmapped)

        status = self._mapper.get_mapping_status()
        manual_count = sum(1 for s in status.values() if s == "manual")

        if len(unmapped) == 0:
            msg = f"✅ 매핑 상태: {mapped}/{total} 완료"
            if manual_count > 0:
                msg += f" ({manual_count}개 필드 수동 설정)"
        else:
            msg = f"⚠️ 매핑 상태: {mapped}/{total} 완료 ({len(unmapped)}개 필드가 매핑되지 않았습니다)"

        self._status_label.setText(msg)

    def _get_field_row(self, field_id: str) -> int:
        """필드 ID로 행 번호 찾기"""
        for row, field in enumerate(self._mapper._template_fields):
            if field["id"] == field_id:
                return row
        return -1

    def _on_load_clicked(self) -> None:
        """불러오기 버튼"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "매핑 파일 불러오기",
            "",
            "매핑 파일 (*.mapping);;모든 파일 (*)",
        )

        if file_path:
            try:
                self._mapper.load_from_file(file_path)
                self._load_current_mappings()
                self._update_status()
                QMessageBox.information(self, "성공", "매핑 파일을 불러왔습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 로드 실패:\n{str(e)}")

    def _on_save_clicked(self) -> None:
        """저장 버튼"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "매핑 파일 저장",
            f"{self._excel_file}.{self._template_name.lower()}.mapping",
            "매핑 파일 (*.mapping);;모든 파일 (*)",
        )

        if file_path:
            try:
                self._mapper.save_to_file(
                    file_path, self._template_name, self._excel_file
                )
                QMessageBox.information(self, "성공", "매핑 파일을 저장했습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 저장 실패:\n{str(e)}")

    def _on_auto_map_clicked(self) -> None:
        """자동 매핑 버튼"""
        self._mapper.reset_to_auto()
        self._load_current_mappings()
        self._update_status()
        QMessageBox.information(self, "완료", "자동 매핑을 다시 실행했습니다.")

    def _on_reset_clicked(self) -> None:
        """초기화 버튼"""
        reply = QMessageBox.question(
            self,
            "확인",
            "모든 수동 매핑을 제거하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._mapper.reset_to_auto()
            self._load_current_mappings()
            self._update_status()

    def _on_confirm_clicked(self) -> None:
        """확인 버튼"""
        mapping = self._mapper.get_mapping()
        self.mapping_changed.emit(mapping)
        self.accept()

    def _apply_styles(self) -> None:
        """다크 테마 스타일 적용"""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3c3f41;
                color: #ffffff;
                gridline-color: #555555;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #555555;
            }
            QComboBox {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 2px;
            }
            QComboBox:hover {
                border: 1px solid #6897bb;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3f41;
                color: #ffffff;
                selection-background-color: #4c4f51;
            }
        """
        )
