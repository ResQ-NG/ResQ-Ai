"""
Custom exception hierarchy for ResQ AI Application, with integrated logging.
"""

from app.infra.logger import main_logger, LoggerStatus


def log_exception(cls, message, details=None):
    log_details = details if details else {}
    main_logger.log(
        message=f"{cls.__name__}: {message}",
        status=LoggerStatus.ERROR,
        **({"details": log_details} if log_details else {}),
    )


class ResQAIException(Exception):
    """Base exception for all ResQ AI errors, with logging."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        log_exception(self.__class__, message, self.details)
        super().__init__(self.message)


class DomainException(ResQAIException):
    """Base for domain-level exception"""

    pass


class ValidationError(DomainException):
    """Data validation errors."""

    pass


class UnsupportedMediaTypeError(DomainException):
    """Unsupported media type."""

    pass


# Infrastructure exceptions
class InfrastructureException(ResQAIException):
    """Base for infrastructure-level errors."""

    pass


class StorageError(InfrastructureException):
    """Storage operation errors."""

    pass


class S3DownloadError(StorageError):
    """S3 download failed."""

    pass


class S3UploadError(StorageError):
    """S3 upload failed."""

    pass


class AIProcessingError(InfrastructureException):
    """AI model processing errors."""

    pass


class DatabaseError(InfrastructureException):
    """Database operation errors."""

    pass


class CacheError(InfrastructureException):
    """Cache operation errors."""

    pass


# Service exceptions
class ServiceException(ResQAIException):
    """Base for service-level errors."""

    pass


class MediaProcessingError(ServiceException):
    """Media processing failed."""

    pass
