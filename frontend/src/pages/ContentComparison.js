import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  TrendingUp, 
  TrendingDown, 
  FileText, 
  Link, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  BarChart3,
  Eye
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { analysisService } from '../services/api';

const ContentComparison = () => {
  const { runId, previousRunId } = useParams();
  const navigate = useNavigate();
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const loadComparison = useCallback(async () => {
    try {
      setLoading(true);
      const data = await analysisService.getContentComparison(runId, previousRunId);
      setComparison(data.comparison);
    } catch (error) {
      console.error('Error loading comparison:', error);
      toast.error('Failed to load content comparison');
    } finally {
      setLoading(false);
    }
  }, [runId, previousRunId]);

  useEffect(() => {
    if (runId && previousRunId) {
      loadComparison();
    }
  }, [loadComparison]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!comparison) {
    return (
      <div className="text-center py-12">
        <XCircle className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No Comparison Data</h3>
        <p className="mt-1 text-sm text-gray-500">
          Unable to load content comparison data.
        </p>
        <div className="mt-6">
          <button 
            onClick={() => navigate(-1)}
            className="btn btn-secondary"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'changes', name: 'Content Changes', icon: FileText },
    { id: 'insights', name: 'AI Insights', icon: Zap },
    { id: 'recommendations', name: 'Recommendations', icon: TrendingUp }
  ];

  const getChangeIcon = (changeType) => {
    switch (changeType) {
      case 'new':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'removed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'modified':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getChangeColor = (changeType) => {
    switch (changeType) {
      case 'new':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'removed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'modified':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center">
            <button
              onClick={() => navigate(-1)}
              className="mr-4 p-2 text-gray-400 hover:text-gray-600"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Content Comparison
              </h1>
              <p className="text-sm text-gray-500">
                AI-powered analysis of content changes between runs
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Comparison Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Pages</p>
              <p className="text-2xl font-semibold text-gray-900">
                {comparison.total_pages_compared}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">New Pages</p>
              <p className="text-2xl font-semibold text-gray-900">
                {comparison.changes_summary.new_pages_count}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Removed Pages</p>
              <p className="text-2xl font-semibold text-gray-900">
                {comparison.changes_summary.removed_pages_count}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Modified Pages</p>
              <p className="text-2xl font-semibold text-gray-900">
                {comparison.changes_summary.modified_pages_count}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Comparison Overview</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-2">Current Run</h4>
                  <p className="text-sm text-gray-600">{comparison.current_run_id}</p>
                </div>
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-2">Previous Run</h4>
                  <p className="text-sm text-gray-600">{comparison.previous_run_id}</p>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Change Summary</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                    <span className="text-sm font-medium text-green-800">New Pages Added</span>
                  </div>
                  <span className="text-lg font-semibold text-green-600">
                    +{comparison.changes_summary.new_pages_count}
                  </span>
                </div>

                <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                  <div className="flex items-center">
                    <XCircle className="h-5 w-5 text-red-600 mr-3" />
                    <span className="text-sm font-medium text-red-800">Pages Removed</span>
                  </div>
                  <span className="text-lg font-semibold text-red-600">
                    -{comparison.changes_summary.removed_pages_count}
                  </span>
                </div>

                <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
                  <div className="flex items-center">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3" />
                    <span className="text-sm font-medium text-yellow-800">Pages Modified</span>
                  </div>
                  <span className="text-lg font-semibold text-yellow-600">
                    {comparison.changes_summary.modified_pages_count}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'changes' && (
          <div className="space-y-6">
            {/* New Pages */}
            {comparison.new_pages.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-medium text-gray-900 mb-4">New Pages</h3>
                <div className="space-y-2">
                  {comparison.new_pages.map((url, index) => (
                    <div key={index} className="flex items-center p-3 bg-green-50 rounded-lg">
                      <CheckCircle className="h-4 w-4 text-green-500 mr-3" />
                      <a 
                        href={url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-green-700 hover:text-green-900 truncate"
                      >
                        {url}
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Removed Pages */}
            {comparison.removed_pages.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Removed Pages</h3>
                <div className="space-y-2">
                  {comparison.removed_pages.map((url, index) => (
                    <div key={index} className="flex items-center p-3 bg-red-50 rounded-lg">
                      <XCircle className="h-4 w-4 text-red-500 mr-3" />
                      <span className="text-sm text-red-700 truncate">{url}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Modified Pages */}
            {comparison.modified_pages.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Modified Pages</h3>
                <div className="space-y-4">
                  {comparison.modified_pages.map((page, index) => (
                    <div key={index} className="p-4 bg-yellow-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <AlertTriangle className="h-4 w-4 text-yellow-500 mr-2" />
                          <span className="text-sm font-medium text-yellow-800">{page.title}</span>
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getChangeColor('modified')}`}>
                          Modified
                        </span>
                      </div>
                      <a 
                        href={page.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-yellow-700 hover:text-yellow-900 block truncate"
                      >
                        {page.url}
                      </a>
                      {page.word_count_change !== 0 && (
                        <div className="mt-2 text-sm text-yellow-600">
                          Word count change: {page.word_count_change > 0 ? '+' : ''}{page.word_count_change}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">AI-Generated Insights</h3>
              
              {comparison.overall_change_assessment && (
                <div className="mb-6">
                  <h4 className="text-md font-medium text-gray-900 mb-2">Overall Assessment</h4>
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">{comparison.overall_change_assessment}</p>
                  </div>
                </div>
              )}

              {comparison.impact_analysis && (
                <div className="mb-6">
                  <h4 className="text-md font-medium text-gray-900 mb-2">Impact Analysis</h4>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <p className="text-sm text-purple-800">{comparison.impact_analysis}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center text-sm text-gray-500">
                <Zap className="h-4 w-4 mr-2" />
                <span>Analysis powered by {comparison.ai_model || 'GPT-3.5-turbo'}</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">AI Recommendations</h3>
              
              {comparison.recommendations && comparison.recommendations.length > 0 ? (
                <div className="space-y-4">
                  {comparison.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start p-4 bg-green-50 rounded-lg">
                      <div className="flex-shrink-0">
                        <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                          <span className="text-xs font-medium text-green-600">{index + 1}</span>
                        </div>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-green-800">{recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <TrendingUp className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No Recommendations</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    No specific recommendations available for this comparison.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContentComparison;
