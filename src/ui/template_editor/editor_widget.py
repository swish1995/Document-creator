"""템플릿 편집기 위젯 모듈

미리보기/매핑 모드를 지원하는 템플릿 편집기입니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl, QTimer, QObject
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFrame,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QComboBox,
    QPushButton,
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    QWebEngineView = None
    QWebChannel = None

import re

from jinja2 import Template as Jinja2Template

from .auto_save import AutoSaveManager
from src.core.logger import get_logger

_logger = get_logger(__name__)


class _MappingBridge(QObject):
    """JS → Python 브릿지 (매핑 미리보기에서 필드 클릭 전달)"""

    field_clicked = pyqtSignal(str)

    @pyqtSlot(str)
    def onFieldClicked(self, field_id: str):
        self.field_clicked.emit(field_id)


class EditorWidget(QWidget):
    """템플릿 편집기 메인 위젯

    2가지 모드 지원:
    - PREVIEW (0): 렌더링 미리보기
    - MAPPING (1): 위지윅 매핑
    """

    # 시그널
    template_changed = pyqtSignal(str)  # 템플릿 ID
    content_modified = pyqtSignal()  # 내용 수정됨
    auto_saved = pyqtSignal(str)  # 자동 저장됨
    scroll_changed = pyqtSignal(int, int)  # 스크롤 위치 변경 (x, y)
    page_loaded = pyqtSignal()  # 페이지 로드 완료
    column_highlight_requested = pyqtSignal(int)  # 데이터 시트 컬럼 하이라이트 요청
    mapping_save_requested = pyqtSignal()  # 매핑 저장 요청
    mapping_save_as_requested = pyqtSignal(str, str)  # 다른 이름으로 저장 (이름, 카테고리 ID)

    # 모드 상수
    MODE_PREVIEW = 0
    MODE_MAPPING = 1

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._template_id: Optional[str] = None
        self._template_path: Optional[Path] = None
        self._html_content: str = ""
        self._preview_data: Dict[str, Any] = {}
        self._preview_data_by_index: List[Any] = []  # 인덱스 기반 데이터
        self._fields: List[Dict[str, Any]] = []
        self._has_excel_data: bool = False  # 엑셀 데이터 로드 여부
        self._modified: bool = False
        self._current_mode: int = self.MODE_PREVIEW
        self._zoom_level: int = 100
        self._last_scroll_pos: tuple = (0, 0)  # 마지막 스크롤 위치
        self._excel_headers: List[str] = []  # 엑셀 헤더 목록
        self._dirty: bool = False  # 매핑 변경 여부
        self._is_builtin: bool = True  # 현재 템플릿이 빌트인인지

        # 스크롤 위치 추적 타이머 (500ms마다 체크)
        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self._check_scroll_position)
        self._scroll_timer.start(500)

        # 자동 저장 관리자
        self._auto_save = AutoSaveManager(self)
        self._auto_save.set_content_getter(self.get_html_content)
        self._auto_save.auto_saved.connect(self.auto_saved.emit)

        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        """UI 초기화"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 스택 위젯 (모드별 뷰)
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # 미리보기 뷰 (index 0)
        self._preview_view = self._create_preview_view()
        self._stack.addWidget(self._preview_view)

        # 매핑 뷰 (index 1)
        self._mapping_view = self._create_mapping_view()
        self._stack.addWidget(self._mapping_view)

    def _create_preview_view(self) -> QWidget:
        """미리보기 뷰 생성"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #2b2b2b;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        if HAS_WEBENGINE:
            self._web_view = QWebEngineView()
            self._web_view.setStyleSheet("""
                QWebEngineView {
                    background-color: #ffffff;
                    border: 2px solid #333333;
                    border-radius: 4px;
                }
            """)
            self._web_view.loadFinished.connect(self._on_page_loaded)
            layout.addWidget(self._web_view)
        else:
            # WebEngine이 없는 경우 대체 뷰
            self._web_view = None
            fallback_label = QLabel("미리보기를 사용하려면 PyQt6-WebEngine이 필요합니다.")
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_label.setStyleSheet("""
                QLabel {
                    background-color: #3a3a3a;
                    color: #888888;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 20px;
                }
            """)
            layout.addWidget(fallback_label)

        return widget

    def _on_page_loaded(self, ok: bool):
        """페이지 로드 완료 시 호출"""
        if ok:
            self.page_loaded.emit()

    def _create_mapping_view(self) -> QWidget:
        """매핑 뷰 생성"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 왼쪽: 필드 목록
        field_panel = self._create_field_panel()
        layout.addWidget(field_panel, 1)

        # 오른쪽: 미리보기 + 오버레이
        preview_panel = self._create_mapping_preview()
        layout.addWidget(preview_panel, 3)

        return widget

    def _create_field_panel(self) -> QWidget:
        """필드 목록 패널 생성"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)

        # 헤더
        header = QLabel("📋 필드 목록")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 4px;
                background-color: transparent;
            }
        """)
        layout.addWidget(header)

        # 필드 목록 트리
        self._field_tree = QTreeWidget()
        self._field_tree.setHeaderLabels(["idx", "라벨", "엑셀 컬럼"])
        self._field_tree.setRootIsDecorated(False)
        self._field_tree.setAlternatingRowColors(True)
        self._field_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #ffffff;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 4px 8px;
            }
            QTreeWidget::item:alternate {
                background-color: #323232;
            }
            QTreeWidget::item:selected {
                background-color: #0d47a1;
            }
            QTreeWidget::item:hover {
                background-color: #3a3a3a;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #cccccc;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #444444;
                font-weight: bold;
                font-size: 10px;
            }
        """)

        # 컬럼 너비 설정
        header_view = self._field_tree.header()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._field_tree.setColumnWidth(0, 45)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self._field_tree.setColumnWidth(1, 120)

        # 필드 클릭 시 하이라이트
        self._field_tree.itemClicked.connect(self._on_field_clicked)

        layout.addWidget(self._field_tree, 1)

        # 저장 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self._btn_save = QPushButton("저장")
        self._btn_save.setFixedHeight(28)
        self._btn_save.setEnabled(False)
        self._btn_save.setStyleSheet("""
            QPushButton {
                background-color: #5ab87a; color: white;
                border: none; padding: 5px 12px; border-radius: 4px;
                font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #6ac88a; }
            QPushButton:disabled { background-color: #444444; color: #666666; }
        """)
        btn_layout.addWidget(self._btn_save)

        self._btn_save_as = QPushButton("다른 이름으로 저장")
        self._btn_save_as.setFixedHeight(28)
        self._btn_save_as.setEnabled(False)
        self._btn_save_as.setStyleSheet("""
            QPushButton {
                background-color: #5a7ab8; color: white;
                border: none; padding: 5px 12px; border-radius: 4px;
                font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #6a8ac8; }
            QPushButton:disabled { background-color: #444444; color: #666666; }
        """)
        self._btn_save.clicked.connect(self._on_save_clicked)
        self._btn_save_as.clicked.connect(self._on_save_as_clicked)

        btn_layout.addWidget(self._btn_save_as)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        return panel

    def _on_field_clicked(self, item: QTreeWidgetItem, column: int):
        """필드 목록에서 아이템 클릭"""
        field_id = item.data(0, Qt.ItemDataRole.UserRole)
        if field_id:
            self.highlight_field(field_id)
            # 데이터 시트 컬럼 하이라이트
            for field in self._fields:
                if field.get("id") == field_id:
                    excel_index = field.get("excel_index")
                    if excel_index is not None:
                        self.column_highlight_requested.emit(excel_index)
                    break

    def _on_mapping_field_clicked(self, field_id: str):
        """매핑 미리보기에서 필드 클릭 → 왼쪽 필드 목록 선택"""
        for i in range(self._field_tree.topLevelItemCount()):
            item = self._field_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == field_id:
                self._field_tree.setCurrentItem(item)
                self._field_tree.scrollToItem(item)
                break

    def _create_mapping_preview(self) -> QWidget:
        """매핑용 미리보기 패널 생성"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)

        # 헤더 영역 (타이틀 + 경고 라벨)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # 타이틀
        header = QLabel("🎯 매핑 미리보기")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 4px;
            }
        """)
        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 미리보기 영역
        if HAS_WEBENGINE:
            self._mapping_web_view = QWebEngineView()
            # QWebChannel 설정 (JS → Python 브릿지)
            self._mapping_bridge = _MappingBridge(self)
            self._mapping_bridge.field_clicked.connect(self._on_mapping_field_clicked)
            self._mapping_channel = QWebChannel(self._mapping_web_view.page())
            self._mapping_channel.registerObject("bridge", self._mapping_bridge)
            self._mapping_web_view.page().setWebChannel(self._mapping_channel)
            layout.addWidget(self._mapping_web_view, 1)
        else:
            self._mapping_web_view = None
            fallback = QLabel("미리보기를 사용하려면 PyQt6-WebEngine이 필요합니다.")
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("color: #888888;")
            layout.addWidget(fallback, 1)

        return panel

    def _setup_shortcuts(self):
        """키보드 단축키 설정"""
        pass  # 편집 기능 제거로 단축키 불필요

    # ========== Public Methods ==========

    def set_excel_headers(self, headers: List[str]):
        """엑셀 헤더 목록 설정

        Args:
            headers: 엑셀 파일의 헤더(컬럼명) 목록
        """
        self._excel_headers = headers
        self._update_field_list()

    def set_template(
        self,
        template_id: str,
        template_path: Path,
        html_content: str,
        fields: Optional[List[Dict[str, Any]]] = None,
        is_builtin: bool = True,
    ):
        """템플릿 설정

        Args:
            template_id: 템플릿 ID
            template_path: 템플릿 파일 경로
            html_content: HTML 내용
            fields: 필드 정의 목록 (선택)
            is_builtin: 빌트인 템플릿 여부
        """
        self._template_id = template_id
        self._template_path = template_path
        self._html_content = html_content
        self._fields = fields or []
        self._is_builtin = is_builtin
        self._modified = False
        self._dirty = False
        self._update_save_buttons()

        # 자동 저장 경로 설정
        self._auto_save.set_file_path(template_path)
        self._auto_save.set_modified(False)

        # 필드 목록 업데이트
        self._update_field_list()

        # 미리보기 업데이트
        self._update_preview()

        self.template_changed.emit(template_id)

    def _update_field_list(self):
        """필드 목록 트리 업데이트"""
        self._field_tree.clear()

        if not self._fields:
            # 필드가 없으면 안내 메시지 표시
            item = QTreeWidgetItem(["", "필드 정보 없음", ""])
            item.setForeground(1, Qt.GlobalColor.gray)
            self._field_tree.addTopLevelItem(item)
            return

        for field in self._fields:
            field_id = field.get("id", "")
            label = field.get("label", field_id)
            excel_column = field.get("excel_column", "")
            excel_index = field.get("excel_index")
            index_text = str(excel_index) if excel_index is not None else ""

            if self._excel_headers:
                # 엑셀 헤더가 있으면 ComboBox로 인라인 편집
                item = QTreeWidgetItem([index_text, label, ""])
                item.setData(0, Qt.ItemDataRole.UserRole, field_id)
                item.setToolTip(1, f"클릭하여 위치 확인: {field_id}")
                self._field_tree.addTopLevelItem(item)

                combo = QComboBox()
                combo.addItems(self._excel_headers)
                if excel_column in self._excel_headers:
                    combo.setCurrentText(excel_column)
                combo.currentTextChanged.connect(
                    lambda text, f=field, it=item: self._on_combo_changed(text, f, it)
                )
                self._field_tree.setItemWidget(item, 2, combo)
            else:
                # 엑셀 헤더가 없으면 텍스트로 표시
                item = QTreeWidgetItem([index_text, label, excel_column])
                item.setData(0, Qt.ItemDataRole.UserRole, field_id)
                item.setToolTip(1, f"클릭하여 위치 확인: {field_id}")
                self._field_tree.addTopLevelItem(item)

    def _on_combo_changed(self, text: str, field: Dict[str, Any], item: QTreeWidgetItem):
        """ComboBox 변경 시 호출"""
        self._dirty = True
        field["excel_column"] = text
        # 새 컬럼의 인덱스 계산
        if text in self._excel_headers:
            new_index = self._excel_headers.index(text)
            field["excel_index"] = new_index
            item.setText(0, str(new_index))
            self.column_highlight_requested.emit(new_index)
        self._update_save_buttons()

    def _update_save_buttons(self):
        """dirty 및 is_builtin 상태에 따라 저장 버튼 활성화/비활성화"""
        if self._dirty:
            self._btn_save_as.setEnabled(True)
            self._btn_save.setEnabled(not self._is_builtin)
        else:
            self._btn_save.setEnabled(False)
            self._btn_save_as.setEnabled(False)

    def load_template_from_path(self, template_path: Path):
        """파일에서 템플릿 로드

        Args:
            template_path: 템플릿 파일 경로
        """
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            self.set_template(template_path.stem, template_path, html_content)
        except Exception as e:
            self._html_content = f"<!-- 파일 로드 실패: {e} -->"
            self._update_preview()

    def _on_save_clicked(self):
        """저장 버튼 클릭"""
        self.mapping_save_requested.emit()
        self._dirty = False
        self._update_save_buttons()

    def _on_save_as_clicked(self):
        """다른 이름으로 저장 버튼 클릭"""
        from src.ui.template_editor.save_as_dialog import SaveAsDialog

        dialog = SaveAsDialog(
            original_name=self._template_id or "",
            categories=self._categories if hasattr(self, '_categories') else [],
            default_category=self._category or "" if hasattr(self, '_category') else "",
            existing_names=self._existing_names if hasattr(self, '_existing_names') else [],
            parent=self,
        )
        if dialog.exec() == SaveAsDialog.DialogCode.Accepted:
            self.mapping_save_as_requested.emit(dialog.get_name(), dialog.get_category())
            self._dirty = False
            self._update_save_buttons()

    def set_save_as_context(self, categories: list, default_category: str, existing_names: list):
        """다른 이름으로 저장 다이얼로그에 필요한 컨텍스트 설정"""
        self._categories = categories
        self._category = default_category
        self._existing_names = existing_names

    def set_mode(self, mode: int):
        """모드 설정

        Args:
            mode: MODE_PREVIEW, MODE_MAPPING
        """
        if mode not in (self.MODE_PREVIEW, self.MODE_MAPPING):
            return

        self._current_mode = mode
        self._stack.setCurrentIndex(mode)

        # 미리보기 업데이트
        self._update_preview()

    def set_preview_data(self, data: Dict[str, Any], data_by_index: Optional[List[Any]] = None):
        """미리보기 데이터 설정

        Args:
            data: 템플릿에 바인딩할 데이터 (헤더명 기반)
            data_by_index: 인덱스 기반 데이터 (중복 헤더 지원)
        """
        self._preview_data = data
        self._preview_data_by_index = data_by_index or []
        self._has_excel_data = bool(data)  # 데이터가 있으면 True

        self._update_preview()

    def _update_preview(self):
        """미리보기 업데이트 (JavaScript 기반 실시간 매핑)"""
        if not self._html_content:
            return

        try:
            # {{ field_id }}를 data-field span으로 변환
            preview_html = self._convert_to_data_fields(self._html_content)

            # 데이터 바인딩 CSS 추가
            data_binding_css = self._get_data_binding_css()

            # 줌 적용
            zoom_css = ""
            if self._zoom_level != 100:
                zoom_css = f"""
                <style>
                    body {{ transform: scale({self._zoom_level / 100}); transform-origin: top left; }}
                </style>
                """

            # 데이터 바인딩 스크립트 생성 (엑셀 데이터가 있을 때만 값 주입)
            data_binding_script = self._get_data_binding_script()

            # CSS 삽입
            if "</head>" in preview_html:
                preview_html = preview_html.replace("</head>", f"{data_binding_css}{zoom_css}</head>")
            else:
                preview_html = f"{data_binding_css}{zoom_css}{preview_html}"

            # Script 삽입
            if "</body>" in preview_html:
                preview_html = preview_html.replace("</body>", f"{data_binding_script}</body>")
            else:
                preview_html = f"{preview_html}{data_binding_script}"

            # 미리보기 뷰 업데이트
            if self._web_view:
                if self._template_path:
                    base_url = QUrl.fromLocalFile(str(self._template_path.parent) + "/")
                    self._web_view.setHtml(preview_html, base_url)
                else:
                    self._web_view.setHtml(preview_html)

            # 매핑 미리보기 뷰 업데이트 (원본 템플릿 + 하이라이트)
            if self._mapping_web_view:
                # 원본 HTML에서 {{ field_id }}를 하이라이트 span으로 감싸기
                mapping_html = self._add_field_highlights_to_template(self._html_content)
                highlight_script = self._get_highlight_script()
                highlight_css = self._get_highlight_css()

                # 줌 CSS 생성
                zoom_css_mapping = ""
                if self._zoom_level != 100:
                    zoom_css_mapping = f"""
                    <style>
                        body {{ transform: scale({self._zoom_level / 100}); transform-origin: top left; }}
                    </style>
                    """

                # CSS와 Script 삽입
                if "</head>" in mapping_html:
                    mapping_html = mapping_html.replace("</head>", f"{highlight_css}{zoom_css_mapping}</head>")
                else:
                    mapping_html = f"{highlight_css}{zoom_css_mapping}{mapping_html}"

                if "</body>" in mapping_html:
                    mapping_html = mapping_html.replace("</body>", f"{highlight_script}</body>")
                else:
                    mapping_html = f"{mapping_html}{highlight_script}"

                if self._template_path:
                    base_url = QUrl.fromLocalFile(str(self._template_path.parent) + "/")
                    self._mapping_web_view.setHtml(mapping_html, base_url)
                else:
                    self._mapping_web_view.setHtml(mapping_html)

        except Exception as e:
            error_html = f"""
            <html>
            <body style="background:#2b2b2b; color:#ff6b6b; padding:20px; font-family:sans-serif;">
                <h3>렌더링 오류</h3>
                <pre>{str(e)}</pre>
            </body>
            </html>
            """
            if self._web_view:
                self._web_view.setHtml(error_html)

    def _convert_to_data_fields(self, html_template: str) -> str:
        """템플릿의 {{ field_id }}를 data-field span으로 변환

        엑셀 데이터 유무와 관계없이 동일한 HTML 구조 생성
        """
        def replace_field(match):
            field_id = match.group(1).strip()
            return f'<span class="data-field" data-field="{field_id}"></span>'

        pattern = r'\{\{\s*(\w+)\s*\}\}'
        return re.sub(pattern, replace_field, html_template)

    def _get_data_binding_css(self) -> str:
        """데이터 바인딩용 CSS"""
        return """
        <style>
        .data-field {
            display: inline;
        }
        .data-field.empty {
            background-color: #fff3cd;
            border: 1px dashed #ffc107;
            border-radius: 2px;
            padding: 0 2px;
            color: #856404;
            font-size: 0.9em;
        }
        .data-field.filled {
            /* 값이 채워지면 일반 텍스트처럼 표시 */
        }
        </style>
        """

    def _get_data_binding_script(self) -> str:
        """데이터 바인딩 JavaScript 생성

        엑셀 데이터가 있으면 값 주입, 없으면 빈 상태 유지
        excel_index가 있으면 인덱스 기반, 없으면 excel_column 기반 매핑
        이미지 필드는 실제 이미지로 표시
        """
        import json
        import base64
        from pathlib import Path

        # 이미지 필드 목록 추출
        image_fields = [
            field.get("id", "")
            for field in self._fields
            if field.get("type") == "image"
        ]

        # 엑셀 데이터가 있으면 매핑된 값으로 변환
        mapped_data = {}
        if self._has_excel_data:
            for field in self._fields:
                field_id = field.get("id", "")
                if not field_id:
                    continue

                value = None

                # excel_index가 있으면 인덱스 기반 매핑 (우선)
                excel_index = field.get("excel_index")
                if excel_index is not None and self._preview_data_by_index:
                    if 0 <= excel_index < len(self._preview_data_by_index):
                        value = self._preview_data_by_index[excel_index]

                # excel_index가 없으면 excel_column 기반 매핑
                elif self._preview_data:
                    excel_column = field.get("excel_column", "")
                    if excel_column and excel_column in self._preview_data:
                        value = self._preview_data[excel_column]

                # 이미지 필드는 Base64 img 태그로 변환
                if field_id in image_fields and value:
                    img_tag = self._convert_image_to_img_tag(value)
                    if img_tag:
                        mapped_data[field_id] = img_tag
                    # 변환 실패하면 저장 안 함 (빈 상태)
                elif value is not None:
                    mapped_data[field_id] = str(value)

        # JSON 직렬화
        data_json = json.dumps(mapped_data, ensure_ascii=False)
        image_fields_json = json.dumps(image_fields, ensure_ascii=False)
        has_data = "true" if self._has_excel_data else "false"

        return f"""
        <script>
        (function() {{
            const excelData = {data_json};
            const imageFields = {image_fields_json};
            const hasExcelData = {has_data};

            // 모든 data-field 요소에 값 바인딩
            document.querySelectorAll('.data-field').forEach(function(el) {{
                const fieldId = el.getAttribute('data-field');
                const isImageField = imageFields.includes(fieldId);

                if (isImageField) {{
                    // 이미지 필드: 실제 이미지 표시
                    if (hasExcelData && excelData[fieldId] !== undefined && excelData[fieldId] !== '') {{
                        // 값이 있으면 img 태그 삽입 (Base64 이미지)
                        el.innerHTML = excelData[fieldId];
                        el.classList.add('filled');
                        el.classList.remove('empty');
                    }} else {{
                        // 값이 없으면 안 보이게 (빈 문자열, 클래스 없음)
                        el.innerHTML = '';
                        el.classList.remove('empty', 'filled');
                    }}
                }} else if (hasExcelData && excelData[fieldId] !== undefined) {{
                    // 일반 필드: 엑셀 데이터가 있고 해당 필드 값이 있으면 표시
                    el.textContent = excelData[fieldId];
                    el.classList.add('filled');
                    el.classList.remove('empty');
                }} else if (!hasExcelData) {{
                    // 엑셀 데이터가 없으면 빈 상태 (플레이스홀더 없음)
                    el.textContent = '';
                    el.classList.remove('empty', 'filled');
                }} else {{
                    // 엑셀 데이터는 있지만 해당 필드가 매핑 안됨
                    el.textContent = '';
                    el.classList.add('empty');
                    el.classList.remove('filled');
                }}
            }});
        }})();
        </script>
        """

    def _convert_image_to_img_tag(self, image_path) -> str:
        """이미지 경로를 Base64 img 태그로 변환"""
        import base64
        from pathlib import Path

        try:
            path = Path(image_path) if not isinstance(image_path, Path) else image_path
            if not path.exists():
                return ""

            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")

            suffix = path.suffix.lower()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_types.get(suffix, "image/png")

            return f'<img src="data:{mime_type};base64,{data}" style="width:100%;height:100%;object-fit:contain;">'
        except Exception:
            return ""

    def _add_field_highlights_to_template(self, html_template: str) -> str:
        """템플릿의 {{ field_id }} 패턴을 하이라이트 span으로 감싸기"""
        # 필드 ID를 라벨로 매핑
        field_labels = {f.get("id", ""): f.get("label", f.get("id", "")) for f in self._fields}

        def replace_field(match):
            field_id = match.group(1).strip()
            label = field_labels.get(field_id, field_id)
            # 공백 + 툴팁(title)으로 표시
            return f'<span class="mapping-field" data-field="{field_id}" title="{label}">&nbsp;</span>'

        # {{ field_id }} 패턴을 찾아서 span으로 감싸기
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        return re.sub(pattern, replace_field, html_template)

    def _add_field_highlights(self, html: str) -> str:
        """매핑 모드용 필드 하이라이트 추가 (렌더링된 HTML)"""
        # 필드 ID를 라벨로 매핑
        field_labels = {f.get("id", ""): f.get("label", f.get("id", "")) for f in self._fields}

        # 하이라이트 스타일 CSS
        highlight_css = """
        <style>
            .mapping-field {
                background-color: #ffeb3b !important;
                color: #000000 !important;
                padding: 1px 4px !important;
                border-radius: 3px !important;
                border: 1px solid #ffc107 !important;
                cursor: pointer !important;
                font-weight: bold !important;
                display: inline-block !important;
                min-width: 20px !important;
                text-align: center !important;
            }
            .mapping-field:hover {
                background-color: #ffc107 !important;
            }
            .mapping-field.highlighted {
                background-color: #ff5722 !important;
                border-color: #e64a19 !important;
                color: #ffffff !important;
                animation: pulse 0.5s ease-in-out 3;
            }
            .mapping-field.empty {
                background-color: #ef5350 !important;
                border-color: #c62828 !important;
                color: #ffffff !important;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
        </style>
        """

        # HTML에서 필드 값을 찾아서 하이라이트 span으로 감싸기
        for field in self._fields:
            field_id = field.get("id", "")
            label = field.get("label", field_id)

            if field_id in self._preview_data:
                value = str(self._preview_data[field_id])
                if value and value.strip():
                    # 값이 있으면 하이라이트
                    escaped_value = re.escape(value)
                    pattern = f'(?<!["\'>])({escaped_value})(?![<"\'])'
                    replacement = f'<span class="mapping-field" data-field="{field_id}" title="{label}">{value}</span>'
                    html = re.sub(pattern, replacement, html, count=1)

        # CSS 삽입
        if "</head>" in html:
            html = html.replace("</head>", f"{highlight_css}</head>")
        else:
            html = f"{highlight_css}{html}"

        # JavaScript 추가
        highlight_js = """
        <script>
            function highlightField(fieldId) {
                document.querySelectorAll('.mapping-field.highlighted').forEach(el => {
                    el.classList.remove('highlighted');
                });
                const field = document.querySelector('[data-field="' + fieldId + '"]');
                if (field) {
                    field.classList.add('highlighted');
                    field.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        </script>
        """
        if "</body>" in html:
            html = html.replace("</body>", f"{highlight_js}</body>")
        else:
            html = f"{html}{highlight_js}"

        return html

    def _get_highlight_css(self) -> str:
        """필드 하이라이트용 CSS 반환"""
        return """
        <style>
        .mapping-field {
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 3px;
            padding: 1px 4px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .mapping-field:hover {
            background-color: #ffe69c;
        }
        .mapping-field.selected {
            background-color: #d4edda;
            border-color: #28a745;
        }
        </style>
        """

    def _get_highlight_script(self) -> str:
        """필드 클릭 이벤트 JavaScript 반환"""
        return """
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script>
        (function() {
            var bridge = null;

            // QWebChannel 연결
            if (typeof QWebChannel !== 'undefined') {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    bridge = channel.objects.bridge;
                });
            }

            // 모든 필드에 클릭 이벤트 추가
            document.querySelectorAll('.mapping-field').forEach(function(el) {
                el.addEventListener('click', function() {
                    const fieldId = this.getAttribute('data-field');

                    // 선택 상태 토글
                    document.querySelectorAll('.mapping-field').forEach(function(f) {
                        f.classList.remove('selected');
                    });
                    this.classList.add('selected');

                    // Python에 전달
                    if (bridge) {
                        bridge.onFieldClicked(fieldId);
                    }
                });
            });

            window.highlightField = function(fieldId) {
                document.querySelectorAll('.mapping-field').forEach(function(el) {
                    el.classList.remove('selected');
                    if (el.getAttribute('data-field') === fieldId) {
                        el.classList.add('selected');
                    }
                });
            };
        })();
        </script>
        """

    def highlight_field(self, field_id: str):
        """특정 필드 하이라이트"""
        if self._mapping_web_view:
            js_code = f'highlightField("{field_id}");'
            self._mapping_web_view.page().runJavaScript(js_code)

    def save_template(self) -> bool:
        """템플릿 저장

        Returns:
            성공 여부
        """
        if not self._template_path:
            return False

        try:
            with open(self._template_path, "w", encoding="utf-8") as f:
                f.write(self._html_content)
            self._modified = False
            self._auto_save.set_modified(False)
            return True
        except Exception:
            return False

    def set_zoom(self, percent: int):
        """줌 설정

        Args:
            percent: 줌 퍼센트
        """
        self._zoom_level = percent
        self._update_preview()

    def toggle_fullscreen(self):
        """전체화면 토글"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def get_html_content(self) -> str:
        """현재 HTML 내용 반환"""
        return self._html_content

    def is_modified(self) -> bool:
        """수정 여부 반환"""
        return self._modified

    def get_current_mode(self) -> int:
        """현재 모드 반환"""
        return self._current_mode

    # ========== Auto Save Methods ==========

    def enable_auto_save(self, enabled: bool = True, interval_ms: int = 60000):
        """자동 저장 활성화/비활성화

        Args:
            enabled: 활성화 여부
            interval_ms: 저장 간격 (밀리초)
        """
        self._auto_save.set_interval(interval_ms)
        if enabled:
            self._auto_save.start()
        else:
            self._auto_save.stop()

    def get_auto_save_manager(self) -> AutoSaveManager:
        """AutoSaveManager 반환"""
        return self._auto_save

    # ========== Scroll Position Methods ==========

    def _check_scroll_position(self):
        """주기적으로 스크롤 위치 확인 후 변경 시 시그널 emit"""
        if not HAS_WEBENGINE or not hasattr(self, '_web_view') or not self._web_view:
            return

        def on_position(x, y):
            if (x, y) != self._last_scroll_pos:
                self._last_scroll_pos = (x, y)
                self.scroll_changed.emit(x, y)

        self.get_scroll_position(on_position)

    def get_scroll_position(self, callback):
        """현재 스크롤 위치 가져오기 (비동기)

        Args:
            callback: 스크롤 위치를 받을 콜백 함수 (x, y)
        """
        if not HAS_WEBENGINE or not hasattr(self, '_web_view'):
            callback(0, 0)
            return

        js_code = "JSON.stringify({x: window.scrollX || 0, y: window.scrollY || 0})"
        self._web_view.page().runJavaScript(js_code, lambda result: self._handle_scroll_result(result, callback))

    def _handle_scroll_result(self, result, callback):
        """스크롤 결과 처리"""
        try:
            import json
            pos = json.loads(result) if result else {"x": 0, "y": 0}
            callback(pos.get("x", 0), pos.get("y", 0))
        except Exception:
            callback(0, 0)

    def set_scroll_position(self, x: int, y: int):
        """스크롤 위치 설정

        Args:
            x: 가로 스크롤 위치
            y: 세로 스크롤 위치
        """
        if not HAS_WEBENGINE or not hasattr(self, '_web_view'):
            return

        js_code = f"window.scrollTo({x}, {y});"
        self._web_view.page().runJavaScript(js_code)
