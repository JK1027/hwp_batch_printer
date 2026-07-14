# file: ui/drop_zone.py
"""
드래그앤드롭 영역 위젯.
HWP/HWPX 파일을 드래그앤드롭으로 받아 AppState에 등록 요청한다.
이 위젯은 파일 검증 로직을 직접 수행하지 않는다.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from core.constants import SUPPORTED_EXTENSIONS


class DropZone(QFrame):
    """파일 드래그앤드롭 수신 영역"""

    # 드롭된 파일 경로 목록을 전달하는 시그널
    files_dropped = Signal(list)
    # 드롭존 클릭 시그널
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropZone")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel("여기에 파일을 놓거나 클릭하여 선택하세요.")
        self._label.setObjectName("dropZoneLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_label = QLabel("📂")
        self._icon_label.setObjectName("dropZoneIcon")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._icon_label)
        layout.addWidget(self._label)

        self.setMinimumHeight(150)

    def mousePressEvent(self, event):
        """마우스 클릭 이벤트 오버라이드"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    # ── 드래그앤드롭 이벤트 ──────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 진입 — 파일 URL이면 허용"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragOver", True)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """드래그 이탈"""
        self.setProperty("dragOver", False)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        """드롭 — 파일 경로 추출 후 시그널 발생"""
        self.setProperty("dragOver", False)
        self.style().polish(self)

        paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                paths.append(file_path)

        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()
