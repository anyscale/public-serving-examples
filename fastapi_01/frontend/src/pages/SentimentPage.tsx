import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface SentimentResult {
  text: string;
  sentiment: string;
  score: number;
  language: string;
  analysis_time_ms: number;
}

const LanguageSelector: React.FC<{
  language: string;
  setLanguage: (lang: string) => void;
}> = ({ language, setLanguage }) => {
  return (
    <div className="mb-4">
      <label className="block text-gray-700 text-sm font-medium mb-2">
        Language
      </label>
      <div className="flex space-x-4">
        <button
          type="button"
          className={`px-4 py-2 rounded-md ${
            language === 'en'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
          onClick={() => setLanguage('en')}
        >
          English
        </button>
        <button
          type="button"
          className={`px-4 py-2 rounded-md ${
            language === 'es'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
          onClick={() => setLanguage('es')}
        >
          Spanish
        </button>
        <button
          type="button"
          className={`px-4 py-2 rounded-md ${
            language === 'fr'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
          onClick={() => setLanguage('fr')}
        >
          French
        </button>
      </div>
    </div>
  );
};

const ResultDisplay: React.FC<{ result: SentimentResult }> = ({ result }) => {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'bg-green-100 text-green-800';
      case 'negative':
        return 'bg-red-100 text-red-800';
      case 'neutral':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="mt-6 bg-white shadow-sm rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Analysis Result</h3>
      
      <div className="space-y-4">
        <div>
          <span className="text-sm text-gray-500">Text Analyzed:</span>
          <p className="bg-gray-50 p-3 rounded mt-1">{result.text}</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-500">Sentiment:</span>
            <div className="flex items-center mt-1">
              <span className={`px-2.5 py-0.5 rounded-full text-sm font-medium ${getSentimentColor(result.sentiment)}`}>
                {result.sentiment.toUpperCase()}
              </span>
            </div>
          </div>
          
          <div>
            <span className="text-sm text-gray-500">Score:</span>
            <p className="font-medium">{result.score.toFixed(4)}</p>
          </div>
          
          <div>
            <span className="text-sm text-gray-500">Confidence:</span>
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
          
          <div>
            <span className="text-sm text-gray-500">Language:</span>
            <p className="font-medium">{result.language}</p>
          </div>
          
          <div>
            <span className="text-sm text-gray-500">Processing Time:</span>
            <p className="font-medium">{result.analysis_time_ms} ms</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const SentimentPage: React.FC = () => {
  const [text, setText] = useState('');
  const [language, setLanguage] = useState('en');
  const [result, setResult] = useState<SentimentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
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
        'http://localhost:8000/api/v1/sentiment',
        { text, language },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setResult(response.data);
    } catch (err) {
      console.error('Sentiment analysis error:', err);
      setError('Failed to analyze sentiment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Sentiment Analysis</h1>
      <p className="text-gray-600 mb-6">
        Determine the emotional tone of text using our NLP sentiment analysis model.
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
              placeholder="Enter text for sentiment analysis..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            ></textarea>
          </div>
          
          <LanguageSelector language={language} setLanguage={setLanguage} />
          
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
            {loading ? 'Analyzing...' : 'Analyze Sentiment'}
          </button>
        </form>
      </div>
      
      {result && <ResultDisplay result={result} />}
      
      <div className="mt-8 bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h3 className="text-md font-medium text-blue-800 mb-2">Quick Examples</h3>
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => setText('I love this product! It works exactly as described and the customer service was excellent.')}
            className="text-sm text-blue-600 hover:text-blue-800 block"
          >
            Positive example
          </button>
          <button
            type="button"
            onClick={() => setText('This is okay I guess. Nothing special about it.')}
            className="text-sm text-blue-600 hover:text-blue-800 block"
          >
            Neutral example
          </button>
          <button
            type="button"
            onClick={() => setText('This product is terrible. It broke after one day and customer service was unhelpful.')}
            className="text-sm text-blue-600 hover:text-blue-800 block"
          >
            Negative example
          </button>
        </div>
      </div>
    </div>
  );
};

export default SentimentPage; 