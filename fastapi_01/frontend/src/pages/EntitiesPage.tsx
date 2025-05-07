import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface Entity {
  text: string;
  type: string;
  start: number;
  end: number;
  score: number;
}

interface EntityResult {
  text: string;
  entities: Entity[];
  analysis_time_ms: number;
}

// Add interface for text segments
interface TextSegment {
  text: string;
  isEntity: boolean;
  entity?: Entity;
}

const getEntityColor = (entityType: string): string => {
  const colors: Record<string, string> = {
    'PERSON': 'bg-purple-100 text-purple-800 border-purple-300',
    'ORGANIZATION': 'bg-blue-100 text-blue-800 border-blue-300',
    'LOCATION': 'bg-green-100 text-green-800 border-green-300',
    'DATE': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'MONEY': 'bg-emerald-100 text-emerald-800 border-emerald-300',
    'PRODUCT': 'bg-red-100 text-red-800 border-red-300',
    'EVENT': 'bg-indigo-100 text-indigo-800 border-indigo-300',
    'WORK_OF_ART': 'bg-pink-100 text-pink-800 border-pink-300',
  };

  return colors[entityType] || 'bg-gray-100 text-gray-800 border-gray-300';
};

const EntityCard: React.FC<{ entity: Entity }> = ({ entity }) => {
  return (
    <div className={`rounded-md p-3 border ${getEntityColor(entity.type)} mb-2`}>
      <div className="flex justify-between">
        <span className="font-medium">{entity.text}</span>
        <span className="text-xs px-2 py-1 rounded-full bg-white">
          {entity.type}
        </span>
      </div>
      <div className="text-xs mt-1">
        <span>Position: {entity.start}-{entity.end}</span>
        <div className="mt-1">
          <div className="flex items-center">
            <span className="mr-2">Confidence:</span>
            <div className="flex-1 h-2 bg-gray-200 rounded-full">
              <div 
                className="h-2 bg-blue-600 rounded-full" 
                style={{ width: `${entity.score * 100}%` }}
              ></div>
            </div>
            <span className="ml-2">{(entity.score * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const HighlightedText: React.FC<{ text: string, entities: Entity[] }> = ({ text, entities }) => {
  if (!entities.length) return <p>{text}</p>;

  // Sort entities by start position
  const sortedEntities = [...entities].sort((a, b) => a.start - b.start);
  
  // Create an array of text segments with highlighted entities
  const segments: TextSegment[] = [];
  let lastIndex = 0;
  
  sortedEntities.forEach((entity, index) => {
    // Add text before this entity
    if (entity.start > lastIndex) {
      segments.push({
        text: text.substring(lastIndex, entity.start),
        isEntity: false,
      });
    }
    
    // Add the entity
    segments.push({
      text: text.substring(entity.start, entity.end),
      isEntity: true,
      entity,
    });
    
    lastIndex = entity.end;
    
    // Add the remaining text after the last entity
    if (index === sortedEntities.length - 1 && lastIndex < text.length) {
      segments.push({
        text: text.substring(lastIndex),
        isEntity: false,
      });
    }
  });
  
  return (
    <p className="whitespace-pre-wrap">
      {segments.map((segment, index) => {
        if (!segment.isEntity) {
          return <span key={index}>{segment.text}</span>;
        }
        
        const entity = segment.entity as Entity;
        return (
          <span 
            key={index}
            className={`${getEntityColor(entity.type)} px-1 rounded cursor-pointer`}
            title={`${entity.type} (${(entity.score * 100).toFixed(1)}%)`}
          >
            {segment.text}
          </span>
        );
      })}
    </p>
  );
};

const EntitiesPage: React.FC = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState<EntityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [minConfidence, setMinConfidence] = useState(0.5);
  const { token } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Please enter some text to analyze');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/entities',
        { text, min_confidence: minConfidence },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setResult(response.data);
    } catch (err) {
      console.error('Entity recognition error:', err);
      setError('Failed to recognize entities. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filteredEntities = result?.entities.filter(
    entity => entity.score >= minConfidence
  ) || [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Named Entity Recognition</h1>
      <p className="text-gray-600 mb-6">
        Extract named entities like people, organizations, locations, and more from text.
      </p>
      
      <div className="bg-white shadow-sm rounded-lg p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="text" className="block text-gray-700 text-sm font-medium mb-2">
              Enter Text to Analyze
            </label>
            <textarea
              id="text"
              rows={4}
              className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
              placeholder="Enter text for entity recognition..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            ></textarea>
          </div>
          
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">
              Minimum Confidence: {(minConfidence * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          
          {error && (
            <div className="text-red-500 text-sm mb-4">{error}</div>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className={`w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              loading ? 'opacity-70 cursor-not-allowed' : ''
            }`}
          >
            {loading ? 'Analyzing...' : 'Extract Entities'}
          </button>
        </form>
      </div>
      
      {result && (
        <div className="mt-6 space-y-6">
          {/* Highlighted Text View */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Highlighted Text</h3>
            <div className="bg-gray-50 p-4 rounded">
              <HighlightedText text={result.text} entities={filteredEntities} />
            </div>
            <div className="mt-2 text-sm text-gray-500">
              Processing Time: {result.analysis_time_ms} ms
            </div>
          </div>
          
          {/* Entity List */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Entities ({filteredEntities.length})
              </h3>
              <div className="text-sm text-gray-500">
                Showing entities with confidence ≥ {(minConfidence * 100).toFixed(0)}%
              </div>
            </div>
            
            {filteredEntities.length === 0 ? (
              <p className="text-gray-500">No entities found with current confidence threshold.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredEntities.map((entity, index) => (
                  <EntityCard key={index} entity={entity} />
                ))}
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
            onClick={() => setText('Apple Inc. is planning to open a new campus in Austin, Texas by 2022, said CEO Tim Cook on January 15th.')}
            className="text-sm text-blue-600 hover:text-blue-800 block"
          >
            Company and location example
          </button>
          <button
            type="button"
            onClick={() => setText('The Eiffel Tower in Paris, France was completed on March 31, 1889 and cost 7,799,401.31 French gold francs to build.')}
            className="text-sm text-blue-600 hover:text-blue-800 block"
          >
            Landmark, location and date example
          </button>
          <button
            type="button"
            onClick={() => setText('J.K. Rowling wrote Harry Potter and the Philosopher\'s Stone, which was later adapted into a movie by Warner Bros.')}
            className="text-sm text-blue-600 hover:text-blue-800 block"
          >
            Person and work of art example
          </button>
        </div>
      </div>
    </div>
  );
};

export default EntitiesPage; 