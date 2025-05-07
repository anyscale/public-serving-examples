# NLP Processing Pipeline - Usage Guide

This project demonstrates a real-time NLP processing pipeline built with FastAPI and Ray Serve, providing sentiment analysis, text classification, and named entity recognition capabilities.

## Prerequisites

- Python 3.9
- Docker and Docker Compose
- Poetry (Python dependency management)

## Getting Started

### Installing Poetry

If you don't have Poetry installed, you can install it with:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

For Windows, you can use PowerShell:

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

Once the application is running, you can access:
- API Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc
- Jaeger UI (for tracing): http://localhost:16686

## Distributed Tracing with Jaeger

This application uses OpenTelemetry for instrumentation and Jaeger for distributed tracing. You can use the Jaeger UI to:

- View request traces across services
- Analyze latency of API endpoints
- Debug performance issues
- Monitor request flow

To access the Jaeger UI, navigate to http://localhost:16686 in your browser.

## API Endpoints

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
- POST `/api/v1/sentiment`: Analyze sentiment of text
- POST `/api/v1/sentiment/stream`: Stream sentiment analysis results
- POST `/api/v1/sentiment/batch`: Batch sentiment analysis (admin only)
- GET `/api/v1/sentiment/examples`: Get sentiment examples

#### Text Classification
- POST `/api/v1/classify`: Classify text into categories
- GET `/api/v1/classify/presets/{preset_name}`: Get predefined label sets
- POST `/api/v1/classify/custom`: Classify text with query parameters

#### Named Entity Recognition
- POST `/api/v1/entities`: Extract named entities from text
- POST `/api/v1/entities/stream`: Stream entity extraction results
- GET `/api/v1/entities/filter`: Filter entities by type and confidence score

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

## Demo Users

The application provides two demo users:
- Regular user: username=`demo`, password=`password`
- Admin user: username=`admin`, password=`password`

## Advanced Features

This project demonstrates many FastAPI features:
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
- Distributed tracing with OpenTelemetry and Jaeger

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
