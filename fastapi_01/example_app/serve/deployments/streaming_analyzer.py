import time
import asyncio
from typing import Dict, Any, List, Generator, AsyncGenerator
import torch
from ray import serve
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from nltk.tokenize import sent_tokenize
import nltk
from example_app.config import MODEL_CONFIGS
import logging

logger = logging.getLogger(__name__)


@serve.deployment(
    name="streaming_analyzer",
    num_replicas=1,
    ray_actor_options={"num_cpus": 0.5, "num_gpus": 0},
    max_ongoing_requests=10,
)
class StreamingAnalyzer:
    def __init__(self):
        # Download nltk data required for sentence tokenization
        nltk.download("punkt")
        nltk.download("punkt_tab")
        print("NLTK data downloaded")
        # Load models
        self.sentiment_model_name = MODEL_CONFIGS["sentiment"]["model_name"]
        self.tokenizer = AutoTokenizer.from_pretrained(self.sentiment_model_name)
        self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
            self.sentiment_model_name
        )

        # Set up NER pipeline
        self.ner_pipeline = pipeline("ner", model=MODEL_CONFIGS["ner"]["model_name"])

        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sentiment_model.to(self.device)

        # Set to evaluation mode
        self.sentiment_model.eval()

        print(f"Loaded streaming analysis models on {self.device}")

    def _split_text_into_chunks(self, text: str, chunk_size: int = 3) -> List[str]:
        """Split text into chunks of sentences."""
        sentences = sent_tokenize(text)
        chunks = []

        for i in range(0, len(sentences), chunk_size):
            chunk = " ".join(sentences[i : i + chunk_size])
            chunks.append(chunk)

        return chunks

    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of a text chunk."""
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.sentiment_model(**inputs)
            scores = torch.nn.functional.softmax(outputs.logits, dim=1)

        positive_score = float(scores[0][1].item())

        if positive_score > 0.6:
            sentiment = "positive"
        elif positive_score < 0.4:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "text": text,
            "sentiment": sentiment,
            "score": positive_score,
        }

    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text chunk."""
        entities = self.ner_pipeline(text)

        # Group entities by word
        grouped_entities = []
        current_entity = None

        for entity in entities:
            if current_entity is None or entity["entity"].startswith("B-"):
                if current_entity:
                    grouped_entities.append(current_entity)
                current_entity = {
                    "entity": entity["entity"].replace("B-", "").replace("I-", ""),
                    "word": entity["word"],
                    "score": float(entity["score"]),
                    "start": entity["start"],
                    "end": entity["end"],
                }
            else:
                # Continue the entity
                current_entity["word"] += entity["word"].replace("##", "")
                current_entity["end"] = entity["end"]
                current_entity["score"] = (
                    current_entity["score"] + float(entity["score"])
                ) / 2

        if current_entity:
            grouped_entities.append(current_entity)

        return grouped_entities

    async def stream_analysis(
        self, text: str, analysis_types: List[str] = ["sentiment", "entities"]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream analysis of text by processing chunks incrementally.

        Args:
            text: The text to analyze
            analysis_types: List of analysis types to perform ("sentiment", "entities")

        Yields:
            Dictionary with chunk analysis results
        """
        chunks = self._split_text_into_chunks(text)

        for i, chunk in enumerate(chunks):
            start_time = time.time()
            result = {
                "chunk_id": i,
                "chunk_text": chunk,
                "total_chunks": len(chunks),
                "progress": (i + 1) / len(chunks),
            }

            # Perform requested analyses
            if "sentiment" in analysis_types:
                sentiment_result = await self._analyze_sentiment(chunk)
                result["sentiment"] = sentiment_result["sentiment"]
                result["sentiment_score"] = sentiment_result["score"]

            if "entities" in analysis_types:
                entities = await self._extract_entities(chunk)
                result["entities"] = entities

            result["processing_time"] = time.time() - start_time

            # Add small delay to simulate processing time and avoid overwhelming client
            await asyncio.sleep(0.1)

            yield result

    async def analyze_document(
        self, text: str, analysis_types: List[str] = ["sentiment", "entities"]
    ) -> Dict[str, Any]:
        """
        Analyze entire document and provide summary statistics.

        This method processes the document in chunks but returns a single comprehensive result.
        """
        chunks = self._split_text_into_chunks(text)
        all_results = []

        for chunk in chunks:
            result = {}

            if "sentiment" in analysis_types:
                sentiment_result = await self._analyze_sentiment(chunk)
                result["sentiment"] = sentiment_result

            if "entities" in analysis_types:
                entities = await self._extract_entities(chunk)
                result["entities"] = entities

            all_results.append(result)

        # Compile summary
        summary = {"text_length": len(text), "chunk_count": len(chunks)}

        if "sentiment" in analysis_types:
            # Calculate overall sentiment
            sentiment_scores = [
                r["sentiment"]["score"] for r in all_results if "sentiment" in r
            ]
            avg_sentiment = (
                sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            )

            if avg_sentiment > 0.6:
                overall_sentiment = "positive"
            elif avg_sentiment < 0.4:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"

            summary["sentiment"] = {
                "overall": overall_sentiment,
                "average_score": avg_sentiment,
                "sentiment_by_chunk": [
                    r["sentiment"]["sentiment"] for r in all_results if "sentiment" in r
                ],
            }

        if "entities" in analysis_types:
            # Collect all entities
            all_entities = []
            for result in all_results:
                if "entities" in result:
                    all_entities.extend(result["entities"])

            # Count entity types
            entity_types = {}
            for entity in all_entities:
                entity_type = entity["entity"]
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1

            summary["entities"] = {
                "count": len(all_entities),
                "by_type": entity_types,
                "all_entities": all_entities,
            }

        return summary
