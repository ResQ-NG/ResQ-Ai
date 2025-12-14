from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.middleware.correlation_id import CorrelationIdMiddleware
from app.core.config import config
from app.api.v1.routes.report import categorize_report, summarize_report
from app.adapters.cache.redis import RedisCache
from app.adapters.cache.redis_stream import RedisStream
from app.infra.logger import main_logger

# Load environment variables from .env file
load_dotenv()


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Manage application lifespan: startup and shutdown events."""
    # Startup: Initialize Redis cache
    try:
        redis_cache = RedisCache()
        fastapi_app.state.redis_cache = redis_cache
        # Test connection
        await redis_cache.ping()
        main_logger.log("Redis cache initialized successfully", "INFO")
    except Exception as e:  # pylint: disable=broad-except
        main_logger.log(f"Failed to initialize Redis cache: {e}", "ERROR")
        raise

    # Startup: Initialize Redis stream
    try:
        redis_stream = RedisStream()
        fastapi_app.state.redis_stream = redis_stream
        main_logger.log("Redis stream initialized successfully", "INFO")
    except Exception as e:  # pylint: disable=broad-except
        main_logger.log(f"Failed to initialize Redis stream: {e}", "ERROR")
        # Don't raise - stream is optional for some operations
        fastapi_app.state.redis_stream = None

    yield

    # Shutdown: Close Redis stream connection
    try:
        if hasattr(fastapi_app.state, "redis_stream") and fastapi_app.state.redis_stream:
            await fastapi_app.state.redis_stream.close()
            main_logger.log("Redis stream connection closed", "INFO")
    except Exception as e:  # pylint: disable=broad-except
        main_logger.log(f"Error closing Redis stream connection: {e}", "ERROR")

    # Shutdown: Close Redis cache connection
    try:
        if hasattr(fastapi_app.state, "redis_cache") and fastapi_app.state.redis_cache:
            await fastapi_app.state.redis_cache.close()
            main_logger.log("Redis cache connection closed", "INFO")
    except Exception as e:  # pylint: disable=broad-except
        main_logger.log(f"Error closing Redis cache connection: {e}", "ERROR")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="ResQ AI Server",
    description="ResQ AI Server provides endpoints for processing and summarizing reports using AI-powered media and text analysis.",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(
    summarize_report.router, prefix="/api/v1/report", tags=["Report Processing"]
)
app.include_router(
        categorize_report.router, prefix="/api/v1/categorize", tags=["Report Categorization"]
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT)
