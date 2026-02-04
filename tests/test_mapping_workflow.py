"""TT7: 매핑 워크플로우 통합 테스트

위지윅 매핑 워크플로우를 테스트합니다.
"""

import pytest
from unittest.mock import MagicMock

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtWidgets import QApplication

from src.ui.template_editor.mapping_overlay import (
    MappingOverlay,
    extract_placeholders_from_html,
    get_placeholder_positions,
)
from src.ui.template_editor.field_picker import FieldPicker, FieldListWidget
from src.ui.template_editor.editor_widget import EditorWidget


@pytest.fixture(scope="module")
def app():
    """QApplication 인스턴스"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_fields():
    """샘플 필드 목록"""
    return [
        {"id": "title", "label": "제목", "excel_column": "Title"},
        {"id": "author", "label": "작성자", "excel_column": "Author"},
        {"id": "date", "label": "날짜", "excel_column": "Date"},
        {"id": "content", "label": "내용", "excel_column": "Content"},
        {"id": "score", "label": "점수", "excel_column": "Score"},
    ]


@pytest.fixture
def sample_html():
    """샘플 HTML"""
    return """<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ title }}</h1>
    <p>작성자: {{ author }}</p>
    <p>날짜: {{ date }}</p>
    <div>{{ content }}</div>
</body>
</html>"""


class TestPlaceholderExtraction:
    """플레이스홀더 추출 테스트"""

    def test_extract_all_placeholders(self, sample_html):
        """HTML에서 모든 플레이스홀더 추출"""
        placeholders = extract_placeholders_from_html(sample_html)

        assert "title" in placeholders
        assert "author" in placeholders
        assert "date" in placeholders
        assert "content" in placeholders

    def test_extract_unique_placeholders(self, sample_html):
        """중복 플레이스홀더 제거"""
        placeholders = extract_placeholders_from_html(sample_html)

        # title이 두 번 사용되지만 한 번만 추출
        assert placeholders.count("title") == 1

    def test_get_positions(self, sample_html):
        """플레이스홀더 위치 정보 추출"""
        positions = get_placeholder_positions(sample_html)

        # 첫 번째 title
        first_title = positions[0]
        assert first_title[0] == "title"
        assert isinstance(first_title[1], int)  # start
        assert isinstance(first_title[2], int)  # end


class TestFieldListWidget:
    """FieldListWidget 테스트"""

    def test_set_fields(self, app, sample_fields):
        """필드 목록 설정"""
        widget = FieldListWidget()
        widget.set_fields(sample_fields)

        assert widget._list.count() == len(sample_fields)

    def test_set_mapped_fields(self, app, sample_fields):
        """매핑된 필드 설정"""
        widget = FieldListWidget()
        widget.set_fields(sample_fields)

        mapped_ids = {"title", "author"}
        widget.set_mapped_fields(mapped_ids)

        # 통계 확인
        assert "2/5" in widget._stats_label.text()

    def test_field_selected_signal(self, app, sample_fields):
        """필드 선택 시그널"""
        widget = FieldListWidget()
        widget.set_fields(sample_fields)

        mock = MagicMock()
        widget.field_selected.connect(mock)

        # 첫 번째 아이템 클릭 시뮬레이션
        item = widget._list.item(0)
        widget._list.setCurrentItem(item)
        widget._on_item_clicked(item)

        mock.assert_called_once()

    def test_search_filter(self, app, sample_fields):
        """검색 필터"""
        widget = FieldListWidget()
        widget.set_fields(sample_fields)

        # 검색어 입력
        widget._search_edit.setText("작성")

        # 필터링 결과
        visible_count = widget._list.count()
        assert visible_count == 1  # "작성자"만 표시


class TestMappingOverlayWorkflow:
    """MappingOverlay 워크플로우 테스트"""

    def test_set_placeholders_from_html(self, app, sample_html):
        """HTML에서 플레이스홀더 설정"""
        overlay = MappingOverlay()

        # HTML에서 플레이스홀더 추출 후 설정
        placeholder_ids = extract_placeholders_from_html(sample_html)
        placeholders = [
            {"id": pid, "label": pid, "rect": QRect(0, i * 30, 100, 25)}
            for i, pid in enumerate(placeholder_ids)
        ]
        overlay.set_placeholders(placeholders)

        assert len(overlay.get_all_placeholders()) == len(placeholder_ids)

    def test_highlight_toggle(self, app):
        """하이라이트 토글"""
        overlay = MappingOverlay()
        placeholders = [{"id": "test", "rect": QRect(0, 0, 100, 25)}]
        overlay.set_placeholders(placeholders)

        # 하이라이트 끄기
        overlay.set_show_highlights(False)
        assert overlay._show_highlights is False

        # 하이라이트 켜기
        overlay.set_show_highlights(True)
        assert overlay._show_highlights is True


class TestFieldPickerWorkflow:
    """FieldPicker 워크플로우 테스트"""

    def test_field_selection(self, app, sample_fields):
        """필드 선택"""
        picker = FieldPicker(sample_fields, QPoint(100, 100))

        # 필드 선택 시그널 연결
        mock = MagicMock()
        picker.field_selected.connect(mock)

        # 첫 번째 필드 선택 및 삽입
        picker._field_list.setCurrentRow(0)
        picker._on_insert()

        mock.assert_called_once()
        args = mock.call_args[0]
        assert args[0] == "title"  # field_id
        assert args[1] == "제목"  # field_label

    def test_search_filter_in_picker(self, app, sample_fields):
        """FieldPicker 검색 필터"""
        picker = FieldPicker(sample_fields, QPoint(100, 100))

        # 검색
        picker._search_edit.setText("날짜")

        # 필터링된 목록
        assert picker._field_list.count() == 1


class TestMappingModeIntegration:
    """매핑 모드 통합 테스트"""

    def test_enter_mapping_mode(self, app):
        """매핑 모드 진입"""
        editor = EditorWidget()
        editor.set_template(
            "test",
            None,
            "<html><body>{{ title }}</body></html>",
        )

        # 매핑 모드로 전환
        editor.set_mode(EditorWidget.MODE_MAPPING)

        assert editor.get_current_mode() == EditorWidget.MODE_MAPPING

    def test_mapping_mode_preserves_content(self, app):
        """매핑 모드에서 내용 보존"""
        editor = EditorWidget()
        html = "<html><body>{{ title }} - {{ content }}</body></html>"
        editor.set_template("test", None, html)

        # 편집
        new_html = "<html><body>{{ header }} - {{ body }}</body></html>"
        editor._html_editor.setPlainText(new_html)

        # 매핑 모드로 전환
        editor.set_mode(EditorWidget.MODE_MAPPING)

        # 편집 모드로 복귀
        editor.set_mode(EditorWidget.MODE_EDIT)

        # 내용 유지
        assert "{{ header }}" in editor.get_html_content()
        assert "{{ body }}" in editor.get_html_content()


class TestMappingWorkflowScenarios:
    """매핑 워크플로우 시나리오 테스트"""

    def test_scenario_add_new_placeholder(self, app, sample_fields):
        """시나리오: 새 플레이스홀더 추가"""
        # 1. 초기 HTML
        html = "<html><body>Hello World</body></html>"

        # 2. 기존 플레이스홀더 없음
        placeholders = extract_placeholders_from_html(html)
        assert len(placeholders) == 0

        # 3. 필드 선택 (시뮬레이션)
        selected_field = sample_fields[0]  # title

        # 4. 플레이스홀더 삽입
        insertion_point = html.find("Hello")
        new_html = html[:insertion_point] + "{{ title }}" + html[insertion_point:]

        # 5. 업데이트된 플레이스홀더 확인
        new_placeholders = extract_placeholders_from_html(new_html)
        assert "title" in new_placeholders

    def test_scenario_replace_placeholder(self, app, sample_fields):
        """시나리오: 플레이스홀더 교체"""
        # 1. 초기 HTML
        html = "<html><body>{{ old_field }}</body></html>"

        # 2. 기존 플레이스홀더
        old_placeholders = extract_placeholders_from_html(html)
        assert "old_field" in old_placeholders

        # 3. 플레이스홀더 교체
        new_html = html.replace("{{ old_field }}", "{{ title }}")

        # 4. 업데이트된 플레이스홀더
        new_placeholders = extract_placeholders_from_html(new_html)
        assert "old_field" not in new_placeholders
        assert "title" in new_placeholders

    def test_scenario_multiple_fields_mapping(self, app, sample_fields):
        """시나리오: 여러 필드 매핑"""
        # 1. 빈 템플릿
        html = """<html>
