"""매핑 오버레이 모듈

미리보기 위에 투명 오버레이를 표시하여 클릭 기반 매핑을 지원합니다.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtWidgets import QWidget, QToolTip


class MappingOverlay(QWidget):
    """매핑 모드 오버레이

    미리보기 위에 투명하게 표시되며, 플레이스홀더 위치를 하이라이트하고
    클릭 이벤트를 캡처합니다.
    """

    # 시그널
    placeholder_clicked = pyqtSignal(str, QPoint)  # field_id, position
    placeholder_inserted = pyqtSignal(str, int)  # field_id, position
    click_position = pyqtSignal(QPoint)  # 클릭 위치 (필드 선택 팝업용)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._placeholders: List[Dict[str, Any]] = []
        self._hovered_placeholder: Optional[Dict[str, Any]] = None
        self._show_highlights: bool = True

        # 투명 배경 설정
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

    def set_placeholders(self, placeholders: List[Dict[str, Any]]):
        """플레이스홀더 목록 설정

        Args:
            placeholders: [{"id": str, "label": str, "rect": QRect}, ...]
        """
        self._placeholders = placeholders
        self.update()

    def set_show_highlights(self, show: bool):
        """하이라이트 표시 여부 설정"""
        self._show_highlights = show
        self.update()

    def clear_placeholders(self):
        """플레이스홀더 초기화"""
        self._placeholders = []
        self._hovered_placeholder = None
        self.update()

    def paintEvent(self, event):
        """오버레이 그리기"""
        if not self._show_highlights:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for placeholder in self._placeholders:
            rect = placeholder.get("rect")
            if not rect:
                continue

            is_hovered = placeholder == self._hovered_placeholder

            # 하이라이트 박스 그리기
            if is_hovered:
                # 호버 상태: 밝은 파란색
                pen = QPen(QColor(33, 150, 243, 200))
                brush = QBrush(QColor(33, 150, 243, 50))
            else:
                # 기본 상태: 노란색
                pen = QPen(QColor(255, 193, 7, 180))
                brush = QBrush(QColor(255, 193, 7, 30))

            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(rect)

            # 필드 ID 라벨 그리기
            if is_hovered:
                label = placeholder.get("label", placeholder.get("id", ""))
                font = QFont()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)

                label_rect = QRect(
                    rect.x(),
                    rect.y() - 18,
                    max(80, len(label) * 8),
                    16,
                )
                painter.fillRect(label_rect, QColor(33, 150, 243, 220))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)

        painter.end()

    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        pos = event.position().toPoint()

        # 호버 상태 업데이트
        hovered = None
        for placeholder in self._placeholders:
            rect = placeholder.get("rect")
            if rect and rect.contains(pos):
                hovered = placeholder
                break

        if hovered != self._hovered_placeholder:
            self._hovered_placeholder = hovered
            self.update()

            # 툴팁 표시
            if hovered:
                label = hovered.get("label", hovered.get("id", ""))
                QToolTip.showText(event.globalPosition().toPoint(), label, self)
            else:
                QToolTip.hideText()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint()

        # 플레이스홀더 클릭 확인
        for placeholder in self._placeholders:
            rect = placeholder.get("rect")
            if rect and rect.contains(pos):
                field_id = placeholder.get("id", "")
                self.placeholder_clicked.emit(field_id, pos)
                return

        # 빈 영역 클릭: 필드 선택 팝업용
        self.click_position.emit(pos)

        super().mousePressEvent(event)

    def leaveEvent(self, event):
        """마우스 이탈 이벤트"""
        self._hovered_placeholder = None
        self.update()
        super().leaveEvent(event)

    def get_placeholder_at(self, pos: QPoint) -> Optional[Dict[str, Any]]:
        """특정 위치의 플레이스홀더 반환"""
        for placeholder in self._placeholders:
            rect = placeholder.get("rect")
            if rect and rect.contains(pos):
                return placeholder
        return None

    def get_all_placeholders(self) -> List[Dict[str, Any]]:
        """모든 플레이스홀더 반환"""
        return self._placeholders.copy()


def extract_placeholders_from_html(html: str) -> List[str]:
    """HTML에서 Jinja2 플레이스홀더 추출

    Args:
        html: HTML 문자열

    Returns:
        플레이스홀더 ID 목록 (중복 제거)
    """
    pattern = r"\{\{\s*(\w+)\s*\}\}"
    matches = re.findall(pattern, html)
    return list(dict.fromkeys(matches))  # 중복 제거, 순서 유지


def get_placeholder_positions(html: str) -> List[Tuple[str, int, int]]:
    """HTML에서 플레이스홀더 위치 정보 추출

    Args:
        html: HTML 문자열

    Returns:
        [(field_id, start, end), ...] 형태의 목록
    """
    pattern = r"\{\{\s*(\w+)\s*\}\}"
    positions = []

    for match in re.finditer(pattern, html):
        field_id = match.group(1)
        start = match.start()
        end = match.end()
        positions.append((field_id, start, end))

    return positions
