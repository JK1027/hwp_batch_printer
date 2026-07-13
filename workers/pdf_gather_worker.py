# file: workers/pdf_gather_worker.py
"""
PDF 모으기 백그라운드 QThread Worker (취소 지원).
"""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import QThread, Signal
from services.pdf_gather_service import PdfGatherService
from services.log_service import LogService


class PdfGatherWorker(QThread):
    """PDF 모으기 작업을 수행하는 QThread 워커"""

    progress = Signal(int, int, str)        # (현재, 전체, 파일명)
    finished_all = Signal(int, int)         # (성공 수, 실패 수)
    log_message = Signal(str)               # 로그 메시지

    def __init__(self, src_dir: Path, dest_dir: Path, action: str,
                 log_service: Optional[LogService] = None, parent=None):
        super().__init__(parent)
        self._src_dir = src_dir
        self._dest_dir = dest_dir
        self._action = action
        self._log = log_service
        self._cancelled = False

    def run(self):
        service = PdfGatherService()
        action_kor = "복사" if self._action == "copy" else "이동"
        self.log_message.emit(f"🔄 PDF 모으기 작업 시작 ({action_kor})...")

        def progress_cb(current: int, total: int, filename: str):
            self.progress.emit(current, total, filename)
            self.log_message.emit(f"  📄 [{current}/{total}] {filename} 처리 중...")

        def cancel_check() -> bool:
            if self._cancelled:
                self.log_message.emit("⛔ 작업이 취소되었습니다")
                return True
            return False

        try:
            success, failed = service.gather_pdfs(
                self._src_dir, self._dest_dir, self._action, progress_cb, cancel_check
            )
            self.log_message.emit(
                f"✅ PDF 모으기 완료 — 성공: {success}, 실패: {failed}"
            )
            if self._log:
                self._log.log_app(
                    f"PDF 모으기 완료 ({action_kor}): "
                    f"원본={self._src_dir}, 대상={self._dest_dir}, "
                    f"성공={success}, 실패={failed}"
                )
            self.finished_all.emit(success, failed)
        except Exception as e:
            self.log_message.emit(f"🔴 PDF 모으기 실패: {e}")
            if self._log:
                self._log.log_error("PDF 모으기 백그라운드 작업 에러", exc=e)
            self.finished_all.emit(0, 0)

    def cancel(self):
        """작업 취소 요청"""
        self._cancelled = True
