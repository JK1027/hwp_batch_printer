# file: ui/control_panel.py
"""
인쇄/PDF 변환 컨트롤 패널.
버튼과 옵션 UI만 담당하며, 비즈니스 로직은 수행하지 않는다.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox,
    QPushButton, QLabel, QSpinBox, QComboBox
)
from PySide6.QtCore import Signal

from core.constants import DEFAULT_COPIES, MAX_COPIES
from core.models import DuplexMode, NupMode


class ControlPanel(QWidget):
    """인쇄/PDF 변환 컨트롤 패널"""

    # ── Signals ──────────────────────────────────────────
    convert_pdf_clicked = Signal()    # PDF 변환 버튼 클릭
    print_clicked = Signal()         # 인쇄 버튼 클릭
    cancel_clicked = Signal()        # 취소 버튼 클릭

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화"""
        main_layout = QHBoxLayout(self)

        # ── 인쇄 옵션 그룹 ───────────────────────────────
        options_group = QGroupBox("인쇄 옵션")
        options_group.setObjectName("optionsGroup")
        options_layout = QVBoxLayout()

        # 매수
        copies_layout = QHBoxLayout()
        copies_layout.addWidget(QLabel("매수:"))
        self._spin_copies = QSpinBox()
        self._spin_copies.setObjectName("spinCopies")
        self._spin_copies.setRange(1, MAX_COPIES)
        self._spin_copies.setValue(DEFAULT_COPIES)
        copies_layout.addWidget(self._spin_copies)

        # 단면/양면
        duplex_layout = QHBoxLayout()
        duplex_layout.addWidget(QLabel("인쇄 면:"))
        self._combo_duplex = QComboBox()
        self._combo_duplex.setObjectName("comboDuplex")
        self._combo_duplex.addItem("단면", DuplexMode.SIMPLEX)
        self._combo_duplex.addItem("양면", DuplexMode.DUPLEX)
        duplex_layout.addWidget(self._combo_duplex)

        # 모아찍기
        nup_layout = QHBoxLayout()
        nup_layout.addWidget(QLabel("모아찍기:"))
        self._combo_nup = QComboBox()
        self._combo_nup.setObjectName("comboNup")
        self._combo_nup.addItem("없음 (1쪽)", NupMode.SINGLE)
        self._combo_nup.addItem("2쪽", NupMode.TWO)
        self._combo_nup.addItem("4쪽", NupMode.FOUR)
        nup_layout.addWidget(self._combo_nup)

        options_layout.addLayout(copies_layout)
        options_layout.addLayout(duplex_layout)
        options_layout.addLayout(nup_layout)
        options_group.setLayout(options_layout)

        # ── 액션 버튼 그룹 ───────────────────────────────
        buttons_group = QGroupBox("작업")
        buttons_group.setObjectName("buttonsGroup")
        buttons_layout = QVBoxLayout()

        self._btn_convert_pdf = QPushButton("📄 PDF 변환")
        self._btn_convert_pdf.setObjectName("btnConvertPdf")
        self._btn_convert_pdf.clicked.connect(self.convert_pdf_clicked.emit)

        self._btn_print = QPushButton("🖨 일괄 인쇄")
        self._btn_print.setObjectName("btnPrint")
        self._btn_print.clicked.connect(self.print_clicked.emit)

        self._btn_cancel = QPushButton("⛔ 취소")
        self._btn_cancel.setObjectName("btnCancel")
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.clicked.connect(self.cancel_clicked.emit)

        buttons_layout.addWidget(self._btn_convert_pdf)
        buttons_layout.addWidget(self._btn_print)
        buttons_layout.addWidget(self._btn_cancel)
        buttons_group.setLayout(buttons_layout)

        main_layout.addWidget(options_group, stretch=2)
        main_layout.addWidget(buttons_group, stretch=1)

    # ── 외부 접근 메서드 ─────────────────────────────────

    def get_copies(self) -> int:
        """설정된 매수 반환"""
        return self._spin_copies.value()

    def get_duplex_mode(self) -> DuplexMode:
        """설정된 단면/양면 모드 반환"""
        return self._combo_duplex.currentData()

    def get_nup_mode(self) -> NupMode:
        """설정된 모아찍기 모드 반환"""
        return self._combo_nup.currentData()

    def set_working(self, is_working: bool):
        """작업 중 상태에 따른 UI 토글"""
        self._btn_convert_pdf.setEnabled(not is_working)
        self._btn_print.setEnabled(not is_working)
        self._btn_cancel.setEnabled(is_working)
        self._spin_copies.setEnabled(not is_working)
        self._combo_duplex.setEnabled(not is_working)
        self._combo_nup.setEnabled(not is_working)
