"""메인 윈도우 모듈

Document Creator의 메인 윈도우를 정의합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLabel,
    QScrollArea,
)

from src.core.template_manager import TemplateManager
from src.core.document_generator import DocumentGenerator
from src.core.logger import get_logger
from src.ui.excel_viewer import ExcelViewer
from src.ui.template_panel import TemplatePanel
from src.ui.export_dialog import ExportDialog
from src.ui.export_progress_dialog import ExportProgressDialog


class MainWindow(QMainWindow):
    """Document Creator 메인 윈도우"""

    MAX_TEMPLATE_PANELS = 5

    # 버튼 색상 정의 (스켈레톤 분석기와 동일)
    BUTTON_COLORS = {
        'export': ('#5ab87a', '#4aa86a', '#6ac88a'),    # 초록색
        'add': ('#5a7ab8', '#4a6aa8', '#6a8ac8'),       # 파란색
    }

    def __init__(self, templates_dir: Optional[Path] = None):
        super().__init__()
        self._logger = get_logger("main_window")
        self._logger.info("MainWindow 초기화 시작")

        self._settings = QSettings("SafetyDoc", "DocumentCreator")
        self._current_file: Optional[Path] = None
        self._template_panels: List[TemplatePanel] = []

        # 템플릿 매니저 초기화
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent.parent / "templates"
        self._templates_dir = templates_dir

        if templates_dir.exists():
            self._template_manager = TemplateManager(templates_dir)
            self._logger.debug(f"템플릿 디렉토리 로드: {templates_dir}")
        else:
            self._template_manager = None
            self._logger.warning(f"템플릿 디렉토리 없음: {templates_dir}")

        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._restore_geometry()

    def _get_button_style(self, color_key: str) -> str:
        """버튼 스타일 생성 (스켈레톤 분석기와 동일)"""
        colors = self.BUTTON_COLORS.get(color_key, self.BUTTON_COLORS['export'])
        base, dark, light = colors

        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {base}, stop:1 {dark});
                color: white;
                border: none;
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {light}, stop:1 {base});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {dark}, stop:1 {base});
            }}
            QPushButton:disabled {{
                background: #444444;
                color: #666666;
            }}
        """

    def _setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Document Creator")
        self.setMinimumSize(1200, 800)

        # 전체 앱 다크 테마 스타일 (스켈레톤 분석기와 동일)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #333333;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #0d47a1;
            }
            QMenu {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #0d47a1;
            }
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #2b2b2b;
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # 상단/하단 스플리터
        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setObjectName("mainSplitter")
        self._splitter.setHandleWidth(8)
        self._splitter.setStyleSheet("""
            QSplitter#mainSplitter::handle:vertical {
                height: 2px;
                margin-top: 1px;
                margin-bottom: 5px;
                background: qlineargradient(
                    x1: 0.25, y1: 0,
                    x2: 0.75, y2: 0,
                    stop: 0 transparent,
                    stop: 0.001 #888888,
                    stop: 0.999 #888888,
                    stop: 1 transparent
                );
            }
        """)
        main_layout.addWidget(self._splitter)

        # 상단 영역 - 템플릿 패널 컨테이너 (스크롤 가능)
        self._template_scroll = QScrollArea()
        self._template_scroll.setWidgetResizable(True)
        self._template_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._template_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._template_scroll.setMinimumHeight(250)

        self._template_container = QWidget()
        self._template_layout = QHBoxLayout(self._template_container)
        self._template_layout.setContentsMargins(0, 0, 0, 0)
        self._template_layout.setSpacing(8)

        # 패널 추가 버튼 (먼저 생성)
        self._add_panel_button = QPushButton("+")
        self._add_panel_button.setFixedSize(40, 40)
        self._add_panel_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                border: 2px dashed #666666;
                border-radius: 8px;
                background-color: #3a3a3a;
                color: #888888;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #888888;
                color: #aaaaaa;
            }
        """)
        self._add_panel_button.clicked.connect(self._on_add_panel)
        self._template_layout.addWidget(self._add_panel_button)

        self._template_layout.addStretch()

        # 초기 템플릿 패널 추가
        if self._template_manager:
            self._add_template_panel()
        self._template_scroll.setWidget(self._template_container)
        self._splitter.addWidget(self._template_scroll)

        # 하단 영역 - 엑셀 뷰어
        self._excel_container = QWidget()
        excel_layout = QVBoxLayout(self._excel_container)
        excel_layout.setContentsMargins(0, 0, 0, 0)

        self._excel_viewer = ExcelViewer()
        self._excel_viewer.file_loaded.connect(self._on_file_loaded)
        self._excel_viewer.preview_row_changed.connect(self._on_preview_row_changed)
        self._excel_viewer.selection_changed.connect(self._on_selection_changed)
        excel_layout.addWidget(self._excel_viewer)

        # 내보내기 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._export_button = QPushButton("내보내기")
        self._export_button.setEnabled(False)
        self._export_button.setMinimumWidth(150)
        self._export_button.setFixedHeight(28)
        self._export_button.setStyleSheet(self._get_button_style('export'))
        self._export_button.clicked.connect(self._on_export_clicked)
        button_layout.addWidget(self._export_button)

        excel_layout.addLayout(button_layout)

        self._splitter.addWidget(self._excel_container)

        # 스플리터 비율 설정 (상단:하단 = 2:3)
        self._splitter.setSizes([300, 500])

    def _add_template_panel(self) -> Optional[TemplatePanel]:
        """템플릿 패널 추가"""
        if not self._template_manager:
            return None

        if len(self._template_panels) >= self.MAX_TEMPLATE_PANELS:
            return None

        panel = TemplatePanel(self._template_manager)
        panel.setMinimumWidth(250)
        panel.close_requested.connect(lambda p=panel: self._on_panel_close_requested(p))
        panel.template_changed.connect(self._on_template_changed)

        # 추가 버튼 앞에 삽입
        insert_index = self._template_layout.count() - 2  # 버튼과 stretch 앞
        self._template_layout.insertWidget(max(0, insert_index), panel)
        self._template_panels.append(panel)

        self._update_add_button_visibility()
        return panel

    def _on_add_panel(self):
        """패널 추가 버튼 클릭"""
        self._add_template_panel()

    def _on_panel_close_requested(self, panel: TemplatePanel):
        """패널 닫기 요청"""
        if panel in self._template_panels:
            self._template_panels.remove(panel)
            panel.deleteLater()
            self._update_add_button_visibility()

    def _update_add_button_visibility(self):
        """추가 버튼 표시/숨김"""
        self._add_panel_button.setVisible(
            len(self._template_panels) < self.MAX_TEMPLATE_PANELS
        )

    def _setup_menu(self):
        """메뉴바 설정"""
        menu_bar = self.menuBar()

        # 파일 메뉴
        self._file_menu = menu_bar.addMenu("파일(&F)")

        # 열기 액션
        open_action = QAction("열기(&O)...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_file)
        self._file_menu.addAction(open_action)

        self._file_menu.addSeparator()

        # 종료 액션
        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        self._file_menu.addAction(exit_action)

        # 편집 메뉴
        self._edit_menu = menu_bar.addMenu("편집(&E)")

        select_all_action = QAction("전체 선택(&A)", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self._on_select_all)
        self._edit_menu.addAction(select_all_action)

        deselect_action = QAction("선택 해제(&D)", self)
        deselect_action.setShortcut("Ctrl+D")
        deselect_action.triggered.connect(self._on_deselect_all)
        self._edit_menu.addAction(deselect_action)

        self._edit_menu.addSeparator()

        export_action = QAction("내보내기(&E)...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export_clicked)
        self._edit_menu.addAction(export_action)

        # 보기 메뉴
        self._view_menu = menu_bar.addMenu("보기(&V)")

        # 도움말 메뉴
        self._help_menu = menu_bar.addMenu("도움말(&H)")

        about_action = QAction("정보(&A)", self)
        about_action.triggered.connect(self._on_about)
        self._help_menu.addAction(about_action)

    def _setup_status_bar(self):
        """상태바 설정"""
        status_bar = self.statusBar()
        status_bar.showMessage("준비")
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #2b2b2b;
                color: #888888;
                border-top: 1px solid #444444;
            }
            QStatusBar::item {
                border: none;
            }
        """)

        # 버전 레이블
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #666666;")
        status_bar.addPermanentWidget(version_label)

    def _restore_geometry(self):
        """윈도우 위치/크기 복원"""
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        state = self._settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        """윈도우 닫기 이벤트"""
        self._logger.info("앱 종료")
        # 윈도우 위치/크기 저장
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def _on_open_file(self):
        """파일 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "엑셀 파일 열기",
            str(Path.home()),
            "Excel Files (*.xlsx *.xls);;All Files (*)",
        )

        if file_path:
            self._load_file(Path(file_path))

    def _load_file(self, file_path: Path):
        """파일 로드"""
        self._logger.info(f"파일 로드 시작: {file_path}")
        try:
            self._excel_viewer.load_file(file_path)
            self._current_file = file_path
            self._logger.info(f"파일 로드 완료: {file_path}")
            self.setWindowTitle(f"Document Creator - {file_path.name}")
        except Exception as e:
            self._logger.error(f"파일 로드 실패: {file_path}, 오류: {e}")
            QMessageBox.critical(self, "오류", f"파일을 열 수 없습니다:\n{e}")

    def _on_file_loaded(self, filename: str, row_count: int):
        """파일 로드 완료"""
        self.statusBar().showMessage(f"파일 로드됨: {filename} ({row_count}행)")

        # 템플릿 패널에 엑셀 헤더 및 파일 경로 전달
        headers = self._excel_viewer._loader.get_headers() if self._excel_viewer._loader else []
        for panel in self._template_panels:
            panel.set_excel_headers(headers)
            if self._current_file:
                panel.set_excel_file_path(str(self._current_file))

        # 첫 번째 행으로 미리보기 업데이트
        self._update_previews(0)

    def _on_preview_row_changed(self, row_index: int):
        """미리보기 행 변경"""
        self._update_previews(row_index)
        self.statusBar().showMessage(f"미리보기: {row_index + 1}행")

    def _update_previews(self, row_index: int):
        """모든 템플릿 패널 미리보기 업데이트"""
        row_data = self._excel_viewer.get_row_data(row_index)
        if row_data:
            for panel in self._template_panels:
                if panel.is_active:
                    panel.update_preview(row_data)

    def _on_selection_changed(self, selected_rows: list):
        """선택 변경"""
        count = len(selected_rows)
        active_templates = sum(1 for p in self._template_panels if p.is_active)

        if count > 0 and active_templates > 0:
            total_files = count * active_templates
            self._export_button.setEnabled(True)
            self._export_button.setText(f"내보내기 ({count}행 × {active_templates}템플릿 = {total_files}개)")
        else:
            self._export_button.setEnabled(False)
            self._export_button.setText("내보내기")

    def _on_template_changed(self, template_name: str):
        """템플릿 변경"""
        # 선택 상태 업데이트
        self._on_selection_changed(self._excel_viewer.get_selected_rows())

        # 현재 미리보기 행으로 업데이트
        preview_row = self._excel_viewer.get_preview_row()
        self._update_previews(preview_row)

    def _on_export_clicked(self):
        """내보내기 버튼 클릭"""
        selected = self._excel_viewer.get_selected_rows()
        active_panels = [p for p in self._template_panels if p.is_active]

        if not selected:
            self._logger.warning("내보내기 시도: 선택된 행 없음")
            QMessageBox.warning(self, "경고", "내보낼 행을 선택해주세요.")
            return

        if not active_panels:
            self._logger.warning("내보내기 시도: 선택된 템플릿 없음")
            QMessageBox.warning(self, "경고", "내보낼 템플릿을 선택해주세요.")
            return

        self._logger.info(f"내보내기 시작: {len(selected)}행, {len(active_panels)}개 템플릿")

        # 템플릿 이름 목록
        template_names = [p.current_template_name for p in active_panels if p.current_template_name]

        # 내보내기 설정 다이얼로그
        export_dialog = ExportDialog(
            row_count=len(selected),
            template_names=template_names,
            parent=self
        )

        if export_dialog.exec() != ExportDialog.DialogCode.Accepted:
            return

        settings = export_dialog.get_settings()

        # 선택된 행 데이터 가져오기
        rows_data = self._excel_viewer.get_selected_data()
        excel_headers = self._excel_viewer._loader.get_headers() if self._excel_viewer._loader else []

        # DocumentGenerator 생성
        generator = DocumentGenerator(self._template_manager)

        # 진행 다이얼로그 표시
        progress_dialog = ExportProgressDialog(
            generator=generator,
            template_names=template_names,
            rows_data=rows_data,
            output_dir=settings["output_dir"],
            settings=settings,
            excel_headers=excel_headers,
            parent=self
        )
        progress_dialog.exec()

        # 결과 표시
        files = progress_dialog.get_generated_files()
        if files:
            self.statusBar().showMessage(f"내보내기 완료: {len(files)}개 파일 생성됨")

    def _on_select_all(self):
        """전체 선택"""
        self._excel_viewer.select_all()

    def _on_deselect_all(self):
        """선택 해제"""
        self._excel_viewer.deselect_all()

    def _on_about(self):
        """정보 다이얼로그"""
        QMessageBox.about(
            self,
            "Document Creator 정보",
            "Document Creator v1.0.0\n\n"
            "Skeleton Analyzer 출력 데이터를\n"
            "인체공학적 평가 문서로 변환합니다.",
        )
