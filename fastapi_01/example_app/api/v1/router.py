from datetime import timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm

from example_app.api.security import (
    Token, User, UserInDB, USERS_DB,
    authenticate_user, create_access_token, get_current_active_user, requires_role
)
from example_app.api.models import HealthResponse
from example_app.config import ACCESS_TOKEN_EXPIRE_MINUTES, API_V1_STR
from example_app.serve import get_deployment
from example_app.api.v1.endpoints.sentiment import router as sentiment_router
from example_app.api.v1.endpoints.classification import router as classification_router
from example_app.api.v1.endpoints.entities import router as entities_router

# Create the API v1 router
router = APIRouter(prefix=API_V1_STR)

# Include all endpoint routers
router.include_router(sentiment_router)
router.include_router(classification_router)
router.include_router(entities_router)

# Authentication endpoints
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(USERS_DB, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time NLP processing.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if "action" not in data or "text" not in data:
                await websocket.send_json({"error": "Invalid message format"})
                continue
                
            action = data["action"]
            text = data["text"]
            
            # Process based on action
            if action == "sentiment":
                sentiment_analyzer = get_deployment("sentiment_analyzer")
                result = await sentiment_analyzer.analyze.remote(text)
                await websocket.send_json(result)
                
            elif action == "entities":
                entity_recognizer = get_deployment("entity_recognizer")
                result = await entity_recognizer.recognize_entities.remote(text)
                await websocket.send_json(result)
                
            elif action == "classify":
                if "labels" not in data or not data["labels"]:
                    await websocket.send_json({"error": "Labels required for classification"})
                    continue
                    
                classifier = get_deployment("text_classifier")
                result = await classifier.classify.remote(text, data["labels"])
                await websocket.send_json(result)
                
            else:
                await websocket.send_json({"error": f"Unknown action: {action}"})
                
    except WebSocketDisconnect:
        pass

# Health check endpoint
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    API health check endpoint.
    
    Returns service status and model availability.
    """
    # Check if models are available
    models_status = {}
    
    for model_name in ["sentiment_analyzer", "text_classifier", "entity_recognizer"]:
        try:
            deployment = get_deployment(model_name)
            # We don't want to actually call the model, just check if it's available
            models_status[model_name] = True
        except Exception:
            models_status[model_name] = False
    
    return {
        "status": "healthy" if all(models_status.values()) else "degraded",
        "version": "1.0",
        "models": models_status,
        "uptime_seconds": 0  # In a real app, you'd track uptime
    }

# Admin-only endpoint
@router.post("/admin/reload-models")
async def reload_models(current_user: User = Depends(requires_role("admin"))):
    """
    Reload NLP models.
    
    Demonstrates admin-only functionality.
    """
    # In a real app, this would actually reload the models
    return {"status": "success", "message": "Models reloaded successfully"} 