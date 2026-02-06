"""라이센스 매니저 모듈

라이센스 상태 관리 및 기능 권한 검증을 담당합니다.
싱글톤 패턴으로 구현되어 앱 전체에서 하나의 인스턴스만 사용합니다.
스켈레톤 분석기와 동일한 라이센스 파일을 공유합니다.
"""

import hashlib
import json
import os
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal as Signal

from .hardware_id import get_hardware_id
from .license_validator import LicenseValidator, ValidationResult


class LicenseMode(Enum):
    """라이센스 모드"""
    FREE = "free"           # 무료 모드 (제한 기능 비활성화)
    LICENSED = "licensed"   # 등록 모드 (모든 기능 활성화)
    DEV = "dev"             # 개발 모드 (모든 기능 활성화, 개발용)


# 기능별 필요 라이센스 정의
# True: 무료 기능, False: 유료 기능
FEATURES: Dict[str, bool] = {
    # 무료 기능
    'excel_load': True,
    'template_view': True,
    'template_edit': True,
    'preview': True,

    # 유료 기능
    'document_generate': False,  # 문서 생성하기
}


class LicenseManager(QObject):
    """라이센스 매니저 (싱글톤)"""

    # 라이센스 상태 변경 시그널
    license_changed = Signal()

    _instance: Optional['LicenseManager'] = None
    _initialized: bool = False

    def __init__(self):
        super().__init__()

        # 이미 초기화된 경우 스킵 (싱글톤)
        if LicenseManager._initialized:
            return

        LicenseManager._initialized = True
        self._license_key: Optional[str] = None
        self._mode: LicenseMode = LicenseMode.FREE
        self._validator = LicenseValidator()

        # 환경변수에서 모드 확인
        self._check_environment_mode()

        # 저장된 라이센스 로드
        self._load_license()

    @classmethod
    def instance(cls) -> 'LicenseManager':
        """싱글톤 인스턴스를 반환합니다."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def _reset_for_testing(cls):
        """테스트용 상태 초기화"""
        if cls._instance is not None:
            # 시그널 연결 해제
            try:
                cls._instance.license_changed.disconnect()
            except (RuntimeError, TypeError):
                pass  # 연결된 슬롯이 없는 경우
        cls._instance = None
        cls._initialized = False

    @property
    def is_licensed(self) -> bool:
        """등록 여부를 반환합니다."""
        if self._mode in (LicenseMode.LICENSED, LicenseMode.DEV):
            return True
        return self._license_key is not None

    @property
    def license_mode(self) -> LicenseMode:
        """현재 라이센스 모드를 반환합니다."""
        return self._mode

    @property
    def license_key(self) -> Optional[str]:
        """등록된 라이센스 키를 반환합니다."""
        return self._license_key

    def set_mode(self, mode: LicenseMode) -> None:
        """라이센스 모드를 설정합니다.

        Args:
            mode: 설정할 모드
        """
        self._mode = mode
        self.license_changed.emit()

    def register(self, key: str) -> bool:
        """라이센스를 등록합니다.

        Args:
            key: 라이센스 키

        Returns:
            등록 성공 여부
        """
        hardware_id = get_hardware_id()
        result = self._validator.validate(key, hardware_id)

        if result == ValidationResult.VALID:
            self._license_key = self._validator.normalize_key(key)
            self._save_license()
            self.license_changed.emit()
            return True

        return False

    def unregister(self) -> None:
        """라이센스 등록을 해제합니다."""
        self._license_key = None
        self._delete_license_file()
        self.license_changed.emit()

    def check_feature(self, feature_name: str) -> bool:
        """기능 사용 권한을 확인합니다.

        Args:
            feature_name: 기능 이름

        Returns:
            사용 가능 여부
        """
        # 개발/강제등록 모드에서는 모든 기능 허용
        if self._mode in (LicenseMode.DEV, LicenseMode.LICENSED):
            return True

        # 알 수 없는 기능은 거부
        if feature_name not in FEATURES:
            return False

        # 무료 기능은 항상 허용
        if FEATURES[feature_name]:
            return True

        # 유료 기능은 등록 상태에서만 허용
        return self.is_licensed

    def _check_environment_mode(self) -> None:
        """환경변수에서 모드를 확인합니다."""
        # 스켈레톤 분석기와 동일한 환경변수 사용
        env_mode = os.environ.get('SKELETON_ANALYZER_LICENSE_MODE', '').lower()

        if env_mode == 'dev':
            self._mode = LicenseMode.DEV
        elif env_mode == 'licensed':
            self._mode = LicenseMode.LICENSED
        # 'free' 또는 빈 값은 기본값 유지

    @classmethod
    def _get_config_path(cls) -> Path:
        """설정 파일 경로를 반환합니다.

        스켈레톤 분석기와 동일한 경로를 사용하여 라이센스를 공유합니다.
        """
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', Path.home()))
        else:  # macOS, Linux
            base = Path.home() / '.config'

        # 스켈레톤 분석기와 동일한 폴더 사용 (라이센스 공유)
        config_dir = base / 'SkeletonAnalyzer'
        config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir / 'license.json'

    def _save_license(self) -> None:
        """라이센스 정보를 파일에 저장합니다."""
        if self._license_key is None:
            return

        config_path = self._get_config_path()

        data = {
            'license_key': self._license_key,
            'hardware_id': get_hardware_id(),
        }

        # 무결성 체크섬 추가
        data['checksum'] = self._calculate_config_checksum(data)

        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_license(self) -> None:
        """저장된 라이센스 정보를 로드합니다."""
        config_path = self._get_config_path()

        if not config_path.exists():
            return

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            # 무결성 검증
            stored_checksum = data.pop('checksum', None)
            expected_checksum = self._calculate_config_checksum(data)

            if stored_checksum != expected_checksum:
                # 변조된 파일 - 삭제하지 않고 무시 (스켈레톤 분석기가 사용 중일 수 있음)
                return

            # 라이센스 키 검증
            license_key = data.get('license_key')
            hardware_id = get_hardware_id()

            result = self._validator.validate(license_key, hardware_id)
            if result == ValidationResult.VALID:
                self._license_key = license_key

        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # 파일 손상 시 무시

    def _delete_license_file(self) -> None:
        """라이센스 파일을 삭제합니다."""
        config_path = self._get_config_path()
        if config_path.exists():
            config_path.unlink()

    def _calculate_config_checksum(self, data: Dict[str, Any]) -> str:
        """설정 데이터의 체크섬을 계산합니다."""
        # 스켈레톤 분석기와 동일한 시크릿 사용
        secret = "SKELETON_ANALYZER_CONFIG_SECRET"
        content = json.dumps(data, sort_keys=True) + secret
        return hashlib.sha256(content.encode()).hexdigest()[:16]
