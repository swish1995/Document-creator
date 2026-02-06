"""PDF 변환기 모듈

QWebEngine을 사용하여 HTML을 PDF로 변환합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable

from PyQt6.QtCore import QObject, QUrl, QMarginsF, pyqtSignal, QEventLoop, QTimer
from PyQt6.QtGui import QPageLayout, QPageSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWidgets import QApplication


class PdfConverter(QObject):
    """QWebEngine 기반 PDF 변환기"""

    conversion_finished = pyqtSignal(bool, str)  # success, path or error

    def __init__(self, parent=None):
        super().__init__(parent)
        self._web_view: Optional[QWebEngineView] = None
        self._current_output_path: Optional[Path] = None
        self._conversion_success = False
        self._conversion_error = ""

    def _ensure_web_view(self):
        """WebEngineView 초기화 (지연 생성)"""
        if self._web_view is None:
            self._web_view = QWebEngineView()
            self._web_view.setMinimumSize(1, 1)
            # 화면에 표시하지 않음
            self._web_view.hide()

    def convert_html_to_pdf(
        self,
        html_path: Path,
        output_path: Path,
        page_width_mm: float = 210,
        page_height_mm: float = 297,
        margins_mm: float = 0,
    ) -> bool:
        """HTML 파일을 PDF로 변환

        Args:
            html_path: 입력 HTML 파일 경로
            output_path: 출력 PDF 파일 경로
            page_width_mm: 페이지 너비 (mm)
            page_height_mm: 페이지 높이 (mm)
            margins_mm: 여백 (mm)

        Returns:
            변환 성공 여부
        """
        self._ensure_web_view()
        self._current_output_path = output_path
        self._conversion_success = False
        self._conversion_error = ""

        # 출력 디렉토리 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 이벤트 루프 생성
        loop = QEventLoop()

        def on_load_finished(ok: bool):
            if not ok:
                self._conversion_error = "HTML 로드 실패"
                self._conversion_success = False
                loop.quit()
                return

            # 페이지 레이아웃 설정
            page_size = QPageSize(QPageSize.PageSizeId.A4)
            if page_width_mm != 210 or page_height_mm != 297:
                from PyQt6.QtCore import QSizeF
                page_size = QPageSize(QSizeF(page_width_mm, page_height_mm), QPageSize.Unit.Millimeter)

            margins = QMarginsF(margins_mm, margins_mm, margins_mm, margins_mm)
            page_layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, margins, QPageLayout.Unit.Millimeter)

            # PDF 변환
            self._web_view.page().printToPdf(str(output_path), page_layout)

        def on_pdf_finished(file_path: str, success: bool):
            self._conversion_success = success
            if not success:
                self._conversion_error = "PDF 변환 실패"
            loop.quit()

        # 시그널 연결
        self._web_view.loadFinished.connect(on_load_finished)
        self._web_view.page().pdfPrintingFinished.connect(on_pdf_finished)

        # HTML 로드
        url = QUrl.fromLocalFile(str(html_path.absolute()))
        self._web_view.load(url)

        # 타임아웃 설정 (30초)
        QTimer.singleShot(30000, loop.quit)

        # 이벤트 루프 실행
        loop.exec()

        # 시그널 연결 해제
        try:
            self._web_view.loadFinished.disconnect(on_load_finished)
            self._web_view.page().pdfPrintingFinished.disconnect(on_pdf_finished)
        except TypeError:
            pass

        return self._conversion_success

    def convert_html_string_to_pdf(
        self,
        html_content: str,
        output_path: Path,
        base_url: Optional[Path] = None,
        page_width_mm: float = 210,
        page_height_mm: float = 297,
        margins_mm: float = 0,
    ) -> bool:
        """HTML 문자열을 PDF로 변환

        Args:
            html_content: HTML 문자열
            output_path: 출력 PDF 파일 경로
            base_url: 기준 URL (상대 경로 해석용)
            page_width_mm: 페이지 너비 (mm)
            page_height_mm: 페이지 높이 (mm)
            margins_mm: 여백 (mm)

        Returns:
            변환 성공 여부
        """
        self._ensure_web_view()
        self._current_output_path = output_path
        self._conversion_success = False
        self._conversion_error = ""

        # 출력 디렉토리 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 이벤트 루프 생성
        loop = QEventLoop()

        def on_load_finished(ok: bool):
            if not ok:
                self._conversion_error = "HTML 로드 실패"
                self._conversion_success = False
                loop.quit()
                return

            # 페이지 레이아웃 설정
            page_size = QPageSize(QPageSize.PageSizeId.A4)
            if page_width_mm != 210 or page_height_mm != 297:
                from PyQt6.QtCore import QSizeF
                page_size = QPageSize(QSizeF(page_width_mm, page_height_mm), QPageSize.Unit.Millimeter)

            margins = QMarginsF(margins_mm, margins_mm, margins_mm, margins_mm)
            page_layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, margins, QPageLayout.Unit.Millimeter)

            # PDF 변환
            self._web_view.page().printToPdf(str(output_path), page_layout)

        def on_pdf_finished(file_path: str, success: bool):
            self._conversion_success = success
            if not success:
                self._conversion_error = "PDF 변환 실패"
            loop.quit()

        # 시그널 연결
        self._web_view.loadFinished.connect(on_load_finished)
        self._web_view.page().pdfPrintingFinished.connect(on_pdf_finished)

        # HTML 로드
        if base_url:
            base = QUrl.fromLocalFile(str(base_url.absolute()) + "/")
        else:
            base = QUrl()
        self._web_view.setHtml(html_content, base)

        # 타임아웃 설정 (30초)
        QTimer.singleShot(30000, loop.quit)

        # 이벤트 루프 실행
        loop.exec()

        # 시그널 연결 해제
        try:
            self._web_view.loadFinished.disconnect(on_load_finished)
            self._web_view.page().pdfPrintingFinished.disconnect(on_pdf_finished)
        except TypeError:
            pass

        return self._conversion_success

    def get_last_error(self) -> str:
        """마지막 에러 메시지 반환"""
        return self._conversion_error

    def cleanup(self):
        """리소스 정리"""
        if self._web_view:
            self._web_view.deleteLater()
            self._web_view = None
