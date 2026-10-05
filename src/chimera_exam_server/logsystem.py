"""Application logging configuration."""

from __future__ import annotations

import logging
import os
import platform
import socket
import sys
from pathlib import Path
from types import TracebackType

from loguru import logger as _logger


logger = _logger
__all__ = ["configure_logging", "logger", "log_startup_info"]


LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level: <8}</level> | "
    "request={extra[request_id]} client={extra[client]} | "
    "{extra[source]} - {message}"
)
DEFAULT_LOG_DIR = Path(__file__).resolve().parent / "logs"


def _add_source(record: dict) -> None:
    if record["extra"].get("source") == "-":
        record["extra"]["source"] = record["name"]


class InterceptHandler(logging.Handler):
    """Forward standard-library records, including Uvicorn, to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        if (
            record.name == "uvicorn.error"
            and record.getMessage() == "Exception in ASGI application"
        ):
            return

        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.bind(source=record.name).opt(
            depth=depth,
            exception=record.exc_info,
        ).log(level, record.getMessage())


def _log_directory() -> Path:
    configured = os.getenv("CHIMERA_LOG_DIR")
    return Path(configured).expanduser() if configured else DEFAULT_LOG_DIR


def configure_logging() -> Path:
    """Configure Loguru and return the active log file path."""
    log_level = os.getenv("CHIMERA_LOG_LEVEL", "INFO").upper()
    log_directory = _log_directory()
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / "chimera.log"

    logger.remove()
    logger.configure(
        extra={"request_id": "-", "client": "-", "source": "-"},
        patcher=_add_source,
    )
    logger.level("INFO", color="<green>")
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level=log_level,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        log_file,
        format=LOG_FORMAT,
        level=log_level,
        colorize=False,
        rotation=os.getenv("CHIMERA_LOG_ROTATION", "10 MB"),
        retention=os.getenv("CHIMERA_LOG_RETENTION", "14 days"),
        compression="gz",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        encoding="utf-8",
    )

    intercept_handler = InterceptHandler()
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        standard_logger = logging.getLogger(logger_name)
        standard_logger.handlers = [intercept_handler]
        standard_logger.propagate = False
    logging.getLogger("uvicorn.access").disabled = True

    sys.excepthook = handle_unhandled_exception
    return log_file


def handle_unhandled_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
        "Unhandled exception"
    )


def log_startup_info(log_file: Path) -> None:
    """Record useful operational facts without dumping private environment data."""
    logger.info(
        "Chimera server starting | host={host} platform={platform} python={python}",
        host=socket.gethostname(),
        platform=platform.platform(),
        python=platform.python_version(),
    )
    logger.info(
        "Logging configured | level={level} file={file}",
        level=os.getenv("CHIMERA_LOG_LEVEL", "INFO").upper(),
        file=log_file,
    )
