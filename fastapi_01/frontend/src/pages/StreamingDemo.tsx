import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface StreamingResult {
  id: number;
  chunk: string;
  chunk_index: number;
  sentiment: string;
  sentiment_score: number;
  entities: Array<{
    text: string;
    type: string;
    start_in_chunk: number;
    end_in_chunk: number;
    confidence: number;
  }>;
  is_final: boolean;
}

const getEntityColor = (entityType: string): string => {
  const colors: Record<string, string> = {
    'PERSON': 'bg-purple-100 text-purple-800',
    'ORGANIZATION': 'bg-blue-100 text-blue-800',
    'LOCATION': 'bg-green-100 text-green-800',
    'DATE': 'bg-yellow-100 text-yellow-800',
    'MONEY': 'bg-emerald-100 text-emerald-800',
    'PRODUCT': 'bg-red-100 text-red-800',
    'EVENT': 'bg-indigo-100 text-indigo-800',
    'WORK_OF_ART': 'bg-pink-100 text-pink-800',
  };

  return colors[entityType] || 'bg-gray-100 text-gray-800';
};

const getSentimentColor = (sentiment: string): string => {
  switch (sentiment.toLowerCase()) {
    case 'positive':
      return 'text-green-600';
    case 'negative':
      return 'text-red-600';
    case 'neutral':
      return 'text-gray-600';
    default:
      return 'text-gray-600';
  }
};

const getSentimentEmoji = (sentiment: string): string => {
  switch (sentiment.toLowerCase()) {
    case 'positive':
      return '😊';
    case 'negative':
      return '😠';
    case 'neutral':
      return '😐';
    default:
      return '';
  }
};

