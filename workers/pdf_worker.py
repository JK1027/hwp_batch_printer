# file: workers/pdf_worker.py
"""
PDF 변환 QThread Worker.
큐 기반 순차 처리. 병렬 변환 금지.
Signal로만 UI 업데이트.
실패 시 다음 파일 계속 진행.
COM 작업은 이 Worker Thread 내부에서만 수행한다.
"""

import pythoncom
from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from core.models import FileTask, FileStatus
from services.hwp_service import HwpService
from services.pdf_service import PdfService
from services.log_service import LogService


class PdfWorker(QThread):
    """
    PDF 변환 백그라운드 워커.
    
    [스레드 안전성 및 상태 관리 원칙]
    본 워커는 메인 스레드와 별개인 백그라운드 QThread에서 동작합니다.
    PySide6/Qt 아키텍처 규칙에 따라 백그라운드 스레드에서 AppState 싱글톤을 직접 수정하거나
    UI 요소를 직접 제어해서는 안 됩니다 (스레드 충돌 및 GUI 크래시 방지).
    따라서 워커는 진행 상태와 결과를 전용 Qt Signal로 송신하고, 메인 스레드의 MainWindow가
    이를 수신하여 AppState를 동기화하고 최종적으로 UI를 안전하게 갱신하도록 설계되었습니다.
    """

    # ── Signals (UI 업데이트용) ───────────────────────────
    progress = Signal(int, int, str)        # (현재, 전체, 파일명)
    file_done = Signal(int, str)            # (파일 인덱스, 상태값)
    finished_all = Signal(int, int)         # (성공 수, 실패 수)
    log_message = Signal(str)               # 로그 메시지

    def __init__(self, tasks: List[FileTask],
                 log_service: Optional[LogService] = None,
                 parent=None):
        super().__init__(parent)
        self._tasks = tasks
        self._log = log_service
        self._cancelled = False

    def run(self):
        """
        큐 순차 처리.
        COM 인스턴스는 이 메서드 내부에서 생성/해제한다.
        하나의 파일 실패가 전체 작업을 중단시키지 않는다.
        """
        # COM 초기화 (Worker Thread용)
        pythoncom.CoInitialize()

        hwp_instance = None
        hwp_service = HwpService(log_service=self._log)
        pdf_service = PdfService(hwp_service, log_service=self._log)

        success = 0
        failed = 0
        total = len(self._tasks)

        try:
            # HWP COM 인스턴스 생성 (전체 배치에서 하나만)
            self.log_message.emit("🔄 HWP 엔진 시작 중...")
            hwp_instance = hwp_service.create_hwp_instance()
            self.log_message.emit("✅ HWP 엔진 준비 완료")

            for i, task in enumerate(self._tasks):
                if self._cancelled:
                    self.log_message.emit("⛔ 작업이 취소되었습니다")
                    # 남은 파일 SKIPPED 처리
                    for j in range(i, total):
                        self.file_done.emit(j, FileStatus.SKIPPED.value)
                    break

                # 진행 상태 시그널
                self.progress.emit(i + 1, total, task.filename)
                self.file_done.emit(i, FileStatus.PROCESSING.value)
                self.log_message.emit(f"📄 [{i+1}/{total}] {task.filename} 변환 중...")

                # PDF 변환 시도
                try:
                    result = pdf_service.convert_to_pdf(hwp_instance, task)

                    if result:
                        success += 1
                        self.file_done.emit(i, FileStatus.SUCCESS.value)
                        self.log_message.emit(f"  ✅ 성공: {task.filename}")
                    else:
                        failed += 1
                        self.file_done.emit(i, FileStatus.FAILED.value)
                        self.log_message.emit(f"  ❌ 실패: {task.filename}")

                except Exception as e:
                    failed += 1
                    self.file_done.emit(i, FileStatus.FAILED.value)
                    self.log_message.emit(
                        f"  ❌ 실패: {task.filename} — {str(e)}"
                    )
                    if self._log:
                        self._log.log_error(
                            f"PDF Worker 예외: {task.filename}", exc=e
                        )

        except Exception as e:
            # COM 인스턴스 생성 실패 등 치명적 오류
            self.log_message.emit(f"🔴 치명적 오류: {str(e)}")
            if self._log:
                self._log.log_error(f"PDF Worker 치명적 오류", exc=e)

        finally:
            # COM 인스턴스 반드시 해제
            if hwp_instance:
                hwp_service.release_hwp(hwp_instance)
                self.log_message.emit("🔄 HWP 엔진 종료")

            # COM 정리
            pythoncom.CoUninitialize()

        self.finished_all.emit(success, failed)

    def cancel(self):
        """취소 요청"""
        self._cancelled = True
