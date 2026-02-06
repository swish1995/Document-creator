"""미리보기 위젯 모듈

템플릿을 렌더링하여 미리보기를 표시합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self._image_fields: List[str] = []  # 이미지 타입 필드 ID 목록
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
        # 이미지 타입 필드 추출
        self._image_fields = []
        if template and template.fields:
            for field in template.fields:
                if field.get("type") == "image":
                    self._image_fields.append(field.get("id", ""))
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
        """HTML 템플릿 렌더링 (Jinja2 사용)"""
        template_path = self._template.template_path

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # 이미지 필드를 플레이스홀더로 변환한 데이터 준비
        preview_data = self._prepare_preview_data()

        # Jinja2로 데이터 바인딩
        jinja_template = Jinja2Template(html_content)
        rendered_html = jinja_template.render(**preview_data)

        # 웹뷰 표시, 스크롤 영역 숨김
        self._scroll_area.hide()
        self._web_view.show()

        # QWebEngineView로 HTML 렌더링 (baseUrl 설정으로 상대 경로 리소스 로드)
        base_url = QUrl.fromLocalFile(str(template_path.parent) + "/")
        self._web_view.setHtml(rendered_html, base_url)

    def _prepare_preview_data(self) -> Dict[str, Any]:
        """미리보기용 데이터 준비 - 이미지 필드는 플레이스홀더로 변환"""
        preview_data = {}

        for key, value in self._data.items():
            if key in self._image_fields:
                # 이미지 필드: 플레이스홀더 HTML로 변환
                if value and str(value).strip():
                    # 값이 있으면 초록 플레이스홀더
                    preview_data[key] = '<div style="width:100%;height:100%;min-width:30px;min-height:30px;background:#d4edda;border:2px dashed #28a745;display:flex;align-items:center;justify-content:center;color:#28a745;font-size:10px;">[IMG]</div>'
                else:
                    # 값이 없으면 안 보이게 (빈 문자열)
                    preview_data[key] = ""
            else:
                # 일반 필드: 그대로 전달
                preview_data[key] = value

        return preview_data

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
