import asyncio
import os
import tempfile
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi.concurrency import run_in_threadpool

class S3Client:
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=os.getenv('AWS_REGION'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        except NoCredentialsError:
            raise RuntimeError("AWS credentials not found. Please check your environment variables.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize S3 client: {str(e)}")

    def _download_s3_file(self, bucket: str, key: str) -> str:
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            self.s3_client.download_fileobj(bucket, key, tmp_file)
            tmp_file.close()
            return tmp_file.name
        except ClientError as e:
            raise RuntimeError(f"Failed to download file from S3: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {str(e)}")

    async def download_s3_file_async(self, bucket: str, key: str) -> str:
        try:
            return await run_in_threadpool(self._download_s3_file, bucket, key)
        except Exception as e:
            raise RuntimeError(f"Failed to download file asynchronously: {str(e)}")
