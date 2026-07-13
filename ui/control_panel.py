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
    convert_folder_pdf_clicked = Signal()  # 폴더 전체 PDF 변환 버튼 클릭
    gather_pdf_clicked = Signal()     # PDF 모으기 버튼 클릭
    print_clicked = Signal()         # 인쇄 버튼 클릭
    cancel_clicked = Signal()        # 취소 버튼 클릭
    reset_clicked = Signal()         # 초기화 버튼 클릭

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

        # 안내 가이드 라벨 추가
        self._lbl_guide = QLabel("※ 인쇄 옵션은 '일괄 인쇄' 시에만 적용됩니다.")
        self._lbl_guide.setObjectName("lblOptionGuide")
        self._lbl_guide.setStyleSheet("color: #ef4444; font-size: 11px; margin-top: 4px;")
        options_layout.addWidget(self._lbl_guide)

        options_group.setLayout(options_layout)

        # ── 액션 버튼 그룹 ───────────────────────────────
        buttons_group = QGroupBox("작업")
        buttons_group.setObjectName("buttonsGroup")
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(4)
        buttons_layout.setContentsMargins(6, 12, 6, 6)

        self._btn_convert_pdf = QPushButton("📄 PDF 변환")
        self._btn_convert_pdf.setObjectName("btnConvertPdf")
        self._btn_convert_pdf.clicked.connect(self.convert_pdf_clicked.emit)

        self._btn_convert_folder_pdf = QPushButton("📁 폴더 전체 pdf변환")
        self._btn_convert_folder_pdf.setObjectName("btnConvertFolderPdf")
        self._btn_convert_folder_pdf.clicked.connect(self.convert_folder_pdf_clicked.emit)

        self._btn_gather_pdf = QPushButton("📂 PDF 모으기")
        self._btn_gather_pdf.setObjectName("btnGatherPdf")
        self._btn_gather_pdf.clicked.connect(self.gather_pdf_clicked.emit)

        self._btn_print = QPushButton("🖨 일괄 인쇄")
        self._btn_print.setObjectName("btnPrint")
        self._btn_print.clicked.connect(self.print_clicked.emit)

        self._btn_reset = QPushButton("🧹 초기화")
        self._btn_reset.setObjectName("btnReset")
        self._btn_reset.clicked.connect(self.reset_clicked.emit)

        self._btn_cancel = QPushButton("⛔ 취소")
        self._btn_cancel.setObjectName("btnCancel")
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.clicked.connect(self.cancel_clicked.emit)

        buttons_layout.addWidget(self._btn_convert_pdf)
        buttons_layout.addWidget(self._btn_convert_folder_pdf)
        buttons_layout.addWidget(self._btn_gather_pdf)
        buttons_layout.addWidget(self._btn_print)
        buttons_layout.addWidget(self._btn_reset)
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

    def reset_settings(self):
        """인쇄 설정 값을 기본값으로 리셋"""
        self._spin_copies.setValue(DEFAULT_COPIES)
        self._combo_duplex.setCurrentIndex(0)
        self._combo_nup.setCurrentIndex(0)

    def sync_button_states(self, has_files: bool, is_working: bool):
        """파일 존재 여부 및 작업 진행 상태에 맞춰 버튼들을 동기화"""
        self._btn_convert_pdf.setEnabled(has_files and not is_working)
        self._btn_convert_folder_pdf.setEnabled(not is_working)
        self._btn_gather_pdf.setEnabled(not is_working)
        self._btn_print.setEnabled(has_files and not is_working)
        self._btn_reset.setEnabled(not is_working)
        self._btn_cancel.setEnabled(is_working)
        self._spin_copies.setEnabled(not is_working)
        self._combo_duplex.setEnabled(not is_working)
        self._combo_nup.setEnabled(not is_working)