const StreamingChunk: React.FC<{ result: StreamingResult }> = ({ result }) => {
  return (
    <div className={`p-4 mb-2 border rounded ${result.is_final ? 'bg-white' : 'bg-gray-50'}`}>
      <div className="flex justify-between mb-2">
        <span className="text-xs text-gray-500">Chunk {result.chunk_index + 1}</span>
        <span className={`flex items-center text-sm font-medium ${getSentimentColor(result.sentiment)}`}>
          {getSentimentEmoji(result.sentiment)} {result.sentiment}
          <span className="ml-1 text-xs text-gray-500">
            ({(result.sentiment_score * 100).toFixed(1)}%)
          </span>
        </span>
      </div>
      
      <div className="text-base">
        {result.entities && result.entities.length > 0 ? (
          <HighlightedChunk chunk={result.chunk} entities={result.entities} />
        ) : (
          <span>{result.chunk}</span>
        )}
      </div>
      
      {result.entities && result.entities.length > 0 && (
        <div className="mt-2">
          <div className="text-xs text-gray-500 mb-1">Entities:</div>
          <div className="flex flex-wrap gap-1">
            {result.entities.map((entity, idx) => (
              <span 
                key={idx}
                className={`text-xs px-2 py-0.5 rounded ${getEntityColor(entity.type)}`}
                title={`Confidence: ${(entity.confidence * 100).toFixed(1)}%`}
              >
                {entity.text} ({entity.type})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const HighlightedChunk: React.FC<{ 
  chunk: string, 
  entities: Array<{
    text: string;
    type: string;
    start_in_chunk: number;
    end_in_chunk: number;
    confidence: number;
  }> 
}> = ({ chunk, entities }) => {
  // If there are no valid entities with start and end positions, just return the text
  const validEntities = entities.filter(e => 
    typeof e.start_in_chunk === 'number' && 
    typeof e.end_in_chunk === 'number' &&
    e.start_in_chunk >= 0 && 
    e.end_in_chunk <= chunk.length
  );
  
  if (validEntities.length === 0) {
    return <span>{chunk}</span>;
  }
  
  // Sort entities by start position
  const sortedEntities = [...validEntities].sort((a, b) => a.start_in_chunk - b.start_in_chunk);
  
  // Create an array of text segments with highlighted entities
  const segments: Array<{
    text: string;
    isEntity: boolean;
    entity?: typeof entities[0];
  }> = [];
  
  let lastIndex = 0;
  
  sortedEntities.forEach((entity, index) => {
    // Add text before this entity
    if (entity.start_in_chunk > lastIndex) {
      segments.push({
        text: chunk.substring(lastIndex, entity.start_in_chunk),
        isEntity: false,
      });
    }
    
    // Add the entity
    segments.push({
      text: chunk.substring(entity.start_in_chunk, entity.end_in_chunk),
      isEntity: true,
      entity,
    });
    
    lastIndex = entity.end_in_chunk;
    
    // Add the remaining text after the last entity
    if (index === sortedEntities.length - 1 && lastIndex < chunk.length) {
      segments.push({
        text: chunk.substring(lastIndex),
        isEntity: false,
      });
    }
  });
  
  return (
    <span>
      {segments.map((segment, index) => {
        if (!segment.isEntity) {
          return <span key={index}>{segment.text}</span>;
        }
        
        const entity = segment.entity!;
        return (
          <span 
            key={index}
            className={`${getEntityColor(entity.type)} px-1 rounded cursor-pointer`}
            title={`${entity.type} (${(entity.confidence * 100).toFixed(1)}%)`}
          >
            {segment.text}
          </span>
        );
      })}
    </span>
  );
};

const StreamingDemo: React.FC = () => {
  const [text, setText] = useState('');
  const [results, setResults] = useState<StreamingResult[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState('');
  const eventSourceRef = useRef<EventSource | null>(null);
  const resultContainerRef = useRef<HTMLDivElement>(null);
  const { token } = useAuth();

  const startStreaming = () => {
    if (!text.trim()) {
      setError('Please enter some text to analyze');
      return;
    }
    
    setResults([]);
    setError('');
    setIsStreaming(true);
    
    // URL encode the parameters with all required fields
    const params = new URLSearchParams({
      text: text,
      min_confidence: '0.5',
      token: token || '' // Ensure token is a string
    }).toString();
    
    // Create EventSource without withCredentials option which can cause CORS issues
    const eventSource = new EventSource(
      `http://localhost:8000/api/v1/streaming/analyze?${params}`
    );
    
    eventSourceRef.current = eventSource;
    
    // Set up event handlers
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received SSE data:", data);
        
        // Add a unique ID for React key if not present
        if (!data.id) {
          data.id = Date.now() + Math.random();
        }
        
        // For status updates, handle differently
        if (data.status) {
          if (data.status === 'error') {
            setError(data.message || 'An error occurred during analysis');
            stopStreaming();
            return;
          }
          
          if (data.status === 'completed') {
            stopStreaming();
            return;
          }
        } else {
          // Format chunk data to match the StreamingResult interface
          const formattedResult: StreamingResult = {
            id: data.chunk_id || Date.now(),
            chunk: data.chunk_text || '',
            chunk_index: data.chunk_id || 0,
            sentiment: data.sentiment || 'neutral',
            sentiment_score: data.sentiment_score || 0.5,
            entities: data.entities?.map((entity: any) => ({
              text: entity.word || entity.text || '',
              type: entity.entity || entity.type || 'MISC',
              start_in_chunk: entity.start || 0,
              end_in_chunk: entity.end || 0,
              confidence: entity.score || entity.confidence || 0.5
            })) || [],
            is_final: data.progress === 1
          };
          
          console.log('Formatted entity data:', formattedResult.entities);
          
          setResults(prev => [...prev, formattedResult]);
        }
      } catch (error) {
        console.error('Error parsing event data:', error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      setError('Error connecting to streaming API. Please try again.');
      stopStreaming();
    };
  };
  
  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  };
  
  // Auto-scroll to bottom when new results come in
  useEffect(() => {
    if (resultContainerRef.current && results.length > 0) {
      resultContainerRef.current.scrollTop = resultContainerRef.current.scrollHeight;
    }
  }, [results]);
  
  // Clean up EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    startStreaming();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Streaming Analysis Demo</h1>
      <p className="text-gray-600 mb-6">
        Experience real-time text processing with Server-Sent Events (SSE).
        Enter a longer text and see how it's processed chunk by chunk.
      </p>
      
      <div className="bg-white shadow-sm rounded-lg p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="text" className="block text-gray-700 text-sm font-medium mb-2">
              Enter Text to Analyze
            </label>
            <textarea
              id="text"
              rows={6}
              className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
              placeholder="Enter a longer text for streaming analysis..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isStreaming}
            ></textarea>
          </div>
          
          {error && (
            <div className="text-red-500 text-sm mb-4">{error}</div>
          )}
          
          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={isStreaming}
              className={`flex-1 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                isStreaming ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              {isStreaming ? 'Streaming...' : 'Start Streaming Analysis'}
            </button>
            
            {isStreaming && (
              <button
                type="button"
                onClick={stopStreaming}
                className="flex-1 inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Stop Stream
              </button>
            )}
          </div>
        </form>
      </div>
      
      {/* Results Section */}
      {results.length > 0 && (
        <div className="mt-6">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-medium text-gray-900">Streaming Results</h3>
            <span className="text-sm text-gray-500">
              {results.length} chunk{results.length !== 1 ? 's' : ''} processed
            </span>
          </div>
          
          <div 
            ref={resultContainerRef}
            className="bg-white border rounded-lg p-4 max-h-96 overflow-y-auto"
          >
            {results.map((result) => (
              <StreamingChunk key={result.id} result={result} />
            ))}
            
            {isStreaming && (
              <div className="flex justify-center p-4">
                <div className="animate-pulse flex space-x-1">
                  <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                  <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                  <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      <div className="mt-8 bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h3 className="text-md font-medium text-blue-800 mb-2">Quick Examples</h3>
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => setText("The history of artificial intelligence began in antiquity, with myths, stories and rumors of artificial beings endowed with intelligence or consciousness by master craftsmen. The seeds of modern AI were planted by philosophers who attempted to describe the process of human thinking as the mechanical manipulation of symbols. This work culminated in the invention of the programmable digital computer in the 1940s, a machine based on the abstract essence of mathematical reasoning. This device and the ideas behind it inspired a handful of scientists to begin seriously discussing the possibility of building an electronic brain.\n\nThe field of AI research was founded at a workshop held on the campus of Dartmouth College in the summer of 1956. Those who attended would become the leaders of AI research for decades. Many of them predicted that a machine as intelligent as a human being would exist in no more than a generation, and they were given millions of dollars to make this vision come true.")}
            className="text-sm text-blue-600 hover:text-blue-800 block"
            disabled={isStreaming}
          >
            AI History example (longer text)
          </button>
          <button
            type="button"
            onClick={() => setText("New York City, often called simply New York and abbreviated as NYC, is the most populous city in the United States. With an estimated 2019 population of 8,336,817 distributed over 302.6 square miles, New York City is also the most densely populated major city in the United States. Located at the southern tip of the U.S. state of New York, the city is the center of the New York metropolitan area, the largest metropolitan area in the world by urban landmass. With almost 20 million people in its metropolitan statistical area and approximately 23 million in its combined statistical area, it is one of the world's most populous megacities. New York City has been described as the cultural, financial, and media capital of the world, significantly influencing commerce, entertainment, research, technology, education, politics, tourism, art, fashion, and sports. Home to the headquarters of the United Nations, New York is an important center for international diplomacy.")}
            className="text-sm text-blue-600 hover:text-blue-800 block"
            disabled={isStreaming}
          >
            New York City example (many entities)
          </button>
        </div>
      </div>
    </div>
  );
};

export default StreamingDemo; 