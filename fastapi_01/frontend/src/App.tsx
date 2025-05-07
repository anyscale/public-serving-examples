import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './App.css';

// Auth
import { AuthProvider } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import DashboardPage from './pages/DashboardPage';
import SentimentPage from './pages/SentimentPage';
import EntitiesPage from './pages/EntitiesPage';
import ClassificationPage from './pages/ClassificationPage';
import StreamingDemo from './pages/StreamingDemo';
import WebSocketDemo from './pages/WebSocketDemo';

// Create a client
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            
            {/* Protected routes */}
            <Route element={<ProtectedRoute />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/sentiment" element={<SentimentPage />} />
              <Route path="/entities" element={<EntitiesPage />} />
              <Route path="/classification" element={<ClassificationPage />} />
              <Route path="/streaming" element={<StreamingDemo />} />
              <Route path="/websocket" element={<WebSocketDemo />} />
            </Route>
            
            {/* Redirect root to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
