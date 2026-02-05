"""템플릿 편집기 위젯 모듈

미리보기/매핑 모드를 지원하는 템플릿 편집기입니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
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
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    QWebEngineView = None

import re

from jinja2 import Template as Jinja2Template

from .auto_save import AutoSaveManager
from src.core.logger import get_logger

_logger = get_logger(__name__)


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

    # 모드 상수
    MODE_PREVIEW = 0
    MODE_MAPPING = 1

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._template_id: Optional[str] = None
        self._template_path: Optional[Path] = None
        self._html_content: str = ""
        self._preview_data: Dict[str, Any] = {}
        self._fields: List[Dict[str, Any]] = []
        self._has_excel_data: bool = False  # 엑셀 데이터 로드 여부
        self._modified: bool = False
        self._current_mode: int = self.MODE_PREVIEW
        self._zoom_level: int = 100

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
        self._field_tree.setHeaderLabels(["라벨", "엑셀 컬럼"])
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
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._field_tree.setColumnWidth(0, 120)

        # 필드 클릭 시 하이라이트
        self._field_tree.itemClicked.connect(self._on_field_clicked)

        layout.addWidget(self._field_tree, 1)

        return panel

    def _on_field_clicked(self, item: QTreeWidgetItem, column: int):
        """필드 목록에서 아이템 클릭"""
        field_id = item.data(0, Qt.ItemDataRole.UserRole)
        if field_id:
            self.highlight_field(field_id)

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
        header = QLabel("🎯 매핑 미리보기 (클릭하여 필드 삽입)")
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

    def set_template(
        self,
        template_id: str,
        template_path: Path,
        html_content: str,
        fields: Optional[List[Dict[str, Any]]] = None,
    ):
        """템플릿 설정

        Args:
            template_id: 템플릿 ID
            template_path: 템플릿 파일 경로
            html_content: HTML 내용
            fields: 필드 정의 목록 (선택)
        """
        self._template_id = template_id
        self._template_path = template_path
        self._html_content = html_content
        self._fields = fields or []
        self._modified = False

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
            item = QTreeWidgetItem(["필드 정보 없음", ""])
            item.setForeground(0, Qt.GlobalColor.gray)
            self._field_tree.addTopLevelItem(item)
            return

        for field in self._fields:
            field_id = field.get("id", "")
            label = field.get("label", field_id)
            excel_column = field.get("excel_column", "")
            item = QTreeWidgetItem([label, excel_column])
            item.setData(0, Qt.ItemDataRole.UserRole, field_id)  # 필드 ID 저장
            item.setToolTip(0, f"클릭하여 위치 확인: {field_id}")
            self._field_tree.addTopLevelItem(item)

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

    def set_preview_data(self, data: Dict[str, Any]):
        """미리보기 데이터 설정

        Args:
            data: 템플릿에 바인딩할 데이터
        """
        self._preview_data = data
        self._has_excel_data = bool(data)  # 데이터가 있으면 True

        self._update_preview()

    def _update_preview(self):
        """미리보기 업데이트"""
        if not self._html_content:
            return

        try:
            # Jinja2 렌더링 (미리보기용)
            template = Jinja2Template(self._html_content)
            rendered = template.render(**self._preview_data)

            # 줌 적용
            if self._zoom_level != 100:
                zoom_css = f"""
                <style>
                    body {{ transform: scale({self._zoom_level / 100}); transform-origin: top left; }}
                </style>
                """
                rendered = rendered.replace("</head>", f"{zoom_css}</head>")

            # 미리보기 뷰 업데이트
            if self._web_view:
                self._web_view.setHtml(rendered)

            # 매핑 미리보기 뷰 업데이트 (원본 템플릿 + 하이라이트)
            if self._mapping_web_view:
                # 원본 HTML에서 {{ field_id }}를 하이라이트 span으로 감싸기
                mapping_html = self._add_field_highlights_to_template(self._html_content)
                highlight_script = self._get_highlight_script()
                highlight_css = self._get_highlight_css()

                # CSS와 Script 삽입
                if "</head>" in mapping_html:
                    mapping_html = mapping_html.replace("</head>", f"{highlight_css}</head>")
                else:
                    mapping_html = f"{highlight_css}{mapping_html}"

                if "</body>" in mapping_html:
                    mapping_html = mapping_html.replace("</body>", f"{highlight_script}</body>")
                else:
                    mapping_html = f"{mapping_html}{highlight_script}"

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
        <script>
        (function() {
            // 모든 필드에 클릭 이벤트 추가
            document.querySelectorAll('.mapping-field').forEach(function(el) {
                el.addEventListener('click', function() {
                    const fieldId = this.getAttribute('data-field');
                    console.log('Field clicked:', fieldId);

                    // 선택 상태 토글
                    document.querySelectorAll('.mapping-field').forEach(function(f) {
                        f.classList.remove('selected');
                    });
                    this.classList.add('selected');
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
