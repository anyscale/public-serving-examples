# Streaming Text Analysis with FastAPI and Ray Serve

This implementation demonstrates how to use FastAPI's streaming response capabilities together with Ray Serve to create a real-time text analysis pipeline.

## Features

- **Incremental Text Processing**: Analyzes text chunk by chunk, returning results as they become available
- **Server-Sent Events (SSE)**: Uses SSE to push updates to the client in real-time
- **Interactive Demo Page**: Includes a web interface for testing the streaming capabilities
- **Multiple Analysis Types**: Supports sentiment analysis and named entity recognition in the same stream
- **Ray Serve Integration**: Deploys the text processing pipeline using Ray Serve for scalability

## How It Works

1. **Text Chunking**: The input text is split into manageable chunks (groups of sentences)
2. **Parallel Processing**: Each chunk is processed independently
3. **Streaming Results**: Results are streamed back to the client as they become available
4. **Real-time Updates**: The client displays results incrementally as they arrive

## API Endpoints

- **POST `/api/v1/streaming/analyze`**: Main streaming endpoint that processes text in chunks and returns results as an SSE stream
- **POST `/api/v1/streaming/analyze/document`**: Processes the entire document in chunks but returns a single comprehensive result
- **GET `/api/v1/streaming/demo`**: Returns an HTML page that demonstrates the streaming capabilities

## Implementation Details

### StreamingAnalyzer Deployment

The `StreamingAnalyzer` class is a Ray Serve deployment that:

1. Splits text into chunks using NLTK's sentence tokenizer
2. Analyzes sentiment using a DistilBERT model
3. Extracts named entities using a BERT-based NER model
4. Yields results as an async generator for streaming

### FastAPI Streaming

FastAPI's `StreamingResponse` is used to create a server-sent events (SSE) stream. The implementation:

1. Creates an async generator that yields JSON results as they become available
2. Formats the results according to the SSE protocol
3. Sets appropriate headers for SSE streaming

### Frontend Demo

The demo page uses JavaScript to:

1. Read the SSE stream using the Fetch API and ReadableStream
2. Parse and display results incrementally
3. Update a progress bar to show processing status
4. Style the results for better visualization

## Running the Demo

1. Start the FastAPI application with Ray Serve
2. Navigate to the `/api/v1/streaming/demo` endpoint in your browser
3. Enter some text to analyze or use the provided example
4. Click "Analyze Text" to see the streaming results in real-time

## Benefits of Streaming

- **Improved User Experience**: Users see partial results immediately instead of waiting for complete processing
- **Reduced Perceived Latency**: The application feels more responsive
- **Better Resource Utilization**: Processing happens in parallel with transmission
- **Scalability**: The system can handle large documents by processing and returning them incrementally
