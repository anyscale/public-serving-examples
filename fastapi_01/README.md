# FastAPI NLP Processing Pipeline

This project demonstrates a real-time NLP (Natural Language Processing) processing pipeline built with FastAPI and Ray Serve, providing sentiment analysis, text classification, named entity recognition, and streaming capabilities.

## Overview

The application integrates several powerful technologies:

- **FastAPI**: A modern, fast web framework for building APIs with Python
- **Ray Serve**: A scalable model serving library for building production machine learning APIs
- **React**: A modern JavaScript library for building user interfaces
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

The frontend provides a modern and intuitive interface to access all these capabilities:
- **Authentication** with JWT tokens
- **Interactive UI** for each NLP feature
- **Real-time Visualization** of processing results
- **Streaming Demo** to see incremental text processing
- **WebSocket Demo** for bi-directional communication
- **Responsive Design** that works on desktop and mobile

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm
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

The easiest way to run the complete application (both backend and frontend) is using the provided script:

```bash
chmod +x start_all.sh
./start_all.sh
```

This will:
- Start a Redis container using Docker Compose
- Start a Jaeger container for distributed tracing
- Install the required dependencies using Poetry
- Start the FastAPI backend application
- Start the React frontend application

Once the application is running, you can access:
- Frontend UI: http://localhost:3000 
- API Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc
- Jaeger UI (for tracing): http://localhost:16686

### Running the Backend Only

If you prefer to run just the backend:

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

### Running the Frontend Only

If you want to run just the frontend (assuming the backend is already running):

```bash
cd frontend
npm install
npm start
```

## Demo Credentials

The application provides two demo users:
- Regular user: username=`demo`, password=`password`
- Admin user: username=`admin`, password=`password`

## API Endpoints

The application offers a comprehensive set of API endpoints. See the [API Documentation](http://localhost:8000/docs) when the application is running for details.

## Frontend Features

The frontend provides a user-friendly interface to interact with all API features:

1. **Dashboard**: System status and feature overview
2. **Sentiment Analysis**: Analyze text emotional tone with visualizations
3. **Entity Recognition**: Extract and display entities with confidence filtering
4. **Text Classification**: Classify text with custom or preset labels
5. **Streaming Demo**: See real-time analysis of text chunks
6. **WebSocket Demo**: Experience bi-directional communication

## Using the Jupyter Notebook

The repository includes a Jupyter notebook (`fastapi_nlp_api_demo.ipynb`) that demonstrates how to interact with all the API endpoints programmatically.

## Implementation Details

See the original README sections for details on:
- FastAPI and Ray Serve Integration
- StreamingAnalyzer Deployment
- FastAPI Streaming
- Benefits of Streaming
- Distributed Tracing with Jaeger

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

For frontend development:

```bash
# Add a new dependency
cd frontend
npm install package-name

# Build for production
npm run build
```

## Stopping the Application

To stop the full application that was started with `start_all.sh`, simply press `Ctrl+C` in the terminal where it's running.

To stop just the backend services:
```bash
docker-compose down
```
