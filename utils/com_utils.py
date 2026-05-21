# file: utils/com_utils.py
"""
COM 객체 유틸리티.
COM 초기화/해제 헬퍼, 잔류 프로세스 정리.
"""

import subprocess
from typing import Optional


def safe_release_com(hwp: Optional[object]) -> None:
    """
    COM 객체 안전 해제.
    예외가 발생해도 무시하고 해제를 시도한다.
    """
    if hwp is None:
        return
    try:
        hwp.Quit()
    except Exception:
        pass


def kill_hwp_processes() -> None:
    """
    잔류 HWP 프로세스 강제 종료.
    COM 비정상 종료 시 복구용.
    """
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", "Hwp.exe"],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass
