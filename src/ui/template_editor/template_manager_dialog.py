"""템플릿 관리 다이얼로그 모듈

기본/사용자 템플릿을 관리하는 다이얼로그입니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
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
    QFileDialog,
    QGroupBox,
    QFormLayout,
    QSplitter,
)

from src.core.template_storage import TemplateStorage, ExtendedTemplate


class TemplateManagerDialog(QDialog):
    """템플릿 관리 다이얼로그

    기본 템플릿 목록과 사용자 템플릿 목록을 관리합니다.
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

        self.setWindowTitle("템플릿 관리")
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
            QPushButton:pressed {
                background-color: #333333;
            }
            QPushButton:disabled {
                color: #666666;
            }
            QLineEdit, QTextEdit {
                background-color: #333333;
                border: 1px solid #444444;
                color: #ffffff;
                border-radius: 4px;
                padding: 4px;
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

        # 기본 템플릿 버튼
        builtin_buttons = QHBoxLayout()
        self._copy_builtin_btn = QPushButton("📋 복사하여 새로 만들기")
        self._copy_builtin_btn.setEnabled(False)
        self._copy_builtin_btn.clicked.connect(self._on_copy_builtin)
        builtin_buttons.addWidget(self._copy_builtin_btn)
        builtin_buttons.addStretch()
        builtin_layout.addLayout(builtin_buttons)

        self._tab_widget.addTab(builtin_tab, "기본 템플릿")

        # 사용자 템플릿 탭
        user_tab = QWidget()
        user_layout = QVBoxLayout(user_tab)
        self._user_list = QListWidget()
        self._user_list.itemSelectionChanged.connect(self._on_user_selected)
        user_layout.addWidget(self._user_list)

        # 사용자 템플릿 버튼
        user_buttons = QHBoxLayout()
        self._new_btn = QPushButton("➕ 새로 만들기")
        self._new_btn.clicked.connect(self._on_new_template)
        user_buttons.addWidget(self._new_btn)

        self._copy_user_btn = QPushButton("📋 복사")
        self._copy_user_btn.setEnabled(False)
        self._copy_user_btn.clicked.connect(self._on_copy_user)
        user_buttons.addWidget(self._copy_user_btn)

        self._delete_btn = QPushButton("🗑️ 삭제")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete)
        user_buttons.addWidget(self._delete_btn)

        user_buttons.addStretch()
        user_layout.addLayout(user_buttons)

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

        self._import_btn = QPushButton("📥 가져오기")
        self._import_btn.clicked.connect(self._on_import)
        button_layout.addWidget(self._import_btn)

        self._export_btn = QPushButton("📤 내보내기")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(self._export_btn)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _create_detail_panel(self) -> QWidget:
        """상세 정보 패널 생성"""
        panel = QGroupBox("템플릿 정보")
        layout = QFormLayout(panel)
        layout.setSpacing(8)

        # 이름
        self._name_edit = QLineEdit()
        self._name_edit.setReadOnly(True)
        layout.addRow("이름:", self._name_edit)

        # ID
        self._id_label = QLabel("-")
        layout.addRow("ID:", self._id_label)

        # 버전
        self._version_label = QLabel("-")
        layout.addRow("버전:", self._version_label)

        # 타입
        self._type_label = QLabel("-")
        layout.addRow("타입:", self._type_label)

        # 기반 템플릿
        self._based_on_label = QLabel("-")
        layout.addRow("기반:", self._based_on_label)

        # 필드 수
        self._fields_label = QLabel("-")
        layout.addRow("필드 수:", self._fields_label)

        # 설명
        self._desc_edit = QTextEdit()
        self._desc_edit.setReadOnly(True)
        self._desc_edit.setMaximumHeight(100)
        layout.addRow("설명:", self._desc_edit)

        return panel

    def _load_templates(self):
        """템플릿 목록 로드"""
        # 기본 템플릿
        self._builtin_list.clear()
        for template in self._storage.get_builtin_templates():
            item = QListWidgetItem(f"📄 {template.name}")
            item.setData(Qt.ItemDataRole.UserRole, template.id)
            self._builtin_list.addItem(item)

        # 사용자 템플릿
        self._user_list.clear()
        for template in self._storage.get_user_templates():
            item = QListWidgetItem(f"📝 {template.name}")
            item.setData(Qt.ItemDataRole.UserRole, template.id)
            self._user_list.addItem(item)

    def _update_detail_panel(self, template: Optional[ExtendedTemplate]):
        """상세 패널 업데이트"""
        if template is None:
            self._name_edit.setText("")
            self._id_label.setText("-")
            self._version_label.setText("-")
            self._type_label.setText("-")
            self._based_on_label.setText("-")
            self._fields_label.setText("-")
            self._desc_edit.setText("")
            return

        self._name_edit.setText(template.name)
        self._name_edit.setReadOnly(template.is_readonly)
        self._id_label.setText(template.id)
        self._version_label.setText(template.version)
        self._type_label.setText(template.template_type)

        if template.metadata and template.metadata.based_on:
            self._based_on_label.setText(template.metadata.based_on)
        else:
            self._based_on_label.setText("-")

        self._fields_label.setText(str(len(template.fields)))

        desc = ""
        if template.metadata and template.metadata.description:
            desc = template.metadata.description
        self._desc_edit.setText(desc)
        self._desc_edit.setReadOnly(template.is_readonly)

    def _on_builtin_selected(self):
        """기본 템플릿 선택"""
        items = self._builtin_list.selectedItems()
        if not items:
            self._selected_template = None
            self._copy_builtin_btn.setEnabled(False)
            self._export_btn.setEnabled(False)
            self._update_detail_panel(None)
            return

        template_id = items[0].data(Qt.ItemDataRole.UserRole)
        self._selected_template = self._storage.get_template(template_id)
        self._copy_builtin_btn.setEnabled(True)
        self._export_btn.setEnabled(True)
        self._update_detail_panel(self._selected_template)

        # 사용자 목록 선택 해제
        self._user_list.clearSelection()

    def _on_user_selected(self):
        """사용자 템플릿 선택"""
        items = self._user_list.selectedItems()
        if not items:
            self._selected_template = None
            self._copy_user_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            self._export_btn.setEnabled(False)
            self._update_detail_panel(None)
            return

        template_id = items[0].data(Qt.ItemDataRole.UserRole)
        self._selected_template = self._storage.get_template(template_id)
        self._copy_user_btn.setEnabled(True)
        self._delete_btn.setEnabled(True)
        self._export_btn.setEnabled(True)
        self._update_detail_panel(self._selected_template)

        # 기본 목록 선택 해제
        self._builtin_list.clearSelection()

    def _on_copy_builtin(self):
        """기본 템플릿 복사"""
        if not self._selected_template:
            return

        name, ok = self._get_new_name(f"{self._selected_template.name} (복사본)")
        if not ok or not name:
            return

        try:
            new_template = self._storage.copy_template(
                self._selected_template.id, name
            )
            self._load_templates()
            self.templates_changed.emit()
            QMessageBox.information(
                self, "성공", f"템플릿 '{name}'이(가) 생성되었습니다."
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"템플릿 복사 실패:\n{e}")

    def _on_copy_user(self):
        """사용자 템플릿 복사"""
        self._on_copy_builtin()  # 동일한 로직

    def _on_new_template(self):
        """새 템플릿 만들기"""
        name, ok = self._get_new_name("새 템플릿")
        if not ok or not name:
            return

        try:
            default_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: sans-serif; padding: 20px; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>내용을 입력하세요.</p>
