from fastapi import APIRouter, UploadFile, File, HTTPException
from app.modules.s3 import S3Client
from app.services.ai import ResQAIMediaProcessor


router = APIRouter()

@router.post("/process/")
async def process_media(file_key: str):
    try:

        file_path = await S3Client().download_s3_file_async(bucket="resq-files", key=file_key)

        result = await ResQAIMediaProcessor().process_media(file_path, media_type)
        # Return the processed result
        return {
            "status": "success",
            "result": result
        }

        # return something later
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
