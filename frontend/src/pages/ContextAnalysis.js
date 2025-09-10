import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Target, 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  ExternalLink,
  Download,
  RefreshCw
} from 'lucide-react';
import { analysisService, applicationService } from '../services/api';
import toast from 'react-hot-toast';

const ContextAnalysis = () => {
  const { appId } = useParams();
  const navigate = useNavigate();
  const [application, setApplication] = useState(null);
  const [runs, setRuns] = useState([]);
  const [selectedRun1, setSelectedRun1] = useState(null);
  const [selectedRun2, setSelectedRun2] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    if (appId) {
      loadApplication();
      loadRuns();
    }
  }, [appId]);

  const loadApplication = async () => {
    try {
      const app = await applicationService.getApplication(appId);
      setApplication(app);
    } catch (error) {
      console.error('Error loading application:', error);
      toast.error('Failed to load application');
    }
  };

  const loadRuns = async () => {
    try {
      setLoading(true);
      const data = await analysisService.getAnalysisRuns(appId, 50);
      // Only show completed runs for comparison
      const completedRuns = data.filter(run => run.status === 'completed');
      setRuns(completedRuns);
    } catch (error) {
      console.error('Error loading runs:', error);
      toast.error('Failed to load analysis runs');
    } finally {
      setLoading(false);
    }
  };

  const handleCompareRuns = async () => {
    if (!selectedRun1 || !selectedRun2) {
      toast.error('Please select both runs to compare');
      return;
    }

    if (selectedRun1.id === selectedRun2.id) {
      toast.error('Please select different runs for comparison');
      return;
    }

    try {
      setComparing(true);
      const result = await analysisService.getContentComparison(
        selectedRun1.id || selectedRun1._id,
        selectedRun2.id || selectedRun2._id
      );
      setComparisonResult(result);
      toast.success('Content comparison completed');
    } catch (error) {
      console.error('Error comparing runs:', error);
      toast.error('Failed to compare runs');
    } finally {
      setComparing(false);
    }
  };

  const handleDownloadComparison = () => {
    if (!comparisonResult) return;
    
    const dataStr = JSON.stringify(comparisonResult, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `content-comparison-${selectedRun1?.id}-${selectedRun2?.id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Comparison report downloaded');
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate(-1)}
              className="mr-4 p-2 text-gray-400 hover:text-gray-600"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
                Context Analysis
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                AI-powered content comparison between analysis runs
              </p>
              {application && (
                <p className="mt-1 text-sm text-blue-600">
                  Application: {application.name} | Website: {application.website_url}
                </p>
              )}
            </div>
          </div>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0 space-x-3">
          <button
            onClick={loadRuns}
            className="btn btn-secondary"
            title="Refresh runs"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Run Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Run 1 Selection */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Select First Run (Current)</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {runs.map((run) => (
              <div
                key={run.id || run._id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedRun1?.id === run.id || selectedRun1?._id === run._id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedRun1(run)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    <span className="text-sm font-medium text-gray-900">
                      {formatDate(run.started_at)}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">{run.status}</span>
                </div>
                <div className="text-xs text-gray-600">
                  Pages: {run.total_pages_analyzed || 0} | Score: {run.overall_score || 0}/100
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Run 2 Selection */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Select Second Run (Previous)</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {runs.map((run) => (
              <div
                key={run.id || run._id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedRun2?.id === run.id || selectedRun2?._id === run._id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedRun2(run)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    <span className="text-sm font-medium text-gray-900">
                      {formatDate(run.started_at)}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">{run.status}</span>
                </div>
                <div className="text-xs text-gray-600">
                  Pages: {run.total_pages_analyzed || 0} | Score: {run.overall_score || 0}/100
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Compare Button */}
      <div className="flex justify-center">
        <button
          onClick={handleCompareRuns}
          disabled={!selectedRun1 || !selectedRun2 || comparing}
          className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {comparing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Comparing...
            </>
          ) : (
            <>
              <Target className="h-4 w-4 mr-2" />
              Compare Content
            </>
          )}
        </button>
      </div>

      {/* Comparison Results */}
      {comparisonResult && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-gray-900">Comparison Results</h3>
            <button
              onClick={handleDownloadComparison}
              className="btn btn-secondary"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Report
            </button>
          </div>

          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {comparisonResult.summary?.total_pages_compared || 0}
              </div>
              <div className="text-sm text-blue-800">Pages Compared</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {comparisonResult.summary?.unchanged_pages || 0}
              </div>
              <div className="text-sm text-green-800">Unchanged</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {comparisonResult.summary?.modified_pages || 0}
              </div>
              <div className="text-sm text-yellow-800">Modified</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {comparisonResult.summary?.new_pages || 0}
              </div>
              <div className="text-sm text-red-800">New Pages</div>
            </div>
          </div>

          {/* AI Analysis */}
          {comparisonResult.ai_analysis && (
            <div className="mb-6">
              <h4 className="text-md font-medium text-gray-900 mb-3">AI Analysis</h4>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {comparisonResult.ai_analysis}
                </p>
              </div>
            </div>
          )}

          {/* Content Changes */}
          {comparisonResult.content_changes && comparisonResult.content_changes.length > 0 && (
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">Content Changes</h4>
              <div className="space-y-4">
                {comparisonResult.content_changes.map((change, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          {change.change_type === 'new' && (
                            <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                          )}
                          {change.change_type === 'modified' && (
                            <AlertTriangle className="h-4 w-4 text-yellow-500 mr-2" />
                          )}
                          <span className="text-sm font-medium text-gray-900">
                            {change.title || 'Untitled Page'}
                          </span>
                        </div>
                        <a
                          href={change.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:text-blue-800 break-all"
                        >
                          {change.url}
                        </a>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded ${
                        change.change_type === 'new' ? 'bg-green-100 text-green-800' :
                        change.change_type === 'modified' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {change.change_type}
                      </span>
                    </div>
                    
                    {change.word_count_change !== 0 && (
                      <div className="text-xs text-gray-600 mt-2">
                        Word count change: {change.word_count_change > 0 ? '+' : ''}{change.word_count_change}
                      </div>
                    )}
                    
                    {change.content_changed && (
                      <div className="text-xs text-yellow-600 mt-1">
                        Content has been modified
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {runs.length === 0 && (
        <div className="text-center py-12">
          <Target className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No completed runs found</h3>
          <p className="mt-1 text-sm text-gray-500">
            You need at least 2 completed analysis runs to perform content comparison.
          </p>
        </div>
      )}
    </div>
  );
};

export default ContextAnalysis;