<body>
    <h1>[TITLE]</h1>
    <p>By [AUTHOR] on [DATE]</p>
    <div>[CONTENT]</div>
</body>
</html>"""

        # 2. 순차적으로 플레이스홀더 삽입
        html = html.replace("[TITLE]", "{{ title }}")
        html = html.replace("[AUTHOR]", "{{ author }}")
        html = html.replace("[DATE]", "{{ date }}")
        html = html.replace("[CONTENT]", "{{ content }}")

        # 3. 모든 플레이스홀더 확인
        placeholders = extract_placeholders_from_html(html)
        assert set(placeholders) == {"title", "author", "date", "content"}

    def test_scenario_verify_mapped_fields(self, app, sample_fields):
        """시나리오: 매핑된 필드 확인"""
        # 1. HTML
        html = "<html>{{ title }} {{ author }} {{ date }}</html>"

        # 2. 사용된 플레이스홀더 추출
        used_placeholders = set(extract_placeholders_from_html(html))

        # 3. 전체 필드와 비교
        all_field_ids = {f["id"] for f in sample_fields}

        # 4. 매핑된/미매핑된 필드 분류
        mapped = used_placeholders & all_field_ids
        unmapped = all_field_ids - used_placeholders

        assert mapped == {"title", "author", "date"}
        assert unmapped == {"content", "score"}


class TestFieldListMappingStatus:
    """필드 목록 매핑 상태 테스트"""

    def test_mapping_status_updates(self, app, sample_fields):
        """매핑 상태 업데이트"""
        widget = FieldListWidget()
        widget.set_fields(sample_fields)

        # 초기: 매핑 없음
        widget.set_mapped_fields(set())
        assert "0/5" in widget._stats_label.text()

        # 일부 매핑
        widget.set_mapped_fields({"title", "author"})
        assert "2/5" in widget._stats_label.text()

        # 전체 매핑
        widget.set_mapped_fields({"title", "author", "date", "content", "score"})
        assert "5/5" in widget._stats_label.text()
