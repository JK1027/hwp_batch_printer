# file: services/hwp_service.py
"""
HWP COM 객체 관리 서비스.
COM 객체 생명주기를 명시적으로 관리한다.
반드시 try/finally로 Quit() 보장.
병렬 COM 작업 금지 — 순차 처리만 허용.
COM 작업은 Worker Thread 내부에서만 수행한다.
"""

import time
from pathlib import Path
from typing import Optional

from core.constants import HWP_COM_PROG_ID
from services.log_service import LogService


class HwpService:
    """
    HWP COM 자동화 서비스.
    COM 인스턴스 생성/해제, 문서 열기/닫기를 관리한다.
    """

    def __init__(self, log_service: Optional[LogService] = None):
        self._log = log_service
        self._spawned_pid: Optional[int] = None

    def create_hwp_instance(self) -> object:
        """
        HWP COM 인스턴스 생성.
        반드시 release_hwp()로 해제해야 한다.

        Returns:
            HWP COM 객체

        Raises:
            RuntimeError: COM 객체 생성 실패 시
        """
        try:
            import os
            import shutil
            import sys
            import win32com
            import win32com.client as win32
            from utils.com_utils import get_hwp_pids

            pids_before = get_hwp_pids()

            try:
                # 1차 시도: EnsureDispatch (사전 빌드된 캐시 사용으로 속도 및 자동 완성 최적화)
                hwp = win32.gencache.EnsureDispatch(HWP_COM_PROG_ID)
            except Exception as dispatch_err:
                if self._log:
                    self._log.log_app(f"EnsureDispatch 실패 (캐시 오염 감지), 캐시 클리어 후 재시도: {dispatch_err}", level="WARNING")
                
                # win32com gen_py 캐시 폴더 삭제 시도 (자가 치유)
                try:
                    if hasattr(win32com, "__gen_path__") and win32com.__gen_path__:
                        gen_py_path = win32com.__gen_path__
                        if os.path.exists(gen_py_path):
                            shutil.rmtree(gen_py_path)
                    
                    # 메모리에 로드된 gen_py 모듈 캐시 제거
                    for key in list(sys.modules.keys()):
                        if key.startswith("win32com.gen_py"):
                            del sys.modules[key]
                    
                    # 2차 시도: EnsureDispatch 재시도
                    hwp = win32.gencache.EnsureDispatch(HWP_COM_PROG_ID)
                except Exception as clean_err:
                    if self._log:
                        self._log.log_app(f"캐시 삭제 후 EnsureDispatch 실패, dynamic.Dispatch 폴백 시도: {clean_err}", level="WARNING")
                    # 3차 시도: gen_py 캐시를 완전히 우회하는 dynamic.Dispatch (Late-binding)
                    import win32com.client.dynamic
                    hwp = win32com.client.dynamic.Dispatch(HWP_COM_PROG_ID)

            # 신규 생성된 HWP PID 감지 (Best-effort 방식)
            pids_after = get_hwp_pids()
            new_pids = pids_after - pids_before
            if new_pids:
                self._spawned_pid = list(new_pids)[0]
                if self._log:
                    self._log.log_app(f"스폰된 HWP COM 프로세스 PID 감지: {self._spawned_pid}")

            # 보안 모듈 처리 및 창 보이지 않게 설정 (안전성 강화)
            try:
                if hasattr(hwp, "XHwpWindows") and hwp.XHwpWindows.Count > 0:
                    hwp.XHwpWindows.Item(0).Visible = False
            except Exception as win_err:
                if self._log:
                    self._log.log_app(f"창 비활성화 설정 건너뜀 (윈도우 초기화 전): {win_err}", level="WARNING")

            try:
                reg_result = hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
                if not reg_result and self._log:
                    self._log.log_app("보안 모듈 등록 실패: RegisterModule이 False를 반환했습니다. (보안 팝업이 나타날 수 있음)", level="WARNING")
            except Exception as mod_err:
                if self._log:
                    self._log.log_app(f"보안 모듈 등록 실패 (이미 등록되었거나 모듈 누락): {mod_err}", level="WARNING")

            if self._log:
                self._log.log_app("HWP COM 인스턴스 생성 완료")

            return hwp

        except Exception as e:
            if self._log:
                self._log.log_error(f"HWP COM 인스턴스 생성 실패: {e}", exc=e)
            raise RuntimeError(f"HWP COM 생성 실패: {e}") from e

    def open_document(self, hwp, path: Path) -> bool:
        """
        HWP 문서 열기 (읽기 전용).
        원본 파일 수정 금지 원칙.

        Args:
            hwp: HWP COM 객체
            path: HWP 파일 경로

        Returns:
            성공 여부
        """
        try:
            # 읽기 전용으로 열기
            result = hwp.Open(
                str(path),
                "",     # 포맷 자동 감지 (HWP/HWPX 확장자 지원 및 경로 특수문자 대응)
                "forceopen:true"  # 잠긴 파일도 열기
            )

            if self._log:
                self._log.log_app(f"문서 열기: {path.name}")

            return bool(result)

        except Exception as e:
            if self._log:
                self._log.log_error(f"문서 열기 실패: {path.name} - {e}", exc=e)
            return False

    def close_document(self, hwp) -> None:
        """
        현재 열린 문서 닫기.
        저장하지 않고 닫는다 (원본 수정 금지).
        """
        try:
            hwp.Clear(option=1)  # 저장 안 함
        except Exception as e:
            if self._log:
                self._log.log_error(f"문서 닫기 실패: {e}", exc=e)

    def release_hwp(self, hwp) -> None:
        """
        HWP COM 객체 안전 해제.
        반드시 finally 블록에서 호출되어야 한다.
        예외가 발생해도 해제를 시도한다.
        """
        if hwp is None:
            return

        try:
            hwp.Quit()
            if self._log:
                self._log.log_app("HWP COM 인스턴스 해제 완료")
        except Exception as e:
            if self._log:
                self._log.log_error(f"HWP COM 해제 중 오류: {e}", exc=e)

            # 강제 프로세스 종료 시도 (특정 PID만 타겟)
            if self._spawned_pid:
                if self._log:
                    self._log.log_app(f"HWP COM 프로세스 강제 격리 종료 시도 (PID: {self._spawned_pid})", level="WARNING")
                from utils.com_utils import kill_process_by_pid
                kill_process_by_pid(self._spawned_pid)
            else:
                if self._log:
                    self._log.log_app("강제 프로세스 종료 건너뜀 (감지된 PID 없음)", level="WARNING")
