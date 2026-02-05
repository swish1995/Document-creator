"""메인 툴바 모듈

상단 메인 툴바 - 기능별 버튼 그룹
스켈레톤 분석기 스타일 (SVG 아이콘 + 색상별 그라데이션)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
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


class ToolbarComboBox(QComboBox):
    """팝업이 콤보박스 바로 아래에 나오는 커스텀 콤보박스"""

    def showPopup(self):
        """팝업 위치를 콤보박스 바로 아래로 조정"""
        super().showPopup()
        # 팝업 위치를 콤보박스 바로 아래로 이동
        popup = self.view().window()
        pos = self.mapToGlobal(QPoint(0, self.height()))
        popup.move(pos)


class MainToolbar(QToolBar):
    """상단 메인 툴바 - 기능별 버튼 그룹

    Layout:
        ┌─ 파일 ───────┐ │ ┌─ 데이터 시트 ────┐ │ ┌─ 템플릿 ──────────────┐ │ ┌─ 편집 모드 ────┐ │ ┌─ 뷰 ─────────┐
        │[열기][저장]  │ │ │[데이터][새로고침]│ │ │[▼ 선택][새로만들기][관리]│ │ │[편집][미리][매핑]│ │ │[%][전체화면]│
        └──────────────┘ │ └──────────────────┘ │ └────────────────────────┘ │ └────────────────┘ │ └─────────────┘
    """

    # 시그널 정의
    data_sheet_toggled = pyqtSignal(bool)  # True=표시, False=숨김
    template_selected = pyqtSignal(str)  # 템플릿 ID
    template_manage_requested = pyqtSignal()
    mode_changed = pyqtSignal(int)  # 0=미리보기, 1=매핑
    zoom_changed = pyqtSignal(int)  # 줌 퍼센트
    generate_requested = pyqtSignal()  # 문서 생성 요청
    exit_requested = pyqtSignal()  # 종료 요청

    # 편집 모드 상수
    MODE_PREVIEW = 0
    MODE_MAPPING = 1

    # 버튼별 색상 정의 (기본색, 어두운색, 밝은색)
    BUTTON_COLORS = {
        'data': ('#5a7ab8', '#4a6aa8', '#6a8ac8'),      # 파란색 (데이터)
        'template': ('#8a5ab8', '#7a4aa8', '#9a6ac8'),  # 보라색 (템플릿)
        'manage': ('#7a7a7a', '#6a6a6a', '#8a8a8a'),    # 회색 (관리)
        'preview': ('#b8825a', '#a8724a', '#c8926a'),   # 주황색 (미리보기)
        'mapping': ('#b85a8a', '#a84a7a', '#c86a9a'),   # 핑크색 (매핑)
        'generate': ('#5ab87a', '#4aa86a', '#6ac88a'),  # 초록색 (문서 생성)
        'exit': ('#c55a5a', '#b54a4a', '#d56a6a'),      # 빨간색 (종료)
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
        colors = self.BUTTON_COLORS.get(color_key, self.BUTTON_COLORS['data'])
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
        arrow_icon_path = self._get_icon_path("dropdown-arrow").replace("\\", "/")

        self.setStyleSheet(f"""
            QToolBar {{
                background-color: #333333;
                border: none;
                padding: 8px 10px;
                spacing: 8px;
            }}
            QComboBox {{
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
                min-width: 100px;
                font-size: 11px;
            }}
            QComboBox:hover {{
                border: 1px solid #666666;
                background-color: #4a4a4a;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: url({arrow_icon_path});
                width: 10px;
                height: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #3a3a3a;
                border: 1px solid #555555;
                selection-background-color: #0d47a1;
                color: #ffffff;
            }}
            QLabel {{
                color: #888888;
                font-size: 10px;
                padding: 0 4px;
            }}
        """)

    def _setup_ui(self):
        """UI 구성"""
        # ========== 왼쪽 그룹 (템플릿 + 모드 + 출력 + 보기) ==========
        self._setup_template_group()
        self._setup_mode_group()
        self._setup_output_group()
        self._setup_view_group()

        # 중앙 스페이서
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        spacer.setStyleSheet("background-color: transparent;")
        self.addWidget(spacer)

        # ========== 오른쪽 그룹 (경고 + 종료) ==========
        self._setup_warning_label()
        self._setup_exit_group()

    def _setup_template_group(self):
        """템플릿 그룹"""
        # 템플릿 라벨
        template_label = QLabel("템플릿:")
        template_label.setStyleSheet("color: #999999; font-size: 12px; margin-right: 4px; background-color: transparent;")
        self.addWidget(template_label)

        # 템플릿 선택 드롭다운
        self.combo_template = ToolbarComboBox()
        self.combo_template.setToolTip("템플릿 선택")
        self.combo_template.setMinimumWidth(120)
        self.combo_template.setFixedHeight(28)
        self.addWidget(self.combo_template)

        # 템플릿 관리 버튼
        self.btn_manage_template = QPushButton(" 관리")
        self.btn_manage_template.setIcon(QIcon(self._get_icon_path("settings")))
        self.btn_manage_template.setIconSize(QSize(14, 14))
        self.btn_manage_template.setFixedHeight(28)
        self.btn_manage_template.setToolTip("템플릿 관리")
        self.btn_manage_template.setStyleSheet(self._get_button_style('manage'))
        self.addWidget(self.btn_manage_template)

    def _setup_mode_group(self):
        """모드 그룹 (미리보기/매핑 + 줌)"""
        # 버튼 그룹 생성 (미리보기/매핑 모드)
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

        # 줌 드롭다운
        self.combo_zoom = ToolbarComboBox()
        self.combo_zoom.setToolTip("확대/축소")
        self.combo_zoom.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.setMinimumWidth(70)
        self.combo_zoom.setFixedHeight(28)
        self.addWidget(self.combo_zoom)

    def _setup_view_group(self):
        """보기 그룹 (데이터만)"""
        # 보기 라벨
        view_label = QLabel("보기:")
        view_label.setStyleSheet("color: #999999; font-size: 12px; margin-right: 4px; background-color: transparent;")
        self.addWidget(view_label)

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

    def _setup_warning_label(self):
        """경고 라벨 (엑셀 파일 없을 때 표시) - 스티커 스타일"""
        self._no_excel_warning = QPushButton(" 엑셀 파일이 없습니다.")
        self._no_excel_warning.setIcon(QIcon(self._get_icon_path("warning")))
        self._no_excel_warning.setIconSize(QSize(16, 16))
        self._no_excel_warning.setFixedHeight(28)
        self._no_excel_warning.setEnabled(False)  # 클릭 비활성화
        self._no_excel_warning.setStyleSheet("""
            QPushButton:disabled {
                color: #e57373;
                background-color: #4a3535;
                font-weight: bold;
                font-size: 12px;
                padding: 4px 14px;
                border-radius: 14px;
                border: 1px solid #5a4545;
                margin-right: 8px;
            }
        """)
        # QToolBar.addWidget()은 QAction을 반환하므로 저장
        self._warning_action = self.addWidget(self._no_excel_warning)

    def _setup_exit_group(self):
        """종료 그룹"""
        # 종료 버튼
        self.btn_exit = QPushButton(" 종료")
        self.btn_exit.setIcon(QIcon(self._get_icon_path("exit")))
        self.btn_exit.setIconSize(QSize(14, 14))
        self.btn_exit.setFixedHeight(28)
        self.btn_exit.setToolTip("프로그램 종료")
        self.btn_exit.setStyleSheet(self._get_button_style('exit'))
        self.addWidget(self.btn_exit)

    def _setup_output_group(self):
        """출력 그룹"""
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
        # 보기 그룹
        self.btn_data_toggle.toggled.connect(self.data_sheet_toggled.emit)
        self.mode_group.idClicked.connect(self.mode_changed.emit)
        self.combo_zoom.currentTextChanged.connect(self._on_zoom_changed)

        # 템플릿 그룹
        self.combo_template.currentTextChanged.connect(self._on_template_changed)
        self.btn_manage_template.clicked.connect(self.template_manage_requested.emit)

        # 출력 그룹
        self.btn_generate.clicked.connect(self.generate_requested.emit)

        # 종료 그룹
        self.btn_exit.clicked.connect(self.exit_requested.emit)

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

    def set_excel_warning_visible(self, visible: bool):
        """엑셀 파일 경고 표시/숨김

        Args:
            visible: 표시 여부
        """
        # QToolBar에서는 QAction의 setVisible()을 사용해야 함
        self._warning_action.setVisible(visible)
