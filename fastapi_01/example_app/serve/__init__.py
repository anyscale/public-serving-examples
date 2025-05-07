from example_app.serve.deployments.classification import TextClassifier
from example_app.serve.deployments.entities import EntityRecognizer
from example_app.serve.deployments.sentiment import SentimentAnalyzer
from example_app.serve.serve_config import start_serve, get_deployment

__all__ = ["start_serve", "get_deployment"]

async def get_sentiment_analyzer():
    """Dependency for sentiment analyzer deployment."""
    return get_deployment(SentimentAnalyzer.name)

async def get_text_classifier():
    """Dependency for text classifier deployment."""
    return get_deployment(TextClassifier.name)

async def get_entity_recognizer():
    """Dependency for entity recognizer deployment."""
    return get_deployment(EntityRecognizer.name) 
