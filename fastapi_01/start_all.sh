#!/bin/bash

echo "Starting FastAPI NLP Processing Pipeline with Frontend"
echo "======================================================"
echo ""

# Check if Docker Compose is installed (checking both standalone and plugin versions)
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Please start Docker and try again."
  exit 1
fi

# Start backend services with docker-compose
echo "Starting Redis and Jaeger containers..."
$COMPOSE_CMD up -d

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
  echo "Poetry is not installed. Please install it by following the instructions:"
  echo "curl -sSL https://install.python-poetry.org | python3 -"
  exit 1
fi

# Start the backend server in the background
echo "Starting FastAPI backend server..."
cd "$(dirname "$0")"

# Check if running in poetry already
if [[ -z "$POETRY_ACTIVE" ]]; then
  # Start the process in the background
  poetry run serve run serve_config.yaml &
  BACKEND_PID=$!
  echo "Backend server started with PID: $BACKEND_PID"
else
  # Already in a poetry shell
  serve run serve_config.yaml &
  BACKEND_PID=$!
  echo "Backend server started with PID: $BACKEND_PID"
fi

# Wait for backend to start up
echo "Waiting for backend to start up..."
sleep 5

# Start the frontend
echo "Starting React frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# Handle script termination
function cleanup {
  echo "Shutting down services..."
  
  # Kill the frontend process if it's running
  if kill -0 $FRONTEND_PID 2>/dev/null; then
    kill $FRONTEND_PID
    echo "Frontend stopped"
  fi
  
  # Kill the backend process if it's running
  if kill -0 $BACKEND_PID 2>/dev/null; then
    kill $BACKEND_PID
    echo "Backend stopped"
  fi
  
  # Stop Docker containers
  cd "$(dirname "$0")"
  $COMPOSE_CMD down
  echo "Docker containers stopped"
  
  echo "All services shut down"
}

# Set up trap to catch termination signals
trap cleanup SIGINT SIGTERM

echo ""
echo "Services are running!"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo "- Jaeger UI (Tracing): http://localhost:16686"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running
wait 