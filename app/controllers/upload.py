from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ai import ResQAIMediaProcessor


router = APIRouter()

@router.post("/process/")
async def process_media(file: UploadFile = File(...)):
    try:
        media_type = file.content_type
        result = await ResQAIMediaProcessor().process_media(file, media_type)
        print(result)
        # return something later
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
