import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Response types
interface WebSocketMessage {
  id: string;
  timestamp: string;
  type: 'sent' | 'received' | 'error' | 'connection';
  action?: string;
  data?: any;
}

interface SentimentResult {
  sentiment: string;
  score: number; // This is used as the confidence value
}

interface EntityResult {
  text: string;
  type: string;
  confidence: number;
}

interface ClassifyResult {
  label: string;
  score: number;
  is_top: boolean;
}

const WebSocketDemo: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [text, setText] = useState('');
  const [action, setAction] = useState('sentiment');
  const [customLabels, setCustomLabels] = useState('positive, negative, neutral');
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [connectionError, setConnectionError] = useState('');
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { token } = useAuth();

  // Connect to WebSocket
  useEffect(() => {
    // Function to establish connection
    const connectWebSocket = () => {
      // Close any existing connection
      if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
        ws.current.close();
      }

      try {
        // Create a new connection
        const socket = new WebSocket(`ws://localhost:8000/api/v1/ws?token=${token}`);
        ws.current = socket;

        // Connection opened
        socket.addEventListener('open', () => {
          setIsConnected(true);
          setConnectionError('');
          setMessages(prev => [
            ...prev,
            {
              id: Date.now().toString(),
              timestamp: new Date().toLocaleTimeString(),
              type: 'connection',
              data: 'Connected to WebSocket server'
            }
          ]);
        });

        // Connection closed
        socket.addEventListener('close', (event) => {
          setIsConnected(false);
          if (!event.wasClean) {
            setConnectionError('Connection closed unexpectedly');
            setMessages(prev => [
              ...prev,
              {
                id: Date.now().toString(),
                timestamp: new Date().toLocaleTimeString(),
                type: 'error',
                data: `Connection closed with code ${event.code}`
              }
            ]);
          } else {
            setMessages(prev => [
              ...prev,
              {
                id: Date.now().toString(),
                timestamp: new Date().toLocaleTimeString(),
                type: 'connection',
                data: 'Disconnected from server'
              }
            ]);
          }
        });

        // Connection error
        socket.addEventListener('error', (error) => {
          console.error('WebSocket error:', error);
          setConnectionError('Error connecting to WebSocket server');
          setMessages(prev => [
            ...prev,
            {
              id: Date.now().toString(),
              timestamp: new Date().toLocaleTimeString(),
              type: 'error',
              data: 'WebSocket connection error'
            }
          ]);
        });

        // Listen for messages
        socket.addEventListener('message', (event) => {
          try {
            const data = JSON.parse(event.data);
            setMessages(prev => [
              ...prev,
              {
                id: Date.now().toString(),
                timestamp: new Date().toLocaleTimeString(),
                type: 'received',
                data
              }
            ]);
          } catch (error) {
            console.error('Error parsing message:', error);
            setMessages(prev => [
              ...prev,
              {
                id: Date.now().toString(),
                timestamp: new Date().toLocaleTimeString(),
                type: 'error',
                data: 'Failed to parse message'
              }
            ]);
          }
        });
      } catch (error) {
        console.error('Failed to connect:', error);
        setConnectionError('Failed to establish WebSocket connection');
      }
    };

    // Connect to WebSocket
    connectWebSocket();

    // Cleanup on component unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [token]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!text.trim()) {
      return;
    }
    
    if (!isConnected || !ws.current) {
      setConnectionError('WebSocket not connected');
      return;
    }
    
    try {
      let messageData: any = { action, text };
      
      // If action is classify, add labels
      if (action === 'classify') {
        const labels = customLabels.split(',').map(label => label.trim()).filter(Boolean);
        messageData.labels = labels;
      }
      
      // Send the message
      ws.current.send(JSON.stringify(messageData));
      
      // Add to messages list
      setMessages(prev => [
        ...prev,
        {
          id: Date.now().toString(),
          timestamp: new Date().toLocaleTimeString(),
          type: 'sent',
          action,
          data: messageData
        }
      ]);
      
      // Clear the input field
      setText('');
      
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now().toString(),
          timestamp: new Date().toLocaleTimeString(),
          type: 'error',
          data: 'Error sending message'
        }
      ]);
    }
  };

  const renderMessageContent = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'connection':
        return (
          <div className="text-blue-500 text-sm">{message.data}</div>
        );
      
      case 'error':
        return (
          <div className="text-red-500 text-sm">{message.data}</div>
        );
      
      case 'sent':
        return (
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-sm font-semibold text-blue-700">
              {message.action?.toUpperCase()} Request:
            </div>
            <pre className="text-xs mt-1 bg-white p-2 rounded overflow-x-auto">
              {JSON.stringify(message.data, null, 2)}
            </pre>
          </div>
        );
      
      case 'received':
        if (message.data.error) {
          return (
            <div className="bg-red-50 p-3 rounded-lg">
              <div className="text-sm font-semibold text-red-700">Error:</div>
              <div className="text-sm mt-1">{message.data.error}</div>
            </div>
          );
        }
        
        if (message.data.sentiment) {
          // Sentiment analysis result
          const result = message.data as SentimentResult;
          const sentimentColor = 
            result.sentiment === 'positive' ? 'text-green-600' :
            result.sentiment === 'negative' ? 'text-red-600' : 'text-gray-600';
          
          return (
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-sm font-semibold text-green-700">Sentiment Result:</div>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <div>
                  <span className="text-xs text-gray-500">Sentiment:</span>
                  <div className={`font-medium ${sentimentColor}`}>
                    {result.sentiment.toUpperCase()}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-gray-500">Score:</span>
                  <div className="font-medium">{result.score.toFixed(4)}</div>
                </div>
                <div className="col-span-2">
                  <span className="text-xs text-gray-500">Confidence:</span>
                  <div className="mt-1">
                    <div className="h-2 bg-gray-200 rounded-full">
                      <div 
                        className="h-2 bg-blue-600 rounded-full" 
                        style={{ width: `${result.score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-600">{(result.score * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </div>
          );
        }
        
        if (message.data.entities) {
          // Named Entity Recognition result
          const entities = message.data.entities as EntityResult[];
          
          return (
            <div className="bg-indigo-50 p-3 rounded-lg">
              <div className="text-sm font-semibold text-indigo-700">
                Entities Result: <span className="font-normal">Found {entities.length} entities</span>
              </div>
              {entities.length > 0 ? (
                <div className="mt-2 space-y-2">
                  {entities.map((entity, idx) => (
                    <div key={idx} className="bg-white p-2 rounded border border-indigo-100">
                      <div className="flex justify-between">
                        <span className="font-medium">{entity.text}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100">
                          {entity.type}
                        </span>
                      </div>
                      <div className="text-xs mt-1 text-gray-500">
                        Confidence: {(entity.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm mt-2 text-gray-500">No entities found.</div>
              )}
            </div>
          );
        }
        
        if (message.data.classifications) {
          // Classification result
          const classifications = message.data.classifications as ClassifyResult[];
          const topClass = message.data.top_class || '';
          
          return (
            <div className="bg-amber-50 p-3 rounded-lg">
              <div className="text-sm font-semibold text-amber-700">
                Classification Result:
              </div>
              <div className="mt-1">
                <span className="text-xs text-gray-500">Top Class:</span>
                <div className="text-sm font-medium bg-amber-100 text-amber-800 px-2 py-0.5 rounded inline-block">
                  {topClass}
                </div>
              </div>
              <div className="mt-2 space-y-1">
                {classifications.map((classification, idx) => (
                  <div 
                    key={idx}
                    className={`flex items-center justify-between p-2 rounded ${
                      classification.is_top ? 'bg-amber-100' : 'bg-white'
                    }`}
                  >
                    <span className="text-sm">{classification.label}</span>
                    <span className="text-xs">
                      {(classification.score * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          );
        }
        
        // Generic response
        return (
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm font-semibold text-gray-700">Response:</div>
            <pre className="text-xs mt-1 bg-white p-2 rounded overflow-x-auto">
              {JSON.stringify(message.data, null, 2)}
            </pre>
          </div>
        );
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">WebSocket Demo</h1>
      <p className="text-gray-600 mb-6">
        Experience bi-directional real-time communication with the NLP backend.
      </p>
      
      <div className="flex flex-col md:flex-row gap-6">
        {/* Left side: Controls */}
        <div className="w-full md:w-1/3">
          <div className="bg-white shadow-sm rounded-lg p-6">
            <div className="flex items-center mb-4">
              <div 
                className={`h-3 w-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
              ></div>
              <span className="font-medium">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            
            {connectionError && (
              <div className="text-red-500 text-sm mb-4">{connectionError}</div>
            )}
            
            <form onSubmit={sendMessage}>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  Action Type
                </label>
                <div className="relative">
                  <select
                    className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    value={action}
                    onChange={(e) => setAction(e.target.value)}
                  >
                    <option value="sentiment">Sentiment Analysis</option>
                    <option value="entities">Named Entity Recognition</option>
                    <option value="classify">Text Classification</option>
                  </select>
                </div>
              </div>
              
              {action === 'classify' && (
                <div className="mb-4">
                  <label htmlFor="customLabels" className="block text-gray-700 text-sm font-medium mb-2">
                    Classification Labels
                  </label>
                  <input
                    type="text"
                    id="customLabels"
                    className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Enter labels separated by commas"
                    value={customLabels}
                    onChange={(e) => setCustomLabels(e.target.value)}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Enter labels, separated by commas
                  </p>
                </div>
              )}
              
              <div className="mb-4">
                <label htmlFor="text" className="block text-gray-700 text-sm font-medium mb-2">
                  Text to Analyze
                </label>
                <textarea
                  id="text"
                  rows={4}
                  className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  placeholder="Enter text to analyze..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  disabled={!isConnected}
                ></textarea>
              </div>
              
              <button
                type="submit"
                disabled={!isConnected || !text.trim()}
                className={`w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                  (!isConnected || !text.trim()) ? 'opacity-70 cursor-not-allowed' : ''
                }`}
              >
                Send Message
              </button>
            </form>
            
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Quick Examples:</h3>
              <div className="space-y-2">
                <button
                  type="button"
                  disabled={!isConnected}
                  onClick={() => {
                    setText('I love this product! It works perfectly and exceeds my expectations.');
                    setAction('sentiment');
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800 block"
                >
                  Positive sentiment example
                </button>
                <button
                  type="button"
                  disabled={!isConnected}
                  onClick={() => {
                    setText('Apple is planning to open a new campus in Austin, Texas this year.');
                    setAction('entities');
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800 block"
                >
                  Entities example
                </button>
                <button
                  type="button"
                  disabled={!isConnected}
                  onClick={() => {
                    setText('How do I change my password on this site?');
                    setAction('classify');
                    setCustomLabels('question, statement, command');
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800 block"
                >
                  Classification example
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Right side: Messages */}
        <div className="w-full md:w-2/3">
          <div className="bg-white shadow-sm rounded-lg p-4 h-[600px] flex flex-col">
            <h2 className="text-lg font-medium mb-3">Messages</h2>
            
            <div className="flex-1 overflow-y-auto border rounded-md p-3 bg-gray-50">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-4">
                  No messages yet. Send a message to see the results.
                </div>
              ) : (
                <div className="space-y-3">
                  {messages.map((message) => (
                    <div key={message.id} className="message">
                      <div className="text-xs text-gray-400 mb-1">
                        {message.timestamp}
                      </div>
                      {renderMessageContent(message)}
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebSocketDemo; 