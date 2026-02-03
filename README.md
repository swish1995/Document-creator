# Document Creator

> Skeleton Analyzer 출력 데이터를 인체공학적 평가 문서로 변환하는 도구

## 개요

**Document Creator**는 [Skeleton Analyzer](../skeleton-analyzer)에서 생성된 엑셀 데이터를 RULA, REBA, OWAS 등의 인체공학적 평가 템플릿에 매핑하여 문서를 생성하는 데스크톱 애플리케이션입니다.

## 주요 기능

### 데이터 입력
- Skeleton Analyzer에서 내보낸 Excel 파일(`.xlsx`) 열기
- 첫 번째 시트(`Capture Data`)의 데이터 로드
- 엑셀 데이터 미리보기 및 행 선택

### 템플릿 관리
- 복수의 템플릿 형식 지원
  - **HTML 템플릿**: HTML + JSON 매핑 정의
  - **이미지 템플릿**: 이미지(PNG/JPG) + JSON 매핑 정의
- 템플릿 미리보기 및 선택
- 사용자 정의 템플릿 추가 가능

### 지원 평가 양식
| 평가 방법 | 설명 |
|----------|------|
| **RULA** | Rapid Upper Limb Assessment - 상지 중심 평가 |
| **REBA** | Rapid Entire Body Assessment - 전신 평가 |
| **OWAS** | Ovako Working Posture Analysis System - 작업 자세 분석 |
| **NLE** | NIOSH Lifting Equation - 들기 작업 위험도 평가 (RWL/LI 산출) |
| **SI** | Strain Index - 상지 반복 작업 위험도 평가 |

### 매핑 및 미리보기
- 엑셀 첫 행(헤더)과 템플릿 필드 자동/수동 매핑
- 매핑 결과 실시간 프리뷰
- 한 줄(엑셀 행)을 복수 템플릿에 동시 매핑

### 문서 생성
- 선택한 행 데이터를 템플릿에 적용
- PDF, 이미지 등 다양한 출력 형식 지원 (예정)

## 화면 구성

