# file: ui/progress_panel.py
"""
진행률 표시 패널.
프로그레스 바, 현재 파일명, 로그 메시지를 표시한다.
Worker를 직접 제어하지 않는다.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QProgressBar, QLabel, QTextEdit
)
from PySide6.QtCore import Qt


class ProgressPanel(QWidget):
    """진행률 및 로그 표시 패널"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── 상태 표시 영역 ───────────────────────────────
        status_layout = QHBoxLayout()

        self._status_label = QLabel("준비")
        self._status_label.setObjectName("statusLabel")

        self._current_file_label = QLabel("")
        self._current_file_label.setObjectName("currentFileLabel")

        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        status_layout.addWidget(self._current_file_label)

        # ── 프로그레스 바 ────────────────────────────────
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("mainProgressBar")
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%v / %m (%p%)")

        # ── 로그 영역 ───────────────────────────────────
        self._log_area = QTextEdit()
        self._log_area.setObjectName("logArea")
        self._log_area.setReadOnly(True)
        self._log_area.setMaximumHeight(120)
        self._log_area.setPlaceholderText("작업 로그가 여기에 표시됩니다...")

        layout.addLayout(status_layout)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._log_area)

    # ── 외부 업데이트 메서드 ─────────────────────────────

    def set_progress(self, current: int, total: int, filename: str = ""):
        """진행률 업데이트"""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        if filename:
            self._current_file_label.setText(f"처리 중: {filename}")

    def set_status(self, text: str):
        """상태 레이블 업데이트"""
        self._status_label.setText(text)

    def append_log(self, message: str):
        """로그 메시지 추가"""
        self._log_area.append(message)
        # 자동 스크롤
        scrollbar = self._log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def reset(self):
        """진행률 초기화"""
        self._progress_bar.setValue(0)
        self._progress_bar.setMaximum(100)
        self._status_label.setText("준비")
        self._current_file_label.setText("")

    def clear_log(self):
        """로그 영역 초기화"""
        self._log_area.clear()
