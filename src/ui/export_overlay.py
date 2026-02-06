"""내보내기 오버레이 모듈

내보내기 진행 상황을 표시하는 오버레이 위젯입니다.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QGraphicsDropShadowEffect,
)


class ExportOverlay(QWidget):
    """내보내기 진행 오버레이

    전체 창을 흐리게 하고 중앙에 진행 상태를 표시합니다.
    """

    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        """UI 초기화"""
        # 전체 창 덮기
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAutoFillBackground(False)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 중앙 컨테이너
        self._center_container = QWidget()
        self._center_container.setFixedSize(400, 200)
        self._center_container.setObjectName("centerContainer")
        self._center_container.setStyleSheet("""
            QWidget#centerContainer {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 12px;
            }
        """)

        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self._center_container.setGraphicsEffect(shadow)

        # 컨테이너 레이아웃
        container_layout = QVBoxLayout(self._center_container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(16)

        # 제목
        self._title_label = QLabel("내보내기 진행 중...")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        container_layout.addWidget(self._title_label)

        # 진행률 바
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%v / %m")
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #444444;
                border: none;
                border-radius: 6px;
                height: 24px;
                text-align: center;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5ab87a, stop:1 #4aa86a);
                border-radius: 6px;
            }
        """)
        container_layout.addWidget(self._progress_bar)

        # 현재 파일명
        self._filename_label = QLabel("")
        self._filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._filename_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 11px;
                background-color: transparent;
            }
        """)
        container_layout.addWidget(self._filename_label)

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_button = QPushButton("취소")
        self._cancel_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a7a7a, stop:1 #6a6a6a);
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a8a8a, stop:1 #7a7a7a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a6a6a, stop:1 #7a7a7a);
            }
        """)
        self._cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_button)

        button_layout.addStretch()
        container_layout.addLayout(button_layout)

        # 중앙 정렬
        main_layout.addStretch()
        center_h_layout = QHBoxLayout()
        center_h_layout.addStretch()
        center_h_layout.addWidget(self._center_container)
        center_h_layout.addStretch()
        main_layout.addLayout(center_h_layout)
        main_layout.addStretch()

    def paintEvent(self, event):
        """배경 그리기 (반투명 어두운 배경)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 반투명 어두운 배경
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))

    def set_total(self, total: int):
        """전체 개수 설정"""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(0)

    def set_progress(self, current: int, total: int, filename: str = ""):
        """진행 상태 업데이트"""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        self._filename_label.setText(filename)

    def set_title(self, title: str):
        """제목 설정"""
        self._title_label.setText(title)

    def show_completed(self, message: str = "내보내기 완료!"):
        """완료 상태 표시"""
        self._title_label.setText(message)
        self._title_label.setStyleSheet("""
            QLabel {
                color: #5ab87a;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        self._cancel_button.setText("닫기")
        self._filename_label.setText("")

    def show_error(self, message: str = "내보내기 실패"):
        """에러 상태 표시"""
        self._title_label.setText(message)
        self._title_label.setStyleSheet("""
            QLabel {
                color: #e57373;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        self._cancel_button.setText("닫기")
        self._filename_label.setText("")

    def reset(self):
        """상태 초기화"""
        self._title_label.setText("내보내기 진행 중...")
        self._title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        self._progress_bar.setValue(0)
        self._filename_label.setText("")
        self._cancel_button.setText("취소")

    def _on_cancel(self):
        """취소 버튼 클릭"""
        self.cancel_requested.emit()

    def resizeEvent(self, event):
        """크기 변경 시 부모에 맞춤"""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
