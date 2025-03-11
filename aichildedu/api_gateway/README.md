# API Gateway

The API Gateway serves as the central entry point for all client requests to the AICHILDEDU platform. It routes requests to the appropriate microservices, handles authentication, and provides monitoring and rate limiting.

## Features

- **Request Routing**: Routes requests to the appropriate microservices based on the URL path
- **Authentication**: Validates JWT tokens and forwards user information to microservices
- **Rate Limiting**: Prevents abuse by limiting the number of requests per client
- **Logging**: Logs all requests and responses for monitoring and debugging
- **Service Health Monitoring**: Regularly checks the health of all microservices
- **Error Handling**: Provides consistent error responses across all services

## Architecture

The API Gateway is built using FastAPI and follows a middleware-based architecture:

```
Client Request
    │
    ▼
┌─────────────────┐
│  LoggingMiddleware  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────┐
│ RateLimitingMiddleware │
└─────────┬───────────┘
          │
          ▼
┌─────────────────┐
│ RequestValidationMiddleware │
└─────────┬───────────┘
          │
          ▼
┌─────────────────┐
│   Route Handler   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────┐
│ Service Registry │
└─────────┬───────────┘
          │
          ▼
┌─────────────────┐
│   Microservice   │
└─────────────────┘
```

## Configuration

The API Gateway is configured using environment variables:

- `USER_SERVICE_URL`: URL of the User Service
- `CONTENT_SERVICE_URL`: URL of the Content Service
- `LEARNING_SERVICE_URL`: URL of the Learning Service
- `AI_TEXT_SERVICE_URL`: URL of the AI Text Generator Service
- `AI_IMAGE_SERVICE_URL`: URL of the AI Image Generator Service
- `AI_VOICE_SERVICE_URL`: URL of the AI Voice Generator Service
- `AI_VIDEO_SERVICE_URL`: URL of the AI Video Generator Service
- `RECOMMENDATION_SERVICE_URL`: URL of the Recommendation Service
- `ANALYTICS_SERVICE_URL`: URL of the Analytics Service
- `RATE_LIMIT_WINDOW`: Time window for rate limiting in seconds (default: 60)
- `RATE_LIMIT_MAX_REQUESTS`: Maximum number of requests per window (default: 100)
- `CORS_ORIGINS`: Comma-separated list of allowed origins for CORS (default: *)

## API Endpoints

### Gateway Management Endpoints

- `GET /`: Root endpoint, returns basic information about the API Gateway
- `GET /health`: Health check endpoint, returns the health status of all services
- `GET /api/services`: Lists all registered services and their status
- `GET /api/routes`: Lists all available API routes

### Service Endpoints

All service endpoints are proxied through the API Gateway with the following prefixes:

- `/api/v1/users`: User Service endpoints
- `/api/v1/content`: Content Service endpoints
- `/api/v1/learning`: Learning Service endpoints
- `/api/v1/ai/text`: AI Text Generator Service endpoints
- `/api/v1/ai/image`: AI Image Generator Service endpoints
- `/api/v1/ai/voice`: AI Voice Generator Service endpoints
- `/api/v1/ai/video`: AI Video Generator Service endpoints

## Development

### Running Locally

To run the API Gateway locally:

```bash
uvicorn aichildedu.api_gateway.main:app --reload --port 8000
```

### Running with Docker

To run the API Gateway with Docker:

```bash
docker build -t aichildedu-api-gateway -f aichildedu/api_gateway/Dockerfile .
docker run -p 8000:8000 aichildedu-api-gateway
```

### Running with Docker Compose

To run the entire AICHILDEDU platform with Docker Compose:

```bash
docker-compose up -d
```

## Testing

To test the API Gateway:

```bash
# Test the health endpoint
curl http://localhost:8000/health

# Test the services endpoint
curl http://localhost:8000/api/services

# Test the routes endpoint
curl http://localhost:8000/api/routes
``` 