# file: services/pdf_gather_service.py
"""
PDF 모으기 서비스.
폴더 내부의 모든 PDF 파일을 찾아 대상 폴더로 복사하거나 이동한다.
이름 중복 시 _1, _2 등을 붙여 덮어쓰기를 방지한다.
"""

import shutil
from pathlib import Path
from typing import Callable, Tuple, Optional


class PdfGatherService:
    """PDF 파일 수집/복사/이동 서비스"""

    def gather_pdfs(self, src_dir: Path, dest_dir: Path, action: str,
                    progress_callback: Callable[[int, int, str, str], None],
                    cancel_check: Optional[Callable[[], bool]] = None) -> Tuple[int, int]:
        """
        src_dir 내의 모든 PDF 파일을 수집하여 dest_dir로 복사 또는 이동한다.
        
        Args:
            src_dir: 원본 검색 디렉토리
            dest_dir: 저장할 대상 디렉토리
            action: "copy" (복사) 또는 "move" (이동)
            progress_callback: 진척도를 전달할 콜백 함수 (현재, 전체, 원본파일명, 대상파일명)
            cancel_check: 취소 여부를 반환하는 콜백 함수 (선택 사항)
            
        Returns:
            (성공 수, 실패 수)
        """
        # 1. 대상 디렉토리 생성
        dest_dir.mkdir(parents=True, exist_ok=True)

        # 2. PDF 파일 목록 재귀 수집
        pdf_files = []
        for f in src_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() == ".pdf":
                # 목적지 폴더 내부의 파일은 검색 및 처리에서 제외하여 무한 루프/오류 방지
                if dest_dir in f.parents or f.parent == dest_dir:
                    continue
                pdf_files.append(f)

        total = len(pdf_files)
        success = 0
        failed = 0

        for i, file_path in enumerate(pdf_files):
            # 협조적 취소 체크
            if cancel_check and cancel_check():
                break

            try:
                dest_path = self._resolve_dest_path(dest_dir, file_path.name)
                progress_callback(i + 1, total, file_path.name, dest_path.name)

                if action == "copy":
                    shutil.copy2(file_path, dest_path)
                elif action == "move":
                    shutil.move(str(file_path), str(dest_path))
                success += 1
            except Exception:
                failed += 1

        return success, failed

    def _resolve_dest_path(self, dest_dir: Path, filename: str) -> Path:
        """이름 중복 방지를 위한 안전한 경로 계산"""
        base_path = dest_dir / filename
        if not base_path.exists():
            return base_path

        stem = base_path.stem
        suffix = base_path.suffix
        counter = 1

        while True:
            new_path = dest_dir / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
