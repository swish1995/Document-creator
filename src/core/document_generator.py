"""문서 생성기 모듈

템플릿과 데이터를 결합하여 문서를 생성합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from jinja2 import Template as Jinja2Template

from src.core.template_manager import TemplateManager, Template
from src.core.mapper import Mapper


class DocumentGeneratorError(Exception):
    """문서 생성기 에러"""

    pass


class DocumentGenerator:
    """문서 생성기

    템플릿과 데이터를 결합하여 HTML/PDF/이미지 문서를 생성합니다.
    """

    def __init__(self, template_manager: TemplateManager):
        self._template_manager = template_manager
        self._cancelled = False

    def cancel(self):
        """생성 취소"""
        self._cancelled = True

    def reset(self):
        """취소 상태 초기화"""
        self._cancelled = False

    def generate_html(
        self,
        template_name: str,
        row_data: Dict[str, Any],
        output_path: Path,
        excel_headers: Optional[List[str]] = None,
    ) -> Path:
        """단일 HTML 문서 생성

        Args:
            template_name: 템플릿 이름
            row_data: 행 데이터
            output_path: 출력 파일 경로
            excel_headers: 엑셀 헤더 (매핑용)

        Returns:
            생성된 파일 경로
        """
        template = self._template_manager.get(template_name)
        if template is None:
            raise DocumentGeneratorError(f"템플릿을 찾을 수 없습니다: {template_name}")

        # 매핑 적용
        if excel_headers:
            mapper = Mapper(template.fields, excel_headers)
            mapped_data = mapper.apply(row_data)
        else:
            # 헤더가 없으면 직접 매핑 시도
            mapped_data = {}
            for field in template.fields:
                field_id = field["id"]
                excel_col = field.get("excel_column", "")
                mapped_data[field_id] = row_data.get(excel_col)

        # HTML 렌더링
        html_content = self._render_html(template, mapped_data)

        # 파일 저장
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        return output_path

    def _render_html(self, template: Template, data: Dict[str, Any]) -> str:
        """HTML 템플릿 렌더링"""
        with open(template.template_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        jinja_template = Jinja2Template(html_template)
        return jinja_template.render(**data)

    def batch_generate_html(
        self,
        template_name: str,
        rows_data: List[Dict[str, Any]],
        output_dir: Path,
        filename_pattern: str = "{template}_{row:03d}.html",
        excel_headers: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Path]:
        """다중 행 HTML 일괄 생성

        Args:
            template_name: 템플릿 이름
            rows_data: 행 데이터 목록
            output_dir: 출력 디렉토리
            filename_pattern: 파일명 패턴
            excel_headers: 엑셀 헤더
            progress_callback: 진행 콜백 (current, total, filename)

        Returns:
            생성된 파일 경로 목록
        """
        self.reset()
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []
        total = len(rows_data)

        for i, row_data in enumerate(rows_data):
            if self._cancelled:
                break

            # 파일명 생성
            filename = filename_pattern.format(
                template=template_name,
                row=i + 1,
                frame=row_data.get("Frame", i + 1),
            )
            output_path = output_dir / filename

            # HTML 생성
            self.generate_html(
                template_name=template_name,
                row_data=row_data,
                output_path=output_path,
                excel_headers=excel_headers,
            )

            generated_files.append(output_path)

            if progress_callback:
                progress_callback(i + 1, total, filename)

        return generated_files

    def batch_generate_all(
        self,
        template_names: List[str],
        rows_data: List[Dict[str, Any]],
        output_dir: Path,
        filename_pattern: str = "{template}_{row:03d}.html",
        structure: str = "flat",  # "flat", "by_template", "by_row"
        excel_headers: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Path]:
        """다중 템플릿 × 다중 행 일괄 생성

        Args:
            template_names: 템플릿 이름 목록
            rows_data: 행 데이터 목록
            output_dir: 출력 디렉토리
            filename_pattern: 파일명 패턴
            structure: 폴더 구조 ("flat", "by_template", "by_row")
            excel_headers: 엑셀 헤더
            progress_callback: 진행 콜백

        Returns:
            생성된 파일 경로 목록
        """
        self.reset()
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []
        total = len(template_names) * len(rows_data)
        current = 0

        for template_name in template_names:
            if self._cancelled:
                break

            for i, row_data in enumerate(rows_data):
                if self._cancelled:
                    break

                current += 1

                # 출력 경로 결정
                if structure == "by_template":
                    sub_dir = output_dir / template_name
                elif structure == "by_row":
                    sub_dir = output_dir / f"row_{i + 1:03d}"
                else:
                    sub_dir = output_dir

                sub_dir.mkdir(parents=True, exist_ok=True)

                # 파일명 생성
                filename = filename_pattern.format(
                    template=template_name,
                    row=i + 1,
                    frame=row_data.get("Frame", i + 1),
                )
                output_path = sub_dir / filename

                # HTML 생성
                self.generate_html(
                    template_name=template_name,
                    row_data=row_data,
                    output_path=output_path,
                    excel_headers=excel_headers,
                )

                generated_files.append(output_path)

                if progress_callback:
                    progress_callback(current, total, filename)

        return generated_files
