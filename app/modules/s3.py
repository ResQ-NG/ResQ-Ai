"""
this is this module for general file processing on """
from typing import Protocol
import tempfile
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi.concurrency import run_in_threadpool


from app.utils.config import config

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


class S3Client:
    """
    Concrete implementation of S3Interface for interacting with AWS S3.

    Example:
        s3 = S3Client()
        file_path = await s3.download_s3_file_async("bucket", "object-key", "image/png")
    """
    def __init__(self):
        """
        Initializes the S3 client using credentials and region from config.

        Raises:
            RuntimeError: If credentials or S3 client initialization fails.
        """
        try:
            self.s3_client = boto3.client(
                "s3",
                region_name=config.AWS_REGION,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            )
        except NoCredentialsError as exc:
            raise RuntimeError(
                "AWS credentials not found. Please check your environment variables."
            ) from exc
        except Exception as e:
            raise RuntimeError(f"Failed to initialize S3 client: {str(e)}") from e

    def _download_s3_file(self, bucket: str, key: str, fileExt: str) -> str:
        """
        Downloads an object from S3 and saves it as a temporary file.

        Args:
            bucket (str): S3 bucket name.
            key (str): Object key.
            fileExt (str): File extension (including dot).

        Returns:
            str: Path to downloaded file.

        Raises:
            RuntimeError: If the download fails.
        """
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=fileExt)
            self.s3_client.download_fileobj(bucket, key, tmp_file)
            tmp_file_path = tmp_file.name
            tmp_file.close()
            return tmp_file_path
        except ClientError as e:
            raise RuntimeError(f"Failed to download file from S3: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {str(e)}") from e

    async def download_s3_file_async(self, bucket: str, key: str, fileType: str) -> str:
        """
        Asynchronously downloads an object from S3 and saves it as a temp file.

        Args:
            bucket (str): S3 bucket name.
            key (str): Object key.
            fileType (str): MIME type, like "image/png".

        Returns:
            str: Path to the downloaded temp file.

        Raises:
            RuntimeError: If the download fails.
        """
        try:
            fileExt = self._extract_suffix_from_filetype(fileType)
            return await run_in_threadpool(self._download_s3_file, bucket, key, fileExt)
        except Exception as e:
            raise RuntimeError(f"Failed to download file asynchronously: {str(e)}") from e

    def _extract_suffix_from_filetype(self, filetype: str) -> str:
        """
        Extract file extension from a MIME type string.

        Args:
            filetype (str): Input MIME type (e.g., "image/jpeg").

        Returns:
            str: File extension with dot (e.g., ".jpeg"), or empty string if format not recognized.
        """
        if not filetype or "/" not in filetype:
            return ""
        split_file = filetype.split("/")
        if len(split_file) < 2:
            return ""
        return f".{split_file[1]}"
