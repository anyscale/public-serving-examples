import time
from typing import Dict, Any, List
import torch
from ray import serve
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

@serve.deployment(
    name="entity_recognizer",
    num_replicas=1,
    ray_actor_options={"num_cpus": 1, "num_gpus": 0},
    max_concurrent_queries=10
)
class EntityRecognizer:
    def __init__(self):
        # Load model and tokenizer
        self.model_name = "dslim/bert-base-NER"
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
            device=0 if self.device == "cuda" else -1
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
            formatted_entities.append({
                "text": entity["word"],
                "start": entity["start"],
                "end": entity["end"],
                "type": entity["entity_group"],
                "score": entity["score"]
            })
            
        processing_time = time.time() - start_time
            
        return {
            "text": text,
            "entities": formatted_entities,
            "processing_time": processing_time
        }
        
    @serve.batch
    async def batch_recognize(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Recognize entities in a batch of texts."""
        results = []
        
        for text in texts:
            result = await self.recognize_entities(text)
            results.append(result)
            
        return results 