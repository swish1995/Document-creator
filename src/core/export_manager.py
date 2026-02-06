"""내보내기 관리자 모듈

전체 내보내기 프로세스를 관리합니다.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import fitz  # PyMuPDF

from jinja2 import Template as Jinja2Template

from src.core.template_manager import TemplateManager
from src.core.mapper import Mapper
from src.core.pdf_converter import PdfConverter
from src.core.logger import get_logger


class ExportManager:
    """내보내기 관리자

    템플릿과 데이터를 결합하여 PDF/PNG 파일을 생성하고
    ZIP 아카이브 또는 단일 파일로 제공합니다.
    """

    def __init__(self, template_manager: TemplateManager, work_dir: Path):
        """
        Args:
            template_manager: 템플릿 매니저
            work_dir: 작업 디렉토리 (임시 파일 저장용)
        """
        self._template_manager = template_manager
        self._work_dir = work_dir
        self._logger = get_logger("export_manager")
        self._cancelled = False
        self._pdf_converter: Optional[PdfConverter] = None

    @staticmethod
    def cleanup_work_dir(work_dir: Path):
        """작업 디렉토리 정리 (프로그램 시작 시 호출)"""
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

    def _ensure_work_dir(self):
        """작업 디렉토리 생성"""
        self._work_dir.mkdir(parents=True, exist_ok=True)

    def _get_pdf_converter(self) -> PdfConverter:
        """PDF 변환기 반환 (지연 생성)"""
        if self._pdf_converter is None:
            self._pdf_converter = PdfConverter()
        return self._pdf_converter

    def cancel(self):
        """내보내기 취소"""
        self._cancelled = True

    def reset(self):
        """취소 상태 초기화"""
        self._cancelled = False

    def export(
        self,
        template_names: List[str],
        rows_data: List[Dict[str, Any]],
        excel_headers: Optional[List[str]],
        output_format: str,  # "pdf" or "png"
        single_file: bool,
        filename_base: str,
        progress_callback: Optional[Callable[[int, int, str, Dict[str, Any]], None]] = None,
        rows_data_by_index: Optional[List[List[Any]]] = None,
        group_by_template: bool = True,
    ) -> Optional[Path]:
        """내보내기 실행

        Args:
            template_names: 템플릿 이름 목록
            rows_data: 행 데이터 목록 (헤더명 기반)
            excel_headers: 엑셀 헤더
            output_format: 출력 형식 ("pdf" 또는 "png")
            single_file: PDF 통합 여부
            filename_base: 기본 파일명
            progress_callback: 진행 콜백 (current, total, filename, row_data)
            rows_data_by_index: 인덱스 기반 행 데이터 (중복 헤더 지원)
            group_by_template: True면 템플릿별, False면 행별 순서

        Returns:
            최종 출력 파일 경로 (ZIP 또는 단일 파일)
        """
        self.reset()
        self._ensure_work_dir()

        total = len(template_names) * len(rows_data)
        current = 0
        generated_files: List[Path] = []

        self._logger.info(f"내보내기 시작: {len(template_names)}개 템플릿 × {len(rows_data)}행, 순서: {'템플릿별' if group_by_template else '행별'}")

        # 1. 각 템플릿 × 행 조합에 대해 PDF 생성
        # 순서: group_by_template=True면 템플릿별, False면 행별
        if group_by_template:
            # 템플릿별: 템플릿1의 모든 행 → 템플릿2의 모든 행 → ...
            iterations = [(t, r, row) for t in template_names for r, row in enumerate(rows_data)]
        else:
            # 행별: 행1의 모든 템플릿 → 행2의 모든 템플릿 → ...
            iterations = [(t, r, row) for r, row in enumerate(rows_data) for t in template_names]

        for template_name, row_idx, row_data in iterations:
            if self._cancelled:
                break

            template = self._template_manager.get(template_name)
            if template is None:
                self._logger.error(f"템플릿 없음: {template_name}")
                continue

            current += 1
            filename = f"{filename_base}_{template_name}_{row_idx + 1:03d}"

            if progress_callback:
                progress_callback(current, total, f"{filename}.pdf", row_data)

            # 매핑 적용
            row_by_index = rows_data_by_index[row_idx] if rows_data_by_index else None
            if excel_headers:
                mapper = Mapper(template.fields, excel_headers)
                mapped_data = mapper.apply(row_data, row_by_index)
            else:
                mapped_data = self._direct_map(template.fields, row_data, row_by_index)

            # HTML 렌더링
            html_content = self._render_html(template.template_path, mapped_data)

            # HTML → PDF 변환
            pdf_path = self._work_dir / f"{filename}.pdf"
            converter = self._get_pdf_converter()
            success = converter.convert_html_string_to_pdf(
                html_content=html_content,
                output_path=pdf_path,
                base_url=template.template_path.parent,
            )

            if success:
                generated_files.append(pdf_path)
                self._logger.debug(f"PDF 생성: {pdf_path}")
            else:
                self._logger.error(f"PDF 변환 실패: {filename}")

        if self._cancelled:
            self._logger.info("내보내기 취소됨")
            return None

        if not generated_files:
            self._logger.error("생성된 파일 없음")
            return None

        # 2. PNG 변환 (필요한 경우)
        if output_format == "png":
            png_files = []
            for pdf_path in generated_files:
                png_path = pdf_path.with_suffix(".png")
                if self._convert_pdf_to_png(pdf_path, png_path):
                    png_files.append(png_path)
            generated_files = png_files

        # 3. PDF 통합 (필요한 경우)
        if output_format == "pdf" and single_file and len(generated_files) > 1:
            merged_path = self._work_dir / f"{filename_base}.pdf"
            if self._merge_pdfs(generated_files, merged_path):
                generated_files = [merged_path]

        # 4. 최종 출력 파일 결정
        if len(generated_files) == 1:
            # 단일 파일: 그대로 반환
            return generated_files[0]
        else:
            # 여러 파일: ZIP 아카이브
            zip_path = self._work_dir / f"{filename_base}.zip"
            return self._create_zip(generated_files, zip_path)

    def _direct_map(self, fields: List[Dict], row_data: Dict[str, Any], row_by_index: List[Any] = None) -> Dict[str, Any]:
        """직접 매핑 (헤더 없을 때)"""
        import base64

        mapped_data = {}
        for field in fields:
            field_id = field["id"]
            excel_col = field.get("excel_column", "")
            excel_index = field.get("excel_index")
            field_type = field.get("type", "text")

            # 인덱스 기반 데이터 우선 사용
            if row_by_index is not None and excel_index is not None:
                if 0 <= excel_index < len(row_by_index):
                    value = row_by_index[excel_index]
                else:
                    value = None
            else:
                value = row_data.get(excel_col)

            # 이미지 타입인 경우 img 태그로 변환
            if field_type == "image" and value is not None:
                value = self._convert_image_to_img_tag(value)

            mapped_data[field_id] = value
        return mapped_data

    def _convert_image_to_img_tag(self, image_path) -> str:
        """이미지 경로를 완전한 img 태그로 변환"""
        data_url = self._convert_image_to_data_url(image_path)
        if data_url:
            return f'<img src="{data_url}" style="width:100%;height:100%;object-fit:contain;">'
        return ""

    def _convert_image_to_data_url(self, image_path) -> str:
        """이미지 경로를 Base64 data URL로 변환"""
        import base64

        try:
            path = Path(image_path) if not isinstance(image_path, Path) else image_path
            if not path.exists():
                return ""

            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")

            suffix = path.suffix.lower()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
            }
            mime_type = mime_types.get(suffix, "image/png")

            return f"data:{mime_type};base64,{data}"
        except Exception:
            return ""

    def _render_html(self, template_path: Path, data: Dict[str, Any]) -> str:
        """HTML 템플릿 렌더링"""
        with open(template_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        jinja_template = Jinja2Template(html_template)
        return jinja_template.render(**data)

    def _convert_pdf_to_png(self, pdf_path: Path, png_path: Path, dpi: int = 300) -> bool:
        """PDF를 PNG로 변환

        Args:
            pdf_path: 입력 PDF 경로
            png_path: 출력 PNG 경로
            dpi: 해상도 (기본 300 DPI, 고품질)

        Returns:
            변환 성공 여부
        """
        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                self._logger.error(f"빈 PDF: {pdf_path}")
                return False

            page = doc[0]
            # DPI를 줌 팩터로 변환 (72 DPI 기준)
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            # alpha=False로 투명 배경 제거, colorspace로 RGB 명시
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(str(png_path))
            doc.close()

            self._logger.debug(f"PNG 변환: {png_path}")
            return True
        except Exception as e:
            self._logger.error(f"PNG 변환 실패: {e}")
            return False

    def _merge_pdfs(self, pdf_paths: List[Path], output_path: Path) -> bool:
        """여러 PDF를 하나로 병합

        Args:
            pdf_paths: 입력 PDF 경로 목록
            output_path: 출력 PDF 경로

        Returns:
            병합 성공 여부
        """
        try:
            merged = fitz.open()
            for pdf_path in pdf_paths:
                doc = fitz.open(pdf_path)
                merged.insert_pdf(doc)
                doc.close()
            # PDF 최적화: 가비지 정리, 압축, 정리
            merged.save(str(output_path), garbage=4, deflate=True, clean=True)
            merged.close()

            self._logger.debug(f"PDF 병합: {output_path}")
            return True
        except Exception as e:
            self._logger.error(f"PDF 병합 실패: {e}")
            return False

    def _create_zip(self, files: List[Path], output_path: Path) -> Optional[Path]:
        """ZIP 아카이브 생성

        Args:
            files: 포함할 파일 목록
            output_path: 출력 ZIP 경로

        Returns:
            생성된 ZIP 경로
        """
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in files:
                    zf.write(file_path, file_path.name)

            self._logger.debug(f"ZIP 생성: {output_path}")
            return output_path
        except Exception as e:
            self._logger.error(f"ZIP 생성 실패: {e}")
            return None

    def cleanup(self):
        """리소스 정리"""
        if self._pdf_converter:
            self._pdf_converter.cleanup()
            self._pdf_converter = None

    def cleanup_work_files(self):
        """작업 파일 정리 (내보내기 완료 후)"""
        if self._work_dir.exists():
            shutil.rmtree(self._work_dir, ignore_errors=True)
            self._logger.debug(f"작업 디렉토리 정리: {self._work_dir}")
