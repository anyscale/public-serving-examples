# Disclaimer

A significant portion of the code in this project was generated using Cursor LLM. As such, it may not be production-ready or handle edge cases robustly. The primary goal of this project is to illustrate an ideal code organization pattern for building large-scale applications with FastAPI and Ray Serve.

# FastAPI NLP Processing Pipeline

A real-time NLP processing pipeline built with FastAPI and Ray Serve that provides sentiment analysis, text classification, named entity recognition, and streaming capabilities.

# Design Goals and Challenges
From the user requirements, we identify key goals:
- Full FastAPI feature support: Ray Serve should not disable any FastAPI feature. Routers, sub-apps, middleware, OpenAPI docs, request streaming, WebSockets, etc., should "just work" as in plain FastAPI. Serve should simply route HTTP to the right deployments.
- Minimal migration pain: Existing FastAPI code (functions, routers, modules) should be usable with little refactoring. Ideally you could take a FastAPI app or APIRouter and serve it via Ray Serve without rewriting it as a class.
- Clear separation of concerns: The interface should make it obvious what code is in Serve deployments (stateful/model logic) versus in FastAPI (pure HTTP/API logic). For example, model classes and pipelines stay in deployment classes, while routing, validation, and DI stay in FastAPI routers.
- Preserve Serve handle API: Deployments should still be able to call other deployments via handle.remote(). This implies keeping class-based deployments (or equivalent) for any code that uses handles.
- Lifecycle management: FastAPI supports startup/shutdown events (@app.on_event("startup"), etc.). The design should allow these hooks to execute at appropriate times. Similarly, Serve deployments can have __init__ or teardown logic.
- Support multiple models under one ingress: It should be easy to serve multiple model deployments behind a shared HTTP frontend. For example, one deployment per model with independent scaling, but one FastAPI app routing among them.

# Architecture

This project implements a layered architecture that integrates FastAPI with Ray Serve:

## 1. API Layer (FastAPI)
- **HTTP Interface**: Handles all web requests, authentication, and response formatting
- **Routing Logic**: Directs requests to appropriate NLP services via Ray Serve handles
- **Input Validation**: Uses Pydantic models for request validation
- **API Documentation**: Auto-generates OpenAPI docs
- **Middleware**: Implements authentication, CORS, and tracing
- **WebSockets**: Manages bi-directional communication channels
- **Static File Serving**: Serves the React frontend application

## 2. Integration Layer
- **Deployment Handles**: Ray Serve handles are injected as FastAPI dependencies
- **Service Registry**: Maps API endpoints to Ray Serve deployments
- **Request Serialization**: Converts between HTTP requests and Ray Serve inputs
- **Response Serialization**: Formats Ray Serve outputs as HTTP responses
- **Streaming Bridge**: Connects FastAPI streaming responses with Ray Serve streaming outputs

## 3. Model Serving Layer (Ray Serve)
- **Deployment Management**: Class-based deployments for NLP models
- **Scaling Policy**: Independent scaling for each model deployment
- **Resource Allocation**: Configurable CPU/GPU allocation per deployment
- **Inter-deployment Communication**: Using Ray Serve handles for pipeline composition
- **Health Monitoring**: Reports deployment health to FastAPI

## 4. Processing Pipeline
- **NLP Models**: Encapsulated in separate deployments
  - Sentiment Analyzer
  - Entity Recognizer
  - Text Classifier
  - Streaming Analyzer
- **Model Composition**: Deployments can call other deployments using handles
- **Resource Isolation**: Each model runs in its own deployment with controlled resources

## 5. Frontend Deployment

The frontend is deployed as part of the Ray Serve application and served through FastAPI's static file handling:

1. **Build Process**:
   - React application is built into static files
   - Static files are placed in the FastAPI static directory
   - FastAPI mounts the static directory to serve the frontend

2. **Integration with Ray Serve**:
   - Frontend is served through the same Ray Serve ingress deployment
   - All requests (API and frontend) go through the same Ray Serve proxy
   - Enables unified deployment and scaling of both frontend and backend

3. **Static File Serving**:
   ```python
   # In FastAPI app initialization
   app.mount("/", StaticFiles(directory="static", html=True), name="static")
   ```

4. **Benefits**:
   - Single deployment for both frontend and backend
   - Unified scaling and resource management
   - Simplified deployment process
   - Consistent routing and middleware application

## Getting Started

```bash
# Quick start
chmod +x start.sh
./start.sh
```

Access:
- Frontend: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc
- Jaeger UI (for tracing): http://localhost:16686
- Ray Dashboard: http://127.0.0.1:8265/#/overview

## Demo Credentials
- Regular user: `demo`/`password`
- Admin user: `admin`/`password` 

## Running Tests

```bash
docker compose up -d
poetry run pytest tests/  -x
```

## Format Code

```bash
poetry run ruff format . --exclude "*.ipynb"
poetry run ruff check --fix . --exclude "*.ipynb"
```
