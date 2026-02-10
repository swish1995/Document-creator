# Document Creator 배포 가이드

## 개요

이 문서는 Document Creator를 윈도우/macOS 사용자에게 배포하는 방법을 설명합니다.

GitHub Actions를 통해 실행 파일을 자동으로 빌드하고 배포할 수 있습니다.

---

## 사전 준비

1. GitHub 저장소에 코드가 푸시되어 있어야 합니다
2. `.github/workflows/build.yml` 워크플로우 파일이 있어야 합니다

---

## 배포 방법

### 방법 1: 태그를 통한 Release 배포 (권장)

정식 버전을 배포할 때 사용합니다. Releases 페이지에 영구 보관됩니다.

```bash
# 1. 변경사항 커밋 및 푸시
git add .
git commit -m "feat: 새 기능 추가"
git push origin main

# 2. 버전 태그 생성
git tag v1.0.0

# 3. 태그 푸시 (빌드 자동 시작)
git push origin v1.0.0
```

#### 버전 태그 규칙
- `v1.0.0` - 정식 릴리즈
- `v1.0.1` - 패치 버전
- `v1.1.0` - 마이너 업데이트
- `v2.0.0` - 메이저 업데이트

#### 다운로드 위치
```
https://github.com/{username}/{repo}/releases
```

---

### 방법 2: 수동 빌드 (테스트용)

개발 중 테스트 빌드가 필요할 때 사용합니다.

1. GitHub 저장소 접속
2. **Actions** 탭 클릭
3. 왼쪽 목록에서 **Build Application** 선택
4. **Run workflow** 버튼 클릭
5. 브랜치 선택 후 **Run workflow** 확인

#### 다운로드 위치
- Actions → 해당 워크플로우 실행 클릭 → 페이지 하단 **Artifacts** 섹션
- 보관 기간: 90일

---

## 빌드 과정

GitHub Actions가 자동으로 수행하는 작업:

1. Windows/macOS 환경에서 Python 3.11 설정
2. 의존성 패키지 설치 (`requirements.txt` + PyInstaller)
3. PyInstaller로 실행 파일 생성 (`document_creator.spec`)
4. 빌드 결과물 압축
5. Artifact 업로드 또는 Release 생성

---

## 배포 파일

| 파일명 | 설명 |
|--------|------|
| `DocumentCreator-Windows.zip` | 윈도우용 (DocumentCreator/ 폴더) |
| `DocumentCreator-macOS.zip` | macOS용 (DocumentCreator.app) |

---

## 사용자에게 배포하기

### Release 링크 공유
```
https://github.com/{username}/{repo}/releases/latest
```

---

## 문제 해결

### 빌드 실패 시
1. Actions 탭에서 실패한 워크플로우 클릭
2. 빨간색으로 표시된 단계 확인
3. 로그에서 오류 메시지 확인

### 일반적인 오류
| 오류 | 원인 | 해결 방법 |
|------|------|----------|
| ModuleNotFoundError | 의존성 누락 | `requirements.txt` 확인 |
| PyInstaller error | spec 파일 오류 | `document_creator.spec` 확인 |
| Template not found | 템플릿 누락 | `templates/` 디렉토리 확인 |

---

## 로컬 빌드

### Windows
```powershell
# 1. 저장소 클론
git clone https://github.com/{username}/{repo}.git
cd document-creator

# 2. 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. 의존성 설치
pip install -r requirements.txt
pip install pyinstaller

# 4. 빌드
pyinstaller document_creator.spec

# 5. 실행 파일 확인
dir dist\DocumentCreator\
```

### macOS
```bash
# 1. 저장소 클론
git clone https://github.com/{username}/{repo}.git
cd document-creator

# 2. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt
pip install pyinstaller

# 4. 빌드
pyinstaller document_creator.spec

# 5. 앱 번들 확인
ls dist/DocumentCreator.app
```

빌드된 파일은 `dist/` 디렉토리에 생성됩니다.
