from enum import Enum


class MediaTypes(Enum):
    IMAGE = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/tiff",
        "image/bmp",
    ]
    VIDEO = [
        "video/mp4",
        "video/mpeg",
        "video/quicktime",
        "video/x-msvideo",
        "video/webm",
    ]
    TEXT = [
        "text/plain",
        "text/html",
        "text/csv",
        "text/markdown",
        "application/json",
        "application/xml",
    ]
    AUDIO = [
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "audio/webm",
        "audio/aac",
        "audio/flac",
    ]
