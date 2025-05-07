import ray
from ray import serve
from typing import Dict, Any

from example_app.serve.deployments.sentiment import SentimentAnalyzer
from example_app.serve.deployments.classification import TextClassifier
from example_app.serve.deployments.entities import EntityRecognizer

from example_app.config import RAY_ADDRESS

def setup_serve():
    """Initialize and set up Ray Serve with all deployments."""
    # Initialize Ray
    if not ray.is_initialized():
        ray.init(address=RAY_ADDRESS, namespace="nlp_pipeline")
    
    # Start Serve
    serve.start(detached=True)
    
    # Deploy models
    SentimentAnalyzer.deploy()
    TextClassifier.deploy()
    EntityRecognizer.deploy()
    
    print("All models deployed successfully!")
    
    return {
        "sentiment_analyzer": SentimentAnalyzer,
        "text_classifier": TextClassifier,
        "entity_recognizer": EntityRecognizer
    }

def get_deployment(name: str):
    """Get deployment handle by name."""
    return serve.get_deployment(name)

def shutdown_serve():
    """Shutdown Ray Serve."""
    serve.shutdown() 