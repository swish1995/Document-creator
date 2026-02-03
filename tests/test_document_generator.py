"""DocumentGenerator 단위 테스트"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def test_template_dir(tmp_path):
    """테스트용 템플릿"""
    template_dir = tmp_path / "templates" / "test"
    template_dir.mkdir(parents=True)

    (template_dir / "test.html").write_text("""
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
        <h1>Frame: {{ frame }}</h1>
        <p>Score: {{ score }}</p>
    </body>
    </html>
    """)

    (template_dir / "test.mapping.json").write_text(json.dumps({
        "name": "Test",
        "version": "1.0",
        "type": "html",
        "fields": [
            {"id": "frame", "label": "Frame", "excel_column": "Frame"},
            {"id": "score", "label": "Score", "excel_column": "Score"}
        ]
    }))

    return tmp_path / "templates"


@pytest.fixture
def document_generator(test_template_dir):
    """DocumentGenerator 인스턴스"""
    from src.core.document_generator import DocumentGenerator
    from src.core.template_manager import TemplateManager

    manager = TemplateManager(test_template_dir)
    return DocumentGenerator(manager)


@pytest.fixture
def sample_rows():
    """샘플 행 데이터"""
    return [
        {"Frame": 1, "Score": 5, "Time": "00:01.00"},
        {"Frame": 2, "Score": 6, "Time": "00:02.00"},
        {"Frame": 3, "Score": 4, "Time": "00:03.00"},
    ]


class TestDocumentGenerator:
    """DocumentGenerator 단위 테스트"""

    def test_generate_single_html(self, document_generator, sample_rows, tmp_path):
        """단일 HTML 생성"""
        output_path = tmp_path / "output.html"
        row_data = sample_rows[0]

        document_generator.generate_html(
            template_name="Test",
            row_data=row_data,
            output_path=output_path
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "Frame: 1" in content
        assert "Score: 5" in content

    def test_batch_generate_html(self, document_generator, sample_rows, tmp_path):
        """다중 행 HTML 일괄 생성"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        files = document_generator.batch_generate_html(
            template_name="Test",
            rows_data=sample_rows,
            output_dir=output_dir,
            filename_pattern="{template}_{row:03d}.html"
        )

        assert len(files) == 3
        assert all(f.exists() for f in files)

    def test_batch_generate_multiple_templates(self, document_generator, sample_rows, tmp_path):
        """다중 템플릿 일괄 생성"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Test 템플릿만 있음
        files = document_generator.batch_generate_all(
            template_names=["Test"],
            rows_data=sample_rows,
            output_dir=output_dir
        )

        assert len(files) == 3  # 3 rows × 1 template

    def test_filename_pattern(self, document_generator, sample_rows, tmp_path):
        """파일명 패턴 적용"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        files = document_generator.batch_generate_html(
            template_name="Test",
            rows_data=sample_rows,
            output_dir=output_dir,
            filename_pattern="{template}_row{row:03d}_f{frame}.html"
        )

        assert files[0].name == "Test_row001_f1.html"
        assert files[1].name == "Test_row002_f2.html"

    def test_output_structure_by_template(self, document_generator, sample_rows, tmp_path):
        """템플릿별 폴더 구조"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        files = document_generator.batch_generate_all(
            template_names=["Test"],
            rows_data=sample_rows,
            output_dir=output_dir,
            structure="by_template"
        )

        # Test/ 폴더 아래에 파일 생성
        assert all("Test" in str(f.parent.name) for f in files)

    def test_progress_callback(self, document_generator, sample_rows, tmp_path):
        """진행 상황 콜백"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        progress_values = []

        def callback(current, total, filename):
            progress_values.append((current, total))

        document_generator.batch_generate_html(
            template_name="Test",
            rows_data=sample_rows,
            output_dir=output_dir,
            progress_callback=callback
        )

        assert len(progress_values) == 3
        assert progress_values[-1] == (3, 3)

    def test_cancel_generation(self, document_generator, sample_rows, tmp_path):
        """생성 취소"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # 첫 번째 파일 후 취소
        call_count = [0]

        def callback(current, total, filename):
            call_count[0] += 1
            if call_count[0] >= 1:
                document_generator.cancel()

        files = document_generator.batch_generate_html(
            template_name="Test",
            rows_data=sample_rows,
            output_dir=output_dir,
            progress_callback=callback
        )

        # 취소되어 1개만 생성
        assert len(files) <= 2
