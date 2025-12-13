import logging
import json
import os
from typing import Optional
from contextvars import ContextVar
from datetime import datetime


# Context variable for async-safe correlation ID storage
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar[str | None](
    "correlation_id", default=None
)


class LoggerStatus:
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


LEVEL_MAP = {
    LoggerStatus.SUCCESS: logging.INFO,
    LoggerStatus.ERROR: logging.ERROR,
    LoggerStatus.WARNING: logging.WARNING,
    LoggerStatus.INFO: logging.INFO,
    LoggerStatus.DEBUG: logging.DEBUG,
}


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for human-readable terminal output.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[34m",  # Blue
        "SUCCESS": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[31;1m",  # Bold Red
        "RESET": "\033[0m",  # Reset
        "BOLD": "\033[1m",  # Bold
        "DIM": "\033[2m",  # Dim
    }

    def format(self, record):
        # Get color for level
        level_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        dim = self.COLORS["DIM"]
        bold = self.COLORS["BOLD"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]

        # Get correlation ID from record
        correlation_id = getattr(record, "correlation_id", None)

        # Build formatted message
        parts = [
            f"{dim}{timestamp}{reset}",
            f"{level_color}{record.levelname:8}{reset}",
        ]

        # Always show correlation ID for SUCCESS and WARNING if present
        if correlation_id and record.levelname in (
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ):
            parts.append(f"{dim}[{correlation_id}]{reset}")
        # For DEBUG/INFO, only show if present - keep as before
        elif correlation_id and record.levelname in ("DEBUG", "INFO"):
            parts.append(f"{dim}[{correlation_id}]{reset}")

        parts.append(f"{bold}{record.getMessage()}{reset}")

        # Add extra fields if present
        if hasattr(record, "extra_fields") and record.extra_fields:
            extra_str = " ".join(
                f"{dim}{k}={v}{reset}" for k, v in record.extra_fields.items()
            )
            parts.append(extra_str)

        return " │ ".join(parts)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging (production).
    """

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Always include correlation ID if present, notably for any level
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class StructuredLogger:
    def __init__(
        self, name: str = "resq-ai", level: str = "DEBUG", use_json: bool = None
    ):
        self.logger = logging.getLogger(name)
        self.set_level(level)

        # Auto-detect environment if not specified
        if use_json is None:
            env = os.getenv("APP_ENV", "development").lower()
            use_json = env in ["production", "prod", "staging"]

        self.use_json = use_json

        # Only add handler if no handlers exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()

            # Choose formatter based on environment
            if use_json:
                formatter = JSONFormatter()
            else:
                formatter = ColoredFormatter()

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.propagate = False

    def set_level(self, level: str):
        numeric_level = getattr(logging, level.upper(), logging.DEBUG)
        self.logger.setLevel(numeric_level)

    def set_correlated_id(self, correlated_id: str):
        """Set correlation ID in async-safe context."""
        correlation_id_ctx.set(correlated_id)

    def get_correlated_id(self) -> Optional[str]:
        """Get correlation ID from context."""
        return correlation_id_ctx.get()

    def clear_correlated_id(self):
        """Clear correlation ID from context."""
        correlation_id_ctx.set(None)

    def log(self, message: str, status: str = LoggerStatus.INFO, **kwargs):
        """
        Log a message with optional extra fields.

        Args:
            message: Log message
            status: Log status (SUCCESS, ERROR, WARNING, INFO, DEBUG)
            **kwargs: Additional fields to include in log
        """
        level = LEVEL_MAP.get(status, logging.INFO)

        # Get correlation ID
        correlation_id = correlation_id_ctx.get()

        # Always attach correlation ID for SUCCESS and WARNING (and ERROR); for others, if present.
        extra = {"correlation_id": correlation_id, "extra_fields": kwargs}

        self.logger.log(level, message, extra=extra)

    # Convenience methods
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.log(message, LoggerStatus.DEBUG, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log(message, LoggerStatus.INFO, **kwargs)

    def success(self, message: str, **kwargs):
        """Log success message. Always includes correlation id if set."""
        self.log(message, LoggerStatus.SUCCESS, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message. Always includes correlation id if set."""
        self.log(message, LoggerStatus.WARNING, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message with optional exception info."""
        level = LEVEL_MAP.get(LoggerStatus.ERROR, logging.ERROR)

        extra = {"correlation_id": correlation_id_ctx.get(), "extra_fields": kwargs}

        self.logger.log(level, message, exc_info=exc_info, extra=extra)


# Create singleton instance
main_logger = StructuredLogger(level="DEBUG")
