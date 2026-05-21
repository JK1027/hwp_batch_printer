# file: utils/file_utils.py
"""
파일/경로 유틸리티.
경로 정규화, 확장자 확인, 안전 파일명 생성 등.
"""

from pathlib import Path

from core.constants import SUPPORTED_EXTENSIONS


def is_hwp_file(path: Path) -> bool:
    """HWP/HWPX 파일 여부 확인"""
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def normalize_path(path_str: str) -> Path:
    """경로 정규화 (절대 경로로 변환)"""
    return Path(path_str).resolve()


def safe_filename(path: Path, suffix: str = ".pdf") -> str:
    """안전한 출력 파일명 생성 (확장자 교체)"""
    return path.with_suffix(suffix).name
