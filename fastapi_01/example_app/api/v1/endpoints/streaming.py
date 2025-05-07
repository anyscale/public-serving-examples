from typing import List, Dict, Any, Optional
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import ray

from example_app.api.security import get_current_active_user, User
from example_app.serve import get_deployment, get_streaming_analyzer

router = APIRouter(prefix="/streaming", tags=["streaming"])


class StreamingTextRequest(BaseModel):
    """Request model for streaming text analysis."""
    text: str = Field(..., min_length=1, max_length=100000, description="Text to analyze")
    analysis_types: List[str] = Field(
        default=["sentiment", "entities"],
        description="Types of analysis to perform"
    )
    chunk_delay: Optional[float] = Field(
        default=None, 
        description="Optional delay between chunks in seconds to simulate slower processing"
    )


@router.post("/analyze")
async def stream_analyze_text(
    request: StreamingTextRequest,
    current_user: User = Depends(get_current_active_user),
    streaming_analyzer = Depends(get_streaming_analyzer)
):
    """
    Stream analysis of text in real-time.
    
    This endpoint processes text in chunks and returns results as they become available.
    It showcases the streaming capabilities of FastAPI and Ray Serve.
    
    Results are streamed as Server-Sent Events (SSE).
    """
    
    async def generate():
        # Send initial processing message
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Starting analysis'})}\n\n"
        
        try:
            # Start the streaming analysis
            async for chunk_result in streaming_analyzer.options(stream=True).stream_analysis.remote(
                request.text, 
                request.analysis_types
            ):
                # Convert result to JSON and yield as SSE
                yield f"data: {json.dumps(chunk_result)}\n\n"
                
                # Add optional delay if specified
                if request.chunk_delay:
                    await asyncio.sleep(request.chunk_delay)
                    
            # Send completion message    
            yield f"data: {json.dumps({'status': 'completed', 'message': 'Analysis complete'})}\n\n"
            
        except Exception as e:
            # Send error message
            error_msg = f"Error during analysis: {str(e)}"
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in Nginx
        }
    )


@router.post("/analyze/document", response_model=Dict[str, Any])
async def analyze_document(
    request: StreamingTextRequest,
    current_user: User = Depends(get_current_active_user),
    streaming_analyzer = Depends(get_streaming_analyzer)
):
    """
    Analyze an entire document with the same streaming backend.
    
    This endpoint processes the document in chunks using the streaming backend
    but returns a single comprehensive result. It's useful for comparing
    streaming vs. non-streaming approaches.
    """
    
    # Process the document
    result = await streaming_analyzer.options(stream=False).analyze_document.remote(
        request.text,
        request.analysis_types
    )
    
    return result


