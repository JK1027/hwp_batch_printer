# file: core/signals.py
"""
커스텀 Qt Signal 정의.
Worker ↔ UI 통신에 사용되는 시그널을 중앙에서 관리한다.
Worker Thread에서 UI 직접 수정 금지 — 반드시 Signal/Slot 사용.
"""

from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    """Worker → UI 통신용 시그널 묶음"""

    # 진행 상태: (현재 인덱스, 전체 수, 현재 파일명)
    progress = Signal(int, int, str)

    # 개별 파일 완료: (파일 인덱스, 상태 문자열)
    file_done = Signal(int, str)

    # 전체 작업 완료: (성공 수, 실패 수)
    finished_all = Signal(int, int)

    # 로그 메시지
    log_message = Signal(str)

    # 에러 발생: (에러 메시지)
    error_occurred = Signal(str)
