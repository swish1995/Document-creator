# 테이블 셀 하이라이트 구현 방식

## 배경

RULA/REBA/OWAS 템플릿의 하단 평가 테이블에서, 매핑된 점수 데이터에 해당하는 교차 셀을 자동으로 하이라이트하는 기능.

## 문제

`editor_widget.py`의 미리보기 모드와 PDF 내보내기의 렌더링 방식이 다르다.

| 컨텍스트 | 렌더링 방식 | `{{field_id}}` 처리 |
|---|---|---|
| **editor_widget 미리보기** | regex 변환 + JS 데이터 바인딩 | `<span class="data-field" data-field="field_id">` 로 변환 |
| **PDF 내보내기** | Jinja2 직접 렌더링 | 실제 값으로 치환 (예: `2`) |

### editor_widget의 regex

```python
pattern = r'\{\{\s*(\w+)\s*\}\}'
```

- `{{upper_arm_score}}` → 매치됨 (변환됨)
- `{{ ns.a_row }}` → 매치 안됨 (`.`이 `\w`에 포함되지 않음)
- `{% set ... %}` → 매치 안됨 (`{% %}` 구문)

## 해결: 이중 접근법

### 1. Jinja2 `<style>` (PDF 내보내기용)

`<head>`에 Jinja2 템플릿 로직으로 CSS `nth-child` 규칙을 생성한다.

```html
<style>
{% set ns = namespace() %}
{% set ns.v = trunk_score|default(0,true)|int + trunk_adjust|default(0,true)|int %}
{% if ns.v < 1 %}{% set ns.v = 1 %}{% elif ns.v > 5 %}{% set ns.v = 5 %}{% endif %}
...
#table-a tbody tr:nth-child({{ ns.row }}) td:nth-child({{ ns.col }}) {
    background-color: #fdba74 !important;
}
</style>
```

- `{{ ns.variable }}` (점 포함) → editor_widget의 regex에 매치되지 않아 안전
- `{% %}` 블록 → regex에 매치되지 않음
- editor_widget에서는 무효한 CSS로 무시됨
- PDF 내보내기에서는 Jinja2가 처리하여 유효한 CSS 규칙 생성

### 2. JavaScript `setTimeout` (editor_widget 미리보기용)

`</body>` 앞에 스크립트를 추가하여, 데이터 바인딩 완료 후 셀을 하이라이트한다.

```html
<script>
setTimeout(function() {
    function getVal(id) {
        var el = document.querySelector('.data-field[data-field="' + id + '"]');
        return (el && el.textContent.trim()) ? parseInt(el.textContent) : NaN;
    }
    // ... 값 읽기 → 셀 인덱스 계산 → 인라인 스타일 적용
}, 50);
</script>
```

- `setTimeout(fn, 50)` → editor_widget이 주입하는 데이터 바인딩 스크립트보다 나중에 실행
- `data-field` span에서 값을 읽어 테이블 셀 인덱스 계산
- PDF 내보내기에서는 `data-field` span이 없어 NaN → 하이라이트 스킵 (CSS가 담당)

## 요약

```
[editor_widget 미리보기]
  Jinja2 <style> → 무효 CSS (무시됨)
  JS setTimeout  → data-field에서 값 읽기 → 인라인 스타일 적용 ✅

[PDF 내보내기]
  Jinja2 <style> → 유효 CSS nth-child 규칙 생성 ✅
  JS setTimeout  → data-field 없음 → NaN → 스킵
```
