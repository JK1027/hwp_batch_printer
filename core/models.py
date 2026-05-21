# file: core/models.py
"""
데이터 모델 정의.
Pydantic 사용 금지 — dataclass 우선 사용 원칙.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List


# ── 상태 열거형 ─────────────────────────────────────────

class FileStatus(str, Enum):
    """개별 파일의 처리 상태"""
    PENDING = "pending"          # 대기 중
    PROCESSING = "processing"    # 처리 중
    SUCCESS = "success"          # 성공
    FAILED = "failed"            # 실패
    SKIPPED = "skipped"          # 건너뜀


class JobStatus(str, Enum):
    """전체 작업의 상태"""
    IDLE = "idle"                # 유휴
    CONVERTING = "converting"    # PDF 변환 중
    PRINTING = "printing"        # 인쇄 중
    CANCELLING = "cancelling"    # 취소 중


class DuplexMode(str, Enum):
    """단면/양면 인쇄 모드"""
    SIMPLEX = "simplex"          # 단면
    DUPLEX = "duplex"            # 양면


class NupMode(int, Enum):
    """모아찍기 모드"""
    SINGLE = 1                   # 1쪽
    TWO = 2                      # 2쪽 모아찍기
    FOUR = 4                     # 4쪽 모아찍기


# ── 데이터 클래스 ───────────────────────────────────────

@dataclass
class FileTask:
    """파일 작업 단위"""
    path: Path                                # 원본 파일 경로
    filename: str = ""                        # 표시용 파일명
    status: FileStatus = FileStatus.PENDING   # 처리 상태
    error_message: str = ""                   # 실패 시 에러 메시지

    def __post_init__(self):
        if not self.filename:
            self.filename = self.path.name


@dataclass
class PrintOptions:
    """인쇄 옵션"""
    copies: int = 1                                 # 인쇄 매수
    duplex: DuplexMode = DuplexMode.SIMPLEX         # 단면/양면
    nup: NupMode = NupMode.SINGLE                   # 모아찍기
    printer_name: str = ""                           # 프린터 이름 (빈 값 = 기본 프린터)


@dataclass
class JobResult:
    """작업 결과 요약"""
    total: int = 0
    success: int = 0
    failed: int = 0
    failed_files: List[str] = field(default_factory=list)
