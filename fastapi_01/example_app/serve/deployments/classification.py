import time
from typing import Any, Dict, List

import torch
from ray import serve
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from example_app.config import MODEL_CONFIGS


@serve.deployment(
    name="text_classifier",
)
class TextClassifier:
    def __init__(self):
        # Load model and tokenizer
        self.model_name = MODEL_CONFIGS["classification"]["model_name"]
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Create pipeline
        self.classifier = pipeline(
            "zero-shot-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1,
        )

        print(f"Loaded classification model {self.model_name} on {self.device}")

    async def classify(
        self, text: str, labels: List[str], multi_label: bool = False
    ) -> Dict[str, Any]:
        """Classify text into given categories."""
        start_time = time.time()

        # Classify text
        result = self.classifier(text, candidate_labels=labels, multi_label=multi_label)

        # Format results
        formatted_labels = []
        for i, label in enumerate(result["labels"]):
            formatted_labels.append({"label": label, "score": result["scores"][i]})

        processing_time = time.time() - start_time

        return {
            "text": text,
            "labels": formatted_labels,
            "processing_time": processing_time,
        }

    @serve.batch
    async def batch_classify(
        self, texts: List[str], labels: List[str], multi_label: bool = False
    ) -> List[Dict[str, Any]]:
        # TODO: Implement batch classification
        pass
