"""메인 툴바 모듈

상단 메인 툴바 - 기능별 버튼 그룹
스켈레톤 분석기 스타일 (SVG 아이콘 + 색상별 그라데이션)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QToolBar,
    QToolButton,
    QPushButton,
    QComboBox,
    QButtonGroup,
    QFrame,
    QWidget,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
)


class MainToolbar(QToolBar):
    """상단 메인 툴바 - 기능별 버튼 그룹

    Layout:
        ┌─ 파일 ───────┐ │ ┌─ 데이터 시트 ────┐ │ ┌─ 템플릿 ──────────────┐ │ ┌─ 편집 모드 ────┐ │ ┌─ 뷰 ─────────┐
        │[열기][저장]  │ │ │[데이터][새로고침]│ │ │[▼ 선택][새로만들기][관리]│ │ │[편집][미리][매핑]│ │ │[%][전체화면]│
        └──────────────┘ │ └──────────────────┘ │ └────────────────────────┘ │ └────────────────┘ │ └─────────────┘
    """

    # 시그널 정의
    file_open_requested = pyqtSignal()
    file_save_requested = pyqtSignal()
    data_sheet_toggled = pyqtSignal(bool)  # True=표시, False=숨김
    data_refresh_requested = pyqtSignal()
    template_selected = pyqtSignal(str)  # 템플릿 ID
    template_new_requested = pyqtSignal()
    template_manage_requested = pyqtSignal()
    mode_changed = pyqtSignal(int)  # 0=미리보기, 1=매핑
    zoom_changed = pyqtSignal(int)  # 줌 퍼센트
    generate_requested = pyqtSignal()  # 문서 생성 요청

    # 편집 모드 상수
    MODE_PREVIEW = 0
    MODE_MAPPING = 1

    # 버튼별 색상 정의 (기본색, 어두운색, 밝은색)
    BUTTON_COLORS = {
        'open': ('#b8a25a', '#a8924a', '#c8b26a'),      # 골드/노란색 (열기)
        'save': ('#5ab87a', '#4aa86a', '#6ac88a'),      # 초록색 (저장)
        'data': ('#5a7ab8', '#4a6aa8', '#6a8ac8'),      # 파란색 (데이터)
        'refresh': ('#3a9a8a', '#2a8a7a', '#4aaa9a'),   # 틸색 (새로고침)
        'template': ('#8a5ab8', '#7a4aa8', '#9a6ac8'),  # 보라색 (템플릿)
        'add': ('#5ab87a', '#4aa86a', '#6ac88a'),       # 초록색 (새로만들기)
        'manage': ('#7a7a7a', '#6a6a6a', '#8a8a8a'),    # 회색 (관리)
        'edit': ('#5a8ab8', '#4a7aa8', '#6a9ac8'),      # 하늘색 (편집)
        'preview': ('#b8825a', '#a8724a', '#c8926a'),   # 주황색 (미리보기)
        'mapping': ('#b85a8a', '#a84a7a', '#c86a9a'),   # 핑크색 (매핑)
        'zoom': ('#7a8a7a', '#6a7a6a', '#8a9a8a'),      # 녹회색 (줌)
        'generate': ('#5ab87a', '#4aa86a', '#6ac88a'),  # 초록색 (문서 생성)
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("mainToolbar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(14, 14))

        self._setup_style()
        self._setup_ui()
        self._connect_signals()

    def _get_icon_path(self, icon_name: str) -> str:
        """아이콘 경로 반환"""
        return str(Path(__file__).parent.parent / "resources" / "icons" / f"{icon_name}.svg")

    def _get_button_style(self, color_key: str, is_checkable: bool = False, is_checked: bool = True) -> str:
        """버튼 스타일 생성 (그라데이션)"""
        colors = self.BUTTON_COLORS.get(color_key, self.BUTTON_COLORS['open'])
        base, dark, light = colors
        text_color = "white" if is_checked else "rgba(255, 255, 255, 0.6)"

        style = f"""
            QPushButton, QToolButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {base}, stop:1 {dark});
                color: {text_color};
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover, QToolButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {light}, stop:1 {base});
            }}
            QPushButton:pressed, QToolButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {dark}, stop:1 {base});
            }}
            QPushButton:disabled, QToolButton:disabled {{
                background: #444444;
                color: #666666;
            }}
        """

        if is_checkable:
            # 체크 상태 스타일 추가
            unchecked_base = '#555555'
            unchecked_dark = '#444444'
            unchecked_light = '#666666'
            style += f"""
                QPushButton:checked, QToolButton:checked {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {base}, stop:1 {dark});
                    color: white;
                }}
                QPushButton:!checked, QToolButton:!checked {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {unchecked_base}, stop:1 {unchecked_dark});
                    color: rgba(255, 255, 255, 0.6);
                }}
                QPushButton:!checked:hover, QToolButton:!checked:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {unchecked_light}, stop:1 {unchecked_base});
                }}
            """

        return style

    def _setup_style(self):
        """툴바 스타일 설정 (스켈레톤 분석기와 동일)"""
        self.setStyleSheet("""
            QToolBar {
                background-color: #333333;
                border: none;
                padding: 8px 10px;
                spacing: 8px;
            }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
                min-width: 100px;
                font-size: 11px;
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
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #888888;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                selection-background-color: #0d47a1;
                color: #ffffff;
            }
            QLabel {
                color: #888888;
                font-size: 10px;
                padding: 0 4px;
            }
        """)

    def _setup_ui(self):
        """UI 구성"""
        # ========== 파일 그룹 ==========
        self._setup_file_group()
        self._add_separator()

        # ========== 데이터 시트 그룹 ==========
        self._setup_data_sheet_group()
        self._add_separator()

        # ========== 템플릿 그룹 ==========
        self._setup_template_group()
        self._add_separator()

        # ========== 편집 모드 그룹 ==========
        self._setup_mode_group()
        self._add_separator()

        # ========== 뷰 그룹 ==========
        self._setup_view_group()

        # 오른쪽 여백
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

    def _add_separator(self):
        """그룹 분리자 추가"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("""
            QFrame {
                background-color: #555555;
                max-width: 1px;
                margin: 4px 8px;
            }
        """)
        self.addWidget(separator)

    def _setup_file_group(self):
        """파일 그룹 버튼"""
        # 열기 버튼
        self.btn_open = QPushButton(" 열기")
        self.btn_open.setIcon(QIcon(self._get_icon_path("folder_open")))
        self.btn_open.setIconSize(QSize(14, 14))
        self.btn_open.setFixedHeight(28)
        self.btn_open.setToolTip("파일 열기 (Ctrl+O)")
        self.btn_open.setShortcut(QKeySequence.StandardKey.Open)
        self.btn_open.setStyleSheet(self._get_button_style('open'))
        self.addWidget(self.btn_open)

        # 저장 버튼
        self.btn_save = QPushButton(" 저장")
        self.btn_save.setIcon(QIcon(self._get_icon_path("save")))
        self.btn_save.setIconSize(QSize(14, 14))
        self.btn_save.setFixedHeight(28)
        self.btn_save.setToolTip("템플릿 저장 (Ctrl+S)")
        self.btn_save.setShortcut(QKeySequence.StandardKey.Save)
        self.btn_save.setEnabled(False)  # 기본 비활성화
        self.btn_save.setStyleSheet(self._get_button_style('save'))
        self.addWidget(self.btn_save)

    def _setup_data_sheet_group(self):
        """데이터 시트 그룹 버튼"""
        # 데이터 시트 토글 버튼
        self.btn_data_toggle = QPushButton(" 데이터")
        self.btn_data_toggle.setIcon(QIcon(self._get_icon_path("data")))
        self.btn_data_toggle.setIconSize(QSize(14, 14))
        self.btn_data_toggle.setFixedHeight(28)
        self.btn_data_toggle.setToolTip("데이터 시트 표시/숨김 (Ctrl+D)")
        self.btn_data_toggle.setCheckable(True)
        self.btn_data_toggle.setChecked(True)  # 기본값: 표시
        self.btn_data_toggle.setShortcut("Ctrl+D")
        self.btn_data_toggle.setStyleSheet(self._get_button_style('data', is_checkable=True))
        self.addWidget(self.btn_data_toggle)

        # 새로고침 버튼
        self.btn_refresh = QPushButton(" 새로고침")
        self.btn_refresh.setIcon(QIcon(self._get_icon_path("refresh")))
        self.btn_refresh.setIconSize(QSize(14, 14))
        self.btn_refresh.setFixedHeight(28)
        self.btn_refresh.setToolTip("데이터 새로고침 (F5)")
        self.btn_refresh.setShortcut("F5")
        self.btn_refresh.setStyleSheet(self._get_button_style('refresh'))
        self.addWidget(self.btn_refresh)

    def _setup_template_group(self):
        """템플릿 그룹"""
        # 템플릿 선택 드롭다운
        self.combo_template = QComboBox()
        self.combo_template.setToolTip("템플릿 선택")
        self.combo_template.setMinimumWidth(120)
        self.combo_template.setFixedHeight(28)
        self.addWidget(self.combo_template)

        # 새 템플릿 버튼
        self.btn_new_template = QPushButton(" 새로 만들기")
        self.btn_new_template.setIcon(QIcon(self._get_icon_path("add")))
        self.btn_new_template.setIconSize(QSize(14, 14))
        self.btn_new_template.setFixedHeight(28)
        self.btn_new_template.setToolTip("새 템플릿 만들기 (Ctrl+N)")
        self.btn_new_template.setShortcut("Ctrl+N")
        self.btn_new_template.setStyleSheet(self._get_button_style('add'))
        self.addWidget(self.btn_new_template)

        # 템플릿 관리 버튼
        self.btn_manage_template = QPushButton(" 관리")
        self.btn_manage_template.setIcon(QIcon(self._get_icon_path("settings")))
        self.btn_manage_template.setIconSize(QSize(14, 14))
        self.btn_manage_template.setFixedHeight(28)
        self.btn_manage_template.setToolTip("템플릿 관리")
        self.btn_manage_template.setStyleSheet(self._get_button_style('manage'))
        self.addWidget(self.btn_manage_template)

    def _setup_mode_group(self):
        """모드 그룹 (라디오 버튼 스타일)"""
        # 버튼 그룹 생성
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)

        # 미리보기 모드 버튼
        self.btn_mode_preview = QPushButton(" 미리보기")
        self.btn_mode_preview.setIcon(QIcon(self._get_icon_path("preview")))
        self.btn_mode_preview.setIconSize(QSize(14, 14))
        self.btn_mode_preview.setFixedHeight(28)
        self.btn_mode_preview.setToolTip("렌더링 미리보기 (Ctrl+P)")
        self.btn_mode_preview.setCheckable(True)
        self.btn_mode_preview.setChecked(True)  # 기본값
        self.btn_mode_preview.setShortcut("Ctrl+P")
        self.btn_mode_preview.setStyleSheet(self._get_button_style('preview', is_checkable=True))
        self.mode_group.addButton(self.btn_mode_preview, self.MODE_PREVIEW)
        self.addWidget(self.btn_mode_preview)

        # 매핑 모드 버튼
        self.btn_mode_mapping = QPushButton(" 매핑")
        self.btn_mode_mapping.setIcon(QIcon(self._get_icon_path("mapping")))
        self.btn_mode_mapping.setIconSize(QSize(14, 14))
        self.btn_mode_mapping.setFixedHeight(28)
        self.btn_mode_mapping.setToolTip("위지윅 매핑 모드 (Ctrl+M)")
        self.btn_mode_mapping.setCheckable(True)
        self.btn_mode_mapping.setShortcut("Ctrl+M")
        self.btn_mode_mapping.setStyleSheet(self._get_button_style('mapping', is_checkable=True))
        self.mode_group.addButton(self.btn_mode_mapping, self.MODE_MAPPING)
        self.addWidget(self.btn_mode_mapping)

    def _setup_view_group(self):
        """뷰 그룹"""
        # 줌 드롭다운
        self.combo_zoom = QComboBox()
        self.combo_zoom.setToolTip("확대/축소")
        self.combo_zoom.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.setMinimumWidth(70)
        self.combo_zoom.setFixedHeight(28)
        self.addWidget(self.combo_zoom)

        # 문서 생성하기 버튼
        self.btn_generate = QPushButton(" 문서 생성하기")
        self.btn_generate.setIcon(QIcon(self._get_icon_path("document")))
        self.btn_generate.setIconSize(QSize(14, 14))
        self.btn_generate.setFixedHeight(28)
        self.btn_generate.setMinimumWidth(120)
        self.btn_generate.setToolTip("선택된 행으로 문서 생성 (Ctrl+G)")
        self.btn_generate.setShortcut("Ctrl+G")
        self.btn_generate.setStyleSheet(self._get_button_style('generate'))
        self.btn_generate.setEnabled(False)  # 기본 비활성화
        self.addWidget(self.btn_generate)

    def _connect_signals(self):
        """시그널 연결"""
        # 파일 그룹
        self.btn_open.clicked.connect(self.file_open_requested.emit)
        self.btn_save.clicked.connect(self.file_save_requested.emit)

        # 데이터 시트 그룹
        self.btn_data_toggle.toggled.connect(self.data_sheet_toggled.emit)
        self.btn_refresh.clicked.connect(self.data_refresh_requested.emit)

        # 템플릿 그룹
        self.combo_template.currentTextChanged.connect(self._on_template_changed)
        self.btn_new_template.clicked.connect(self.template_new_requested.emit)
        self.btn_manage_template.clicked.connect(self.template_manage_requested.emit)

        # 편집 모드 그룹
        self.mode_group.idClicked.connect(self.mode_changed.emit)

        # 뷰 그룹
        self.combo_zoom.currentTextChanged.connect(self._on_zoom_changed)
        self.btn_generate.clicked.connect(self.generate_requested.emit)

    def _on_template_changed(self, text: str):
        """템플릿 선택 변경"""
        if text:
            # 콤보박스 아이템의 데이터(ID)를 가져옴
            index = self.combo_template.currentIndex()
            template_id = self.combo_template.itemData(index)
            if template_id:
                self.template_selected.emit(template_id)
            else:
                self.template_selected.emit(text)

    def _on_zoom_changed(self, text: str):
        """줌 변경"""
        try:
            zoom = int(text.replace("%", ""))
            self.zoom_changed.emit(zoom)
        except ValueError:
            pass

    # ========== Public Methods ==========

    def set_templates(self, templates: List[tuple]):
        """템플릿 드롭다운 업데이트

        Args:
            templates: (id, name) 튜플 목록
        """
        self.combo_template.blockSignals(True)
        self.combo_template.clear()

        for template_id, template_name in templates:
            self.combo_template.addItem(template_name, template_id)

        self.combo_template.blockSignals(False)

    def set_current_template(self, template_id: str):
        """현재 템플릿 설정

        Args:
            template_id: 템플릿 ID
        """
        for i in range(self.combo_template.count()):
            if self.combo_template.itemData(i) == template_id:
                self.combo_template.setCurrentIndex(i)
                break

    def set_data_sheet_visible(self, visible: bool):
        """데이터 시트 표시 상태 설정

        Args:
            visible: 표시 여부
        """
        self.btn_data_toggle.blockSignals(True)
        self.btn_data_toggle.setChecked(visible)
        self.btn_data_toggle.blockSignals(False)

    def set_mode(self, mode: int):
        """편집 모드 설정

        Args:
            mode: MODE_EDIT, MODE_PREVIEW, MODE_MAPPING
        """
        button = self.mode_group.button(mode)
        if button:
            button.setChecked(True)

    def set_zoom(self, percent: int):
        """줌 설정

        Args:
            percent: 줌 퍼센트 (50, 75, 100, 125, 150, 200)
        """
        self.combo_zoom.setCurrentText(f"{percent}%")

    def set_save_enabled(self, enabled: bool):
        """저장 버튼 활성화/비활성화

        Args:
            enabled: 활성화 여부
        """
        self.btn_save.setEnabled(enabled)

    def set_generate_enabled(self, enabled: bool):
        """문서 생성 버튼 활성화/비활성화

        Args:
            enabled: 활성화 여부
        """
        self.btn_generate.setEnabled(enabled)

    def set_generate_text(self, text: str):
        """문서 생성 버튼 텍스트 변경

        Args:
            text: 버튼 텍스트
        """
        self.btn_generate.setText(f" {text}")

    def get_current_mode(self) -> int:
        """현재 편집 모드 반환"""
        return self.mode_group.checkedId()

    def get_current_zoom(self) -> int:
        """현재 줌 퍼센트 반환"""
        try:
            return int(self.combo_zoom.currentText().replace("%", ""))
        except ValueError:
            return 100

    def is_data_sheet_visible(self) -> bool:
        """데이터 시트 표시 여부"""
        return self.btn_data_toggle.isChecked()
