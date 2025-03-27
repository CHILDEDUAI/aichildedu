import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer

from aichildedu.common.auth import get_current_user_id, get_optional_user_id
from aichildedu.common.config import settings

logger = logging.getLogger("api_gateway.routes")

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token", auto_error=False)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    """
    Proxy all requests to the appropriate service.
    
    Args:
        request: The incoming request
        path: The request path
        
    Returns:
        The response from the service
    """
    # Get full path including query parameters
    full_path = f"/api/v1/{path}"
    if request.query_params:
        # Convert query params to dict
        params = dict(request.query_params)
    else:
        params = {}
    
    # Get request headers
    headers = dict(request.headers)
    
    # Remove headers that should not be forwarded
    headers.pop("host", None)
    
    # Get request body for methods that may have a body
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except json.JSONDecodeError:
            # If not JSON, try to get form data
            try:
                body = dict(await request.form())
            except Exception:
                # If not form data, use raw body
                body = await request.body()
                if not body:
                    body = None
    
    # Get service registry from app state
    service_registry = request.app.state.service_registry
    
    try:
        # Forward the request to the appropriate service
        response = await service_registry.forward_request(
            method=request.method,
            path=full_path,
            headers=headers,
            params=params,
            body=body
        )
        
        # Create response with the same status code and headers
        content = response.content
        status_code = response.status_code
        response_headers = dict(response.headers)
        
        # Create FastAPI response
        return Response(
            content=content,
            status_code=status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logger.error(f"Error proxying request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/api/services", response_model=Dict[str, Dict[str, Any]])
async def list_services(request: Request):
    """
    List all registered services and their status.
    
    Args:
        request: The incoming request
        
    Returns:
        A dictionary of service information
    """
    # Get service registry from app state
    service_registry = request.app.state.service_registry
    
    # Check health of all services
    health_info = await service_registry.check_health()
    
    return health_info


@router.get("/api/routes", response_model=List[Dict[str, str]])
async def list_routes(request: Request):
    """
    List all available API routes.
    
    Args:
        request: The incoming request
        
    Returns:
        A list of route information
    """
    # Get service registry from app state
    service_registry = request.app.state.service_registry
    
    routes = []
    
    # Add routes for each service
    for service_id, service in service_registry.services.items():
        routes.append({
            "service": service["name"],
            "prefix": service["prefix"],
            "status": service["status"]
        })
    
    return routes 