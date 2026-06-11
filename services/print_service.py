# file: services/print_service.py
"""
인쇄 처리 서비스.
HWP COM의 PrintOut 메서드를 사용한다.
순차 처리만 허용 — 병렬 인쇄 금지.
"""

import time
from typing import List, Optional

from core.models import FileTask, PrintOptions, DuplexMode, NupMode
from services.hwp_service import HwpService
from services.log_service import LogService


class PrintService:
    """인쇄 서비스"""

    def __init__(self, hwp_service: HwpService,
                 log_service: Optional[LogService] = None):
        self._hwp = hwp_service
        self._log = log_service

    def print_file(self, hwp_instance, file_task: FileTask,
                   options: PrintOptions) -> bool:
        """
        HWP 파일을 인쇄한다.
        옵션: 매수, 단면/양면, 모아찍기.

        Args:
            hwp_instance: 이미 생성된 HWP COM 인스턴스
            file_task: 인쇄할 파일 작업
            options: 인쇄 옵션

        Returns:
            성공 여부
        """
        start_time = time.time()
        source_path = file_task.path

        try:
            # 1. 문서 열기
            if not self._hwp.open_document(hwp_instance, source_path):
                raise RuntimeError(f"문서 열기 실패: {source_path.name}")

            # 2. 인쇄 설정
            act = hwp_instance.CreateAction("Print")
            pset = act.CreateSet()
            act.GetDefault(pset)

            # 매수 (한글 API에서 인쇄 매수 파라미터는 "NumCopy"입니다)
            pset.SetItem("NumCopy", options.copies)

            # 모아찍기 (한글 API에서 모아찍기는 "PrintMethod" 파라미터로 지정합니다)
            # 0: 기본 인쇄, 4: 2쪽 모아찍기, 6: 4쪽 모아찍기
            if options.nup == NupMode.TWO:
                pset.SetItem("PrintMethod", 4)
            elif options.nup == NupMode.FOUR:
                pset.SetItem("PrintMethod", 6)
            else:
                pset.SetItem("PrintMethod", 0)

            # 프린터 지정 (빈 값이면 기본 프린터)
            if options.printer_name:
                pset.SetItem("PrinterName", options.printer_name)

            # 3. 인쇄 실행
            act.Execute(pset)

            # 4. 문서 닫기
            self._hwp.close_document(hwp_instance)

            elapsed = time.time() - start_time
            options_str = (
                f"copies={options.copies}, "
                f"duplex={options.duplex.value}, "
                f"nup={options.nup.value}"
            )
            if self._log:
                self._log.log_print(
                    source_path.name, "SUCCESS",
                    printer=options.printer_name or "(기본)",
                    options=options_str,
                    elapsed=elapsed,
                )
            return True

        except Exception as e:
            elapsed = time.time() - start_time

            # 문서 닫기 시도
            try:
                self._hwp.close_document(hwp_instance)
            except Exception:
                pass

            options_str = (
                f"copies={options.copies}, "
                f"duplex={options.duplex.value}, "
                f"nup={options.nup.value}"
            )
            if self._log:
                self._log.log_print(
                    source_path.name, "FAILED",
                    printer=options.printer_name or "(기본)",
                    options=options_str,
                    error=str(e),
                    elapsed=elapsed,
                )
                self._log.log_error(
                    f"인쇄 실패: {source_path.name}", exc=e
                )
            return False

    def get_available_printers(self) -> List[str]:
        """시스템에 설치된 프린터 목록 반환"""
        try:
            import win32print
            printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
            return [p[2] for p in printers]
        except Exception:
            return []
