#!/bin/bash

echo "Starting NLP Pipeline with FastAPI and Ray Serve using Poetry"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed (checking both standalone and plugin versions)
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Python 3.9 is installed
if ! command -v python3.9 &> /dev/null; then
    echo "Python 3.9 is not installed. Please install Python 3.9 first."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install Poetry first."
    echo "You can install it with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Ensure Poetry uses Python 3.9
echo "Configuring Poetry to use Python 3.9..."
poetry env use python3.9

# Start Redis and Jaeger containers
echo "Starting Redis and Jaeger containers..."
$COMPOSE_CMD up -d

# Wait for Redis and Jaeger to start
echo "Waiting for Redis and Jaeger to start..."
sleep 5

# Install dependencies with Poetry
echo "Installing dependencies with Poetry..."
poetry install

# Start the application
echo "Starting FastAPI application..."
echo "Once started, you can access:"
echo "- API Documentation: http://localhost:8000/docs"
echo "- ReDoc Documentation: http://localhost:8000/redoc"
echo "- Jaeger UI (for tracing): http://localhost:16686"
poetry run python main.py
