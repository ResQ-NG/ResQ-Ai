from fastapi import APIRouter, UploadFile, File, HTTPException
from app.modules.s3 import S3Client
from app.services.ai import ResQAIMediaProcessor


router = APIRouter()
from pydantic import BaseModel

class MediaRequest(BaseModel):
    file_key: str
    file_type: str

@router.post("/process-report-media/")
async def process_media(request: MediaRequest):
    try:
        file_path = await S3Client().download_s3_file_async(bucket="resq-files", key=request.file_key)
        result = await ResQAIMediaProcessor().process_media(file_path, request.file_type)

        # Return the processed result
        return {
            "status": "success",
            "result": result
        }

        # return something later
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
