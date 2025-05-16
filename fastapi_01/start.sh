#!/bin/bash

set -e  # Exit on any error

echo "Starting FastAPI NLP Processing Pipeline with Frontend"
echo "======================================================"
echo ""

# ===== STEP 1: Check Dependencies =====

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install it by following the instructions:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm first."
    exit 1
fi

# ===== STEP 2: Start Backend Services =====

# Start Redis and Jaeger containers
echo "Starting Redis and Jaeger containers..."
$COMPOSE_CMD up -d

# Wait for Redis and Jaeger to start
echo "Waiting for Redis and Jaeger to start..."
sleep 5

# ===== STEP 3: Build Frontend =====

echo "Building frontend for serving through Ray Serve..."
cd "$(dirname "$0")/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build the frontend
echo "Building frontend production build..."
npm run build

# Check if the build was successful
if [ ! -d "build" ]; then
    echo "Error: Build directory wasn't created. Check for errors above."
    exit 1
fi

echo "Frontend build completed successfully!"
echo "The build directory is located at: $(pwd)/build"

# Navigate back to the root directory
cd ..

# ===== STEP 4: Install Python Dependencies =====

# Configure Poetry and install dependencies
echo "Installing Python dependencies with Poetry..."
poetry install

# ===== STEP 5: Start Application =====

# Run the application using Ray Serve
echo "Starting the application using Ray Serve..."
echo "Once started, you can access:"
echo "- Frontend: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo "- ReDoc Documentation: http://localhost:8000/redoc"
echo "- Jaeger UI (for tracing): http://localhost:16686"
echo "- Ray Dashboard: http://127.0.0.1:8265/#/overview"

# Handle script termination
function cleanup {
    echo "Shutting down services..."
    
    # Stop Docker containers
    $COMPOSE_CMD down
    echo "Docker containers stopped"

    echo "All services shut down"
}

# Set up trap to catch termination signals
trap cleanup SIGINT SIGTERM

# set the environment variable for the tracing exporter
export ANYSCALE_TRACING_EXPORTER_IMPORT_PATH="example_app.trace_exporter:default_tracing_exporter"
export ANYSCALE_TRACING_SAMPLING_RATIO=1.0

# Start the application
poetry run serve run serve_config.yaml

echo "Application stopped" 