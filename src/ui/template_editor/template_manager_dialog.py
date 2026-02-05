"""템플릿 설정 다이얼로그 모듈

템플릿의 이름, 설명, 활성화 상태를 관리하는 다이얼로그입니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Any

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
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
)

from src.core.template_storage import TemplateStorage, ExtendedTemplate
from src.core.template_manager import SAFETY_INDICATORS
from src.ui.utils.styled_message_box import StyledMessageBox


class ToggleSwitch(QWidget):
    """스마트폰 스타일 토글 스위치"""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(36, 18)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.update()

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self.toggled.emit(self._checked)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경 트랙
        track_rect = QRectF(0, 0, self.width(), self.height())
        track_radius = self.height() / 2

        if not self.isEnabled():
            track_color = QColor("#3a3a3a")
            knob_color = QColor("#666666")
        elif self._checked:
            track_color = QColor("#5ab87a")
            knob_color = QColor("#ffffff")
        else:
            track_color = QColor("#555555")
            knob_color = QColor("#ffffff")

        # 트랙 그리기
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, track_radius, track_radius)

        # 노브 (원형)
        knob_margin = 2
        knob_diameter = self.height() - (knob_margin * 2)
        if self._checked:
            knob_x = self.width() - knob_diameter - knob_margin
        else:
            knob_x = knob_margin
        knob_y = knob_margin

        painter.setBrush(knob_color)
        painter.drawEllipse(QRectF(knob_x, knob_y, knob_diameter, knob_diameter))


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
        self._pending_changes: Dict[str, Dict[str, Any]] = {}  # 템플릿별 변경사항
        self._original_values: Dict[str, Dict[str, Any]] = {}  # 템플릿별 원본 값
        self._skip_save_prompt = False  # 취소 시 저장 확인 건너뛰기

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
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 메인 스플리터
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # 왼쪽: 템플릿 목록
        left_group = QGroupBox("템플릿")
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(8, 12, 8, 8)

        self._template_list = QListWidget()
        self._template_list.itemSelectionChanged.connect(self._on_template_selected)
        left_layout.addWidget(self._template_list)

        splitter.addWidget(left_group)

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
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _create_detail_panel(self) -> QWidget:
        """상세 정보 패널 생성"""
        panel = QGroupBox("정보")
        main_layout = QVBoxLayout(panel)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 16, 12, 12)

        # 상단 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # 활성화 토글 스위치
        self._active_toggle = ToggleSwitch()
        self._active_toggle.setChecked(True)
        self._active_toggle.toggled.connect(self._on_toggle_active)
        form_layout.addRow("상태:", self._active_toggle)

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

    def _get_template_active_state(self, template: ExtendedTemplate) -> bool:
        """템플릿의 활성화 상태 (pending 변경사항 포함)"""
        # pending 변경사항이 있으면 그 값 사용
        if template.id in self._pending_changes:
            if 'is_active' in self._pending_changes[template.id]:
                return self._pending_changes[template.id]['is_active']

        # 없으면 원본 값 사용
        if template.metadata and hasattr(template.metadata, 'is_active'):
            return template.metadata.is_active
        return True

    def _load_templates(self):
        """템플릿 목록 로드 (안전지표 순서로 정렬)"""
        self._template_list.clear()

        # 모든 템플릿 가져와서 정렬
        all_templates = sorted(
            self._storage.get_all_templates(),
            key=self._get_template_sort_key
        )

        for template in all_templates:
            # 활성화 상태 확인 (pending 포함)
            is_active = self._get_template_active_state(template)

            # 비활성화된 템플릿은 회색으로 표시
            if is_active:
                item = QListWidgetItem(f"  {template.name}")
            else:
                item = QListWidgetItem(f"  {template.name} (비활성)")
                item.setForeground(Qt.GlobalColor.gray)

            item.setData(Qt.ItemDataRole.UserRole, template.id)
            self._template_list.addItem(item)

        # 첫 번째 템플릿 자동 선택
        if self._template_list.count() > 0:
            self._template_list.setCurrentRow(0)

    def _save_current_to_pending(self):
        """현재 템플릿의 변경사항을 pending에 저장 (원본과 다른 경우에만)"""
        if not self._selected_template:
            return

        template_id = self._selected_template.id
        original = self._original_values.get(template_id, {})

        # 현재 값
        current_is_active = self._active_toggle.isChecked()
        current_name = self._name_edit.text().strip()
        current_desc = self._desc_edit.toPlainText().strip()

        # 원본과 비교하여 변경된 것만 pending에 저장
        has_changes = False

        if current_is_active != original.get('is_active', True):
            if template_id not in self._pending_changes:
                self._pending_changes[template_id] = {}
            self._pending_changes[template_id]['is_active'] = current_is_active
            has_changes = True

        if current_name != original.get('name', ''):
            if template_id not in self._pending_changes:
                self._pending_changes[template_id] = {}
            self._pending_changes[template_id]['name'] = current_name
            has_changes = True

        if current_desc != original.get('description', ''):
            if template_id not in self._pending_changes:
                self._pending_changes[template_id] = {}
            self._pending_changes[template_id]['description'] = current_desc
            has_changes = True

        # 변경사항이 없으면 pending에서 제거
        if not has_changes and template_id in self._pending_changes:
            del self._pending_changes[template_id]

    def _update_detail_panel(self, template: Optional[ExtendedTemplate]):
        """상세 패널 업데이트"""
        # 변경 감지 일시 중지
        self._name_edit.blockSignals(True)
        self._desc_edit.blockSignals(True)
        self._active_toggle.blockSignals(True)

        if template is None:
            self._name_edit.setText("")
            self._name_edit.setReadOnly(True)
            self._type_label.setText("-")
            self._indicator_label.setText("-")
            self._fields_label.setText("-")
            self._desc_edit.setText("")
            self._desc_edit.setReadOnly(True)
            self._active_toggle.setChecked(False)
            self._active_toggle.setEnabled(False)
        else:
            # 원본 값 저장 (아직 저장되지 않은 경우에만)
            if template.id not in self._original_values:
                # 원본 이름
                orig_name = template.name
                # 원본 설명
                if template.metadata and template.metadata.description:
                    orig_desc = template.metadata.description
                elif template.description:
                    orig_desc = template.description
                else:
                    orig_desc = ""
                # 원본 활성화 상태
                if template.metadata and hasattr(template.metadata, 'is_active'):
                    orig_active = template.metadata.is_active
                else:
                    orig_active = True

                self._original_values[template.id] = {
                    'name': orig_name,
                    'description': orig_desc,
                    'is_active': orig_active,
                }

            # pending 변경사항이 있으면 그 값 사용, 없으면 원본 사용
            pending = self._pending_changes.get(template.id, {})
            original = self._original_values[template.id]

            # 이름
            name = pending.get('name', original['name'])
            self._name_edit.setText(name)
            self._name_edit.setReadOnly(False)

            self._type_label.setText(template.template_type.upper())
            self._indicator_label.setText(template.safety_indicator or "-")
            self._fields_label.setText(str(len(template.fields)))

            # 설명
            desc = pending.get('description', original['description'])
            self._desc_edit.setText(desc)
            self._desc_edit.setReadOnly(False)

            # 활성화 상태
            is_active = pending.get('is_active', original['is_active'])
            self._active_toggle.setChecked(is_active)
            self._active_toggle.setEnabled(True)

        # 변경 감지 재개
        self._name_edit.blockSignals(False)
        self._desc_edit.blockSignals(False)
        self._active_toggle.blockSignals(False)

    def _on_value_changed(self):
        """값 변경 시 pending에 저장"""
        self._save_current_to_pending()
        # 목록 업데이트 (비활성 표시 등)
        self._refresh_current_item()

    def _on_toggle_active(self):
        """활성화 토글 스위치 변경"""
        self._save_current_to_pending()
        # 목록 업데이트 (비활성 표시 등)
        self._refresh_current_item()

    def _refresh_current_item(self):
        """현재 선택된 아이템의 표시 업데이트"""
        if not self._selected_template:
            return

        items = self._template_list.selectedItems()
        if not items:
            return

        item = items[0]
        is_active = self._active_toggle.isChecked()
        name = self._name_edit.text().strip() or self._selected_template.name

        if is_active:
            item.setText(f"  {name}")
            item.setForeground(Qt.GlobalColor.white)
        else:
            item.setText(f"  {name} (비활성)")
            item.setForeground(Qt.GlobalColor.gray)

    def _on_template_selected(self):
        """템플릿 선택 (저장 확인 없이 바로 전환)"""
        # 현재 템플릿의 변경사항을 pending에 저장
        self._save_current_to_pending()

        items = self._template_list.selectedItems()
        if not items:
            self._selected_template = None
            self._update_detail_panel(None)
            return

        template_id = items[0].data(Qt.ItemDataRole.UserRole)
        self._selected_template = self._storage.get_template(template_id)
        self._update_detail_panel(self._selected_template)

    def _save_all_changes(self):
        """모든 변경사항 일괄 저장"""
        if not self._pending_changes:
            return True

        try:
            for template_id, changes in self._pending_changes.items():
                template = self._storage.get_template(template_id)
                if not template:
                    continue

                # 활성화 상태 저장
                if 'is_active' in changes:
                    self._storage.update_template_active(template_id, changes['is_active'])

                # 이름/설명 저장
                if 'name' in changes and changes['name'] != template.name:
                    self._storage.update_template_name(template_id, changes['name'])
                if 'description' in changes:
                    self._storage.update_template_description(template_id, changes['description'])

            self._pending_changes.clear()
            self.templates_changed.emit()
            return True

        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")
            return False

    def _on_save(self):
        """저장 버튼 클릭"""
        # 현재 템플릿의 변경사항도 pending에 저장
        self._save_current_to_pending()

        if not self._pending_changes:
            self._skip_save_prompt = True
            self.close()
            return

        # 저장 확인
        if StyledMessageBox.confirm_save(self):
            self._save_all_changes()
        # "예" 또는 "아니오" 모두 닫기
        self._skip_save_prompt = True
        self.close()

    def _on_cancel(self):
        """취소 버튼 클릭 - 저장 확인 없이 바로 닫기"""
        self._skip_save_prompt = True
        self.close()

    def get_selected_template_id(self) -> Optional[str]:
        """선택된 템플릿 ID 반환"""
        if self._selected_template:
            return self._selected_template.id
        return None

    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트"""
        # 취소 버튼으로 닫는 경우 저장 확인 건너뛰기
        if self._skip_save_prompt:
            event.accept()
            return

        # 현재 템플릿의 변경사항도 pending에 저장
        self._save_current_to_pending()

        if self._pending_changes:
            if StyledMessageBox.confirm_save(self):
                self._save_all_changes()
            event.accept()
        else:
            event.accept()
