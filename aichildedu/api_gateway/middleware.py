import logging
import time
from typing import Callable, Dict

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from aichildedu.common.config import settings
from aichildedu.common.exceptions import APIError

logger = logging.getLogger("api_gateway.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request and response information.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, log details, and pass to the next middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response from the next middleware or endpoint
        """
        # Generate a unique request ID
        request_id = request.headers.get("X-Request-ID", f"req_{time.time()}")
        
        # Add request ID to the request state
        request.state.request_id = request_id
        
        # Log the request
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Record start time
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log the response
            logger.info(
                f"Response {request_id}: {response.status_code} "
                f"processed in {process_time:.4f}s"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            return response
            
        except Exception as e:
            # Log the error
            logger.error(
                f"Error {request_id}: {str(e)} "
                f"after {time.time() - start_time:.4f}s",
                exc_info=True
            )
            raise


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests.
    Uses a simple in-memory store for demonstration purposes.
    In production, use Redis or another distributed cache.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self.rate_limit_window = settings.RATE_LIMIT_WINDOW  # seconds
        self.rate_limit_max_requests = settings.RATE_LIMIT_MAX_REQUESTS
        self.client_requests: Dict[str, Dict] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, apply rate limiting, and pass to the next middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response from the next middleware or endpoint
        """
        # Skip rate limiting for certain paths
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        current_time = time.time()
        
        if client_id in self.client_requests:
            client_data = self.client_requests[client_id]
            
            # Clean up old requests
            if current_time - client_data["window_start"] > self.rate_limit_window:
                client_data["window_start"] = current_time
                client_data["request_count"] = 0
            
            # Check if rate limit exceeded
            if client_data["request_count"] >= self.rate_limit_max_requests:
                logger.warning(f"Rate limit exceeded for client {client_id}")
                
                # Return rate limit error
                return Response(
                    content='{"error":"rate_limit_exceeded","detail":"Too many requests"}',
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "Retry-After": str(int(self.rate_limit_window - (current_time - client_data["window_start"])))
                    }
                )
            
            # Increment request count
            client_data["request_count"] += 1
        else:
            # First request from this client
            self.client_requests[client_id] = {
                "window_start": current_time,
                "request_count": 1
            }
        
        # Process the request
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get a unique identifier for the client.
        
        Args:
            request: The incoming request
            
        Returns:
            A unique identifier for the client
        """
        # Use API key if available
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key}"
        
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating requests.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, validate it, and pass to the next middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response from the next middleware or endpoint
        """
        # Validate content type for POST, PUT, PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")
            
            if not content_type.startswith("application/json") and not content_type.startswith("multipart/form-data"):
                return Response(
                    content='{"error":"invalid_content_type","detail":"Content-Type must be application/json or multipart/form-data"}',
                    status_code=415,
                    media_type="application/json"
                )
        
        # Process the request
        return await call_next(request) 