# file: ui/file_list_panel.py
"""
파일 목록 테이블 위젯.
등록된 파일과 상태를 표시한다.
파일 I/O나 비즈니스 로직은 수행하지 않는다.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel
)
from PySide6.QtCore import Qt

from core.app_state import AppState
from core.models import FileStatus


# 상태별 표시 텍스트
STATUS_DISPLAY = {
    FileStatus.PENDING: "⏳ 대기",
    FileStatus.PROCESSING: "🔄 처리 중",
    FileStatus.SUCCESS: "✅ 성공",
    FileStatus.FAILED: "❌ 실패",
    FileStatus.SKIPPED: "⏭ 건너뜀",
}


class FileListPanel(QWidget):
    """파일 목록 테이블 패널"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = AppState.instance()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── 헤더 영역 ───────────────────────────────────
        header_layout = QHBoxLayout()

        self._file_count_label = QLabel("파일: 0개")
        self._file_count_label.setObjectName("fileCountLabel")

        self._btn_clear = QPushButton("전체 삭제")
        self._btn_clear.setObjectName("btnClear")
        self._btn_clear.clicked.connect(self._on_clear)

        self._btn_remove = QPushButton("선택 삭제")
        self._btn_remove.setObjectName("btnRemove")
        self._btn_remove.clicked.connect(self._on_remove_selected)

        header_layout.addWidget(self._file_count_label)
        header_layout.addStretch()
        header_layout.addWidget(self._btn_remove)
        header_layout.addWidget(self._btn_clear)

        # ── 테이블 ──────────────────────────────────────
        self._table = QTableWidget()
        self._table.setObjectName("fileTable")
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["파일명", "경로", "상태"])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )

        layout.addLayout(header_layout)
        layout.addWidget(self._table)

    def _connect_signals(self):
        """AppState 시그널 연결"""
        self._state.files_changed.connect(self.refresh_table)
        self._state.file_status_changed.connect(self._on_file_status_changed)

    # ── 테이블 갱신 ──────────────────────────────────────

    def refresh_table(self):
        """전체 테이블 새로고침"""
        files = self._state.get_files()
        self._table.setRowCount(len(files))

        for row, task in enumerate(files):
            self._table.setItem(row, 0, QTableWidgetItem(task.filename))
            self._table.setItem(row, 1, QTableWidgetItem(str(task.path.parent)))
            self._table.setItem(
                row, 2, QTableWidgetItem(STATUS_DISPLAY.get(task.status, ""))
            )

        self._file_count_label.setText(f"파일: {len(files)}개")

    def _on_file_status_changed(self, index: int, status_str: str):
        """개별 파일 상태 변경 시 해당 행만 업데이트"""
        try:
            status = FileStatus(status_str)
            display = STATUS_DISPLAY.get(status, status_str)
            self._table.setItem(index, 2, QTableWidgetItem(display))
        except (ValueError, IndexError):
            pass

    # ── 버튼 핸들러 ──────────────────────────────────────

    def _on_clear(self):
        """전체 삭제"""
        if not self._state.is_working():
            self._state.clear_files()

    def _on_remove_selected(self):
        """선택된 행 삭제 (역순으로 제거하여 인덱스 안전)"""
        if self._state.is_working():
            return
        rows = sorted(
            set(idx.row() for idx in self._table.selectedIndexes()),
            reverse=True,
        )
        for row in rows:
            self._state.remove_file(row)
