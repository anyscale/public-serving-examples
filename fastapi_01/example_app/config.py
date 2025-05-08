import os
import secrets

# API Settings
API_V1_STR = "/api/v1"
API_V2_STR = "/api/v2"
PROJECT_NAME = "NLP Processing Pipeline"

# Authentication
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_URI = f"redis://{REDIS_HOST}:{REDIS_PORT}"

# Rate Limiting
RATE_LIMIT_PER_MINUTE = 100

# Ray Serve
RAY_ADDRESS = os.getenv("RAY_ADDRESS", "local")

# NLP Models
MODEL_CONFIGS = {
    "sentiment": {
        "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
    },
    "classification": {
        "model_name": "facebook/bart-large-mnli",
    },
    "summarization": {
        "model_name": "sshleifer/distilbart-cnn-12-6",
    },
    "translation": {
        "model_name": "Helsinki-NLP/opus-mt-en-fr",
    },
    "ner": {
        "model_name": "dslim/bert-base-NER",
    },
}
