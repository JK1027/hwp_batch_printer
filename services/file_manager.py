# file: services/file_manager.py
"""
파일 등록/제거/검증 서비스.
원본 파일 수정 금지 원칙 준수.
"""

from pathlib import Path
from typing import List

from core.constants import SUPPORTED_EXTENSIONS
from core.models import FileTask


class FileManager:
    """파일 관리 서비스"""

    def validate_file(self, path: Path) -> bool:
        """파일이 유효한지 검증 (존재 여부 + 확장자)"""
        return path.exists() and path.suffix.lower() in SUPPORTED_EXTENSIONS

    def filter_hwp_files(self, paths: List[str]) -> List[Path]:
        """경로 목록에서 유효한 HWP/HWPX 파일만 필터링"""
        result = []
        for p in paths:
            path = Path(p)
            if self.validate_file(path):
                result.append(path)
        return result

    def check_duplicate(self, path: Path, existing: List[FileTask]) -> bool:
        """중복 파일 여부 확인"""
        existing_paths = {t.path for t in existing}
        return path in existing_paths
