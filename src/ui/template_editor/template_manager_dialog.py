"""템플릿 설정 다이얼로그 모듈

기본/사용자 템플릿의 이름, 설명, 활성화 상태를 관리하는 다이얼로그입니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QSplitter,
    QCheckBox,
)

from src.core.template_storage import TemplateStorage, ExtendedTemplate
from src.core.template_manager import SAFETY_INDICATORS


# 버튼별 색상 정의 (기본색, 어두운색, 밝은색)
BUTTON_COLORS = {
    'save': ('#5ab87a', '#4aa86a', '#6ac88a'),      # 초록색 (저장)
    'cancel': ('#7a7a7a', '#6a6a6a', '#8a8a8a'),    # 회색 (취소)
}


def _get_icon_path(icon_name: str) -> str:
    """아이콘 경로 반환"""
    return str(Path(__file__).parent.parent.parent / "resources" / "icons" / f"{icon_name}.svg")


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


class TemplateManagerDialog(QDialog):
    """템플릿 설정 다이얼로그

    템플릿의 이름, 설명, 활성화 상태를 관리합니다.
    """

    # 시그널
    template_selected = pyqtSignal(str)  # 템플릿 ID
    templates_changed = pyqtSignal()  # 템플릿 목록 변경됨

    def __init__(
        self, template_storage: TemplateStorage, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._storage = template_storage
        self._selected_template: Optional[ExtendedTemplate] = None
        self._has_changes = False

        self.setWindowTitle("템플릿 설정")
        self.setMinimumSize(700, 500)
        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        """UI 초기화"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #333333;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #444444;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #333333;
                border-bottom: 1px solid #333333;
            }
            QListWidget {
                background-color: #333333;
                border: 1px solid #444444;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QLineEdit, QTextEdit {
                background-color: #333333;
                border: 1px solid #444444;
                color: #ffffff;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit:read-only, QTextEdit:read-only {
                background-color: #2a2a2a;
                color: #888888;
            }
            QGroupBox {
                border: 1px solid #444444;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                padding: 0 4px;
            }
            QLabel {
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #555555;
                background-color: #333333;
            }
            QCheckBox::indicator:checked {
                background-color: #5ab87a;
                border: 1px solid #4aa86a;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #666666;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 메인 스플리터
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # 왼쪽: 탭 위젯 (기본/사용자 템플릿)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._tab_widget = QTabWidget()
        left_layout.addWidget(self._tab_widget)

        # 기본 템플릿 탭
        builtin_tab = QWidget()
        builtin_layout = QVBoxLayout(builtin_tab)
        self._builtin_list = QListWidget()
        self._builtin_list.itemSelectionChanged.connect(self._on_builtin_selected)
        builtin_layout.addWidget(self._builtin_list)

        self._tab_widget.addTab(builtin_tab, "기본 템플릿")

        # 사용자 템플릿 탭
        user_tab = QWidget()
        user_layout = QVBoxLayout(user_tab)
        self._user_list = QListWidget()
        self._user_list.itemSelectionChanged.connect(self._on_user_selected)
        user_layout.addWidget(self._user_list)

        self._tab_widget.addTab(user_tab, "사용자 템플릿")

        splitter.addWidget(left_widget)

        # 오른쪽: 상세 정보
        right_widget = self._create_detail_panel()
        splitter.addWidget(right_widget)

        # 스플리터 비율 설정
        splitter.setSizes([300, 400])

        # 하단 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._save_btn = QPushButton(" 저장")
        self._save_btn.setIcon(QIcon(_get_icon_path("confirm")))
        self._save_btn.setIconSize(QSize(14, 14))
        self._save_btn.setFixedHeight(28)
        self._save_btn.setStyleSheet(_get_button_style('save'))
        self._save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self._save_btn)

        cancel_btn = QPushButton(" 취소")
        cancel_btn.setIcon(QIcon(_get_icon_path("cancel")))
        cancel_btn.setIconSize(QSize(14, 14))
        cancel_btn.setFixedHeight(28)
        cancel_btn.setStyleSheet(_get_button_style('cancel'))
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _create_detail_panel(self) -> QWidget:
        """상세 정보 패널 생성"""
        panel = QGroupBox("템플릿 정보")
        main_layout = QVBoxLayout(panel)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 16, 12, 12)

        # 상단 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # 활성화 체크박스
        self._active_checkbox = QCheckBox("활성화")
        self._active_checkbox.setChecked(True)
        self._active_checkbox.stateChanged.connect(self._on_value_changed)
        form_layout.addRow("상태:", self._active_checkbox)

        # 이름
        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._on_value_changed)
        form_layout.addRow("이름:", self._name_edit)

        # 타입
        self._type_label = QLabel("-")
        form_layout.addRow("타입:", self._type_label)

        # 안전지표
        self._indicator_label = QLabel("-")
        form_layout.addRow("안전지표:", self._indicator_label)

        # 필드 수
        self._fields_label = QLabel("-")
        form_layout.addRow("필드 수:", self._fields_label)

        main_layout.addLayout(form_layout)

        # 상하 여백
        main_layout.addSpacing(8)

        # 설명 라벨
        desc_label = QLabel("설명:")
        main_layout.addWidget(desc_label)

        # 설명 (적당한 크기)
        self._desc_edit = QTextEdit()
        self._desc_edit.setMinimumHeight(150)
        self._desc_edit.textChanged.connect(self._on_value_changed)
        main_layout.addWidget(self._desc_edit, 1)

        return panel

    def _get_template_sort_key(self, template: ExtendedTemplate) -> tuple:
        """템플릿 정렬 키 (안전지표 순서: RULA → REBA → OWAS → NLE → SI)"""
        indicator = template.safety_indicator
        if indicator and indicator in SAFETY_INDICATORS:
            order_index = SAFETY_INDICATORS.index(indicator)
        else:
            order_index = len(SAFETY_INDICATORS)
        return (order_index, template.name.upper())

    def _load_templates(self):
        """템플릿 목록 로드 (안전지표 순서로 정렬)"""
        # 기본 템플릿 (정렬)
        self._builtin_list.clear()
        builtin_templates = sorted(
            self._storage.get_builtin_templates(),
            key=self._get_template_sort_key
        )
        for template in builtin_templates:
            item = QListWidgetItem(f"  {template.name}")
            item.setData(Qt.ItemDataRole.UserRole, template.id)
            self._builtin_list.addItem(item)

        # 사용자 템플릿 (정렬)
        self._user_list.clear()
        user_templates = sorted(
            self._storage.get_user_templates(),
            key=self._get_template_sort_key
        )
        for template in user_templates:
            item = QListWidgetItem(f"  {template.name}")
            item.setData(Qt.ItemDataRole.UserRole, template.id)
            self._user_list.addItem(item)

    def _update_detail_panel(self, template: Optional[ExtendedTemplate]):
        """상세 패널 업데이트"""
        # 변경 감지 일시 중지
        self._name_edit.blockSignals(True)
        self._desc_edit.blockSignals(True)
        self._active_checkbox.blockSignals(True)

        if template is None:
            self._name_edit.setText("")
            self._name_edit.setReadOnly(True)
            self._type_label.setText("-")
            self._indicator_label.setText("-")
            self._fields_label.setText("-")
            self._desc_edit.setText("")
            self._desc_edit.setReadOnly(True)
            self._active_checkbox.setChecked(False)
            self._active_checkbox.setEnabled(False)
        else:
            self._name_edit.setText(template.name)
            self._name_edit.setReadOnly(template.is_readonly)
            self._type_label.setText(template.template_type)
            self._indicator_label.setText(template.safety_indicator or "-")
            self._fields_label.setText(str(len(template.fields)))

            # 설명: metadata 우선, 없으면 template.description 사용
            desc = ""
            if template.metadata and template.metadata.description:
                desc = template.metadata.description
            elif template.description:
                desc = template.description
            self._desc_edit.setText(desc)
            self._desc_edit.setReadOnly(template.is_readonly)

            # 활성화 상태 (metadata에서 가져오기, 기본값 True)
            is_active = True
            if template.metadata and hasattr(template.metadata, 'is_active'):
                is_active = template.metadata.is_active
            self._active_checkbox.setChecked(is_active)
            self._active_checkbox.setEnabled(not template.is_readonly)

        # 변경 감지 재개
        self._name_edit.blockSignals(False)
        self._desc_edit.blockSignals(False)
        self._active_checkbox.blockSignals(False)

        self._has_changes = False

    def _on_value_changed(self):
        """값 변경 감지"""
        self._has_changes = True

    def _on_builtin_selected(self):
        """기본 템플릿 선택"""
        # 변경사항 확인
        if self._has_changes:
            self._prompt_save_changes()

        items = self._builtin_list.selectedItems()
        if not items:
            self._selected_template = None
            self._update_detail_panel(None)
            return

        template_id = items[0].data(Qt.ItemDataRole.UserRole)
        self._selected_template = self._storage.get_template(template_id)
        self._update_detail_panel(self._selected_template)

        # 사용자 목록 선택 해제
        self._user_list.clearSelection()

    def _on_user_selected(self):
        """사용자 템플릿 선택"""
        # 변경사항 확인
        if self._has_changes:
            self._prompt_save_changes()

        items = self._user_list.selectedItems()
        if not items:
            self._selected_template = None
            self._update_detail_panel(None)
            return

        template_id = items[0].data(Qt.ItemDataRole.UserRole)
        self._selected_template = self._storage.get_template(template_id)
        self._update_detail_panel(self._selected_template)

        # 기본 목록 선택 해제
        self._builtin_list.clearSelection()

    def _prompt_save_changes(self):
        """변경사항 저장 여부 확인"""
        reply = QMessageBox.question(
            self,
            "변경사항 저장",
            "변경사항이 있습니다. 저장하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._save_current_template()

        self._has_changes = False

    def _save_current_template(self):
        """현재 템플릿 저장"""
        if not self._selected_template or self._selected_template.is_readonly:
            return

        try:
            # 이름 업데이트
            new_name = self._name_edit.text().strip()
            if new_name and new_name != self._selected_template.name:
                self._storage.update_template_name(self._selected_template.id, new_name)

            # 설명 업데이트
            new_desc = self._desc_edit.toPlainText().strip()
            self._storage.update_template_description(self._selected_template.id, new_desc)

            # 활성화 상태 업데이트
            is_active = self._active_checkbox.isChecked()
            self._storage.update_template_active(self._selected_template.id, is_active)

            self._has_changes = False
            self._load_templates()
            self.templates_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"템플릿 저장 실패:\n{e}")

    def _on_save(self):
        """저장 버튼 클릭"""
        if not self._selected_template:
            QMessageBox.warning(self, "알림", "저장할 템플릿을 선택하세요.")
            return

        if self._selected_template.is_readonly:
            QMessageBox.warning(self, "알림", "기본 템플릿은 수정할 수 없습니다.")
            return

        self._save_current_template()
        QMessageBox.information(self, "성공", "템플릿이 저장되었습니다.")

    def get_selected_template_id(self) -> Optional[str]:
        """선택된 템플릿 ID 반환"""
        if self._selected_template:
            return self._selected_template.id
        return None

    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트"""
        if self._has_changes:
            reply = QMessageBox.question(
                self,
                "변경사항 저장",
                "저장하지 않은 변경사항이 있습니다. 저장하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._save_current_template()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