@router.get("/demo")
async def get_demo_page():
    """
    Return a simple HTML page that demonstrates the streaming API.
    
    This page includes a text input field and displays streaming results
    in real-time.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Streaming NLP Analysis Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .container {
                display: flex;
                gap: 20px;
            }
            .input-section, .results-section {
                flex: 1;
                padding: 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            textarea {
                width: 100%;
                min-height: 300px;
                margin-bottom: 10px;
            }
            button {
                padding: 10px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            #results {
                height: 400px;
                overflow-y: auto;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            .chunk {
                margin-bottom: 15px;
                padding: 10px;
                border-left: 3px solid #4CAF50;
                background-color: #f0f0f0;
            }
            .entity {
                display: inline-block;
                margin: 2px;
                padding: 2px 5px;
                border-radius: 3px;
            }
            .PER { background-color: #ffcccc; }
            .ORG { background-color: #ccffcc; }
            .LOC { background-color: #ccccff; }
            .MISC { background-color: #ffffcc; }
            .sentiment-positive { color: green; }
            .sentiment-negative { color: red; }
            .sentiment-neutral { color: gray; }
            .progress-bar {
                height: 20px;
                background-color: #e0e0e0;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .progress-bar-fill {
                height: 100%;
                background-color: #4CAF50;
                border-radius: 10px;
                width: 0%;
                transition: width 0.3s ease;
            }
        </style>
    </head>
    <body>
        <h1>Streaming NLP Analysis Demo</h1>
        <p>This demo showcases real-time text analysis using FastAPI streaming responses and Ray Serve.</p>
        
        <div class="progress-bar">
            <div id="progress" class="progress-bar-fill"></div>
        </div>
        
        <div class="container">
            <div class="input-section">
                <h2>Input</h2>
                <textarea id="text-input" placeholder="Enter text to analyze...">The Apple conference in San Francisco was attended by Tim Cook. Microsoft announced their latest Surface device at the event. The event was hosted at the Moscone Center.</textarea>
                <div>
                    <label><input type="checkbox" id="sentiment-check" checked> Sentiment Analysis</label>
                    <label><input type="checkbox" id="entities-check" checked> Named Entity Recognition</label>
                </div>
                <div>
                    <label>Artificial delay between chunks (ms): <input type="number" id="delay-input" value="300" min="0" max="5000"></label>
                </div>
                <button id="analyze-btn">Analyze Text</button>
            </div>
            
            <div class="results-section">
                <h2>Results <small>(streaming)</small></h2>
                <div id="results"></div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const analyzeBtn = document.getElementById('analyze-btn');
                const textInput = document.getElementById('text-input');
                const resultsDiv = document.getElementById('results');
                const progressBar = document.getElementById('progress');
                const sentimentCheck = document.getElementById('sentiment-check');
                const entitiesCheck = document.getElementById('entities-check');
                const delayInput = document.getElementById('delay-input');
                
                analyzeBtn.addEventListener('click', function() {
                    startAnalysis();
                });
                
                function startAnalysis() {
                    // Clear previous results
                    resultsDiv.innerHTML = '';
                    progressBar.style.width = '0%';
                    analyzeBtn.disabled = true;
                    
                    // Get analysis types
                    const analysisTypes = [];
                    if (sentimentCheck.checked) analysisTypes.push('sentiment');
                    if (entitiesCheck.checked) analysisTypes.push('entities');
                    
                    // Calculate delay in seconds
                    const delayInSeconds = parseInt(delayInput.value) / 1000;
                    
                    // Prepare request
                    const request = {
                        text: textInput.value,
                        analysis_types: analysisTypes,
                        chunk_delay: delayInSeconds
                    };
                    
                    // Make the streaming request
                    fetch('/api/v1/streaming/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(request)
                    }).then(response => {
                        const reader = response.body.getReader();
                        const decoder = new TextDecoder();
                        
                        return new ReadableStream({
                            start(controller) {
                                function push() {
                                    reader.read().then(({ done, value }) => {
                                        if (done) {
                                            controller.close();
                                            analyzeBtn.disabled = false;
                                            return;
                                        }
                                        
                                        const chunk = decoder.decode(value, { stream: true });
                                        processChunk(chunk);
                                        controller.enqueue(value);
                                        push();
                                    });
                                }
                                
                                push();
                            }
                        });
                    });
                }
                
                function processChunk(textChunk) {
                    // Split the chunk by double newlines (SSE format)
                    const lines = textChunk.split('\\n\\n');
                    
                    lines.forEach(line => {
                        if (line.startsWith('data:')) {
                            // Extract the JSON data
                            const jsonStr = line.substring(5).trim();
                            try {
                                const data = JSON.parse(jsonStr);
                                displayResult(data);
                            } catch (e) {
                                console.error('Error parsing JSON:', e);
                            }
                        }
                    });
                }
                
                function displayResult(data) {
                    // Handle status messages
                    if (data.status === 'processing' || data.status === 'completed' || data.status === 'error') {
                        const statusDiv = document.createElement('div');
                        statusDiv.className = 'status-message';
                        statusDiv.innerHTML = `<strong>${data.status}:</strong> ${data.message}`;
                        resultsDiv.appendChild(statusDiv);
                        resultsDiv.scrollTop = resultsDiv.scrollHeight;
                        return;
                    }
                    
                    // Handle chunk results
                    if (data.chunk_id !== undefined) {
                        // Update progress bar
                        progressBar.style.width = `${data.progress * 100}%`;
                        
                        // Create chunk div
                        const chunkDiv = document.createElement('div');
                        chunkDiv.className = 'chunk';
                        
                        // Add chunk header
                        chunkDiv.innerHTML = `<h3>Chunk ${data.chunk_id + 1}/${data.total_chunks}</h3>`;
                        chunkDiv.innerHTML += `<p>${data.chunk_text}</p>`;
                        
                        // Add sentiment if available
                        if (data.sentiment) {
                            const sentimentClass = `sentiment-${data.sentiment}`;
                            chunkDiv.innerHTML += `<p>Sentiment: <span class="${sentimentClass}">${data.sentiment}</span> (${(data.sentiment_score * 100).toFixed(1)}%)</p>`;
                        }
                        
                        // Add entities if available
                        if (data.entities && data.entities.length > 0) {
                            const entitiesDiv = document.createElement('div');
                            entitiesDiv.innerHTML = '<p>Entities:</p>';
                            
                            const entitiesList = document.createElement('div');
                            data.entities.forEach(entity => {
                                const entitySpan = document.createElement('span');
                                entitySpan.className = `entity ${entity.entity}`;
                                entitySpan.textContent = `${entity.word} (${entity.entity})`;
                                entitiesList.appendChild(entitySpan);
                            });
                            
                            entitiesDiv.appendChild(entitiesList);
                            chunkDiv.appendChild(entitiesDiv);
                        }
                        
                        // Add processing time
                        chunkDiv.innerHTML += `<p><small>Processed in ${(data.processing_time * 1000).toFixed(0)}ms</small></p>`;
                        
                        resultsDiv.appendChild(chunkDiv);
                        resultsDiv.scrollTop = resultsDiv.scrollHeight;
                    }
                }
            });
        </script>
    </body>
    </html>
    """
    
    return StreamingResponse(
        content=iter([html_content]), 
        media_type="text/html"
    ) 