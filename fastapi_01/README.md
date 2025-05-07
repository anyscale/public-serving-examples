# FastAPI NLP Processing Pipeline

This project demonstrates a real-time NLP (Natural Language Processing) processing pipeline built with FastAPI and Ray Serve, providing sentiment analysis, text classification, named entity recognition, and streaming capabilities.

## Overview

The application integrates several powerful technologies:

- **FastAPI**: A modern, fast web framework for building APIs with Python
- **Ray Serve**: A scalable model serving library for building production machine learning APIs
- **Streaming Responses**: Real-time text processing with server-sent events (SSE)
- **WebSockets**: For bi-directional real-time communication
- **Distributed Tracing**: Using OpenTelemetry and Jaeger

## Features

The API provides the following NLP capabilities:
- **Sentiment Analysis**: Determine the emotional tone of text
- **Named Entity Recognition**: Extract entities like people, places, organizations
- **Text Classification**: Categorize text into predefined labels
- **Incremental Text Processing**: Analyze text chunk by chunk with streaming results
- **WebSocket Real-time Processing**: Bi-directional communication for instant analysis

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Poetry (Python dependency management)

### Installing Poetry

If you don't have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

For Windows (PowerShell):

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Running the Application

1. Clone this repository:
```bash
git clone <repository-url>
cd fastapi_01
```

2. Run the application using the Poetry startup script:
```bash
chmod +x start_poetry.sh
./start_poetry.sh
```

This will:
- Start a Redis container using Docker Compose
- Start a Jaeger container for distributed tracing
- Install the required dependencies using Poetry
- Start the FastAPI application

If you prefer to run the commands manually:

```bash
# Start Redis and Jaeger
docker-compose up -d

# Configure Poetry to use Python 3.9
poetry env use python3.9

# Install dependencies
poetry install

# Run the application
poetry run python main.py
```

Alternatively, you can use uvicorn directly:

```bash
uvicorn example_app.main:app --reload
```

Once the application is running, you can access:
- API Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc
- Jaeger UI (for tracing): http://localhost:16686

## API Endpoints

The application offers a comprehensive set of API endpoints:

### Authentication

1. Get an access token:
```bash
curl -X POST "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=password"
```

2. Use the token with other endpoints:
```bash
curl -X POST "http://localhost:8000/api/v1/sentiment" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I really enjoyed this movie, it was fantastic!",
    "language": "en"
  }'
```

### NLP Capabilities

#### Sentiment Analysis
- **POST `/api/v1/sentiment`**: Analyze sentiment of text
- **POST `/api/v1/sentiment/stream`**: Stream sentiment analysis results
- **POST `/api/v1/sentiment/batch`**: Batch sentiment analysis (admin only)
- **GET `/api/v1/sentiment/examples`**: Get sentiment examples

#### Text Classification
- **POST `/api/v1/classify`**: Classify text into categories
- **GET `/api/v1/classify/presets/{preset_name}`**: Get predefined label sets
- **POST `/api/v1/classify/custom`**: Classify text with query parameters

#### Named Entity Recognition
- **POST `/api/v1/entities`**: Extract named entities from text
- **POST `/api/v1/entities/stream`**: Stream entity extraction results
- **GET `/api/v1/entities/filter`**: Filter entities by type and confidence score

#### Streaming API
- **POST `/api/v1/streaming/analyze`**: Main streaming endpoint that processes text in chunks and returns results as an SSE stream
- **POST `/api/v1/streaming/analyze/document`**: Processes the entire document in chunks but returns a single comprehensive result
- **GET `/api/v1/streaming/demo`**: Returns an HTML page that demonstrates the streaming capabilities

### WebSocket API

Connect to the WebSocket endpoint for real-time processing:
```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/ws");

// Sentiment Analysis
ws.send(JSON.stringify({
  action: "sentiment",
  text: "I love this product!"
}));

// Entity Recognition
ws.send(JSON.stringify({
  action: "entities",
  text: "Apple Inc. is headquartered in Cupertino, California."
}));

// Classification
ws.send(JSON.stringify({
  action: "classify",
  text: "How do I reset my password?",
  labels: ["question", "statement", "command"]
}));
```

## Using the Jupyter Notebook

The repository includes a Jupyter notebook (`fastapi_nlp_api_demo.ipynb`) that demonstrates how to interact with all the API endpoints:

1. Launch Jupyter Notebook:
```bash
jupyter notebook
```

2. Open `fastapi_nlp_api_demo.ipynb`

3. Update the configuration in the second cell:
```python
# API configuration
BASE_URL = "http://localhost:8000/api/v1"
# Default credentials (update these)
USERNAME = "demo"
PASSWORD = "password"
```

4. Run all cells to see examples of:
   - Authentication and token acquisition
   - Health checks
   - Sentiment analysis
   - Named entity recognition
   - Text classification
   - WebSocket connections for real-time processing
   - Admin actions

## Implementation Details

### FastAPI and Ray Serve Integration

The application leverages FastAPI's modern features for API development and Ray Serve's scalable model serving capabilities:

- **FastAPI Features Used**:
  - OAuth2 with JWT authentication
  - Role-based access control
  - Request validation with Pydantic
  - Dependency injection
  - Background tasks
  - Middleware for logging and rate limiting
  - Streaming responses
  - WebSockets
  - Custom exception handlers
  - Path and query parameters
  - Caching with Redis

- **Ray Serve Capabilities**:
  - Model deployment and scaling
  - Horizontal scaling of inference workloads

### StreamingAnalyzer Deployment

The `StreamingAnalyzer` class is a Ray Serve deployment that:

1. Splits text into chunks using NLTK's sentence tokenizer
2. Analyzes sentiment using a DistilBERT model
3. Extracts named entities using a BERT-based NER model
4. Yields results as an async generator for streaming

### FastAPI Streaming

FastAPI's `StreamingResponse` is used to create a server-sent events (SSE) stream. The implementation:

1. Creates an async generator that yields JSON results as they become available
2. Formats the results according to the SSE protocol
3. Sets appropriate headers for SSE streaming

## Benefits of Streaming

- **Improved User Experience**: Users see partial results immediately instead of waiting for complete processing
- **Reduced Perceived Latency**: The application feels more responsive
- **Better Resource Utilization**: Processing happens in parallel with transmission
- **Scalability**: The system can handle large documents by processing and returning them incrementally

## Distributed Tracing with Jaeger

This application uses OpenTelemetry for instrumentation and Jaeger for distributed tracing. You can use the Jaeger UI to:

- View request traces across services
- Analyze latency of API endpoints
- Debug performance issues
- Monitor request flow

To access the Jaeger UI, navigate to http://localhost:16686 in your browser.

## Demo Users

The application provides two demo users:
- Regular user: username=`demo`, password=`password`
- Admin user: username=`admin`, password=`password`

## Development

For development, Poetry provides several useful commands:

```bash
# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Export requirements.txt (if needed)
poetry export -f requirements.txt > requirements.txt
```

## Stopping the Application

To stop the application:
1. Press Ctrl+C to stop the FastAPI server
2. Run `docker-compose down` to stop and remove the Redis and Jaeger containers