```
┌─────────────────────────────────────────────────────────────────────┐
│                              상단 영역                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 템플릿 1  │ │ 템플릿 2  │ │ 템플릿 3  │ │ 템플릿 4  │ │ 템플릿 5  │  │
│  │  (RULA)  │ │  (REBA)  │ │  (OWAS)  │ │   [+]    │ │   [+]    │  │
│  │          │ │          │ │          │ │          │ │          │  │
│  │ 프리뷰   │ │ 프리뷰   │ │ 프리뷰   │ │          │ │          │  │
│  │ 영역     │ │ 영역     │ │ 영역     │ │          │ │          │  │
│  │          │ │          │ │          │ │          │ │          │  │
│  │    [x]   │ │    [x]   │ │    [x]   │ │          │ │          │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                              하단 영역                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  [엑셀 열기]                                                 │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  # │ Time     │ Frame │ Upper Arm │ Lower Arm │ Wrist │ ...│   │
│  │  1 │ 00:01.83 │  44   │     5     │     2     │   2   │    │   │
│  │  2 │ 00:02.54 │  61   │     4     │     2     │   2   │    │   │
│  │  3 │ 00:03.12 │  75   │     4     │     1     │   2   │    │   │
│  │ ...│   ...    │  ...  │    ...    │    ...    │  ...  │    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 상단 영역 - 템플릿 패널
- 최대 **5개**의 템플릿 패널을 가로로 배치
- 각 패널에서 템플릿 선택 및 프리뷰 표시
- 패널 추가(`[+]`) 및 삭제(`[x]`) 가능
- 선택한 엑셀 행의 데이터가 각 템플릿에 매핑되어 표시

### 하단 영역 - 엑셀 데이터 뷰어
- 엑셀 파일 열기 버튼
- 첫 번째 시트의 데이터만 테이블 형태로 표시
- 행 선택 시 상단 템플릿에 데이터 자동 매핑

## 입력 데이터 형식

Skeleton Analyzer에서 생성되는 엑셀 파일 구조:

| 시트명 | 설명 |
|--------|------|
| `Capture Data` | 캡처된 프레임별 관절 각도 및 평가 점수 (메인 데이터) |
| `RULA_A`, `RULA_B`, `RULA_C` | RULA 참조 테이블 |
| `REBA_A`, `REBA_B`, `REBA_C` | REBA 참조 테이블 |
| `OWAS_AC` | OWAS 참조 테이블 |
| `NLE_FM` | NLE Frequency Multiplier 참조 테이블 |
| `SI_*` | Strain Index 관련 테이블 |

### 주요 데이터 컬럼 (Capture Data)

```
Frame, Skeleton, Time, Captured,
Upper Arm, Lower Arm, Wrist, Wrist Twist, Neck, Trunk, Leg,
Score A, Score B, Score, Risk,
Back, Arms, Legs, Load, Code, AC,
NLE_H, NLE_V, NLE_D, NLE_A, NLE_F, NLE_C, NLE_Load, NLE_RWL, NLE_LI, NLE_Risk,
SI_IE, SI_DE, SI_EM, SI_HWP, SI_SW, SI_DD, SI_Score, SI_Risk, ...
```

## 템플릿 형식

### HTML 템플릿
```
template/
├── rula.html          # HTML 레이아웃
└── rula.mapping.json  # 필드 매핑 정의
```

### 이미지 템플릿
```
template/
├── owas.png           # 템플릿 이미지
└── owas.mapping.json  # 좌표 및 필드 매핑 정의
```

### NLE 템플릿
```
template/
├── nle.html           # NLE 평가 레이아웃
└── nle.mapping.json   # 필드 매핑 정의 (RWL, LI, 승수 등)
```

### SI 템플릿
```
template/
├── si.html            # SI 평가 레이아웃
└── si.mapping.json    # 필드 매핑 정의 (6개 승수, SI 점수 등)
```

### 매핑 JSON 예시

#### RULA 매핑
```json
{
  "name": "RULA",
  "version": "1.0",
  "fields": [
    {
      "id": "upper_arm",
      "label": "Upper Arm",
      "excel_column": "Upper Arm",
      "position": { "x": 120, "y": 85 }
    },
    {
      "id": "score",
      "label": "최종 점수",
      "excel_column": "Score",
      "position": { "x": 450, "y": 520 }
    }
  ]
}
```

#### NLE 매핑
```json
{
  "name": "NLE",
  "version": "1.0",
  "fields": [
    {
      "id": "h",
      "label": "수평 거리 (H)",
      "excel_column": "NLE_H",
      "unit": "cm"
    },
    {
      "id": "v",
      "label": "수직 높이 (V)",
      "excel_column": "NLE_V",
      "unit": "cm"
    },
    {
      "id": "rwl",
      "label": "권장 무게 한도 (RWL)",
      "excel_column": "NLE_RWL",
      "unit": "kg"
    },
    {
      "id": "li",
      "label": "들기 지수 (LI)",
      "excel_column": "NLE_LI"
    },
    {
      "id": "risk",
      "label": "위험 수준",
      "excel_column": "NLE_Risk"
    }
  ]
}
```

#### SI 매핑
```json
{
  "name": "SI",
  "version": "1.0",
  "fields": [
    {
      "id": "ie",
      "label": "노력 강도 (IE)",
      "excel_column": "SI_IE"
    },
    {
      "id": "de",
      "label": "노력 지속시간 (DE)",
      "excel_column": "SI_DE"
    },
    {
      "id": "em",
      "label": "분당 노력 횟수 (EM)",
      "excel_column": "SI_EM"
    },
    {
      "id": "hwp",
      "label": "손/손목 자세 (HWP)",
      "excel_column": "SI_HWP"
    },
    {
      "id": "sw",
      "label": "작업 속도 (SW)",
      "excel_column": "SI_SW"
    },
    {
      "id": "dd",
      "label": "일일 작업 시간 (DD)",
      "excel_column": "SI_DD"
    },
    {
      "id": "score",
      "label": "SI 점수",
      "excel_column": "SI_Score"
    },
    {
      "id": "risk",
      "label": "위험 수준",
      "excel_column": "SI_Risk"
    }
  ]
}
```

## 기술 스택 (예정)

- **Language**: Python 3.11+
- **UI Framework**: PyQt6
- **Excel 처리**: openpyxl
- **PDF 생성**: reportlab / weasyprint
- **이미지 처리**: Pillow

## 관련 프로젝트

- [Skeleton Analyzer](../skeleton-analyzer) - 동영상 기반 인체 포즈 분석 및 인체공학적 평가

## 라이센스

(추후 결정)

---

> 이 프로젝트는 현재 설계 단계입니다.
