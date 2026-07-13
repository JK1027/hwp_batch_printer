# file: ui/main_window.py
"""
메인 윈도우.
위젯 조립과 레이아웃 관리, Signal/Slot 연결만 담당한다.
COM 호출, 파일 저장, 긴 작업 수행 금지.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PySide6.QtCore import Qt

from core.constants import (
    APP_WINDOW_TITLE,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    PDF_OUTPUT_DIR_NAME,
)
from core.app_state import AppState
from core.models import PrintOptions, FileStatus, JobStatus

from ui.drop_zone import DropZone
from ui.file_list_panel import FileListPanel
from ui.control_panel import ControlPanel
from ui.progress_panel import ProgressPanel

from workers.pdf_worker import PdfWorker
from workers.print_worker import PrintWorker
from services.log_service import LogService


class MainWindow(QMainWindow):
    """HWP Batch Printer 메인 윈도우"""

    def __init__(self):
        super().__init__()
        self._state = AppState.instance()
        self._log = LogService.instance()
        self._current_worker: Optional[PdfWorker | PrintWorker] = None
        self._setup_window()
        self._setup_ui()
        self._connect_signals()

    def _setup_window(self):
        """윈도우 기본 설정"""
        self.setWindowTitle(APP_WINDOW_TITLE)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

    def _setup_ui(self):
        """위젯 조립"""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── 드래그앤드롭 영역 ────────────────────────────
        self._drop_zone = DropZone()

        # ── 파일 목록 ───────────────────────────────────
        self._file_list = FileListPanel()

        # ── 컨트롤 패널 ─────────────────────────────────
        self._control_panel = ControlPanel()

        # ── 진행률 패널 ─────────────────────────────────
        self._progress_panel = ProgressPanel()

        # ── 레이아웃 조립 ────────────────────────────────
        layout.addWidget(self._drop_zone)
        layout.addWidget(self._file_list, stretch=1)
        layout.addWidget(self._control_panel)
        layout.addWidget(self._progress_panel)

    def _connect_signals(self):
        """Signal/Slot 연결"""
        # 드래그앤드롭 → AppState에 파일 추가
        self._drop_zone.files_dropped.connect(self._on_files_dropped)

        # 컨트롤 패널 버튼
        self._control_panel.convert_pdf_clicked.connect(self._on_convert_pdf)
        self._control_panel.convert_folder_pdf_clicked.connect(self._on_convert_folder_pdf)
        self._control_panel.print_clicked.connect(self._on_print)
        self._control_panel.reset_clicked.connect(self._on_reset)
        self._control_panel.cancel_clicked.connect(self._on_cancel)

    # ── 이벤트 핸들러 ────────────────────────────────────

    def _on_files_dropped(self, paths: list):
        """드롭된 파일 처리"""
        added = self._state.add_files(paths)
        if added > 0:
            self._progress_panel.append_log(f"📁 {added}개 파일 추가됨")
        else:
            self._progress_panel.append_log("⚠️ 추가할 수 있는 HWP/HWPX 파일이 없습니다")

    # ── PDF 변환 ─────────────────────────────────────────

    def _on_convert_pdf(self):
        """PDF 변환 시작"""
        if self._state.file_count() == 0:
            QMessageBox.warning(self, "알림", "파일을 먼저 추가해주세요.")
            return

        if self._state.is_working():
            QMessageBox.warning(self, "알림", "이미 작업이 진행 중입니다.")
            return

        # 상태 초기화 및 UI 전환
        self._state.reset_all_status()
        self._state.set_job_status(JobStatus.CONVERTING)
        self._control_panel.set_working(True)
        self._progress_panel.reset()
        self._progress_panel.set_status("PDF 변환 중...")

        tasks = self._state.get_files()
        self._log.log_app(f"PDF 변환 시작: {len(tasks)}개 파일")

        # Worker 생성 및 Signal 연결
        self._current_worker = PdfWorker(
            tasks=tasks,
            log_service=self._log,
            parent=self,
        )
        self._current_worker.progress.connect(self._progress_panel.set_progress)
        self._current_worker.file_done.connect(self._on_worker_file_done)
        self._current_worker.finished_all.connect(
            lambda s, f: self._on_job_finished("PDF 변환", s, f)
        )
        self._current_worker.log_message.connect(self._progress_panel.append_log)
        self._current_worker.start()

    def _on_convert_folder_pdf(self):
        """폴더 전체 PDF 변환 시작"""
        if self._state.is_working():
            QMessageBox.warning(self, "알림", "이미 작업이 진행 중입니다.")
            return

        # 기존 대기 파일이 있을 때 경고창 띄우기
        if self._state.file_count() > 0:
            reply = QMessageBox.question(
                self,
                "확인",
                "현재 등록된 파일 목록을 모두 비우고 폴더 변환을 진행하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # 1. 입력 폴더 선택
        input_dir = QFileDialog.getExistingDirectory(self, "한글(HWP/HWPX) 파일이 있는 입력 폴더 선택")
        if not input_dir:
            return

        input_path = Path(input_dir)

        # 2. 폴더 탐색 (재귀적 탐색)
        hwp_files = []
        for ext in ["*.hwp", "*.hwpx"]:
            for f in input_path.rglob(ext):
                # 심볼릭 링크 및 Junction 무시
                if f.is_symlink():
                    continue
                hwp_files.append(f)

        # 대소문자 구분 및 중복 방지 정렬
        hwp_files = sorted(list(set(hwp_files)), key=lambda p: str(p).lower())

        if not hwp_files:
            QMessageBox.warning(self, "알림", "선택한 폴더 내에 한글(HWP/HWPX) 파일이 존재하지 않습니다.")
            return

        # 3. 사전 확인 단계 (UX 개선)
        confirm_reply = QMessageBox.question(
            self,
            "확인",
            f"총 {len(hwp_files)}개의 한글 파일을 찾았습니다.\n변환을 시작하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if confirm_reply == QMessageBox.StandardButton.No:
            return

        # 기존 목록 비우고 새로운 파일 목록 추가
        self._state.clear_files()
        
        # 파일 추가 (원본 폴더 자동 저장 옵션 전달)
        added = self._state.add_files(
            [str(f) for f in hwp_files], 
            use_source_dir_as_output=True
        )
        
        self._progress_panel.append_log(f"📁 폴더 검색 완료: {added}개 파일 추가됨")

        # PDF 변환 자동 실행
        self._state.reset_all_status()
        self._state.set_job_status(JobStatus.CONVERTING)
        self._control_panel.set_working(True)
        self._progress_panel.reset()
        self._progress_panel.set_status("PDF 변환 중...")

        tasks = self._state.get_files()
        self._log.log_app(f"폴더 전체 PDF 변환 시작: {len(tasks)}개 파일")

        # Worker 생성 및 Signal 연결
        self._current_worker = PdfWorker(
            tasks=tasks,
            log_service=self._log,
            parent=self,
        )
        self._current_worker.progress.connect(self._progress_panel.set_progress)
        self._current_worker.file_done.connect(self._on_worker_file_done)
        self._current_worker.finished_all.connect(
            lambda s, f: self._on_job_finished("폴더 전체 PDF 변환", s, f)
        )
        self._current_worker.log_message.connect(self._progress_panel.append_log)
        self._current_worker.start()

    # ── 일괄 인쇄 ────────────────────────────────────────

    def _on_print(self):
        """인쇄 시작"""
        if self._state.file_count() == 0:
            QMessageBox.warning(self, "알림", "파일을 먼저 추가해주세요.")
            return

        if self._state.is_working():
            QMessageBox.warning(self, "알림", "이미 작업이 진행 중입니다.")
            return

        # 인쇄 옵션 수집
        options = PrintOptions(
            copies=self._control_panel.get_copies(),
            duplex=self._control_panel.get_duplex_mode(),
            nup=self._control_panel.get_nup_mode(),
        )
        self._state.set_print_options(options)

        # 상태 초기화 및 UI 전환
        self._state.reset_all_status()
        self._state.set_job_status(JobStatus.PRINTING)
        self._control_panel.set_working(True)
        self._progress_panel.reset()
        self._progress_panel.set_status("인쇄 중...")

        tasks = self._state.get_files()
        self._log.log_app(f"일괄 인쇄 시작: {len(tasks)}개 파일")

        # Worker 생성 및 Signal 연결
        self._current_worker = PrintWorker(
            tasks=tasks,
            options=options,
            log_service=self._log,
            parent=self,
        )
        self._current_worker.progress.connect(self._progress_panel.set_progress)
        self._current_worker.file_done.connect(self._on_worker_file_done)
        self._current_worker.finished_all.connect(
            lambda s, f: self._on_job_finished("일괄 인쇄", s, f)
        )
        self._current_worker.log_message.connect(self._progress_panel.append_log)
        self._current_worker.start()

    # ── 취소 ─────────────────────────────────────────────

    def _on_cancel(self):
        """작업 취소"""
        if self._current_worker and self._current_worker.isRunning():
            self._state.set_job_status(JobStatus.CANCELLING)
            self._current_worker.cancel()
            self._progress_panel.set_status("취소 중...")
            self._progress_panel.append_log("⛔ 취소 요청됨...")

    # ── 초기화 ─────────────────────────────────────────────

    def _on_reset(self):
        """전체 초기화"""
        if self._state.is_working():
            QMessageBox.warning(self, "알림", "작업 진행 중에는 초기화할 수 없습니다.")
            return

        reply = QMessageBox.question(
            self,
            "초기화",
            "등록된 파일 목록과 모든 설정을 초기화하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._state.reset()
            self._control_panel.reset_settings()
            self._progress_panel.reset()
            self._progress_panel.set_status("대기 중")
            self._progress_panel.append_log("🧹 파일 목록과 설정을 초기화했습니다.")

    # ── Worker 콜백 ──────────────────────────────────────

    def _on_worker_file_done(self, index: int, status_str: str):
        """Worker에서 개별 파일 처리 완료 시"""
        try:
            status = FileStatus(status_str)
            self._state.set_file_status(index, status)
        except ValueError:
            pass

    def _on_job_finished(self, job_type: str, success: int, failed: int):
        """작업 완료 처리"""
        self._state.set_job_status(JobStatus.IDLE)
        self._control_panel.set_working(False)
        self._progress_panel.set_status("완료")
        self._progress_panel.append_log(
            f"✅ {job_type} 완료 — 성공: {success}, 실패: {failed}"
        )

        self._log.log_app(f"{job_type} 완료: 성공={success}, 실패={failed}")

        # AppState 내부 상태 검증을 위한 구조화된 덤프 출력
        try:
            dump_tasks = self._state.get_files()
            status_summary = {}
            for t in dump_tasks:
                status_summary[t.status.name] = status_summary.get(t.status.name, 0) + 1
            dump_str = ", ".join(f"{k}: {v}" for k, v in status_summary.items())
            self._log.log_app(f"[AppState SSOT 검증] 전체 파일: {len(dump_tasks)}개 | 상태 집계 -> {dump_str}")
        except Exception as dump_err:
            self._log.log_app(f"[AppState SSOT 검증 오류] 상태를 덤프하는 데 실패했습니다: {dump_err}", level="WARNING")

        self._current_worker = None

        # PDF 변환 완료 후 출력 폴더 열기 제안
        if "PDF" in job_type and success > 0:
            files = self._state.get_files()
            if files:
                if files[0].output_dir:
                    output_dir = files[0].output_dir
                else:
                    output_dir = files[0].path.parent / PDF_OUTPUT_DIR_NAME
                
                if output_dir.exists():
                    reply = QMessageBox.question(
                        self,
                        "변환 완료",
                        f"PDF 변환이 완료되었습니다.\n"
                        f"성공: {success}, 실패: {failed}\n\n"
                        f"출력 폴더를 열까요?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        os.startfile(str(output_dir))
