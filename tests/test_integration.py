"""통합 테스트"""

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
def integration_setup(tmp_path):
    """통합 테스트 환경 설정"""
    # 템플릿 디렉토리 생성
    templates_dir = tmp_path / "templates"
    rula_dir = templates_dir / "rula"
    rula_dir.mkdir(parents=True)

    (rula_dir / "rula.html").write_text("""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>RULA: Frame {{ frame }}</h1>
        <p>Score: {{ score }}</p>
    </body>
    </html>
    """)

    (rula_dir / "rula.mapping.json").write_text(json.dumps({
        "name": "RULA",
        "version": "1.0",
        "type": "html",
        "fields": [
            {"id": "frame", "label": "Frame", "excel_column": "Frame"},
            {"id": "score", "label": "Score", "excel_column": "Score"}
        ]
    }))

    # 테스트 엑셀 파일 경로
    fixtures_dir = Path(__file__).parent / "fixtures"
    sample_xlsx = fixtures_dir / "sample.xlsx"

    return {
        "templates_dir": templates_dir,
        "sample_xlsx": sample_xlsx,
        "output_dir": tmp_path / "output",
    }


class TestIntegration:
    """통합 테스트"""

    def test_excel_to_html_workflow(self, integration_setup):
        """Excel → HTML 워크플로우"""
        from src.core.excel_loader import ExcelLoader
        from src.core.template_manager import TemplateManager
        from src.core.document_generator import DocumentGenerator

        setup = integration_setup

        # 1. 엑셀 로드
        loader = ExcelLoader()
        loader.load(setup["sample_xlsx"])
        assert loader.row_count > 0

        # 2. 템플릿 매니저
        manager = TemplateManager(setup["templates_dir"])
        assert len(manager.get_all()) == 1

        # 3. 문서 생성
        generator = DocumentGenerator(manager)
        setup["output_dir"].mkdir(parents=True, exist_ok=True)

        rows = loader.get_all_rows()
        files = generator.batch_generate_html(
            template_name="RULA",
            rows_data=rows,
            output_dir=setup["output_dir"],
            excel_headers=loader.get_headers(),
        )

        # 검증
        assert len(files) == loader.row_count
        assert all(f.exists() for f in files)

        # 내용 확인
        content = files[0].read_text()
        assert "RULA" in content

    def test_main_window_with_templates(self, qapp, integration_setup):
        """메인 윈도우 템플릿 로드"""
        from src.ui.main_window import MainWindow

        setup = integration_setup
        window = MainWindow(templates_dir=setup["templates_dir"])

        assert window._template_manager is not None
        assert len(window._template_panels) >= 1

        window.close()

    def test_excel_viewer_selection_flow(self, qapp, integration_setup):
        """ExcelViewer 선택 흐름"""
        from src.ui.excel_viewer import ExcelViewer

        setup = integration_setup
        viewer = ExcelViewer()
        viewer.load_file(setup["sample_xlsx"])

        # 초기 상태
        assert viewer.row_count > 0
        assert len(viewer.get_selected_rows()) == 0

        # 전체 선택
        viewer.select_all()
        assert len(viewer.get_selected_rows()) == viewer.row_count

        # 선택 해제
        viewer.deselect_all()
        assert len(viewer.get_selected_rows()) == 0

        viewer.close()

    def test_end_to_end_export(self, qapp, integration_setup):
        """E2E 내보내기 테스트"""
        from src.core.excel_loader import ExcelLoader
        from src.core.template_manager import TemplateManager
        from src.core.document_generator import DocumentGenerator

        setup = integration_setup

        # 엑셀 로드
        loader = ExcelLoader()
        loader.load(setup["sample_xlsx"])

        # 행 선택 (전체)
        all_rows = loader.get_all_rows()
        selected_indices = list(range(len(all_rows)))

        # 템플릿 선택
        manager = TemplateManager(setup["templates_dir"])
        template_names = manager.template_names

        # 내보내기
        generator = DocumentGenerator(manager)
        output_dir = setup["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)

        files = generator.batch_generate_all(
            template_names=template_names,
            rows_data=all_rows,
            output_dir=output_dir,
            structure="by_template",
            excel_headers=loader.get_headers(),
        )

        # 검증
        expected_count = len(all_rows) * len(template_names)
        assert len(files) == expected_count
