import os

from fastapi import APIRouter, HTTPException
from app.modules.s3 import S3Client
from app.schema.upload import AIResponse, Detection, MediaRequest, Metadata, ProcessTextContentRequest, Summary
from app.services.ai import ResQAIMediaProcessor
from app.utils.logger import main_logger, Status

router = APIRouter()




@router.post("/process-report-media/", response_model=AIResponse)
async def process_media(request: MediaRequest):
    file_path = None
    try:
        file_path = await S3Client().download_s3_file_async(
            bucket=os.getenv("BUCKET_NAME"),
            key=request.file_key,
            fileType=request.file_type,
        )
        result = await ResQAIMediaProcessor().process_media(
            file_path, request.file_type
        )

        # Return structured response using the defined Pydantic model
        return AIResponse(
            status=result.get("status", "success"),
            metadata=Metadata(
                path=result.get("metadata", {}).get("path", ""),
                format=result.get("metadata", {}).get("format", ""),
                dimensions=result.get("metadata", {}).get("dimensions", ""),
                size_kb=result.get("metadata", {}).get("size_kb", 0.0),
            ),
            summary=Summary(
                detections=[
                    Detection(
                        class_=detection.get("class", ""),
                        confidence=detection.get("confidence", 0.0),
                        bbox=detection.get("bbox", [0.0, 0.0, 0.0, 0.0]),
                    )
                    for detection in result.get("summary", {}).get("detections", [])
                ],
                summary_text=result.get("summary", {}).get("summary_text", ""),
            ),
        )
    except Exception as e:
        main_logger(f"error processing media file {e}", Status.ERROR)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass



@router.post("/process-report-text-content/", response_model=AIResponse)
async def process_text_content(request: ProcessTextContentRequest):
    try:
        result = await ResQAIMediaProcessor().process_text(request.summary)

        # Return structured response using the defined Pydantic model
        return AIResponse(
            status=result.get("status", "success"),
            metadata=Metadata(
                path="",
                format="text",
                dimensions="",
                size_kb=0.0,
            ),
            summary=Summary(
                detections=[],
                summary_text=result.get("summary_text", ""),
            ),
        )
    except Exception as e:
        main_logger(f"error processing text content: {e}", Status.ERROR)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
