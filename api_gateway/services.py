import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

from common.config import settings

logger = logging.getLogger("api_gateway.services")


class ServiceRegistry:
    """
    Registry for managing microservices.
    Handles service discovery, health checks, and request forwarding.
    """
    
    def __init__(self):
        """
        Initialize the service registry.
        """
        self.services: Dict[str, Dict[str, Any]] = {}
        self.client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """
        Initialize the service registry.
        """
        logger.info("Initializing service registry")
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True
        )
        
        # Register services from configuration
        self._register_services_from_config()
        
        # Perform initial health check
        await self.check_health()
    
    async def close(self):
        """
        Close the service registry and release resources.
        """
        logger.info("Closing service registry")
        
        if self.client:
            await self.client.aclose()
    
    def _register_services_from_config(self):
        """
        Register services from configuration.
        """
        # User service
        self.services["user"] = {
            "name": "User Service",
            "base_url": settings.USER_SERVICE_URL,
            "prefix": "/api/v1/users",
            "health_endpoint": "/health",
            "status": "unknown",
            "last_check": 0,
        }
        
        # Content service
        self.services["content"] = {
            "name": "Content Service",
            "base_url": settings.CONTENT_SERVICE_URL,
            "prefix": "/api/v1/content",
            "health_endpoint": "/health",
            "status": "unknown",
            "last_check": 0,
        }
        
        # AI text generator service
        self.services["ai_text"] = {
            "name": "AI Text Generator",
            "base_url": settings.AI_TEXT_SERVICE_URL,
            "prefix": "/api/v1/ai/text",
            "health_endpoint": "/health",
            "status": "unknown",
            "last_check": 0,
        }
        
        # AI image generator service
        self.services["ai_image"] = {
            "name": "AI Image Generator",
            "base_url": settings.AI_IMAGE_SERVICE_URL,
            "prefix": "/api/v1/ai/image",
            "health_endpoint": "/health",
            "status": "unknown",
            "last_check": 0,
        }
        
        # AI voice generator service
        self.services["ai_voice"] = {
            "name": "AI Voice Generator",
            "base_url": settings.AI_VOICE_SERVICE_URL,
            "prefix": "/api/v1/ai/voice",
            "health_endpoint": "/health",
            "status": "unknown",
            "last_check": 0,
        }
        
        # AI video generator service
        self.services["ai_video"] = {
            "name": "AI Video Generator",
            "base_url": settings.AI_VIDEO_SERVICE_URL,
            "prefix": "/api/v1/ai/video",
            "health_endpoint": "/health",
            "status": "unknown",
            "last_check": 0,
        }
        
        # Learning service
        self.services["learning"] = {
            "name": "Learning Service",
            "base_url": settings.LEARNING_SERVICE_URL,
            "prefix": "/api/v1/learning",
            "health_endpoint": "/health",
            "status": "unknown",
            "last_check": 0,
        }
        
        logger.info(f"Registered {len(self.services)} services")
    
    async def check_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Check the health of all registered services.
        
        Returns:
            A dictionary of service health information
        """
        logger.info("Checking health of all services")
        
        health_info = {}
        check_tasks = []
        
        # Create tasks for checking each service
        for service_id, service in self.services.items():
            check_tasks.append(self._check_service_health(service_id, service))
        
        # Run all health checks concurrently
        await asyncio.gather(*check_tasks)
        
        # Collect health information
        for service_id, service in self.services.items():
            health_info[service_id] = {
                "name": service["name"],
                "status": service["status"],
                "last_check": service["last_check"],
            }
        
        return health_info
    
    async def _check_service_health(self, service_id: str, service: Dict[str, Any]):
        """
        Check the health of a specific service.
        
        Args:
            service_id: The service identifier
            service: The service information
        """
        if not self.client:
            logger.error("HTTP client not initialized")
            return
        
        health_url = f"{service['base_url']}{service['health_endpoint']}"
        service["last_check"] = time.time()
        
        try:
            response = await self.client.get(health_url)
            
            if response.status_code == 200:
                service["status"] = "healthy"
                logger.info(f"Service {service_id} is healthy")
            else:
                service["status"] = "unhealthy"
                logger.warning(f"Service {service_id} returned status code {response.status_code}")
        
        except Exception as e:
            service["status"] = "unavailable"
            logger.error(f"Error checking health of service {service_id}: {str(e)}")
    
    def get_service_url(self, service_id: str) -> str:
        """
        Get the base URL for a service.
        
        Args:
            service_id: The service identifier
            
        Returns:
            The base URL for the service
            
        Raises:
            HTTPException: If the service is not found
        """
        if service_id not in self.services:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service {service_id} not found"
            )
        
        return self.services[service_id]["base_url"]
    
    def get_service_for_path(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get the service for a specific path.
        
        Args:
            path: The request path
            
        Returns:
            The service information or None if no service matches
        """
        for service in self.services.values():
            if path.startswith(service["prefix"]):
                return service
        
        return None
    
    async def forward_request(
        self, 
        method: str, 
        path: str, 
        headers: Dict[str, str], 
        params: Dict[str, str],
        body: Any = None
    ) -> httpx.Response:
        """
        Forward a request to the appropriate service.
        
        Args:
            method: The HTTP method
            path: The request path
            headers: The request headers
            params: The query parameters
            body: The request body
            
        Returns:
            The response from the service
            
        Raises:
            HTTPException: If the service is not found or unavailable
        """
        if not self.client:
            logger.error("HTTP client not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service registry not initialized"
            )
        
        # Find the service for this path
        service = self.get_service_for_path(path)
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No service found for path {path}"
            )
        
        # Check if service is healthy
        if service["status"] == "unavailable":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service['name']} is currently unavailable"
            )
        
        # Construct the target URL
        target_url = f"{service['base_url']}{path}"
        
        try:
            # Forward the request
            response = await self.client.request(
                method=method,
                url=target_url,
                headers=headers,
                params=params,
                json=body if body else None,
                timeout=httpx.Timeout(30.0)
            )
            
            return response
            
        except httpx.TimeoutException:
            logger.error(f"Request to {service['name']} timed out")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request timed out"
            )
            
        except httpx.RequestError as e:
            logger.error(f"Error forwarding request to {service['name']}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error communicating with service"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error forwarding request: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            ) 