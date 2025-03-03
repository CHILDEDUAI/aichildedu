import json
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class ServiceClient:
    """
    Client for making HTTP requests to other microservices.
    Handles authentication token forwarding and error management.
    """
    
    def __init__(
        self, 
        base_url: str, 
        timeout: float = 10.0,
        auth_token: Optional[str] = None
    ):
        """
        Initialize service client
        
        Args:
            base_url: Base URL of the service
            timeout: Request timeout in seconds
            auth_token: Optional authentication token
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auth_token = auth_token
    
    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to service
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            data: Request data
            params: Query parameters
            headers: Custom headers
            auth_token: Optional authentication token (overrides instance token)
            timeout: Request timeout (overrides instance timeout)
            
        Returns:
            Response data
            
        Raises:
            HTTPException: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Prepare headers
        request_headers = headers.copy() if headers else {}
        token = auth_token or self.auth_token
        
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
            
        # Use our timeout or instance default
        request_timeout = timeout or self.timeout
        
        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data if data is not None else None,
                    headers=request_headers,
                )
                
                # Raise HTTPException for error status codes
                if response.status_code >= 400:
                    error_detail = "Unknown error"
                    
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", str(error_data))
                    except json.JSONDecodeError:
                        error_detail = response.text or f"Error {response.status_code}"
                        
                    logger.error(
                        f"Service request failed: {method} {url} -> {response.status_code}: {error_detail}"
                    )
                    
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=error_detail,
                    )
                    
                # Return response data for successful requests
                if response.status_code != 204:  # No content
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return {"data": response.text}
                else:
                    return {}
                    
        except httpx.RequestError as e:
            logger.exception(f"Request error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service communication error: {str(e)}",
            )
    
    # Convenience methods for common HTTP methods
    async def get(
        self, 
        endpoint: str, 
        *, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make GET request"""
        return await self.request("GET", endpoint, params=params, **kwargs)
    
    async def post(
        self, 
        endpoint: str, 
        *, 
        data: Any = None, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make POST request"""
        return await self.request("POST", endpoint, data=data, **kwargs)
    
    async def put(
        self, 
        endpoint: str, 
        *, 
        data: Any = None, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make PUT request"""
        return await self.request("PUT", endpoint, data=data, **kwargs)
    
    async def patch(
        self, 
        endpoint: str, 
        *, 
        data: Any = None, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make PATCH request"""
        return await self.request("PATCH", endpoint, data=data, **kwargs)
    
    async def delete(
        self, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self.request("DELETE", endpoint, **kwargs)

def create_service_client(
    service_url: str,
    auth_token: Optional[str] = None,
    timeout: float = 10.0
) -> ServiceClient:
    """
    Create service client
    
    Args:
        service_url: Base URL of the service
        auth_token: Optional authentication token
        timeout: Request timeout in seconds
        
    Returns:
        ServiceClient instance
    """
    return ServiceClient(service_url, timeout=timeout, auth_token=auth_token) 