from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from app.domain.schema.upload import AILightCategorizeRequest, AILightCategorizeResponse
from app.services.ai_categorizer import ResQAICategorizer
from app.infra.logger import main_logger

router = APIRouter()


def get_categorizer(request: Request):
    """Dependency to get categorizer with injected Redis cache and stream."""
    redis_cache = request.app.state.redis_cache
    redis_stream = getattr(request.app.state, "redis_stream", None)
    return ResQAICategorizer(cache=redis_cache, stream=redis_stream)


async def process_categorization(categorizer: ResQAICategorizer, title: str, description: str, report_id: str, category_key: str = "categories:tree"):
    try:
        categories = await categorizer.categorize_report(title, description, category_key, report_id=report_id)
        main_logger.log(f"Categorization complete. Found {len(categories)} categories", "INFO")
        return categories
    except Exception as e:
        main_logger.log(f"error performing background light categorize on report: {e}", "ERROR")
        raise


@router.post("/light-categorize", response_model=AILightCategorizeResponse)
async def light_categorize_report(
    req_body: AILightCategorizeRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    try:
        # Get categorizer with injected dependencies
        categorizer = get_categorizer(request)

        # Schedule background categorization task and return immediately
        background_tasks.add_task(
            process_categorization,
            categorizer,
            req_body.title,
            req_body.description,
            req_body.report_id,
            req_body.cache_key
        )
        return AILightCategorizeResponse(message="Categorization started. Results will be pushed to stream")
    except Exception as e:
        main_logger.log(f"error scheduling light categorize on report: {e}", "ERROR")
        raise HTTPException(
            status_code=500, detail=f"Processing failed: {str(e)}"
        ) from e
