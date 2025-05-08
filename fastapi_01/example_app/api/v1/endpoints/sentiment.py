import json
import time
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from example_app.api.models import SentimentResponse, TextRequest
from example_app.api.security import User, get_current_active_user, requires_role
from example_app.db.database import (
    generate_cache_key,
    get_cached_response,
    set_cached_response,
    store_request_history,
)
from example_app.serve import get_sentiment_analyzer

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.post("", response_model=SentimentResponse)
async def analyze_sentiment(
    request: TextRequest,
    current_user: User = Depends(get_current_active_user),
    sentiment_analyzer=Depends(get_sentiment_analyzer),
):
    """
    Analyze sentiment of the provided text.

    Returns sentiment label (positive, negative, neutral) with a confidence score.
    """
    # Try to get from cache
    cache_key = await generate_cache_key("sentiment", request.text)
    cached_result = await get_cached_response(cache_key)

    if cached_result:
        return cached_result

    # Call model
    result = await sentiment_analyzer.analyze.remote(request.text, request.language)

    # Cache result
    await set_cached_response(cache_key, result, expire=3600)

    # Store in history
    await store_request_history(
        current_user.username,
        "/sentiment",
        {"text": request.text, "language": request.language},
    )

    return result


@router.post("/stream")
async def stream_sentiment(
    request: TextRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Stream sentiment analysis results.

    This endpoint demonstrates streaming response capabilities.
    """
    sentiment_analyzer = get_deployment("sentiment_analyzer")

    async def generate():
        # Start streaming
        yield json.dumps({"status": "processing"}) + "\n"

        # Process sentiment
        start_time = time.time()
        result = await sentiment_analyzer.analyze.remote(request.text, request.language)

        # Simulate stream chunks (in a real app, the model would stream tokens)
        yield json.dumps({"status": "analyzing", "progress": 0.5}) + "\n"
        time.sleep(0.5)  # Simulate processing time

        # Return final result
        yield json.dumps(result) + "\n"

    return StreamingResponse(generate(), media_type="application/json")


@router.post("/batch", response_model=List[SentimentResponse])
async def batch_sentiment_analysis(
    texts: List[TextRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(requires_role("admin")),
):
    """
    Batch sentiment analysis for multiple texts.

    This endpoint demonstrates batch processing and requires admin role.
    """
    if len(texts) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 10 texts",
        )

    sentiment_analyzer = get_deployment("sentiment_analyzer")

    # Extract just the text strings for batch processing
    text_strings = [text.text for text in texts]

    # Process in batch
    results = await sentiment_analyzer.batch_analyze.remote(text_strings)

    # Add to background task for logging
    background_tasks.add_task(
        store_request_history,
        current_user.username,
        "/sentiment/batch",
        {"text_count": len(texts)},
    )

    return results


@router.get("/examples")
async def get_sentiment_examples():
    """Get example texts with sentiment labels."""
    return [
        {"text": "I love this product, it's amazing!", "expected": "positive"},
        {"text": "This is the worst experience ever.", "expected": "negative"},
        {"text": "The package arrived on time.", "expected": "neutral"},
    ]
