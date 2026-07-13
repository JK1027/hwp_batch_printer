# file: services/pdf_service.py
"""
PDF 변환 서비스.
HWP COM의 SaveAs(PDF)를 사용한다.
안전 저장: temp.pdf → 확인 → rename.
출력 폴더: 원본폴더/PDF_OUTPUT/
순차 처리만 허용. 병렬 변환 금지.
"""

import time
import tempfile
from pathlib import Path
from typing import Optional

from core.models import FileTask
from core.constants import PDF_OUTPUT_DIR_NAME
from services.hwp_service import HwpService
from services.log_service import LogService


class PdfService:
    """PDF 변환 서비스"""

    # HWP SaveAs 포맷 상수 (PDF)
    HWP_SAVE_FORMAT_PDF = "PDF"

    def __init__(self, hwp_service: HwpService,
                 log_service: Optional[LogService] = None):
        self._hwp = hwp_service
        self._log = log_service

    def convert_to_pdf(self, hwp_instance, file_task: FileTask) -> bool:
        """
        HWP 파일을 PDF로 변환한다.
        안전 저장 방식 (temp → 확인 → rename) 사용.

        Args:
            hwp_instance: 이미 생성된 HWP COM 인스턴스
            file_task: 변환할 파일 작업

        Returns:
            성공 여부
        """
        start_time = time.time()
        source_path = file_task.path
        
        # 출력 디렉토리 결정 (relative_dir 반영)
        if file_task.output_dir:
            output_dir = file_task.output_dir
            if file_task.relative_dir:
                output_dir = output_dir / file_task.relative_dir
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = self.ensure_output_dir(source_path)
            
        output_path = output_dir / source_path.with_suffix(".pdf").name

        try:
            # 2. 문서 열기
            if not self._hwp.open_document(hwp_instance, source_path):
                raise RuntimeError(f"문서 열기 실패: {source_path.name}")

            # 3. temp 파일로 PDF 저장 (Safe Save)
            temp_path = output_path.with_suffix(".tmp.pdf")

            try:
                try:
                    # 1차 시도: 3개 인자 전달 (Format, Arg 포함) - Early-Binding 및 최신 한글 대응
                    hwp_instance.SaveAs(
                        str(temp_path),
                        self.HWP_SAVE_FORMAT_PDF,
                        ""
                    )
                except (TypeError, Exception) as inner_err:
                    # 매개변수 개수 부족 또는 COM 오류(-2147352562)인 경우 2개 인자로 폴백 시도
                    is_param_err = False
                    if isinstance(inner_err, TypeError):
                        is_param_err = True
                    else:
                        hresult = getattr(inner_err, "hresult", None)
                        if hresult == -2147352562 or "2147352562" in str(inner_err):
                            is_param_err = True
                    
                    if is_param_err:
                        hwp_instance.SaveAs(
                            str(temp_path),
                            self.HWP_SAVE_FORMAT_PDF
                        )
                    else:
                        raise
            except Exception as e:
                raise RuntimeError(f"PDF 저장 실패 (경로: {source_path}): {e}") from e

            # 4. temp 파일 검증
            if not temp_path.exists() or temp_path.stat().st_size == 0:
                if temp_path.exists():
                    temp_path.unlink()
                raise RuntimeError("PDF 파일 생성 검증 실패 (빈 파일)")

            # 5. 최종 rename (기존 파일이 있으면 덮어쓰기)
            if output_path.exists():
                output_path.unlink()
            temp_path.rename(output_path)

            # 6. 문서 닫기
            self._hwp.close_document(hwp_instance)

            elapsed = time.time() - start_time
            if self._log:
                self._log.log_convert(
                    str(source_path), "SUCCESS", elapsed=elapsed
                )
            return True

        except Exception as e:
            elapsed = time.time() - start_time

            # 문서 닫기 시도
            try:
                self._hwp.close_document(hwp_instance)
            except Exception:
                pass

            # temp 파일 정리
            temp_path = output_path.with_suffix(".tmp.pdf")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

            if self._log:
                self._log.log_convert(
                    str(source_path), "FAILED",
                    error=str(e), elapsed=elapsed
                )
                self._log.log_error(
                    f"PDF 변환 실패 (경로: {source_path})", exc=e
                )
            return False

    def get_output_path(self, source_path: Path) -> Path:
        """PDF 출력 경로 계산"""
        output_dir = source_path.parent / PDF_OUTPUT_DIR_NAME
        return output_dir / source_path.with_suffix(".pdf").name

    def ensure_output_dir(self, source_path: Path) -> Path:
        """출력 디렉토리 생성 (없으면 자동 생성)"""
        output_dir = source_path.parent / PDF_OUTPUT_DIR_NAME
        output_dir.mkdir(exist_ok=True)
        return output_dir
