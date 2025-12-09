
import logging
import json
from typing import Optional
from contextvars import ContextVar  # ← Add this

# ✅ Context variable for async-safe correlation ID storage
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class LoggerStatus:
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


LEVEL_MAP = {
    LoggerStatus.SUCCESS: logging.INFO,
    LoggerStatus.ERROR: logging.ERROR,
    LoggerStatus.WARNING: logging.WARNING,
    LoggerStatus.INFO: logging.INFO,
    LoggerStatus.DEBUG: logging.DEBUG,
}


class StructuredLogger:
    def __init__(self, name: str = "main", level: str = "DEBUG"):
        self.logger = logging.getLogger(name)
        self.set_level(level)

        # Only add handler if no handlers exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.propagate = False

    def set_level(self, level: str):
        numeric_level = getattr(logging, level.upper(), logging.DEBUG)
        self.logger.setLevel(numeric_level)

    def set_correlated_id(self, correlated_id: str):
        """Set correlation ID in async-safe context."""
        correlation_id_ctx.set(correlated_id)  # ✅ Thread-safe!

    def get_correlated_id(self) -> Optional[str]:
        """Get correlation ID from context."""
        return correlation_id_ctx.get()

    def clear_correlated_id(self):
        """Clear correlation ID from context."""
        correlation_id_ctx.set(None)

    def log(self, message: str, status: str = LoggerStatus.INFO, **kwargs):
        structured = {
            "status": status,
            "message": message,
        }

        # ✅ Get from context variable instead of instance variable
        correlated_id = correlation_id_ctx.get()
        if correlated_id:
            structured["correlated_id"] = correlated_id

        if kwargs:
            structured.update(kwargs)

        log_func = self.logger.log
        level = LEVEL_MAP.get(status, logging.INFO)
        log_func(level, json.dumps(structured))


# The main structured logger instance
main_logger = StructuredLogger(level="DEBUG")
