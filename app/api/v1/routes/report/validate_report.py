from fastapi import APIRouter, BackgroundTasks, Request, HTTPException

from app.domain.schema.validate import (
    AIPredictiveValidationRequest,
    AIPredictiveValidationResponse,
)
from app.infra.logger import main_logger
from app.services.ai_validator import ResQAIValidator


router = APIRouter()


def get_validator(request: Request):
    """
    Dependency to get validator with injected dependencies.
    """
    redis_stream = getattr(request.app.state, "redis_stream", None)
    return ResQAIValidator(stream=redis_stream)


async def process_validation(
    validator: ResQAIValidator,
    req_body: AIPredictiveValidationRequest,
    correlated_id: str = None,
):
    """
    Background task to process validation and stream results.

    Args:
        validator: The validator instance
        req_body: The validation request body
        correlated_id: Optional correlation ID for logging/tracing
    """
    try:
        # Set correlation ID in logger for background task
        if correlated_id and hasattr(validator.logger, "set_correlated_id"):
            validator.logger.set_correlated_id(correlated_id)

        validation_result = await validator.validate_report(req_body, correlated_id=correlated_id)
        main_logger.log(
            f"Validation complete for report_id={req_body.report_id}. "
            f"Status: {validation_result.final_validity_status}, "
            f"Confidence: {validation_result.confidence_score}%",
            "INFO",
        )
        return validation_result
    except Exception as e:
        main_logger.log(
            f"error performing background validation on report_id={req_body.report_id}: {e}",
            "ERROR",
        )
        raise


@router.post("/predictive-validation", response_model=AIPredictiveValidationResponse)
async def predictive_validation_on_report(
    req_body: AIPredictiveValidationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """
    Endpoint to start predictive validation on a report.
    Validation runs in the background and results are streamed via Redis.
    """
    try:
        # Get validator with injected dependencies
        validator = get_validator(request)

        # Capture correlation ID - try request.state first (set by middleware), fallback to main_logger
        correlated_id = getattr(request.state, "correlation_id", None)
        if not correlated_id and hasattr(main_logger, "get_correlated_id"):
            correlated_id = main_logger.get_correlated_id()

        # Ensure it's also in request.state if we got it from logger
        if correlated_id and not hasattr(request.state, "correlation_id"):
            request.state.correlation_id = correlated_id

        # Schedule background validation task and return immediately
        background_tasks.add_task(
            process_validation,
            validator,
            req_body,
            correlated_id,
        )

        return AIPredictiveValidationResponse(
            message="Validation started. Results will be pushed to stream."
        )
    except Exception as e:
        main_logger.log(f"error scheduling validation on report: {e}", "ERROR")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}") from e
