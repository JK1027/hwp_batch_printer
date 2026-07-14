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
from PySide6.QtGui import QColor, QBrush
from pathlib import Path

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

# 상태별 색상 (배경색, 텍스트색)
STATUS_COLORS = {
    FileStatus.PENDING: {
        "bg": "#ffffff",
        "fg": "#1f2937"
    },
    FileStatus.PROCESSING: {
        "bg": "#eff6ff",  # Light blue (Blue 50)
        "fg": "#1d4ed8"  # Blue 700
    },
    FileStatus.SUCCESS: {
        "bg": "#ecfdf5",  # Emerald 50
        "fg": "#047857"  # Emerald 700
    },
    FileStatus.FAILED: {
        "bg": "#fef2f2",  # Red 50
        "fg": "#b91c1c"  # Red 700
    },
    FileStatus.SKIPPED: {
        "bg": "#f3f4f6",  # Slate 100
        "fg": "#4b5563"  # Slate 600
    }
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
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["파일명", "경로", "상태", "관리"])
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
        self._table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )

        layout.addLayout(header_layout)
        layout.addWidget(self._table)

    def _connect_signals(self):
        """AppState 시그널 연결"""
        self._state.files_changed.connect(self.refresh_table)
        self._state.file_status_changed.connect(self._on_file_status_changed)
        self._table.cellClicked.connect(self._on_cell_clicked)

    # ── 테이블 갱신 ──────────────────────────────────────

    def _style_row(self, row: int, status: FileStatus):
        """행의 모든 셀에 상태에 맞는 스타일 적용"""
        colors = STATUS_COLORS.get(status, {"bg": "#ffffff", "fg": "#1f2937"})
        bg_color = QColor(colors["bg"])
        fg_color = QColor(colors["fg"])

        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                item.setBackground(QBrush(bg_color))
                item.setForeground(QBrush(fg_color))

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
            
            # 관리 열 (삭제 텍스트 아이콘)
            del_item = QTableWidgetItem("❌")
            del_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            del_item.setToolTip("대기열에서 삭제")
            self._table.setItem(row, 3, del_item)
            
            self._style_row(row, task.status)

        self._file_count_label.setText(f"파일: {len(files)}개")

    def _on_cell_clicked(self, row: int, col: int):
        """셀 클릭 핸들러 - 4번째 열(삭제) 클릭 처리"""
        if col == 3:  # 관리(삭제) 열
            if self._state.is_working():
                return
            
            name_item = self._table.item(row, 0)
            path_item = self._table.item(row, 1)
            if name_item and path_item:
                filename = name_item.text()
                parent_dir = path_item.text()
                full_path = Path(parent_dir) / filename
                self._state.remove_file_by_path(full_path)

    def _on_file_status_changed(self, index: int, status_str: str):
        """개별 파일 상태 변경 시 해당 행만 업데이트"""
        try:
            status = FileStatus(status_str)
            display = STATUS_DISPLAY.get(status, status_str)
            
            # 셀 항목이 없을 때 예외 방지를 위해 QTableWidgetItem 존재 유무 파악 후 설정
            item = self._table.item(index, 2)
            if item:
                item.setText(display)
            else:
                self._table.setItem(index, 2, QTableWidgetItem(display))
                
            self._style_row(index, status)
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
