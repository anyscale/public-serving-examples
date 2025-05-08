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

## Architectural Comparison with Ray's Official Documentation

Ray's official documentation generally promotes a Serve-first mindset where users define class-based Ray Serve deployments with an `__init__` and `__call__` method, optionally wrapping FastAPI apps inside the Serve deployment. While that works for small to medium use cases, it can create architectural limitations when building large-scale FastAPI applications. Here's a breakdown of the key contrasts between this approach and the typical Ray documentation pattern:

### ⚙️ 1. Ownership of the FastAPI App

#### 📘 Ray Docs Pattern:
- FastAPI app is created inside a RayServeDeployment class
- Developers define endpoints inside the deployment or attach a FastAPI app in `__init__`

```python
@serve.deployment
class MyDeployment:
    @self.app.get("/hello")
    async def hello(self):
        return {"msg": "hello"}
```

#### ✅ This Pattern:
- FastAPI is the owner of routing, middleware, OpenAPI, etc.
- Ray Serve wraps around the existing app via `serve.run(app)` or an entrypoint deployment
- Clean separation between API layer and deployment logic

**Advantage**: Enables modular, large-scale FastAPI apps with routers, DI, middleware, WebSockets, and static file serving without entangling with Serve logic.

### 🧱 2. Layered Architecture & Separation of Concerns

#### 📘 Ray Docs Pattern:
- Encourages colocating model logic and API logic in the same deployment
- Minimal guidance on layering API vs processing logic

#### ✅ This Pattern:
- Explicit layered architecture:
  - API Layer → FastAPI
  - Integration Layer → Serialization and handle injection
  - Model Layer → Ray Serve deployments per NLP model
  - Frontend Layer → Served through FastAPI

**Advantage**: Easier testing, scaling, and division of responsibilities across teams. Each component can evolve independently.

### 🔄 3. Serve Handles and Dependency Injection

#### 📘 Ray Docs Pattern:
- Serve handles are often accessed via DeploymentHandle objects available as class attributes.

#### ✅ This Pattern:
- Serve handles are injected into FastAPI routes as dependencies
- Encourages declarative and testable code

```python
@router.post("/classify")
async def classify(request: InputModel, classifier_handle = Depends(get_classifier_handle)):
    result = await classifier_handle.classify.remote(request.text)
```

**Advantage**: Enables clearer interfaces, better unit tests, and more idiomatic FastAPI.

### 📈 4. Startup and Lifecycle Events

#### 📘 Ray Docs Pattern:
- `@app.on_event("startup")` is discouraged or not well-integrated in Serve-managed apps
- Ray Serve deployments rely on `__init__` for lifecycle logic

#### ✅ This Pattern:
- Supports full FastAPI lifecycle: `@app.on_event`, lifespan context, etc.
- Ray Serve lifecycle (`__init__`, `__del__`, or custom cleanup) is orthogonal to FastAPI's

**Advantage**: Enables side effects (e.g., DB connection, telemetry) in a standard FastAPI way without coupling them to model deployments.

### 📦 5. FastAPI Plugin Integration

#### 📘 Ray Docs Pattern:
- Limited to plugins that are compatible with `cloudpickle`, due to the need to serialize FastAPI app instances inside Serve deployments.
- Many popular plugins (e.g., OpenTelemetry for FastAPI) do not work reliably with this approach.

#### ✅ This Pattern:
- Fully compatible with any FastAPI plugin, including OpenTelemetry and other middleware.
- Since the FastAPI app is defined at the top level and not serialized, there are no restrictions on the types of features or extensions developers can use.

### 📦 6. Frontend Integration

#### 📘 Ray Docs Pattern:
- No guidance on serving frontend apps with FastAPI and Ray Serve

#### ✅ This Pattern:
- Frontend (React) is built into static files and served by FastAPI
- Frontend and backend share the same ingress

**Advantage**: Unified DevOps flow and deployment for full-stack services.

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
