"""TT4: MappingOverlay 단위 테스트

MappingOverlay 클릭 처리 및 플레이스홀더 하이라이트를 테스트합니다.
"""

import pytest
from unittest.mock import MagicMock

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtWidgets import QApplication

from src.ui.template_editor.mapping_overlay import (
    MappingOverlay,
    extract_placeholders_from_html,
    get_placeholder_positions,
)


@pytest.fixture(scope="module")
def app():
    """QApplication 인스턴스"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def overlay(app):
    """MappingOverlay 인스턴스"""
    return MappingOverlay()


class TestMappingOverlayInit:
    """MappingOverlay 초기화 테스트"""

    def test_overlay_created(self, overlay):
        """오버레이 생성 확인"""
        assert overlay is not None

    def test_empty_placeholders_initially(self, overlay):
        """초기 플레이스홀더 비어있음"""
        assert overlay.get_all_placeholders() == []

    def test_show_highlights_default_true(self, overlay):
        """기본 하이라이트 표시"""
        assert overlay._show_highlights is True


class TestPlaceholderManagement:
    """플레이스홀더 관리 테스트"""

    def test_set_placeholders(self, overlay):
        """플레이스홀더 설정"""
        placeholders = [
            {"id": "title", "label": "제목", "rect": QRect(10, 10, 100, 20)},
            {"id": "content", "label": "내용", "rect": QRect(10, 40, 100, 20)},
        ]
        overlay.set_placeholders(placeholders)

        assert len(overlay.get_all_placeholders()) == 2

    def test_clear_placeholders(self, overlay):
        """플레이스홀더 초기화"""
        placeholders = [{"id": "test", "rect": QRect(0, 0, 10, 10)}]
        overlay.set_placeholders(placeholders)
        overlay.clear_placeholders()

        assert overlay.get_all_placeholders() == []

    def test_get_placeholder_at(self, overlay):
        """특정 위치의 플레이스홀더 반환"""
        placeholders = [
            {"id": "title", "rect": QRect(10, 10, 100, 20)},
        ]
        overlay.set_placeholders(placeholders)

        # 플레이스홀더 내부
        result = overlay.get_placeholder_at(QPoint(50, 15))
        assert result is not None
        assert result["id"] == "title"

        # 플레이스홀더 외부
        result = overlay.get_placeholder_at(QPoint(200, 200))
        assert result is None


class TestHighlightControl:
    """하이라이트 표시 제어 테스트"""

    def test_set_show_highlights(self, overlay):
        """하이라이트 표시 설정"""
        overlay.set_show_highlights(False)
        assert overlay._show_highlights is False

        overlay.set_show_highlights(True)
        assert overlay._show_highlights is True


class TestSignals:
    """시그널 테스트"""

    def test_click_position_signal(self, overlay):
        """클릭 위치 시그널"""
        mock = MagicMock()
        overlay.click_position.connect(mock)

        # 빈 영역 클릭 시뮬레이션
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import QPointF

        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        overlay.mousePressEvent(event)

        mock.assert_called_once()

    def test_placeholder_clicked_signal(self, overlay):
        """플레이스홀더 클릭 시그널"""
        mock = MagicMock()
        overlay.placeholder_clicked.connect(mock)

        placeholders = [
            {"id": "title", "rect": QRect(10, 10, 100, 20)},
        ]
        overlay.set_placeholders(placeholders)

        # 플레이스홀더 클릭 시뮬레이션
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import QPointF

        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(50, 15),  # 플레이스홀더 내부
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        overlay.mousePressEvent(event)

        mock.assert_called_once()
        args = mock.call_args[0]
        assert args[0] == "title"


class TestExtractPlaceholders:
    """플레이스홀더 추출 함수 테스트"""

    def test_extract_single_placeholder(self):
        """단일 플레이스홀더 추출"""
        html = "<html><body>{{ title }}</body></html>"
        result = extract_placeholders_from_html(html)

        assert result == ["title"]

    def test_extract_multiple_placeholders(self):
        """다중 플레이스홀더 추출"""
        html = "<html><body>{{ title }} {{ content }} {{ author }}</body></html>"
        result = extract_placeholders_from_html(html)

        assert result == ["title", "content", "author"]

    def test_extract_duplicate_placeholders(self):
        """중복 플레이스홀더 제거"""
        html = "<html>{{ title }} {{ title }} {{ content }}</html>"
        result = extract_placeholders_from_html(html)

        assert result == ["title", "content"]

    def test_extract_no_placeholders(self):
        """플레이스홀더 없음"""
        html = "<html><body>No placeholders</body></html>"
        result = extract_placeholders_from_html(html)

        assert result == []

    def test_extract_with_whitespace(self):
        """공백 포함 플레이스홀더"""
        html = "{{title}} {{  content  }} {{ author}}"
        result = extract_placeholders_from_html(html)

        assert "title" in result
        assert "content" in result
        assert "author" in result


class TestGetPlaceholderPositions:
    """플레이스홀더 위치 정보 추출 테스트"""

    def test_get_positions_single(self):
        """단일 플레이스홀더 위치"""
        html = "Hello {{ name }}!"
        result = get_placeholder_positions(html)

        assert len(result) == 1
        assert result[0][0] == "name"  # field_id
        assert result[0][1] == 6  # start
        assert result[0][2] == 16  # end

    def test_get_positions_multiple(self):
        """다중 플레이스홀더 위치"""
        html = "{{ title }} - {{ author }}"
        result = get_placeholder_positions(html)

        assert len(result) == 2
        assert result[0][0] == "title"
        assert result[1][0] == "author"

    def test_get_positions_empty(self):
        """플레이스홀더 없음"""
        html = "No placeholders here"
        result = get_placeholder_positions(html)

        assert result == []
