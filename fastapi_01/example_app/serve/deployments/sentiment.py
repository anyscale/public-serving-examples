import time
from typing import Dict, Any, List
import torch
from ray import serve
from transformers import AutoTokenizer, AutoModelForSequenceClassification

@serve.deployment(
    name="sentiment_analyzer",
    num_replicas=1,
    ray_actor_options={"num_cpus": 1, "num_gpus": 0},
    max_concurrent_queries=10
)
class SentimentAnalyzer:
    def __init__(self):
        # Load model and tokenizer
        self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
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
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
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
            "processing_time": processing_time
        }
        
    @serve.batch
    async def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment for a batch of texts."""
        results = []
        
        for text in texts:
            result = await self.analyze(text)
            results.append(result)
            
        return results 