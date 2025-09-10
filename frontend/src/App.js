import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './services/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Applications from './pages/Applications';
import AnalysisRuns from './pages/AnalysisRuns';
import AnalysisInsights from './pages/AnalysisInsights';
import ContextComparison from './pages/ContextComparison';
import ContentComparison from './pages/ContentComparison';
import ContextAnalysis from './pages/ContextAnalysis';
import Layout from './components/Layout';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }
  
  return user ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Toaster position="top-right" />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/applications" element={
              <ProtectedRoute>
                <Layout>
                  <Applications />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/runs" element={
              <ProtectedRoute>
                <Layout>
                  <AnalysisRuns />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/runs/:appId" element={
              <ProtectedRoute>
                <Layout>
                  <AnalysisRuns />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/insights/:runId" element={
              <ProtectedRoute>
                <Layout>
                  <AnalysisInsights />
                </Layout>
              </ProtectedRoute>
            } />
        <Route path="/compare/:appId" element={
          <ProtectedRoute>
            <Layout>
              <ContextComparison />
            </Layout>
          </ProtectedRoute>
        } />
        <Route path="/context-analysis/:appId" element={
          <ProtectedRoute>
            <Layout>
              <ContextAnalysis />
            </Layout>
          </ProtectedRoute>
        } />
        <Route path="/content-comparison/:runId/:previousRunId" element={
          <ProtectedRoute>
            <Layout>
              <ContentComparison />
            </Layout>
          </ProtectedRoute>
        } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
