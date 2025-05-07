# FastAPI NLP API Demo

This repository contains a demo FastAPI application that provides NLP (Natural Language Processing) services and a Jupyter notebook to interact with the API.

## Features

The API provides the following NLP capabilities:
- Sentiment Analysis
- Named Entity Recognition
- Text Classification
- WebSocket real-time processing

## Getting Started

### Prerequisites

- Python 3.7+
- FastAPI
- Ray Serve (for model deployments)
- Jupyter Notebook

### Installation

1. Clone this repository
2. Install the dependencies:
```bash
pip install -r requirements.txt
```
3. Start the FastAPI server:
```bash
uvicorn example_app.main:app --reload
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
USERNAME = "admin"
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

## API Documentation

When the API is running, the auto-generated documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example Curl Commands

You can also interact with the API using curl commands:

```bash
# Get an access token
curl -X POST "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password"

# Check API health
curl -X GET "http://localhost:8000/api/v1/health"

# Analyze sentiment
curl -X POST "http://localhost:8000/api/v1/sentiment" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product!", "language": "en"}'
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
