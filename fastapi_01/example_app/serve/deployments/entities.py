import time
from typing import Any, Dict, List

import torch
from ray import serve
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

from example_app.config import MODEL_CONFIGS


@serve.deployment(
    name="entity_recognizer",
)
class EntityRecognizer:
    def __init__(self):
        # Load model and tokenizer
        self.model_name = MODEL_CONFIGS["ner"]["model_name"]
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)

        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Create pipeline
        self.ner = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            aggregation_strategy="simple",
            device=0 if self.device == "cuda" else -1,
        )

        print(f"Loaded NER model {self.model_name} on {self.device}")

    async def recognize_entities(self, text: str) -> Dict[str, Any]:
        """Recognize named entities in text."""
        start_time = time.time()

        # Get entities
        entities_output = self.ner(text)

        # Format entities
        formatted_entities = []
        for entity in entities_output:
            formatted_entities.append(
                {
                    "text": entity["word"],
                    "start": entity["start"],
                    "end": entity["end"],
                    "type": entity["entity_group"],
                    "score": float(entity["score"]),
                }
            )

        processing_time = float(time.time() - start_time)

        return {
            "text": text,
            "entities": formatted_entities,
            "processing_time": processing_time,
        }

    @serve.batch
    async def batch_recognize(self, texts: List[str]) -> List[Dict[str, Any]]:
        # TODO: Implement batch entity recognition
        pass
