# file: core/constants.py
"""
애플리케이션 전역 상수 정의.
하드코딩 경로 금지 원칙에 따라 모든 설정값을 여기서 관리한다.
"""

from pathlib import Path


# ── 앱 정보 ──────────────────────────────────────────────
APP_NAME = "HWP Batch Printer"
APP_VERSION = "0.1.0"
APP_WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"

# ── 윈도우 기본 크기 ────────────────────────────────────
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 650
MIN_WINDOW_WIDTH = 700
MIN_WINDOW_HEIGHT = 500

# ── 지원 파일 확장자 ────────────────────────────────────
SUPPORTED_EXTENSIONS = {".hwp", ".hwpx"}

# ── 출력 폴더 이름 ──────────────────────────────────────
PDF_OUTPUT_DIR_NAME = "PDF_OUTPUT"

# ── 로그 디렉토리 ───────────────────────────────────────
LOG_DIR_NAME = "logs"
LOG_FILES = {
    "app": "app.log",
    "convert": "convert.log",
    "print": "print.log",
    "error": "error.log",
}

# ── HWP COM ─────────────────────────────────────────────
HWP_COM_PROG_ID = "HWPFrame.HwpObject"

# ── 기본 인쇄 설정 ──────────────────────────────────────
DEFAULT_COPIES = 1
MAX_COPIES = 999

# ── UI 스레드 안전 임계값 (ms) ──────────────────────────
UI_BLOCKING_THRESHOLD_MS = 500
