# file: core/app_state.py
"""
중앙 상태 관리자 (Singleton).
모든 공유 상태는 이 클래스를 통해서만 관리한다.
Frame ↔ Frame 직접 상태 공유 금지.
"""

from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from core.models import FileTask, FileStatus, PrintOptions, JobStatus, JobResult
from core.constants import SUPPORTED_EXTENSIONS

from pathlib import Path


class AppState(QObject):
    """
    애플리케이션 전역 상태 관리자.
    Singleton 패턴으로 단일 인스턴스만 유지한다.
    상태 변경 시 Qt Signal로 UI에 통지한다.
    """

    # ── Signals ──────────────────────────────────────────
    files_changed = Signal()                    # 파일 목록 변경
    job_started = Signal(str)                   # 작업 시작 (작업 유형)
    job_progress = Signal(int, int, str)        # (현재, 전체, 파일명)
    job_finished = Signal(str, int, int)        # (작업 유형, 성공 수, 실패 수)
    file_status_changed = Signal(int, str)      # (인덱스, 새 상태)
    log_message = Signal(str)                   # 로그 메시지

    _instance: Optional["AppState"] = None

    @classmethod
    def instance(cls) -> "AppState":
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._file_tasks: List[FileTask] = []
        self._print_options: PrintOptions = PrintOptions()
        self._job_status: JobStatus = JobStatus.IDLE

    # ── 파일 관리 ────────────────────────────────────────

    def add_files(self, paths: List[str], output_dir: Optional[Path] = None,
                  root_input_dir: Optional[Path] = None) -> int:
        """
        파일 경로 목록을 추가한다.
        중복/미지원 확장자는 필터링한다.
        Returns: 실제 추가된 파일 수
        """
        added = 0
        existing_paths = {t.path for t in self._file_tasks}

        for p in paths:
            path = Path(p)
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if path in existing_paths:
                continue
            if not path.exists():
                continue

            # root_input_dir이 있으면 상대 경로 디렉토리 계산
            relative_dir = None
            if root_input_dir:
                try:
                    relative_dir = path.parent.relative_to(root_input_dir)
                except ValueError:
                    pass

            self._file_tasks.append(
                FileTask(path=path, output_dir=output_dir, relative_dir=relative_dir)
            )
            existing_paths.add(path)
            added += 1

        if added > 0:
            self.files_changed.emit()
        return added

    def remove_file(self, index: int) -> None:
        """인덱스로 파일 제거"""
        if 0 <= index < len(self._file_tasks):
            self._file_tasks.pop(index)
            self.files_changed.emit()

    def clear_files(self) -> None:
        """모든 파일 제거"""
        self._file_tasks.clear()
        self.files_changed.emit()

    def get_files(self) -> List[FileTask]:
        """전체 파일 목록 반환"""
        return list(self._file_tasks)

    def get_pending_files(self) -> List[FileTask]:
        """대기 중인 파일만 반환"""
        return [t for t in self._file_tasks if t.status == FileStatus.PENDING]

    def file_count(self) -> int:
        """등록된 파일 수"""
        return len(self._file_tasks)

    # ── 파일 상태 관리 ───────────────────────────────────

    def set_file_status(self, index: int, status: FileStatus,
                        error_message: str = "") -> None:
        """개별 파일 상태 업데이트"""
        if 0 <= index < len(self._file_tasks):
            self._file_tasks[index].status = status
            self._file_tasks[index].error_message = error_message
            self.file_status_changed.emit(index, status.value)

    def reset_all_status(self) -> None:
        """모든 파일 상태를 PENDING으로 초기화"""
        for task in self._file_tasks:
            task.status = FileStatus.PENDING
            task.error_message = ""
        self.files_changed.emit()

    # ── 작업 상태 관리 ───────────────────────────────────

    def set_job_status(self, status: JobStatus) -> None:
        """전체 작업 상태 변경"""
        self._job_status = status

    def get_job_status(self) -> JobStatus:
        """현재 작업 상태 반환"""
        return self._job_status

    def is_working(self) -> bool:
        """작업 진행 중 여부"""
        return self._job_status not in (JobStatus.IDLE,)

    # ── 인쇄 옵션 관리 ───────────────────────────────────

    def get_print_options(self) -> PrintOptions:
        """현재 인쇄 옵션 반환"""
        return self._print_options

    def set_print_options(self, options: PrintOptions) -> None:
        """인쇄 옵션 설정"""
        self._print_options = options

    # ── 초기화 ───────────────────────────────────────────

    def reset(self) -> None:
        """전체 상태 초기화"""
        self._file_tasks.clear()
        self._print_options = PrintOptions()
        self._job_status = JobStatus.IDLE
        self.files_changed.emit()
