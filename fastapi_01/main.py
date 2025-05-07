import logging
import time
import json
import numpy as np
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ray import serve

from example_app.api.middleware import add_middleware
from example_app.api.v1.router import router as v1_router
from example_app.db.database import close_redis
from example_app.serve import start_serve
from example_app.config import PROJECT_NAME
from example_app.serve.ingress_deployment import IngressDeployment
from example_app.telemetry import setup_opentelemetry, get_tracer
from example_app.serve.deployments.sentiment import SentimentAnalyzer
from example_app.serve.deployments.classification import TextClassifier
from example_app.serve.deployments.entities import EntityRecognizer
from example_app.api.v1.endpoints.classification import ClassificationError
from fastapi import status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")


# Custom NumPy JSON encoder
class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# Create FastAPI app
fastapi_app = FastAPI(
    title=PROJECT_NAME,
    description="A real-time NLP processing pipeline with FastAPI and Ray Serve",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    default_response_class=JSONResponse,
)

# Add routers
fastapi_app.include_router(v1_router)

# Add middleware
add_middleware(fastapi_app)


# Add exception handlers
@fastapi_app.exception_handler(ClassificationError)
async def classification_error_handler(request, exc):
    """Custom exception handler for classification errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error_type": exc.name, "detail": exc.message, "error_code": 1001},
    )


# # Set up OpenTelemetry instrumentation
# setup_opentelemetry(
#     app=fastapi_app,
#     service_name="nlp-pipeline",
#     jaeger_host="jaeger",
#     jaeger_port=14268,
#     sampling_ratio=1.0,  # Sample all requests in development
#     console_export=True,  # For debugging
# )

# # Get a tracer for this service
# tracer = get_tracer("nlp-pipeline")

# Start time for uptime calculation
start_time = time.time()

app = start_serve(fastapi_app)
