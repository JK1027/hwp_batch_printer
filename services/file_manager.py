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

    def discover_hwp_files(self, paths: List[str]) -> List[Path]:
        """
        입력 경로 목록을 가공하여 모든 HWP/HWPX 파일을 탐색하고 정렬된 리스트로 반환한다.
        폴더 경로의 경우 하위 디렉토리를 재귀 검색하며, 숨김 폴더/파일(.으로 시작) 및 __pycache__ 등은 건너뛴다.
        """
        discovered = []
        for p in paths:
            path = Path(p)
            if path.is_dir():
                discovered.extend(self._scan_directory_recursively(path))
            elif path.is_file():
                if self.validate_file(path):
                    discovered.append(path)
        # 문자열 사전순 정렬
        return sorted(discovered, key=lambda x: str(x).lower())

    def _scan_directory_recursively(self, directory: Path) -> List[Path]:
        """숨김 폴더 및 특정 개발/임시 폴더를 제외하고 한글 파일을 재귀 수집"""
        result = []
        ignored_names = {".git", ".vscode", "__pycache__", "node_modules", "venv", ".idea"}
        
        try:
            stack = [directory]
            while stack:
                curr = stack.pop()
                try:
                    for entry in curr.iterdir():
                        if entry.name.startswith(".") or entry.name in ignored_names:
                            continue
                        if entry.is_dir():
                            stack.append(entry)
                        elif entry.is_file():
                            if entry.suffix.lower() in SUPPORTED_EXTENSIONS:
                                result.append(entry)
                except PermissionError:
                    continue  # 권한 부족한 경로는 스킵
        except Exception:
            pass
            
        return result
