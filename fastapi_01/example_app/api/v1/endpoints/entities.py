from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import json
import asyncio
import time
from fastapi import BackgroundTasks

from example_app.api.models import TextRequest, EntityResponse
from example_app.api.security import get_current_active_user, User
from example_app.serve import get_deployment, get_entity_recognizer
from example_app.db.database import generate_cache_key, get_cached_response, set_cached_response, store_request_history

router = APIRouter(prefix="/entities", tags=["entities"])

@router.post("", response_model=EntityResponse)
async def extract_entities(
    request: TextRequest,
    current_user: User = Depends(get_current_active_user),
    entity_recognizer = Depends(get_entity_recognizer)
):
    """
    Extract named entities from text.
    
    Identifies people, organizations, locations, dates, etc. in the input text.
    """
    # Try to get from cache
    cache_key = await generate_cache_key("entities", request.text)
    cached_result = await get_cached_response(cache_key)
    
    if cached_result:
        return cached_result
    
    result = await entity_recognizer.recognize_entities.remote(request.text)
    
    # Cache result
    await set_cached_response(cache_key, result, expire=3600)
    
    # Store in history
    await store_request_history(
        current_user.username, 
        "/entities", 
        {"text": request.text}
    )
    
    return result

@router.post("/stream")
async def stream_entities(
    request: TextRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Stream entity extraction results.
    
    This endpoint demonstrates streaming response for entity extraction.
    """
    entity_recognizer = get_deployment("entity_recognizer")
    
    async def generate():
        # Initial response
        yield json.dumps({"status": "processing"}) + "\n"
        
        # Get entities
        result = await entity_recognizer.recognize_entities.remote(request.text)
        
        # Stream entities one by one (simulating real-time extraction)
        if result["entities"]:
            for i, entity in enumerate(result["entities"]):
                # Simulate processing delay
                await asyncio.sleep(0.2)
                
                # Stream each entity
                yield json.dumps({
                    "status": "extracting",
                    "progress": (i + 1) / len(result["entities"]),
                    "entity": entity
                }) + "\n"
        
        # Final result
        yield json.dumps({
            "status": "completed",
            "text": result["text"],
            "entities_count": len(result["entities"]),
            "processing_time": result["processing_time"]
        }) + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/json"
    )

@router.get("/filter")
async def filter_entities(
    text: str = Query(..., min_length=1, description="Text to analyze"),
    entity_types: List[str] = Query(None, description="Entity types to include"),
    min_score: float = Query(0.5, ge=0, le=1, description="Minimum confidence score")
):
    """
    Filter entities by type and confidence score.
    
    Demonstrates query parameter validation and filtering.
    """
    # Get Ray Serve deployment
    entity_recognizer = get_deployment("entity_recognizer")
    
    # Get all entities
    result = await entity_recognizer.recognize_entities.remote(text)
    
    # Filter entities
    filtered_entities = result["entities"]
    
    if entity_types:
        filtered_entities = [e for e in filtered_entities if e["type"] in entity_types]
        
    filtered_entities = [e for e in filtered_entities if e["score"] >= min_score]
    
    # Return filtered result
    return {
        "text": result["text"],
        "entities": filtered_entities,
        "processing_time": result["processing_time"],
        "filtered_from": len(result["entities"]),
        "filtered_to": len(filtered_entities)
    } 