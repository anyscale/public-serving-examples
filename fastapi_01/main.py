import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from ray import serve

from example_app.serve import get_serve_app
from example_app.config import PROJECT_NAME
from example_app.serve.serve_config import INGRESS_APP_NAME
from example_app.telemetry import setup_opentelemetry
from example_app.api.v1.endpoints.classification import ClassificationError
from fastapi import status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")


# Create FastAPI app
fastapi_app = FastAPI(
    title=PROJECT_NAME,
    description="A real-time NLP processing pipeline with FastAPI and Ray Serve",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    default_response_class=JSONResponse,
)


def app_init_func(app: FastAPI):
    from example_app.api.middleware import add_middleware
    from example_app.api.v1.router import router as v1_router

    # Define exception handler
    async def classification_error_handler(request, exc):
        """Custom exception handler for classification errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error_type": exc.name, "detail": exc.message, "error_code": 1001},
        )

    # Register exception handler
    app.add_exception_handler(ClassificationError, classification_error_handler)

    # add routers
    app.include_router(v1_router)

    # add middleware
    add_middleware(app)

    # Add static files - frontend build
    frontend_build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "build")
    if os.path.exists(frontend_build_dir):
        logger.info(f"Mounting frontend static files from {frontend_build_dir}")
        app.mount("/", StaticFiles(directory=frontend_build_dir, html=True), name="frontend")
    else:
        logger.warning(f"Frontend build directory not found at {frontend_build_dir}")

    # Set up OpenTelemetry instrumentation
    setup_opentelemetry(
        app=app,
        service_name="nlp-pipeline",
        jaeger_host="localhost",
        jaeger_port=6831,
        otlp_endpoint="localhost:4317",
        sampling_ratio=1.0,  # Sample all requests in development
        console_export=True,  # For debugging
    )


serve_ingress_app = get_serve_app(fastapi_app, app_init_func)

if __name__ == "__main__":
    serve.run(serve_ingress_app, name=INGRESS_APP_NAME, route_prefix="/", blocking=True)
