from typing import Protocol


class S3Interface(Protocol):
    """
    Protocol for S3 client classes. Ensures all S3 clients implement these methods.
    """

    def _download_s3_file(self, bucket: str, key: str, fileExt: str) -> str:
        """
        Downloads a file from an S3 bucket synchronously.

        Args:
            bucket (str): Name of the S3 bucket.
            key (str): Object key in S3.
            fileExt (str): File extension to use for the temporary file.

        Returns:
            str: Path to the downloaded temporary file.

        Raises:
            RuntimeError: If download fails or other error occurs.
        """

    async def download_s3_file_async(self, bucket: str, key: str, fileType: str) -> str:
        """
        Downloads a file from S3 asynchronously using a threadpool.

        Args:
            bucket (str): S3 bucket name.
            key (str): Object key in S3.
            fileType (str): MIME type of the file to extract extension.

        Returns:
            str: Path to the downloaded temporary file.

        Raises:
            RuntimeError: If download fails or other error occurs.
        """

    def _extract_suffix_from_filetype(self, filetype: str) -> str:
        """
        Extract file extension from MIME type string.

        Args:
            filetype (str): MIME type, e.g., "image/jpeg".

        Returns:
            str: File extension including dot, e.g., ".jpeg". Returns empty string if not parsable.
        """
