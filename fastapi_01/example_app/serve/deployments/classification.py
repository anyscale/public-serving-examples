import time
from typing import Dict, Any, List
import torch
from ray import serve
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline


@serve.deployment(
    name="text_classifier",
    num_replicas=1,
    ray_actor_options={"num_cpus": 1, "num_gpus": 0},
    max_ongoing_requests=10,
)
class TextClassifier:
    def __init__(self):
        # Load model and tokenizer
        self.model_name = "facebook/bart-large-mnli"
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
