"""TemplatePanel UI 테스트"""

import json
import pytest
from pathlib import Path
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """PyQt6 애플리케이션 인스턴스"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def test_templates_dir(tmp_path):
    """테스트용 템플릿 디렉토리"""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # RULA 템플릿
    rula_dir = templates_dir / "rula"
    rula_dir.mkdir()
    (rula_dir / "rula.html").write_text("""
    <html>
    <body>
        <h1>RULA Assessment</h1>
        <p>Upper Arm: {{ upper_arm }}</p>
        <p>Score: {{ score }}</p>
    </body>
    </html>
    """)
    (rula_dir / "rula.mapping.json").write_text(json.dumps({
        "name": "RULA",
        "version": "1.0",
        "type": "html",
        "fields": [
            {"id": "upper_arm", "label": "Upper Arm", "excel_column": "Upper Arm"},
            {"id": "score", "label": "Score", "excel_column": "Score"}
        ]
    }))

    # REBA 템플릿
    reba_dir = templates_dir / "reba"
    reba_dir.mkdir()
    (reba_dir / "reba.html").write_text("<html><body>REBA</body></html>")
    (reba_dir / "reba.mapping.json").write_text(json.dumps({
        "name": "REBA",
        "version": "1.0",
        "type": "html",
        "fields": []
    }))

    return templates_dir


@pytest.fixture
def template_panel(qapp, test_templates_dir):
    """TemplatePanel 인스턴스"""
    from src.ui.template_panel import TemplatePanel
    from src.core.template_manager import TemplateManager

    manager = TemplateManager(test_templates_dir)
    panel = TemplatePanel(manager)
    yield panel
    panel.close()


class TestTemplatePanel:
    """TemplatePanel UI 테스트"""

    def test_widget_creation(self, template_panel):
        """위젯 생성"""
        assert template_panel is not None

    def test_template_dropdown_exists(self, template_panel):
        """템플릿 선택 드롭다운 존재"""
        from PyQt6.QtWidgets import QComboBox

        assert hasattr(template_panel, "_template_combo")
        assert isinstance(template_panel._template_combo, QComboBox)

    def test_template_dropdown_has_items(self, template_panel):
        """드롭다운에 템플릿 목록"""
        combo = template_panel._template_combo
        assert combo.count() >= 2  # RULA, REBA

    def test_preview_area_exists(self, template_panel):
        """프리뷰 영역 존재"""
        assert hasattr(template_panel, "_preview_widget")
        assert template_panel._preview_widget is not None

    def test_close_button_exists(self, template_panel):
        """닫기 버튼 존재"""
        assert hasattr(template_panel, "_close_button")

    def test_select_template(self, template_panel):
        """템플릿 선택"""
        template_panel.set_template("RULA")
        assert template_panel.current_template_name == "RULA"

    def test_template_changed_signal(self, template_panel, qtbot):
        """템플릿 변경 시그널"""
        with qtbot.waitSignal(template_panel.template_changed, timeout=1000):
            template_panel.set_template("REBA")

    def test_update_preview_with_data(self, template_panel):
        """데이터로 프리뷰 업데이트"""
        data = {"upper_arm": 3, "score": 5}
        template_panel.set_template("RULA")
        template_panel.update_preview(data)
        # 에러 없이 실행되면 성공

    def test_close_requested_signal(self, template_panel, qtbot):
        """닫기 요청 시그널"""
        with qtbot.waitSignal(template_panel.close_requested, timeout=1000):
            template_panel._close_button.click()

    def test_is_active_property(self, template_panel):
        """활성 상태 속성"""
        template_panel.set_template("RULA")
        assert template_panel.is_active

    def test_get_template(self, template_panel):
        """현재 템플릿 가져오기"""
        template_panel.set_template("RULA")
        template = template_panel.get_template()
        assert template is not None
        assert template.name == "RULA"
