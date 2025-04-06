from app.utils.constants import MediaTypes

def get_file_type(file_mime_type: str) -> str:
    """
    Determine the type of file based on its MIME type.

    :param file_mime_type: The MIME type of the file.
    :return: The type of the file (e.g., 'image', 'video', 'text', 'audio') or 'unknown' if the type is not recognized.
    """
    for media_type, mime_types in MediaTypes.items():
        if file_mime_type in mime_types:
            return media_type
    return "unknown"
