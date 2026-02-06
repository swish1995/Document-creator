"""라이센스 키 검증 모듈

라이센스 키 형식, 체크섬, 하드웨어 매칭을 검증합니다.
스켈레톤 분석기와 동일한 키 형식을 사용합니다.

키 형식: XXXX-XXXX-XXXX-XXXX (19자리)
- 첫 8자리 (XXXX-XXXX): 하드웨어 ID 해시
- 다음 4자리 (XXXX): 제품 코드
- 마지막 4자리 (XXXX): 체크섬
"""

import hashlib
import re
from enum import Enum
from typing import Optional


class ValidationResult(Enum):
    """검증 결과 열거형"""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_CHECKSUM = "invalid_checksum"
    HARDWARE_MISMATCH = "hardware_mismatch"


class LicenseValidator:
    """라이센스 키 검증기"""

    # 키 형식 정규식: XXXX-XXXX-XXXX-XXXX (영숫자)
    KEY_PATTERN = re.compile(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$')

    # 제품 코드 (스켈레톤 분석기와 동일)
    PRODUCT_CODE = "SA25"

    def normalize_key(self, key: Optional[str]) -> str:
        """키를 정규화합니다.

        Args:
            key: 원본 라이센스 키

        Returns:
            정규화된 키 (대문자, 공백 제거)
        """
        if key is None:
            return ""
        return key.strip().upper()

    def validate_format(self, key: Optional[str]) -> bool:
        """키 형식을 검증합니다.

        Args:
            key: 라이센스 키

        Returns:
            형식이 유효하면 True
        """
        if key is None:
            return False

        normalized = self.normalize_key(key)
        return bool(self.KEY_PATTERN.match(normalized))

    def validate_checksum(self, key: str) -> bool:
        """체크섬을 검증합니다.

        Args:
            key: 라이센스 키

        Returns:
            체크섬이 유효하면 True
        """
        normalized = self.normalize_key(key)
        if not self.validate_format(normalized):
            return False

        # 키에서 체크섬 부분 분리
        parts = normalized.split('-')
        key_without_checksum = '-'.join(parts[:3])
        provided_checksum = parts[3]

        # 체크섬 계산
        expected_checksum = self._calculate_checksum(key_without_checksum)

        return provided_checksum == expected_checksum

    def validate_hardware(self, key: str, hardware_id: str) -> bool:
        """하드웨어 ID 매칭을 검증합니다.

        Args:
            key: 라이센스 키
            hardware_id: 현재 시스템의 하드웨어 ID

        Returns:
            하드웨어가 일치하면 True
        """
        normalized = self.normalize_key(key)
        if not self.validate_format(normalized):
            return False

        # 키에서 하드웨어 해시 부분 추출 (첫 8자리)
        parts = normalized.split('-')
        key_hardware_hash = parts[0] + parts[1]

        # 현재 하드웨어 ID의 해시와 비교
        expected_hash = self._hash_hardware_for_key(hardware_id)

        return key_hardware_hash == expected_hash

    def validate(self, key: str, hardware_id: str) -> ValidationResult:
        """종합 검증을 수행합니다.

        Args:
            key: 라이센스 키
            hardware_id: 현재 시스템의 하드웨어 ID

        Returns:
            ValidationResult 열거형 값
        """
        normalized = self.normalize_key(key)

        # 1. 형식 검증
        if not self.validate_format(normalized):
            return ValidationResult.INVALID_FORMAT

        # 2. 체크섬 검증
        if not self.validate_checksum(normalized):
            return ValidationResult.INVALID_CHECKSUM

        # 3. 하드웨어 매칭
        if not self.validate_hardware(normalized, hardware_id):
            return ValidationResult.HARDWARE_MISMATCH

        return ValidationResult.VALID

    def generate_test_key(self, hardware_id: str) -> str:
        """테스트용 라이센스 키를 생성합니다.

        Args:
            hardware_id: 하드웨어 ID

        Returns:
            유효한 라이센스 키
        """
        # 하드웨어 해시 (8자리)
        hw_hash = self._hash_hardware_for_key(hardware_id)

        # 키 구성: HW_HASH(8) + PRODUCT_CODE(4)
        key_without_checksum = f"{hw_hash[:4]}-{hw_hash[4:]}-{self.PRODUCT_CODE}"

        # 체크섬 계산
        checksum = self._calculate_checksum(key_without_checksum)

        return f"{key_without_checksum}-{checksum}"

    def _hash_hardware_for_key(self, hardware_id: str) -> str:
        """하드웨어 ID를 키용 해시로 변환합니다.

        Args:
            hardware_id: 하드웨어 ID

        Returns:
            8자리 대문자 16진수
        """
        hash_obj = hashlib.sha256(hardware_id.encode())
        return hash_obj.hexdigest()[:8].upper()

    def _calculate_checksum(self, key_without_checksum: str) -> str:
        """체크섬을 계산합니다.

        Args:
            key_without_checksum: 체크섬을 제외한 키 부분

        Returns:
            4자리 체크섬
        """
        # 스켈레톤 분석기와 동일한 시크릿 사용
        secret = "SKELETON_ANALYZER_LICENSE"
        data = f"{key_without_checksum}:{secret}"
        hash_obj = hashlib.sha256(data.encode())
        return hash_obj.hexdigest()[:4].upper()
