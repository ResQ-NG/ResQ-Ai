from typing import Dict
from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.middleware.correlation_id import CorrelationIdMiddleware
from app.core.config import config
from app.api.v1.routes.report.process_report import router as process_report_router


# Load environment variables from .env file
load_dotenv()


# Initialize FastAPI app
app = FastAPI(
    title="ResQ AI Server",
    description="ResQ AI Server provides endpoints for processing and summarizing reports using AI-powered media and text analysis.",
    version="0.1.0",
)

# Add CorrelationIdMiddleware for request correlation ID tracking
app.add_middleware(CorrelationIdMiddleware)


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a welcoming message for the ResQ AI API.

    Returns:
        Dict[str, str]: A dictionary with an inviting welcome message and helpful information.
    """
    return {
        "message": "👋 Welcome to ResQ AI! 🤖",
        "info": "This API provides AI-powered endpoints for media and text report analysis. Visit /docs for interactive documentation.",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint that returns the status of the API.

    Returns:
        Dict[str, str]: Status indicating the API is healthy.
    """
    return {"status": "ok", "message": "ResQ AI API is healthy"}


# Include application routers
app.include_router(process_report_router, prefix="/api/v1/report", tags=["Report Processing"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT)
