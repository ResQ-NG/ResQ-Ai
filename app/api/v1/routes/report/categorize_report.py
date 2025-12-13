from fastapi import APIRouter, Depends, HTTPException
from app.domain.schema.upload import AILightCategorizeRequest, AILightCategorizeResponse
from app.services.ai_processor import ResQAIProcessor
from app.infra.logger import main_logger

router = APIRouter()


def get_processor():
    return ResQAIProcessor()


@router.post("/light-categorize", response_model=AILightCategorizeResponse)
async def light_categorize_report(
    request: AILightCategorizeRequest,
    processor: ResQAIProcessor = Depends(get_processor),
):
    try:
        _ = await processor.categorize_report(request.title, request.description)

        return AILightCategorizeResponse(message="All tags has been pushed to stream")
    except Exception as e:
        main_logger.log(f"error performing light categorize on report: {e}", "ERROR")
        raise HTTPException(
            status_code=500, detail=f"Processing failed: {str(e)}"
        ) from e
