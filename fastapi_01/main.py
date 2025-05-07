import logging
import time
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from example_app.api.middleware import add_middleware
from example_app.api.v1.router import router as v1_router
from example_app.db.database import close_redis
from example_app.serve import setup_serve
from example_app.config import PROJECT_NAME
from example_app.telemetry import setup_opentelemetry, get_tracer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")

# Create FastAPI app
app = FastAPI(
    title=PROJECT_NAME,
    description="A real-time NLP processing pipeline with FastAPI and Ray Serve",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add routers
app.include_router(v1_router)

# Add middleware
add_middleware(app)

# Set up OpenTelemetry instrumentation
setup_opentelemetry(
    app=app,
    service_name="nlp-pipeline",
    jaeger_host="jaeger",
    jaeger_port=14268,
    sampling_ratio=1.0,  # Sample all requests in development
    console_export=True,  # For debugging
)

# Get a tracer for this service
tracer = get_tracer("nlp-pipeline")

# Start time for uptime calculation
start_time = time.time()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    with tracer.start_as_current_span("startup_event"):
        logger.info("Starting NLP Pipeline service")
        
        # Initialize Ray Serve
        try:
            deployments = setup_serve()
            logger.info(f"Initialized Ray Serve with deployments: {list(deployments.keys())}")
        except Exception as e:
            logger.error(f"Failed to initialize Ray Serve: {e}")
            raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    with tracer.start_as_current_span("shutdown_event"):
        logger.info("Shutting down NLP Pipeline service")
        
        # Close Redis connections
        await close_redis()
        logger.info("Closed Redis connections")

# Root endpoint
@app.get("/")
async def root(request: Request) -> Dict[str, Any]:
    """Root endpoint with service information."""
    with tracer.start_as_current_span("root_endpoint"):
        return {
            "service": PROJECT_NAME,
            "version": "1.0.0",
            "uptime_seconds": time.time() - start_time,
            "endpoints": {
                "api_v1": "/api/v1",
                "documentation": "/docs",
                "jaeger_ui": "http://localhost:16686",  # Jaeger UI endpoint
                "health": "/api/v1/health"
            }
        }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions."""
    with tracer.start_as_current_span("global_exception"):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred",
                "error_type": type(exc).__name__
            }
        )

if __name__ == "__main__":
    import uvicorn
    
    # Start the application
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 