"""미리보기 위젯 모듈

템플릿을 렌더링하여 미리보기를 표시합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtGui import QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView

from jinja2 import Template as Jinja2Template

from src.core.template_manager import Template


class PreviewWidget(QWidget):
    """미리보기 위젯

    HTML 또는 이미지 템플릿을 렌더링하여 표시합니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._template: Optional[Template] = None
        self._data: Dict[str, Any] = {}
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # HTML 렌더링용 웹뷰
        self._web_view = QWebEngineView()
        # 템플릿 배경색을 그대로 사용 (WYSIWYG)
        self._web_view.setStyleSheet("background-color: white;")
        layout.addWidget(self._web_view)

        # 이미지용 스크롤 영역 (처음엔 숨김)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #3a3a3a;
                border: none;
            }
        """)

        # 컨텐츠 레이블 (이미지/플레이스홀더용)
        self._content_label = QLabel()
        self._content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_label.setWordWrap(True)
        self._content_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 10px;
            }
        """)

        self._scroll_area.setWidget(self._content_label)
        layout.addWidget(self._scroll_area)

        self._show_placeholder()

    def _show_placeholder(self):
        """플레이스홀더 표시"""
        self._web_view.hide()
        self._scroll_area.show()
        self._content_label.setText("템플릿을 선택하세요")
        self._content_label.setStyleSheet("""
            QLabel {
                background-color: #3a3a3a;
                color: #666666;
                font-size: 14px;
                padding: 20px;
            }
        """)

    def set_template(self, template: Optional[Template]):
        """템플릿 설정"""
        self._template = template
        self._render()

    def update_data(self, data: Dict[str, Any]):
        """데이터 업데이트"""
        self._data = data
        self._render()

    def _render(self):
        """미리보기 렌더링"""
        if self._template is None:
            self._show_placeholder()
            return

        try:
            if self._template.template_type == "html":
                self._render_html()
            else:
                self._render_image()
        except Exception as e:
            self._web_view.hide()
            self._scroll_area.show()
            self._content_label.setText(f"렌더링 오류: {e}")
            self._content_label.setStyleSheet("""
                QLabel {
                    background-color: #3a2a2a;
                    color: #ff6b6b;
                    padding: 20px;
                }
            """)

    def _render_html(self):
        """HTML 템플릿 렌더링 (QWebEngineView 사용)"""
        template_path = self._template.template_path

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Jinja2로 데이터 바인딩
        jinja_template = Jinja2Template(html_content)
        rendered_html = jinja_template.render(**self._data)

        # 웹뷰 표시, 스크롤 영역 숨김
        self._scroll_area.hide()
        self._web_view.show()

        # QWebEngineView로 HTML 렌더링
        self._web_view.setHtml(rendered_html)

    def _render_image(self):
        """이미지 템플릿 렌더링"""
        template_path = self._template.template_path

        # 웹뷰 숨기고 스크롤 영역 표시
        self._web_view.hide()
        self._scroll_area.show()

        pixmap = QPixmap(str(template_path))
        if pixmap.isNull():
            self._content_label.setText("이미지를 로드할 수 없습니다")
            return

        # 크기 조정
        scaled = pixmap.scaled(
            self._scroll_area.width() - 20,
            self._scroll_area.height() - 20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self._content_label.setPixmap(scaled)
        self._content_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                padding: 10px;
            }
        """)

    def clear(self):
        """미리보기 초기화"""
        self._template = None
        self._data = {}
        self._show_placeholder()
