from fastapi import APIRouter, BackgroundTasks, Request
from app.domain.schema.upload import EvidenceAnalysisRequest, EvidenceAnalysisResponse
from app.services.ai_processor import ResQAIProcessor
from app.infra.logger import main_logger

router = APIRouter()


def get_processor(request: Request):
    """Dependency to get processor with injected Redis stream and S3 client."""
    redis_stream = getattr(request.app.state, "redis_stream", None)
    s3_client = getattr(request.app.state, "s3_client", None)
    return ResQAIProcessor(stream=redis_stream, s3_client=s3_client)


async def process_evidence(
    processor: ResQAIProcessor,
    file_key: str,
    file_type: str,
    report_id: int,
    correlated_id: str = None,
):
    """Background task to process evidence."""
    try:
        await processor.analyze_evidence(
            file_key=file_key,
            file_type=file_type,
            report_id=report_id,
            correlated_id=correlated_id,
        )
        main_logger.log(f"Evidence analysis complete for: {file_key}", "INFO")
    except Exception as e:
        main_logger.log(f"Error in background evidence analysis: {e}", "ERROR")
        raise


@router.post("/analyze-evidence", response_model=EvidenceAnalysisResponse)
async def analyze_evidence(
    req_body: EvidenceAnalysisRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """
    Analyze evidence file from S3.

    Downloads the file from S3 using the provided file_key,
    routes to the appropriate processor based on file_type (MIME type),
    and pushes results to the Redis stream.

    This endpoint runs analysis in the background and returns immediately.

    Supported file types:
    - Images: image/jpeg, image/png, image/gif, image/webp, image/tiff, image/bmp
    - Videos: video/mp4, video/mpeg, video/quicktime, video/x-msvideo, video/webm
    - Audio: audio/mpeg, audio/wav, audio/ogg, audio/webm, audio/aac, audio/flac
    - Text: text/plain, text/html, text/csv, text/markdown, application/json, application/xml
    """
    # Get processor with injected stream
    processor = get_processor(request)

    # Get correlation ID from request state (set by middleware) or header
    correlated_id = getattr(request.state, "correlation_id", None)
    if not correlated_id:
        correlated_id = request.headers.get("X-Correlation-ID")

    main_logger.log(
        f"Evidence analysis request: file_key={req_body.file_key}, "
        f"type={req_body.file_type}, report_id={req_body.report_id}",
        "INFO",
    )

    # Schedule background analysis task
    background_tasks.add_task(
        process_evidence,
        processor,
        req_body.file_key,
        req_body.file_type,
        req_body.report_id,
        correlated_id,
    )

    return EvidenceAnalysisResponse(
        message="Evidence analysis started. Results will be pushed to stream.",
    )
