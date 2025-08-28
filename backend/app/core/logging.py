"""Logging configuration using structlog."""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from .config import settings


def setup_logging() -> None:
    """Configure structured logging."""

    # Configure Python logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


class LoggerAdapter:
    """Adapter to add context to all log messages."""

    def __init__(self, logger: structlog.BoundLogger, **kwargs: Any):
        self.logger = logger
        self.context = kwargs

    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """Add context that will be included in all log messages."""
        return LoggerAdapter(self.logger, **{**self.context, **kwargs})

    def _log(self, level: str, event: str, **kwargs: Any) -> None:
        getattr(self.logger, level)(event, **{**self.context, **kwargs})

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log("debug", event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log("info", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log("warning", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log("error", event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        self._log("exception", event, **kwargs)
