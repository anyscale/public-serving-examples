import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface HealthData {
  status: string;
  version: string;
  models: {
    sentiment_analyzer: boolean;
    text_classifier: boolean;
    entity_recognizer: boolean;
  };
  uptime_seconds: number;
}

interface FeatureTileProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  to: string;
  available?: boolean;
}

const FeatureTile: React.FC<FeatureTileProps> = ({ 
  title, 
  description, 
  icon, 
  to, 
  available = true 
}) => {
  return (
    <Link
      to={to}
      className={`block p-6 bg-white rounded-lg border shadow-sm hover:shadow-md ${
        !available ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      onClick={(e) => {
        if (!available) e.preventDefault();
      }}
    >
      <div className="flex items-center mb-2">
        <div className="mr-2 text-blue-600">{icon}</div>
        <h5 className="text-xl font-bold text-gray-900">{title}</h5>
      </div>
      <p className="text-gray-700">{description}</p>
      {!available && (
        <div className="mt-2 text-sm text-red-500">Currently unavailable</div>
      )}
    </Link>
  );
};

const DashboardPage: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuth();

  useEffect(() => {
    const fetchHealthData = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/v1/health', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setHealthData(response.data);
      } catch (err) {
        console.error('Error fetching health data', err);
        setError('Failed to fetch system status');
      } finally {
        setLoading(false);
      }
    };

    fetchHealthData();
  }, [token]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      
      {/* System Status */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <h2 className="text-lg font-semibold mb-3">System Status</h2>
        
        {loading && <p>Loading system status...</p>}
        
        {error && <p className="text-red-500">{error}</p>}
        
        {healthData && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className={`font-medium ${
                healthData.status === 'healthy' ? 'text-green-600' : 'text-yellow-600'
              }`}>
                {healthData.status.charAt(0).toUpperCase() + healthData.status.slice(1)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Version</p>
              <p className="font-medium">{healthData.version}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Sentiment Analyzer</p>
              <p className={`font-medium ${
                healthData.models.sentiment_analyzer ? 'text-green-600' : 'text-red-600'
              }`}>
                {healthData.models.sentiment_analyzer ? 'Available' : 'Unavailable'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Entity Recognizer</p>
              <p className={`font-medium ${
                healthData.models.entity_recognizer ? 'text-green-600' : 'text-red-600'
              }`}>
                {healthData.models.entity_recognizer ? 'Available' : 'Unavailable'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Text Classifier</p>
              <p className={`font-medium ${
                healthData.models.text_classifier ? 'text-green-600' : 'text-red-600'
              }`}>
                {healthData.models.text_classifier ? 'Available' : 'Unavailable'}
              </p>
            </div>
          </div>
        )}
      </div>
      
      {/* Features */}
      <h2 className="text-lg font-semibold mb-3">Features</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <FeatureTile
          title="Sentiment Analysis"
          description="Determine the emotional tone of text"
          to="/sentiment"
          available={healthData?.models.sentiment_analyzer}
          icon={
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
            </svg>
          }
        />
        
        <FeatureTile
          title="Entity Recognition"
          description="Extract people, places, organizations, etc."
          to="/entities"
          available={healthData?.models.entity_recognizer}
          icon={
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z" />
            </svg>
          }
        />
        
        <FeatureTile
          title="Text Classification"
          description="Categorize text into predefined labels"
          to="/classification"
          available={healthData?.models.text_classifier}
          icon={
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
            </svg>
          }
        />
        
        <FeatureTile
          title="Streaming Analysis"
          description="Real-time text processing with server-sent events"
          to="/streaming"
          icon={
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
          }
        />
        
        <FeatureTile
          title="WebSocket Demo"
          description="Bi-directional real-time communication"
          to="/websocket"
          icon={
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
            </svg>
          }
        />
      </div>
    </div>
  );
};

export default DashboardPage; 