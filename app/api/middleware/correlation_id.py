from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from uuid import uuid4
from app.infra.logger import main_logger


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation id
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))

        # Set in async-safe context
        main_logger.set_correlated_id(correlation_id)

        # Store in request state for easy access
        request.state.correlation_id = correlation_id

        try:
            # Proceed to next middleware/endpoint
            response = await call_next(request)

            # Add the Correlation-ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response
        finally:
            # ✅ Clean up after request completes
            main_logger.clear_correlated_id()
