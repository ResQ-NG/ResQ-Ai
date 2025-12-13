from fastapi import APIRouter, HTTPException, Depends
from app.domain.schema.upload import (
    AIResponseLightSummarizationRequest,
    AIResponseLightSummarizationResponse,
)
from app.infra.logger import main_logger
from app.services.ai_processor import ResQAIProcessor

router = APIRouter()


def get_processor():
    return ResQAIProcessor()


@router.post("/light-summarize", response_model=AIResponseLightSummarizationResponse)
async def summarize_report_text_content(
    request: AIResponseLightSummarizationRequest,
    processor: ResQAIProcessor = Depends(get_processor),
):
    try:
        result = await processor.process_report_tags(
            request.tags, request.extra_description
        )
        return AIResponseLightSummarizationResponse(
            title=result.get("title", "Untitled"),
            description=result.get("description", ""),
        )
    except Exception as e:
        main_logger.log(f"error processing text content: {e}", "ERROR")
        raise HTTPException(
            status_code=500, detail=f"Processing failed: {str(e)}"
        ) from e
