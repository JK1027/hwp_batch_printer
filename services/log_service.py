# file: services/log_service.py
"""
로그 기록 관리 서비스.
로그 분리 원칙: app.log / convert.log / print.log / error.log
필수 기록 항목: 파일명, 작업 시간, 작업 결과, 에러 메시지, traceback, 프린터 옵션
"""

import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.constants import LOG_DIR_NAME, LOG_FILES


class LogService:
    """
    로그 서비스.
    4개 분리 로거: app / convert / print / error
    """

    _instance: Optional["LogService"] = None

    @classmethod
    def instance(cls, base_dir: Optional[Path] = None) -> "LogService":
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls(base_dir or Path.cwd())
            cls._instance.setup_loggers()
        return cls._instance

    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._log_dir = base_dir / LOG_DIR_NAME
        self._loggers: dict[str, logging.Logger] = {}

    def setup_loggers(self) -> None:
        """로그 디렉토리 생성 및 로거 초기화"""
        self._log_dir.mkdir(exist_ok=True)

        # 공통 포맷
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        for key, filename in LOG_FILES.items():
            logger = logging.getLogger(f"hwp_batch_{key}")
            logger.setLevel(logging.DEBUG)

            # 기존 핸들러 제거 (중복 방지)
            logger.handlers.clear()

            # 파일 핸들러
            file_handler = logging.FileHandler(
                self._log_dir / filename,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            self._loggers[key] = logger

    def _get_logger(self, key: str) -> logging.Logger:
        """로거 반환 (없으면 기본 로거)"""
        return self._loggers.get(key, logging.getLogger(f"hwp_batch_{key}"))

    # ── app.log ──────────────────────────────────────────

    def log_app(self, message: str, level: str = "INFO") -> None:
        """앱 일반 로그"""
        logger = self._get_logger("app")
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

    # ── convert.log ──────────────────────────────────────

    def log_convert(self, filename: str, result: str,
                    error: str = "", elapsed: float = 0.0) -> None:
        """
        PDF 변환 로그.
        필수: 파일명, 작업 결과
        선택: 에러 메시지, 소요 시간
        """
        logger = self._get_logger("convert")
        msg = f"[{result}] {filename}"
        if elapsed > 0:
            msg += f" ({elapsed:.1f}s)"
        if error:
            msg += f" | ERROR: {error}"
        logger.info(msg)

    # ── print.log ────────────────────────────────────────

    def log_print(self, filename: str, result: str,
                  printer: str = "", options: str = "",
                  error: str = "", elapsed: float = 0.0) -> None:
        """
        인쇄 로그.
        필수: 파일명, 작업 결과
        선택: 프린터명, 옵션, 에러 메시지, 소요 시간
        """
        logger = self._get_logger("print")
        msg = f"[{result}] {filename}"
        if printer:
            msg += f" | printer={printer}"
        if options:
            msg += f" | options={options}"
        if elapsed > 0:
            msg += f" ({elapsed:.1f}s)"
        if error:
            msg += f" | ERROR: {error}"
        logger.info(msg)

    # ── error.log ────────────────────────────────────────

    def log_error(self, message: str, exc: Optional[Exception] = None) -> None:
        """
        에러 로그.
        traceback 자동 포함.
        """
        logger = self._get_logger("error")
        logger.error(message)
        if exc:
            tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
            logger.error("".join(tb))
