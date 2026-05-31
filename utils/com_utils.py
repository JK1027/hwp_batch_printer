# file: utils/com_utils.py
"""
COM 객체 유틸리티.
COM 초기화/해제 헬퍼, 잔류 프로세스 정리.
"""

import subprocess
from typing import Optional, Set


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
    COM 비정상 종료 시 복구용 (전체 Hwp.exe를 강제 종료함).
    """
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", "Hwp.exe"],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass


def get_hwp_pids() -> Set[int]:
    """
    현재 실행 중인 Hwp.exe 프로세스의 PID 목록을 반환한다.
    """
    pids = set()
    try:
        res = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Hwp.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        for line in res.stdout.strip().splitlines():
            parts = line.split(",")
            if len(parts) >= 2:
                pid_str = parts[1].strip('"')
                if pid_str.isdigit():
                    pids.add(int(pid_str))
    except Exception:
        pass
    return pids


def kill_process_by_pid(pid: int) -> None:
    """
    특정 PID의 프로세스를 강제 종료한다.
    """
    try:
        subprocess.run(
            ["taskkill", "/f", "/pid", str(pid)],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass

