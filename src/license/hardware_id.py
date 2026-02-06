"""하드웨어 ID 생성 모듈

시스템의 고유 하드웨어 ID를 생성합니다.
- macOS: system_profiler에서 Hardware UUID 획득
- Windows: WMIC에서 시스템 UUID 획득
- Linux: /etc/machine-id 읽기

결과는 SHA-256 해시의 앞 16자리 (대문자)로 반환됩니다.
"""

import hashlib
import platform
import subprocess
import uuid
from typing import Optional

# 캐시된 하드웨어 ID
_cached_hardware_id: Optional[str] = None


def get_hardware_id() -> str:
    """하드웨어 ID를 반환합니다.

    Returns:
        16자리 대문자 16진수 문자열 (SHA-256 해시 prefix)
    """
    global _cached_hardware_id

    if _cached_hardware_id is not None:
        return _cached_hardware_id

    try:
        raw_id = _get_raw_hardware_id()
        _cached_hardware_id = _hash_hardware_id(raw_id)
    except Exception:
        # 폴백: MAC 주소 기반 UUID 사용
        fallback_id = str(uuid.getnode())
        _cached_hardware_id = _hash_hardware_id(fallback_id)

    return _cached_hardware_id


def clear_cache() -> None:
    """캐시된 하드웨어 ID를 초기화합니다. (테스트용)"""
    global _cached_hardware_id
    _cached_hardware_id = None


def _get_raw_hardware_id() -> str:
    """플랫폼별 원시 하드웨어 ID를 획득합니다.

    Returns:
        시스템 고유 식별자 문자열

    Raises:
        RuntimeError: 하드웨어 ID 획득 실패 시
    """
    system = platform.system()

    if system == 'Darwin':
        return _get_macos_hardware_id()
    elif system == 'Windows':
        return _get_windows_hardware_id()
    elif system == 'Linux':
        return _get_linux_hardware_id()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def _get_macos_hardware_id() -> str:
    """macOS에서 Hardware UUID를 획득합니다."""
    result = subprocess.run(
        ['system_profiler', 'SPHardwareDataType'],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise RuntimeError("system_profiler failed")

    # "Hardware UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" 파싱
    for line in result.stdout.split('\n'):
        if 'Hardware UUID' in line:
            uuid_part = line.split(':')[-1].strip()
            return uuid_part

    raise RuntimeError("Hardware UUID not found")


def _get_windows_hardware_id() -> str:
    """Windows에서 시스템 UUID를 획득합니다."""
    # WMIC 명령 사용
    result = subprocess.run(
        ['wmic', 'csproduct', 'get', 'UUID'],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        # PowerShell 폴백
        result = subprocess.run(
            ['powershell', '-Command',
             "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"],
            capture_output=True,
            text=True,
            timeout=10
        )

    if result.returncode != 0:
        raise RuntimeError("Failed to get Windows UUID")

    # UUID 추출 (첫 번째 줄은 헤더)
    lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    if len(lines) >= 2:
        return lines[1]
    elif lines:
        return lines[0]

    raise RuntimeError("Windows UUID not found")


def _get_linux_hardware_id() -> str:
    """Linux에서 machine-id를 획득합니다."""
    # /etc/machine-id 먼저 시도
    try:
        with open('/etc/machine-id', 'r') as f:
            machine_id = f.read().strip()
            if machine_id:
                return machine_id
    except FileNotFoundError:
        pass

    # /var/lib/dbus/machine-id 폴백
    try:
        with open('/var/lib/dbus/machine-id', 'r') as f:
            machine_id = f.read().strip()
            if machine_id:
                return machine_id
    except FileNotFoundError:
        pass

    # DMI 정보 폴백
    try:
        result = subprocess.run(
            ['cat', '/sys/class/dmi/id/product_uuid'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    raise RuntimeError("Linux machine ID not found")


def _hash_hardware_id(raw_id: str) -> str:
    """원시 하드웨어 ID를 SHA-256 해시로 변환합니다.

    Args:
        raw_id: 원시 하드웨어 식별자

    Returns:
        16자리 대문자 16진수 문자열
    """
    hash_obj = hashlib.sha256(raw_id.encode())
    return hash_obj.hexdigest()[:16].upper()
