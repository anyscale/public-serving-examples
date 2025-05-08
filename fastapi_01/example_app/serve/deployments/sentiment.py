import time
from typing import Any, Dict, List

import torch
from ray import serve
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from example_app.config import MODEL_CONFIGS


@serve.deployment(
    name="sentiment_analyzer",
)
class SentimentAnalyzer:
    def __init__(self):
        # Load model and tokenizer
        self.model_name = MODEL_CONFIGS["sentiment"]["model_name"]
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        # Set to evaluation mode
        self.model.eval()

        print(f"Loaded sentiment analysis model {self.model_name} on {self.device}")

    async def analyze(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Analyze sentiment of a text."""
        start_time = time.time()

        # Tokenize and predict
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            scores = torch.nn.functional.softmax(outputs.logits, dim=1)

        # Get prediction
        positive_score = scores[0][1].item()

        # Determine sentiment label
        if positive_score > 0.6:
            sentiment = "positive"
        elif positive_score < 0.4:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        processing_time = time.time() - start_time

        return {
            "text": text,
            "sentiment": sentiment,
            "score": positive_score,
            "language": language,
            "processing_time": processing_time,
        }

    @serve.batch
    async def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        # TODO: Implement batch sentiment analysis
        pass
