"""메인 윈도우 모듈

Document Creator의 메인 윈도우를 정의합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon
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
from src.core.template_storage import TemplateStorage
from src.core.export_manager import ExportManager
from src.core.logger import get_logger
from src.ui.excel_viewer import ExcelViewer
from src.ui.template_panel import TemplatePanel
from src.ui.main_toolbar import MainToolbar
from src.ui.template_editor import TemplateManagerDialog, EditorWidget
from src.ui.export_dialog import ExportDialog
from src.ui.export_overlay import ExportOverlay
from src.ui.help_dialog import HelpDialog
from src.license import LicenseManager
from src.license.license_dialog import LicenseDialog


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
        self._template_panels: List[TemplatePanel] = []  # 호환성 유지
        self._data_sheet_visible = True
        self._current_template_id: Optional[str] = None
        self._template_scroll_positions: Dict[str, tuple] = {}  # 템플릿별 스크롤 위치

        # 작업 디렉토리 설정 및 정리 (고아 파일 방지)
        self._work_dir = Path(__file__).parent.parent.parent / "worked"
        ExportManager.cleanup_work_dir(self._work_dir)
        self._logger.debug(f"작업 디렉토리 정리: {self._work_dir}")

        # 내보내기 관련 상태
        self._export_manager: Optional[ExportManager] = None
        self._export_overlay: Optional[ExportOverlay] = None
        self._is_exporting = False

        # 템플릿 매니저 및 저장소 초기화
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent.parent / "templates"
        self._templates_dir = templates_dir

        if templates_dir.exists():
            self._template_manager = TemplateManager(templates_dir)
            self._template_storage = TemplateStorage(templates_dir)
            self._logger.debug(f"템플릿 디렉토리 로드: {templates_dir}")
        else:
            self._template_manager = None
            self._template_storage = None
            self._logger.warning(f"템플릿 디렉토리 없음: {templates_dir}")

        self._setup_ui()
        self._setup_overlay()
        self._setup_toolbar()
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
            QToolBar {
                background-color: #333333;
                border: none;
                border-bottom: 1px solid #444444;
                padding: 8px 10px 8px 16px;
                spacing: 8px;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-bottom: 1px solid #444444;
                padding: 6px 8px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QMenuBar::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a7ab8, stop:1 #4a6aa8);
            }
            QMenuBar::item:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6aa8, stop:1 #3a5a98);
            }
            QMenu {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a7ab8, stop:1 #4a6aa8);
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 4px 8px;
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
        main_layout.setContentsMargins(8, 0, 8, 8)  # 상단 마진 0 (툴바와 색상 차이 제거)

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

        # 상단 영역 - 템플릿 편집기
        self._editor_widget = EditorWidget()
        self._editor_widget.setMinimumHeight(250)
        self._editor_widget.content_modified.connect(self._on_editor_content_modified)
        self._editor_widget.auto_saved.connect(self._on_editor_auto_saved)
        self._editor_widget.scroll_changed.connect(self._on_scroll_changed)
        self._editor_widget.page_loaded.connect(self._on_page_loaded)
        self._editor_widget.column_highlight_requested.connect(self._on_column_highlight_requested)
        self._editor_widget.mapping_save_requested.connect(self._on_mapping_save)
        self._editor_widget.mapping_save_as_requested.connect(self._on_mapping_save_as)
        self._pending_scroll_restore: Optional[str] = None  # 페이지 로드 후 복구할 템플릿 ID
        self._splitter.addWidget(self._editor_widget)

        # 하단 영역 - 엑셀 뷰어
        self._excel_container = QWidget()
        excel_layout = QVBoxLayout(self._excel_container)
        excel_layout.setContentsMargins(0, 0, 0, 0)

        self._excel_viewer = ExcelViewer()
        self._excel_viewer.file_loaded.connect(self._on_file_loaded)
        self._excel_viewer.preview_row_changed.connect(self._on_preview_row_changed)
        self._excel_viewer.selection_changed.connect(self._on_selection_changed)
        excel_layout.addWidget(self._excel_viewer)

        self._excel_container.setMinimumHeight(150)
        self._splitter.addWidget(self._excel_container)

        # 스플리터로 패널이 완전히 축소되지 않도록 설정
        self._splitter.setChildrenCollapsible(False)

        # 스플리터 비율 설정 (상단:하단 = 2:3)
        self._splitter.setSizes([300, 500])

    def _setup_toolbar(self):
        """메인 툴바 설정"""
        self._toolbar = MainToolbar(self)
        self.addToolBar(self._toolbar)

        # 툴바 시그널 연결
        self._toolbar.data_sheet_toggled.connect(self._on_data_sheet_toggled)
        self._toolbar.template_selected.connect(self._on_toolbar_template_selected)
        self._toolbar.template_manage_requested.connect(self._on_manage_templates)
        self._toolbar.category_filter_changed.connect(self._on_category_filter_changed)
        self._toolbar.mode_changed.connect(self._on_mode_changed)
        self._toolbar.zoom_changed.connect(self._on_zoom_changed)
        self._toolbar.generate_requested.connect(self._on_export_clicked)
        self._toolbar.exit_requested.connect(self._on_exit_requested)

        # 템플릿 목록 업데이트 및 첫 번째 템플릿 로드
        self._update_toolbar_templates()
        self._load_initial_template()

    def _get_template_sort_key(self, template) -> tuple:
        """템플릿 정렬 키 반환 (카테고리 → 안전지표 순서 → 이름순)"""
        from src.core.template_manager import SAFETY_INDICATORS

        category = getattr(template, 'category', None)
        # 카테고리 순서 조회
        cat_order = 999
        if category and hasattr(self, '_template_manager') and self._template_manager:
            for cat in self._template_manager.categories:
                if cat["id"] == category:
                    cat_order = cat.get("sort_order", 999)
                    break
        # 안전지표 순서 (RULA=0, REBA=1, OWAS=2, NLE=3, SI=4)
        si = getattr(template, 'safety_indicator', None)
        si_order = len(SAFETY_INDICATORS)
        if si and si in SAFETY_INDICATORS:
            si_order = SAFETY_INDICATORS.index(si)
        return (not template.is_builtin, cat_order, si_order, template.name.upper())

    def _update_toolbar_templates(self):
        """툴바의 템플릿 드롭다운 업데이트 (카테고리 그룹핑 + 빌트인/사용자 구분)"""
        if self._template_storage:
            all_templates = self._template_storage.get_all_templates()
            sorted_templates = sorted(all_templates, key=self._get_template_sort_key)

            # 활성화된 템플릿만 표시 (카테고리 + 빌트인 정보 포함)
            templates = []
            for t in sorted_templates:
                is_active = True
                if t.metadata and hasattr(t.metadata, 'is_active'):
                    is_active = t.metadata.is_active
                if is_active:
                    category = getattr(t, 'category', None)
                    templates.append((t.id, t.name, category, t.is_builtin))

            # 카테고리 목록 가져오기
            categories = []
            if hasattr(self, '_template_manager') and self._template_manager:
                categories = self._template_manager.categories

            if categories:
                self._toolbar.set_templates_grouped(templates, categories)
            else:
                # 카테고리 없으면 기존 방식
                self._toolbar.set_templates([(t[0], t[1]) for t in templates])

    def _load_initial_template(self):
        """앱 시작 시 첫 번째 활성화된 템플릿 로드"""
        if self._template_storage and not self._current_template_id:
            all_templates = self._template_storage.get_all_templates()
            if all_templates:
                # 안전지표 순서로 정렬
                sorted_templates = sorted(all_templates, key=self._get_template_sort_key)

                # 첫 번째 활성화된 템플릿 찾기
                for template in sorted_templates:
                    is_active = True
                    if template.metadata and hasattr(template.metadata, 'is_active'):
                        is_active = template.metadata.is_active
                    if is_active:
                        self._toolbar.set_current_template(template.id)
                        self._on_toolbar_template_selected(template.id)
                        break

    def _on_category_filter_changed(self, category_id: str):
        """카테고리 필터 변경"""
        self._toolbar._update_template_combo(filter_category=category_id)
        # 콤보 재구성 후 선택된 첫 번째 템플릿으로 에디터 갱신
        index = self._toolbar.combo_template.currentIndex()
        template_id = self._toolbar.combo_template.itemData(index)
        if template_id:
            self._on_toolbar_template_selected(template_id)

    def _on_column_highlight_requested(self, column_index: int):
        """EditorWidget에서 컬럼 하이라이트 요청"""
        if self._data_sheet_visible:
            self._excel_viewer.highlight_column(column_index)

    def _on_data_sheet_toggled(self, visible: bool):
        """데이터 시트 표시/숨김 토글"""
        self._data_sheet_visible = visible
        self._excel_container.setVisible(visible)

        if not visible and self._current_file:
            # 숨김 시 상태바에 파일 정보 표시
            row_count = self._excel_viewer.row_count if hasattr(self._excel_viewer, 'row_count') else 0
            self.statusBar().showMessage(f"📊 {self._current_file.name} ({row_count}행) - 데이터 시트 숨김")
        elif visible:
            self.statusBar().showMessage("데이터 시트 표시됨")

    def _on_toolbar_template_selected(self, template_id: str):
        """툴바에서 템플릿 선택"""
        if not self._template_storage:
            return

        # 매핑 변경 중 다른 템플릿 선택 시 경고
        if self._editor_widget.is_dirty:
            from src.ui.utils.styled_message_box import StyledMessageBox
            result = StyledMessageBox.question(
                self,
                "매핑 변경 확인",
                "저장되지 않은 매핑 정보는 사라집니다.\n다른 템플릿으로 전환하시겠습니까?"
            )
            if not result:
                # 취소 → 현재 템플릿 유지
                if self._current_template_id:
                    self._toolbar.set_current_template(self._current_template_id)
                return
            self._editor_widget.restore_original_fields()

        # 스크롤 위치는 scroll_changed 시그널로 실시간 저장됨

        template = self._template_storage.get_template(template_id)
        if template:
            self._current_template_id = template_id
            # 페이지 로드 완료 후 스크롤 복구를 위해 저장
            self._pending_scroll_restore = template_id
            try:
                html_content = template.template_path.read_text(encoding="utf-8")
                self._editor_widget.set_template(
                    template_id,
                    template.template_path,
                    html_content,
                    fields=template.fields,
                    is_builtin=template.is_builtin,
                )
                # 다른 이름으로 저장 다이얼로그 컨텍스트 설정
                self._update_save_as_context(template)
                self.statusBar().showMessage(f"템플릿 로드됨: {template.name}")
            except Exception as e:
                self._logger.error(f"템플릿 로드 실패: {e}")
                QMessageBox.warning(self, "경고", f"템플릿을 로드할 수 없습니다:\n{e}")

    def _update_save_as_context(self, template):
        """다른 이름으로 저장 다이얼로그에 필요한 컨텍스트를 EditorWidget에 전달"""
        categories = []
        if hasattr(self, '_template_manager') and self._template_manager:
            categories = self._template_manager.categories

        default_category = getattr(template, 'category', '') or ''

        existing_names = []
        if self._template_storage:
            # 빌트인 + 사용자 템플릿 이름 모두 포함 (대소문자 무시 중복 방지)
            existing_names = [t.name for t in self._template_storage.get_all_templates()]

        self._editor_widget.set_save_as_context(categories, default_category, existing_names)

    def _on_mapping_save(self):
        """매핑 저장 요청 처리 (사용자 템플릿 덮어쓰기)"""
        if not self._template_storage or not self._current_template_id:
            return

        template = self._template_storage.get_template(self._current_template_id)
        if not template or template.is_readonly:
            return

        try:
            modified_fields = self._editor_widget._fields
            self._template_storage.update_user_mapping(
                self._current_template_id, modified_fields
            )
            self.statusBar().showMessage("매핑이 저장되었습니다.")
        except Exception as e:
            self._logger.error(f"매핑 저장 실패: {e}")
            QMessageBox.warning(self, "경고", f"매핑 저장에 실패했습니다:\n{e}")

    def _on_mapping_save_as(self, name: str, category: str):
        """다른 이름으로 저장 요청 처리 (새 사용자 템플릿 생성)"""
        if not self._template_storage or not self._current_template_id:
            return

        try:
            modified_fields = self._editor_widget._fields
            new_template = self._template_storage.create_user_template_from(
                src_id=self._current_template_id,
                name=name,
                category=category,
                modified_fields=modified_fields,
            )

            # 툴바 템플릿 목록 갱신
            self._update_toolbar_templates()

            # 새로 생성된 템플릿으로 전환
            self._toolbar.set_current_template(new_template.id)
            self._on_toolbar_template_selected(new_template.id)

            self.statusBar().showMessage(f"새 템플릿 '{name}'이(가) 생성되었습니다.")
        except Exception as e:
            self._logger.error(f"템플릿 생성 실패: {e}")
            QMessageBox.warning(self, "경고", f"템플릿 생성에 실패했습니다:\n{e}")

    def _on_page_loaded(self):
        """페이지 로드 완료 시 스크롤 위치 복구"""
        if self._pending_scroll_restore:
            template_id = self._pending_scroll_restore
            self._pending_scroll_restore = None
            self._restore_scroll_position(template_id)

    def _on_scroll_changed(self, x: int, y: int):
        """스크롤 위치 변경 시 실시간 저장"""
        if self._current_template_id:
            self._template_scroll_positions[self._current_template_id] = (x, y)

    def _save_current_scroll_position(self):
        """현재 템플릿의 스크롤 위치 저장 (deprecated - 실시간 저장으로 대체)"""
        pass  # 스크롤 위치는 _on_scroll_changed에서 실시간으로 저장됨

    def _restore_scroll_position(self, template_id: str):
        """저장된 스크롤 위치 복구"""
        if template_id in self._template_scroll_positions:
            x, y = self._template_scroll_positions[template_id]
            self._editor_widget.set_scroll_position(x, y)

    def _on_manage_templates(self):
        """템플릿 관리 다이얼로그"""
        if not self._template_storage:
            QMessageBox.warning(self, "경고", "템플릿 저장소를 사용할 수 없습니다.")
            return

        dialog = TemplateManagerDialog(self._template_storage, self)
        dialog.templates_changed.connect(self._on_templates_changed)
        dialog.exec()

    def _on_templates_changed(self):
        """템플릿 목록 변경됨"""
        # 템플릿 매니저 새로고침
        if self._template_manager:
            self._template_manager.refresh()
        # 템플릿 저장소 새로고침
        if self._template_storage:
            self._template_storage.refresh()
        # 툴바 업데이트
        self._update_toolbar_templates()

        # 현재 선택된 템플릿이 비활성화되었는지 확인
        if self._current_template_id and self._template_storage:
            current_template = self._template_storage.get_template(self._current_template_id)
            if current_template:
                is_active = True
                if current_template.metadata and hasattr(current_template.metadata, 'is_active'):
                    is_active = current_template.metadata.is_active

                if not is_active:
                    # 비활성화된 템플릿이 선택됨 - 첫 번째 활성 템플릿으로 변경
                    self._select_first_active_template()

        # 생성 버튼 텍스트 갱신
        self._update_generate_button_text()

    def _update_generate_button_text(self):
        """생성 버튼 텍스트 갱신"""
        if hasattr(self, '_excel_viewer') and self._excel_viewer:
            self._on_selection_changed(self._excel_viewer.get_selected_rows())

    def _select_first_active_template(self):
        """첫 번째 활성화된 템플릿 선택"""
        if not self._template_storage:
            return

        all_templates = self._template_storage.get_all_templates()
        sorted_templates = sorted(all_templates, key=self._get_template_sort_key)

        for template in sorted_templates:
            is_active = True
            if template.metadata and hasattr(template.metadata, 'is_active'):
                is_active = template.metadata.is_active
            if is_active:
                self._toolbar.set_current_template(template.id)
                self._on_toolbar_template_selected(template.id)
                break

    def _on_mode_changed(self, mode: int):
        """모드 변경"""
        mode_names = {0: "미리보기", 1: "매핑"}

        # 매핑 모드 → 미리보기 모드 전환 시 미저장 경고
        if mode == EditorWidget.MODE_PREVIEW and self._editor_widget.is_dirty:
            from src.ui.utils.styled_message_box import StyledMessageBox
            result = StyledMessageBox.question(
                self,
                "매핑 변경 확인",
                "저장되지 않은 매핑 정보는 사라집니다.\n모드를 전환하시겠습니까?"
            )
            if not result:
                # 취소 → 매핑 모드 유지
                self._toolbar.set_mode(EditorWidget.MODE_MAPPING)
                return
            # 원복
            self._editor_widget.restore_original_fields()

        self._editor_widget.set_mode(mode)
        # 매핑 모드가 아니면 컬럼 하이라이트 해제
        if mode != EditorWidget.MODE_MAPPING:
            self._excel_viewer.clear_highlight()
        self.statusBar().showMessage(f"모드: {mode_names.get(mode, '알 수 없음')}")

    def _on_zoom_changed(self, zoom: int):
        """줌 변경"""
        self._editor_widget.set_zoom(zoom)
        self.statusBar().showMessage(f"확대/축소: {zoom}%")

    def _on_editor_content_modified(self):
        """편집기 내용 수정됨"""
        pass  # 저장 버튼 제거됨

    def _on_editor_auto_saved(self, path: str):
        """편집기 자동 저장됨"""
        self.statusBar().showMessage(f"자동 저장됨: {path}")

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

        # 매핑 메뉴
        self._mapping_menu = menu_bar.addMenu("매핑(&M)")

        # 보기 메뉴
        self._view_menu = menu_bar.addMenu("보기(&V)")

        # 도움말 메뉴
        self._help_menu = menu_bar.addMenu("도움말(&H)")

        usage_action = QAction("사용 방법(&U)", self)
        usage_action.triggered.connect(self._on_usage)
        self._help_menu.addAction(usage_action)

        self._help_menu.addSeparator()

        license_action = QAction("라이센스 등록(&L)...", self)
        license_action.triggered.connect(self._on_license)
        self._help_menu.addAction(license_action)

        self._help_menu.addSeparator()

        about_action = QAction("정보(&A)", self)
        about_action.triggered.connect(self._on_about)
        self._help_menu.addAction(about_action)

    def _setup_overlay(self):
        """내보내기 오버레이 설정"""
        self._export_overlay = ExportOverlay(self.centralWidget())
        self._export_overlay.cancel_requested.connect(self._on_export_cancel)
        self._export_overlay.hide()

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

    def _restore_geometry(self):
        """윈도우 위치/크기 및 상태 복원"""
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        state = self._settings.value("windowState")
        if state:
            self.restoreState(state)

        # 보기 상태 복원 (데이터 시트 표시 여부)
        data_visible = self._settings.value("dataSheetVisible", True, type=bool)
        self._toolbar.set_data_sheet_visible(data_visible)
        self._excel_container.setVisible(data_visible)
        self._data_sheet_visible = data_visible

        # 모드 상태 복원 (미리보기/매핑)
        mode = self._settings.value("viewMode", 0, type=int)
        self._toolbar.set_mode(mode)

        # 템플릿별 스크롤 위치 복구
        import json
        scroll_data = self._settings.value("templateScrollPositions", "{}")
        try:
            self._template_scroll_positions = json.loads(scroll_data)
            # 키를 문자열로, 값을 튜플로 변환
            self._template_scroll_positions = {
                k: tuple(v) if isinstance(v, list) else v
                for k, v in self._template_scroll_positions.items()
            }
        except Exception:
            self._template_scroll_positions = {}

        # 카테고리 필터 복구
        saved_category = self._settings.value("categoryFilter", "")
        if saved_category:
            combo = self._toolbar.combo_category_filter
            for i in range(combo.count()):
                if combo.itemData(i) == saved_category:
                    combo.setCurrentIndex(i)
                    break

        # 확대/축소 복구
        zoom = self._settings.value("zoomLevel", 100, type=int)
        self._toolbar.set_zoom(zoom)
        self._editor_widget.set_mode(mode)

    def resizeEvent(self, event):
        """윈도우 크기 변경 이벤트"""
        super().resizeEvent(event)
        # 오버레이 크기 조정
        if self._export_overlay and self._export_overlay.isVisible():
            self._export_overlay.setGeometry(self.centralWidget().rect())

    def closeEvent(self, event):
        """윈도우 닫기 이벤트"""
        from src.ui.utils.styled_message_box import StyledMessageBox

        # 내보내기 중이면 경고
        if self._is_exporting:
            QMessageBox.warning(self, "경고", "내보내기 진행 중입니다.\n완료 후 종료해주세요.")
            event.ignore()
            return

        result = StyledMessageBox.question(
            self,
            "종료 확인",
            "프로그램을 종료하시겠습니까?"
        )

        if result:
            self._logger.info("앱 종료")

            # 이미지 디렉토리 정리
            if self._excel_viewer._loader:
                self._excel_viewer._loader.cleanup_images()

            # 작업 디렉토리 정리
            ExportManager.cleanup_work_dir(self._work_dir)

            # 윈도우 위치/크기 저장
            self._settings.setValue("geometry", self.saveGeometry())
            self._settings.setValue("windowState", self.saveState())
            # 보기 상태 저장
            self._settings.setValue("dataSheetVisible", self._toolbar.is_data_sheet_visible())
            # 모드 상태 저장
            self._settings.setValue("viewMode", self._toolbar.get_current_mode())
            self._settings.setValue("zoomLevel", self._toolbar.get_current_zoom())

            # 카테고리 필터 저장
            cat_index = self._toolbar.combo_category_filter.currentIndex()
            cat_id = self._toolbar.combo_category_filter.itemData(cat_index)
            if cat_id:
                self._settings.setValue("categoryFilter", cat_id)

            # 템플릿별 스크롤 위치 저장
            import json
            self._settings.setValue("templateScrollPositions", json.dumps(self._template_scroll_positions))

            event.accept()
        else:
            event.ignore()

    def _on_exit_requested(self):
        """종료 버튼 클릭"""
        self.close()

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

        # 엑셀 파일 경고 숨김
        self._toolbar.set_excel_warning_visible(False)

        # 템플릿 패널에 엑셀 헤더 및 파일 경로 전달 (호환성 유지)
        headers = self._excel_viewer._loader.get_headers() if self._excel_viewer._loader else []
        for panel in self._template_panels:
            panel.set_excel_headers(headers)
            if self._current_file:
                panel.set_excel_file_path(str(self._current_file))

        # EditorWidget에 엑셀 헤더 전달
        self._editor_widget.set_excel_headers(headers)

        # 첫 번째 행으로 미리보기 업데이트
        self._update_previews(0)

    def _on_preview_row_changed(self, row_index: int):
        """미리보기 행 변경"""
        self._update_previews(row_index)
        self.statusBar().showMessage(f"미리보기: {row_index + 1}행")

    def _update_previews(self, row_index: int):
        """모든 템플릿 패널 미리보기 업데이트"""
        row_data = self._excel_viewer.get_row_data(row_index)
        row_data_by_index = self._excel_viewer.get_row_data_by_index(row_index)
        if row_data:
            # 기존 TemplatePanel 업데이트 (호환성)
            for panel in self._template_panels:
                if panel.is_active:
                    panel.update_preview(row_data)

            # EditorWidget 미리보기 데이터 업데이트 (인덱스 기반 데이터 포함)
            self._editor_widget.set_preview_data(row_data, row_data_by_index)

    def _get_active_template_count(self) -> int:
        """활성화된 템플릿 개수 반환"""
        if not self._template_storage:
            return 0

        count = 0
        for template in self._template_storage.get_all_templates():
            is_active = True
            if template.metadata and hasattr(template.metadata, 'is_active'):
                is_active = template.metadata.is_active
            if is_active:
                count += 1
        return count

    def _on_selection_changed(self, selected_rows: list):
        """선택 변경"""
        count = len(selected_rows)
        # 활성화된 모든 템플릿 개수 사용
        total_templates = self._get_active_template_count()

        if count > 0 and total_templates > 0:
            total_files = count * total_templates
            self._toolbar.set_generate_enabled(True)
            self._toolbar.set_generate_text(f"문서 생성하기 ({count}행 × {total_templates}템플릿 = {total_files}개)")
        else:
            self._toolbar.set_generate_enabled(False)
            self._toolbar.set_generate_text("문서 생성하기")

    def _on_template_changed(self, template_name: str):
        """템플릿 변경"""
        # 선택 상태 업데이트
        self._on_selection_changed(self._excel_viewer.get_selected_rows())

        # 현재 미리보기 행으로 업데이트
        preview_row = self._excel_viewer.get_preview_row()
        self._update_previews(preview_row)

    def _get_active_template_names(self) -> List[str]:
        """활성화된 모든 템플릿 이름 목록 반환 (카테고리 순서)"""
        if not self._template_storage:
            return []

        active_templates = []
        for template in self._template_storage.get_all_templates():
            is_active = True
            if template.metadata and hasattr(template.metadata, 'is_active'):
                is_active = template.metadata.is_active
            if is_active:
                active_templates.append(template)

        sorted_templates = sorted(active_templates, key=self._get_template_sort_key)
        return [t.name for t in sorted_templates]

    def _on_export_clicked(self):
        """내보내기 버튼 클릭"""
        selected = self._excel_viewer.get_selected_rows()

        if not selected:
            self._logger.warning("내보내기 시도: 선택된 행 없음")
            QMessageBox.warning(self, "경고", "내보낼 행을 선택해주세요.")
            return

        # 활성화된 모든 템플릿 목록 가져오기
        template_names = self._get_active_template_names()

        if not template_names:
            self._logger.warning("내보내기 시도: 활성화된 템플릿 없음")
            QMessageBox.warning(self, "경고", "활성화된 템플릿이 없습니다.")
            return

        self._logger.info(f"내보내기 시작: {len(selected)}행, {len(template_names)}개 템플릿")

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
        rows_data_by_index = self._excel_viewer.get_selected_data_by_index()
        excel_headers = self._excel_viewer._loader.get_headers() if self._excel_viewer._loader else []

        # 내보내기 실행
        self._run_export(
            template_names=template_names,
            rows_data=rows_data,
            rows_data_by_index=rows_data_by_index,
            excel_headers=excel_headers,
            settings=settings,
        )

    def _run_export(
        self,
        template_names: List[str],
        rows_data: list,
        rows_data_by_index: list,
        excel_headers: list,
        settings: dict,
    ):
        """내보내기 실행"""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        self._is_exporting = True

        # UI 비활성화
        self._set_ui_enabled(False)

        # 오버레이 표시
        self._export_overlay.reset()
        self._export_overlay.setGeometry(self.centralWidget().rect())
        self._export_overlay.set_total(len(template_names) * len(rows_data))
        self._export_overlay.show()
        self._export_overlay.raise_()

        # ExportManager 생성
        self._export_manager = ExportManager(self._template_manager, self._work_dir)

        # 진행 콜백
        def on_progress(current: int, total: int, filename: str, row_data: dict):
            self._export_overlay.set_progress(current, total, filename)
            # 미리보기 업데이트 (현재 처리 중인 행)
            if row_data:
                row_data_by_index = {i: v for i, v in enumerate(row_data.values())}
                self._editor_widget.set_preview_data(row_data, row_data_by_index)
            QApplication.processEvents()

        # 내보내기 실행 (별도 타이머로 UI 업데이트 후 실행)
        def do_export():
            try:
                result_path = self._export_manager.export(
                    template_names=template_names,
                    rows_data=rows_data,
                    excel_headers=excel_headers,
                    output_format=settings["format"],
                    single_file=settings["single_file"],
                    filename_base=settings["filename"],
                    progress_callback=on_progress,
                    rows_data_by_index=rows_data_by_index,
                    group_by_template=settings.get("group_by_template", True),
                )

                if result_path:
                    self._on_export_complete(result_path, settings)
                else:
                    if self._export_manager._cancelled:
                        self._export_overlay.show_error("내보내기 취소됨")
                    else:
                        self._export_overlay.show_error("내보내기 실패")
                    self._is_exporting = False
                    # UI는 오버레이 닫기 버튼 클릭 시 활성화됨

            except Exception as e:
                self._logger.error(f"내보내기 오류: {e}")
                self._export_overlay.show_error(f"오류: {str(e)[:50]}")
                self._is_exporting = False
                # UI는 오버레이 닫기 버튼 클릭 시 활성화됨

        QTimer.singleShot(100, do_export)

    def _on_export_complete(self, result_path: Path, settings: dict):
        """내보내기 완료 처리"""
        self._export_overlay.show_completed()

        # 저장 위치 선택 다이얼로그
        if result_path.suffix == ".zip":
            filter_str = "ZIP 파일 (*.zip)"
            default_name = f"{settings['filename']}.zip"
        elif result_path.suffix == ".png":
            filter_str = "PNG 이미지 (*.png)"
            default_name = f"{settings['filename']}.png"
        else:
            filter_str = "PDF 파일 (*.pdf)"
            default_name = f"{settings['filename']}.pdf"

        # 마지막 저장 경로 불러오기
        last_export_dir = self._settings.value("last_export_dir", str(Path.home()))
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "내보내기 파일 저장",
            str(Path(last_export_dir) / default_name),
            filter_str,
        )

        if save_path:
            import shutil
            try:
                shutil.copy2(result_path, save_path)
                # 저장 경로 기억
                self._settings.setValue("last_export_dir", str(Path(save_path).parent))
                self._logger.info(f"파일 저장 완료: {save_path}")
                self.statusBar().showMessage(f"내보내기 완료: {save_path}")
                # 저장 완료 알림
                QMessageBox.information(self, "저장 완료", f"파일이 저장되었습니다.\n\n{save_path}")
            except Exception as e:
                self._logger.error(f"파일 저장 실패: {e}")
                QMessageBox.critical(self, "오류", f"파일 저장 실패:\n{e}")

        # 작업 파일 정리
        if self._export_manager:
            self._export_manager.cleanup_work_files()
            self._export_manager.cleanup()
            self._export_manager = None

        self._export_overlay.hide()
        self._is_exporting = False
        self._set_ui_enabled(True)

    def _on_export_cancel(self):
        """내보내기 취소"""
        if self._is_exporting and self._export_manager:
            self._export_manager.cancel()
            self._logger.info("내보내기 취소 요청")
        else:
            # 이미 완료/에러 상태면 오버레이 닫기
            self._export_overlay.hide()
            if self._export_manager:
                self._export_manager.cleanup_work_files()
                self._export_manager.cleanup()
                self._export_manager = None
            self._is_exporting = False
            self._set_ui_enabled(True)

    def _set_ui_enabled(self, enabled: bool):
        """UI 활성화/비활성화"""
        self._toolbar.setEnabled(enabled)
        self.menuBar().setEnabled(enabled)
        self._excel_viewer.setEnabled(enabled)
        self._editor_widget.setEnabled(enabled)

    def _on_select_all(self):
        """전체 선택"""
        self._excel_viewer.select_all()

    def _on_deselect_all(self):
        """선택 해제"""
        self._excel_viewer.deselect_all()

    def _on_usage(self):
        """사용 방법 다이얼로그"""
        dialog = HelpDialog(self)
        dialog.show_usage()

    def _on_about(self):
        """정보 다이얼로그"""
        dialog = HelpDialog(self)
        dialog.show_about()

    def _on_license(self):
        """라이센스 등록 다이얼로그"""
        dialog = LicenseDialog(self)
        dialog.exec()
