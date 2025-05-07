from typing import List, Dict, Any, Optional
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import ray
import logging

from example_app.api.security import get_current_active_user, User, verify_token
from example_app.serve import get_deployment, get_streaming_analyzer

router = APIRouter(prefix="/streaming", tags=["streaming"])


class StreamingTextRequest(BaseModel):
    """Request model for streaming text analysis."""

    text: str = Field(
        ..., min_length=1, max_length=100000, description="Text to analyze"
    )
    analysis_types: List[str] = Field(
        default=["sentiment", "entities"], description="Types of analysis to perform"
    )
    chunk_delay: Optional[float] = Field(
        default=None,
        description="Optional delay between chunks in seconds to simulate slower processing",
    )


@router.post("/analyze")
@router.get("/analyze")
async def stream_analyze_text(
    request: StreamingTextRequest = None,
    text: str = Query(None, description="Text to analyze"),
    analysis_types: List[str] = Query(["sentiment", "entities"], description="Types of analysis to perform"),
    min_confidence: float = Query(0.5, description="Minimum confidence threshold for entities"),
    chunk_delay: Optional[float] = Query(None, description="Optional delay between chunks in seconds"),
    token: str = Query(None, description="Authentication token"),
    streaming_analyzer=Depends(get_streaming_analyzer),
):
    """
    Stream analysis of text in real-time.

    This endpoint processes text in chunks and returns results as they become available.
    It showcases the streaming capabilities of FastAPI and Ray Serve.

    Results are streamed as Server-Sent Events (SSE).
    """
    
    # Manually verify token for SSE connections
    if token:
        try:
            # This will raise an exception if token is invalid
            user = await verify_token(token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Handle both query parameters (GET) and JSON body (POST)
    request_text = text if text else (request.text if request else None)
    request_analysis_types = analysis_types if request is None else request.analysis_types
    request_chunk_delay = chunk_delay if request is None else request.chunk_delay
    
    if not request_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text parameter is required"
        )

    async def generate():
        # Send initial processing message
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Starting analysis'})}\n\n"
        await asyncio.sleep(0.1)  # Small delay to ensure the client processes the first message

        try:
            # Start the streaming analysis
            chunk_count = 0
            async for chunk_result in streaming_analyzer.options(
                stream=True
            ).stream_analysis.remote(request_text, request_analysis_types):
                # Add chunk index for tracking
                chunk_count += 1
                
                # Ensure chunk_id is present for frontend mapping
                if 'chunk_id' not in chunk_result:
                    chunk_result['chunk_id'] = chunk_count
                    
                # Add progress information if not present
                if 'progress' not in chunk_result and 'total_chunks' in chunk_result:
                    chunk_result['progress'] = chunk_count / chunk_result['total_chunks']
                
                # Format entities for frontend compatibility
                if 'entities' in chunk_result and chunk_result['entities']:
                    # Add correct start/end positions for entity highlighting
                    for entity in chunk_result['entities']:
                        # Make sure we use the naming convention expected by frontend
                        entity['text'] = entity.get('word', '')
                        entity['type'] = entity.get('entity', 'MISC')
                        entity['confidence'] = entity.get('score', 0.5)
                        
                        # Ensure these are named correctly for frontend
                        entity['start_in_chunk'] = entity.get('start', 0)
                        entity['end_in_chunk'] = entity.get('end', 0)
                
                # Convert result to JSON and yield as SSE
                yield f"data: {json.dumps(chunk_result)}\n\n"
                await asyncio.sleep(0.1)  # Small delay between chunks for stability

                # Add optional delay if specified
                if request_chunk_delay:
                    await asyncio.sleep(request_chunk_delay)

            # Send completion message
            yield f"data: {json.dumps({'status': 'completed', 'message': 'Analysis complete'})}\n\n"

        except Exception as e:
            # Log the error
            import traceback
            logger = logging.getLogger("api.streaming")
            logger.error(f"Streaming error: {str(e)}\n{traceback.format_exc()}")
            
            # Send error message
            error_msg = f"Error during analysis: {str(e)}"
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in Nginx
            "Access-Control-Allow-Origin": "*",  # Allow any origin for SSE
        },
    )


@router.post("/analyze/document", response_model=Dict[str, Any])
async def analyze_document(
    request: StreamingTextRequest,
    current_user: User = Depends(get_current_active_user),
    streaming_analyzer=Depends(get_streaming_analyzer),
):
    """
    Analyze an entire document with the same streaming backend.

    This endpoint processes the document in chunks using the streaming backend
    but returns a single comprehensive result. It's useful for comparing
    streaming vs. non-streaming approaches.
    """

    # Process the document
    result = await streaming_analyzer.options(stream=False).analyze_document.remote(
        request.text, request.analysis_types
    )

    return result
