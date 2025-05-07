from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from fastapi.responses import JSONResponse

from exmaple_app.api.models import ClassificationRequest, ClassificationResponse
from exmaple_app.api.security import get_current_active_user, User
from exmaple_app.serve import get_deployment
from exmaple_app.db.database import generate_cache_key, get_cached_response, set_cached_response, store_request_history

router = APIRouter(prefix="/classify", tags=["classification"])

@router.post("", response_model=ClassificationResponse)
async def classify_text(
    request: ClassificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Classify text into given categories.
    
    Provide a list of possible labels and the model will classify the text accordingly.
    """
    # Validate request
    if not request.labels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one label must be provided"
        )
    
    # Try to get from cache
    cache_key = await generate_cache_key(
        "classify", 
        f"{request.text}|{','.join(request.labels)}|{request.multi_label}"
    )
    cached_result = await get_cached_response(cache_key)
    
    if cached_result:
        return cached_result
    
    # Get Ray Serve deployment
    classifier = get_deployment("text_classifier")
    
    # Call model
    result = await classifier.classify.remote(
        request.text, 
        request.labels,
        request.multi_label
    )
    
    # Cache result
    await set_cached_response(cache_key, result, expire=3600)
    
    # Store in history
    await store_request_history(
        current_user.username, 
        "/classify", 
        {
            "text": request.text, 
            "labels": request.labels,
            "multi_label": request.multi_label
        }
    )
    
    return result

@router.get("/presets/{preset_name}")
async def get_classification_preset(
    preset_name: str = Path(..., description="Name of the classification preset"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get predefined label sets for classification.
    
    Demonstrates path parameters and custom error handling.
    """
    presets = {
        "emotions": ["joy", "sadness", "anger", "fear", "surprise", "disgust"],
        "topics": ["sports", "politics", "technology", "entertainment", "health", "business"],
        "intent": ["question", "statement", "command", "request", "complaint"]
    }
    
    if preset_name not in presets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_name}' not found"
        )
        
    return {"name": preset_name, "labels": presets[preset_name]}

class ClassificationError(Exception):
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message

@router.exception_handler(ClassificationError)
async def classification_error_handler(request, exc):
    """Custom exception handler for classification errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_type": exc.name,
            "detail": exc.message,
            "error_code": 1001
        }
    )

@router.post("/custom")
async def custom_classification(
    text: str = Query(..., description="Text to classify"),
    labels: List[str] = Query(..., description="Labels for classification")
):
    """
    Classify text with query parameters instead of JSON body.
    
    Demonstrates query parameters and custom exceptions.
    """
    if len(labels) > 10:
        raise ClassificationError(
            name="too_many_labels",
            message="Maximum 10 labels allowed for custom classification"
        )
        
    # Get Ray Serve deployment
    classifier = get_deployment("text_classifier")
    
    # Call model
    result = await classifier.classify.remote(text, labels, False)
    
    return result 