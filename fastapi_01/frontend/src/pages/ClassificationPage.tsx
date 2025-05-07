import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface ClassificationResult {
  text: string;
  labels: {
    label: string;
    score: number;
  }[];
  processing_time: number;
}

interface Preset {
  name: string;
  labels: string[];
  description: string;
}

const ClassificationPage: React.FC = () => {
  const [text, setText] = useState('');
  const [customLabels, setCustomLabels] = useState('');
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [presetLoading, setPresetLoading] = useState(false);
  const [error, setError] = useState('');
  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState('');
  const { token } = useAuth();

  // Fetch presets
  useEffect(() => {
    const fetchPresets = async () => {
      setPresetLoading(true);
      try {
        // This is a mock implementation - modify to use actual API if available
        // In a real app, you might call an endpoint like:
        // const response = await axios.get('http://localhost:8000/api/v1/classify/presets', 
        //   { headers: { Authorization: `Bearer ${token}` } }
        // );
        
        // For now, we'll use a static list of presets
        const mockPresets: Preset[] = [
          {
            name: 'sentiment',
            labels: ['positive', 'negative', 'neutral'],
            description: 'Basic sentiment classification'
          },
          {
            name: 'emotion',
            labels: ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust'],
            description: 'Emotional tone detection'
          },
          {
            name: 'intent',
            labels: ['question', 'statement', 'command', 'request'],
            description: 'User intent classification'
          },
          {
            name: 'support',
            labels: ['bug_report', 'feature_request', 'account_issue', 'billing_question', 'general_inquiry'],
            description: 'Customer support categorization'
          }
        ];
        
        setPresets(mockPresets);
      } catch (err) {
        console.error('Error fetching presets:', err);
      } finally {
        setPresetLoading(false);
      }
    };

    fetchPresets();
  }, [token]);

  const handlePresetChange = (presetName: string) => {
    setSelectedPreset(presetName);
    const preset = presets.find(p => p.name === presetName);
    if (preset) {
      setCustomLabels(preset.labels.join(', '));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Please enter some text to classify');
      return;
    }
    
    if (!customLabels.trim()) {
      setError('Please enter at least one label');
      return;
    }
    
    const labels = customLabels.split(',').map(label => label.trim()).filter(Boolean);
    
    if (labels.length < 2) {
      setError('Please enter at least two labels, separated by commas');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/classify',
        { text, labels },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setResult(response.data);
    } catch (err) {
      console.error('Classification error:', err);
      setError('Failed to classify text. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Text Classification</h1>
      <p className="text-gray-600 mb-6">
        Categorize text into custom labels or use predefined presets.
      </p>
      
      <div className="bg-white shadow-sm rounded-lg p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="text" className="block text-gray-700 text-sm font-medium mb-2">
              Enter Text to Classify
            </label>
            <textarea
              id="text"
              rows={4}
              className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
              placeholder="Enter text for classification..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            ></textarea>
          </div>
          
          {/* Preset Selector */}
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">
              Preset Labels (Optional)
            </label>
            <div className="relative">
              <select
                className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                value={selectedPreset}
                onChange={(e) => handlePresetChange(e.target.value)}
                disabled={presetLoading}
              >
                <option value="">Select a preset or customize below</option>
                {presets.map((preset) => (
                  <option key={preset.name} value={preset.name}>
                    {preset.name.charAt(0).toUpperCase() + preset.name.slice(1)} - {preset.description}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          {/* Custom Labels */}
          <div className="mb-4">
            <label htmlFor="customLabels" className="block text-gray-700 text-sm font-medium mb-2">
              Classification Labels
            </label>
            <input
              type="text"
              id="customLabels"
              className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
              placeholder="Enter labels separated by commas (e.g. positive, negative, neutral)"
              value={customLabels}
              onChange={(e) => setCustomLabels(e.target.value)}
            />
            <p className="mt-1 text-xs text-gray-500">
              Enter at least two labels, separated by commas
            </p>
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
            {loading ? 'Classifying...' : 'Classify Text'}
          </button>
        </form>
      </div>
      
      {/* Result Display */}
      {result && (
        <div className="mt-6 bg-white shadow-sm rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Classification Result</h3>
          
          <div className="space-y-4">
            <div>
              <span className="text-sm text-gray-500">Text Analyzed:</span>
              <p className="bg-gray-50 p-3 rounded mt-1">{result.text}</p>
            </div>
            
            <div>
              <span className="text-sm text-gray-500">Top Classification:</span>
              <div className="flex items-center mt-1">
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  {result.labels && result.labels.length > 0 ? result.labels[0].label : 'No classification'}
                </span>
              </div>
            </div>
            
            <div>
              <span className="text-sm text-gray-500">All Classifications:</span>
              <div className="mt-3">
                {result.labels && result.labels.map((classification, index) => (
                  <div 
                    key={index}
                    className={`flex items-center justify-between p-3 ${
                      index === 0 ? 'bg-blue-50' : 'bg-gray-50'
                    } rounded-md mb-2`}
                  >
                    <span className={`font-medium ${
                      index === 0 ? 'text-blue-700' : 'text-gray-700'
                    }`}>
                      {classification.label}
                      {index === 0 && (
                        <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                          Top Match
                        </span>
                      )}
                    </span>
                    <div className="flex items-center">
                      <div className="w-24 h-2 bg-gray-200 rounded-full mr-2">
                        <div 
                          className="h-2 bg-blue-600 rounded-full" 
                          style={{ width: `${classification.score * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600">
                        {(classification.score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="text-sm text-gray-500">
              Processing Time: {result.processing_time * 1000} ms
            </div>
          </div>
        </div>
      )}
      
      <div className="mt-8 bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h3 className="text-md font-medium text-blue-800 mb-2">Quick Examples</h3>
        <div className="space-y-2">
          <div>
            <button
              type="button"
              onClick={() => {
                setText('I love this product! It works exactly as described and the customer service was excellent.');
                handlePresetChange('sentiment');
              }}
              className="text-sm text-blue-600 hover:text-blue-800 block"
            >
              Sentiment example
            </button>
          </div>
          <div>
            <button
              type="button"
              onClick={() => {
                setText('How do I reset my password? I\'ve tried multiple times but the reset link never arrives in my inbox.');
                setCustomLabels('question, statement, bug_report, account_issue');
              }}
              className="text-sm text-blue-600 hover:text-blue-800 block"
            >
              Support question example
            </button>
          </div>
          <div>
            <button
              type="button"
              onClick={() => {
                setText('I can\'t believe they cancelled our favorite show. This is so disappointing and frustrating!');
                handlePresetChange('emotion');
              }}
              className="text-sm text-blue-600 hover:text-blue-800 block"
            >
              Emotion example
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClassificationPage; 