</body>
</html>
"""
            new_template = self._storage.create_template(
                name=name,
                html_content=default_html,
                fields=[{"id": "title", "label": "제목", "excel_column": "Title"}],
                description="새로 생성된 템플릿",
            )
            self._load_templates()
            self.templates_changed.emit()

            # 사용자 탭으로 전환
            self._tab_widget.setCurrentIndex(1)

            QMessageBox.information(
                self, "성공", f"템플릿 '{name}'이(가) 생성되었습니다."
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"템플릿 생성 실패:\n{e}")

    def _on_delete(self):
        """템플릿 삭제"""
        if not self._selected_template:
            return

        if self._selected_template.is_builtin:
            QMessageBox.warning(self, "경고", "기본 템플릿은 삭제할 수 없습니다.")
            return

        reply = QMessageBox.question(
            self,
            "삭제 확인",
            f"'{self._selected_template.name}' 템플릿을 삭제하시겠습니까?\n이 작업은 취소할 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._storage.delete_template(self._selected_template.id)
            self._selected_template = None
            self._load_templates()
            self._update_detail_panel(None)
            self.templates_changed.emit()
            QMessageBox.information(self, "성공", "템플릿이 삭제되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"템플릿 삭제 실패:\n{e}")

    def _on_import(self):
        """템플릿 가져오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "템플릿 가져오기",
            str(Path.home()),
            "ZIP Files (*.zip);;All Files (*)",
        )

        if not file_path:
            return

        try:
            new_template = self._storage.import_template(Path(file_path))
            self._load_templates()
            self.templates_changed.emit()

            # 사용자 탭으로 전환
            self._tab_widget.setCurrentIndex(1)

            QMessageBox.information(
                self, "성공", f"템플릿 '{new_template.name}'이(가) 가져와졌습니다."
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"템플릿 가져오기 실패:\n{e}")

    def _on_export(self):
        """템플릿 내보내기"""
        if not self._selected_template:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "템플릿 내보내기",
            str(Path.home() / f"{self._selected_template.name}.zip"),
            "ZIP Files (*.zip)",
        )

        if not file_path:
            return

        try:
            self._storage.export_template(self._selected_template.id, Path(file_path))
            QMessageBox.information(
                self, "성공", f"템플릿이 '{file_path}'로 내보내졌습니다."
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"템플릿 내보내기 실패:\n{e}")

    def _get_new_name(self, default: str) -> tuple:
        """새 이름 입력 받기"""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self, "템플릿 이름", "템플릿 이름을 입력하세요:", text=default
        )
        return name, ok

    def get_selected_template_id(self) -> Optional[str]:
        """선택된 템플릿 ID 반환"""
        if self._selected_template:
            return self._selected_template.id
        return None
