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
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    QWebEngineView = None

from jinja2 import Template as Jinja2Template

from .auto_save import AutoSaveManager


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
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        if HAS_WEBENGINE:
            self._web_view = QWebEngineView()
            self._web_view.setStyleSheet("""
                QWebEngineView {
                    background-color: #ffffff;
                    border: 1px solid #444444;
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
            }
        """)
        layout.addWidget(header)

        # 필드 목록 (TODO: Phase 3에서 구현)
        self._field_list = QLabel("필드 목록이 여기에 표시됩니다.")
        self._field_list.setStyleSheet("""
            QLabel {
                color: #888888;
                padding: 8px;
            }
        """)
        self._field_list.setWordWrap(True)
        layout.addWidget(self._field_list, 1)

        return panel

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

        # 헤더
        header = QLabel("🎯 매핑 미리보기 (클릭하여 필드 삽입)")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 4px;
            }
        """)
        layout.addWidget(header)

        # 미리보기 영역 (TODO: Phase 3에서 MappingOverlay 추가)
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

    def set_template(self, template_id: str, template_path: Path, html_content: str):
        """템플릿 설정

        Args:
            template_id: 템플릿 ID
            template_path: 템플릿 파일 경로
            html_content: HTML 내용
        """
        self._template_id = template_id
        self._template_path = template_path
        self._html_content = html_content
        self._modified = False

        # 자동 저장 경로 설정
        self._auto_save.set_file_path(template_path)
        self._auto_save.set_modified(False)

        # 미리보기 업데이트
        self._update_preview()

        self.template_changed.emit(template_id)

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
        self._update_preview()

    def _update_preview(self):
        """미리보기 업데이트"""
        if not self._html_content:
            return

        try:
            # Jinja2 렌더링
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

            # 매핑 미리보기 뷰 업데이트
            if self._mapping_web_view:
                self._mapping_web_view.setHtml(rendered)

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
