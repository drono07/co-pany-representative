import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Activity, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw,
  Eye,
  Download,
  Trash2
} from 'lucide-react';
import { analysisService, applicationService } from '../services/api';
import toast from 'react-hot-toast';
import StatusIndicator from '../components/StatusIndicator';
import ProgressBar from '../components/ProgressBar';

const AnalysisRuns = () => {
  const { appId } = useParams();
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [activeTasks, setActiveTasks] = useState(new Map()); // Track active tasks
  const [isStartingAnalysis, setIsStartingAnalysis] = useState(false);

  useEffect(() => {
    if (appId) {
      loadApplication();
      loadRuns();
    } else {
      loadAllRuns();
    }
  }, [appId]);

  // Monitor active tasks
  useEffect(() => {
    if (activeTasks.size === 0) return;

    const interval = setInterval(async () => {
      const updatedTasks = new Map();
      
      for (const [taskId, taskInfo] of activeTasks) {
        try {
          const status = await analysisService.getTaskStatus(taskId);
          updatedTasks.set(taskId, status);
          
          // If task is completed or failed, remove from monitoring
          if (status.ready) {
            if (status.successful) {
              toast.success('Analysis completed successfully!');
            } else if (status.failed) {
              toast.error('Analysis failed');
            }
            // Reload runs to show updated data
            loadRuns();
          }
        } catch (error) {
          console.error('Failed to get task status:', error);
        }
      }
      
      setActiveTasks(updatedTasks);
    }, 2000); // Check every 2 seconds

    return () => clearInterval(interval);
  }, [activeTasks]);

  const loadApplication = async () => {
    try {
      const data = await applicationService.getApplication(appId);
      setApplication(data);
    } catch (error) {
      console.error('Failed to load application:', error);
    }
  };

  const loadRuns = async () => {
    try {
      const data = await analysisService.getAnalysisRuns(appId);
      setRuns(data);
    } catch (error) {
      toast.error('Failed to load analysis runs');
      console.error('Runs error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAllRuns = async () => {
    try {
      const data = await analysisService.getAllAnalysisRuns();
      setRuns(data || []);
    } catch (error) {
      toast.error('Failed to load analysis runs');
      console.error('Runs error:', error);
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!appId) {
      toast.error('No application selected');
      return;
    }

    setIsStartingAnalysis(true);
    try {
      const result = await analysisService.startAnalysis(appId);
      toast.success('Analysis started successfully!');
      
      // Add task to monitoring
      if (result.task_id) {
        setActiveTasks(prev => new Map(prev).set(result.task_id, {
          status: 'PENDING',
          ready: false,
          run_id: result.run_id,
          meta: { progress: 0 }
        }));
      }
      
      // Reload runs to show the new run
      loadRuns();
    } catch (error) {
      toast.error('Failed to start analysis');
    } finally {
      setIsStartingAnalysis(false);
    }
  };

  const handleViewDetails = async (runId) => {
    // Navigate to insights page using React Router
    navigate(`/insights/${runId}`);
  };

  const handleDownloadReport = async (runId) => {
    try {
      const response = await analysisService.getAnalysisRun(runId);
      const dataStr = JSON.stringify(response, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analysis-report-${runId}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success('Report downloaded successfully');
    } catch (error) {
      console.error('Error downloading report:', error);
      toast.error('Failed to download report');
    }
  };

  const handleDeleteRun = async (runId) => {
    if (!window.confirm('Are you sure you want to delete this analysis run? This action cannot be undone.')) {
      return;
    }

    try {
      await analysisService.deleteAnalysisRun(runId);
      // Remove from local state immediately for better UX
      setRuns(prevRuns => prevRuns.filter(run => run.id !== runId && run._id !== runId));
      toast.success('Analysis run deleted successfully');
    } catch (error) {
      toast.error('Failed to delete analysis run');
      console.error('Delete error:', error);
      // Reload runs to restore the correct state
      if (appId) {
        loadRuns();
      } else {
        loadAllRuns();
      }
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Activity className="h-5 w-5 text-blue-500" />;
      case 'failed':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRunStatus = (run) => {
    const runId = run.id || run._id;
    
    // Check if this run has an active task
    for (const [taskId, taskInfo] of activeTasks) {
      if (taskInfo.run_id === runId) {
        return {
          status: taskInfo.status === 'SUCCESS' ? 'completed' : 
                  taskInfo.status === 'FAILURE' ? 'failed' : 'running',
          isActive: !taskInfo.ready,
          progress: taskInfo.meta?.progress || 0,
          taskInfo: taskInfo
        };
      }
    }
    return {
      status: run.status || 'pending',
      isActive: false,
      progress: run.status === 'completed' ? 100 : 
                run.status === 'failed' ? 100 : 0,
      taskInfo: null
    };
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
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Analysis Runs
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            {application ? `Analysis runs for ${application.name}` : 'All analysis runs'}
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0 space-x-3">
          {appId && (
            <button
              onClick={handleStartAnalysis}
              disabled={isStartingAnalysis}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStartingAnalysis ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Starting...
                </>
              ) : (
                <>
                  <Activity className="h-4 w-4 mr-2" />
                  Start Analysis
                </>
              )}
            </button>
          )}
          <button
            onClick={() => {
              if (appId) {
                loadRuns();
              } else {
                loadAllRuns();
              }
            }}
            className="btn btn-secondary"
            title="Refresh runs"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Runs Table */}
      {runs.length > 0 ? (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  {!appId && (
                    <>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Application
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Website
                      </th>
                    </>
                  )}
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Completed
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Pages Analyzed
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Overall Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[200px]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {runs.map((run) => {
                  const runStatus = getRunStatus(run);
                  console.log('Run data:', run);
                  console.log('Run status:', run.status);
                  console.log('RunStatus:', runStatus);
                  return (
                    <tr key={run.id || run._id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusIndicator 
                          status={runStatus.status} 
                          isActive={runStatus.isActive}
                          size="sm"
                        />
                      </td>
                      {!appId && (
                        <>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {run.application_name || 'Unknown'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <a 
                              href={run.website_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 truncate max-w-xs block"
                              title={run.website_url}
                            >
                              {run.website_url}
                            </a>
                          </td>
                        </>
                      )}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(run.started_at || run.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {run.completed_at ? formatDate(run.completed_at) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {run.total_pages_analyzed || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {run.overall_score ? `${run.overall_score}/100` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {runStatus.status === 'running' && runStatus.isActive ? (
                        <div className="flex items-center space-x-2">
                          <ProgressBar 
                            progress={runStatus.progress || 0}
                            status={runStatus.status}
                            className="w-20"
                          />
                          <span className="text-xs text-gray-500">
                            {runStatus.progress || 0}%
                          </span>
                        </div>
                      ) : runStatus.status === 'pending' ? (
                        <span className="text-xs text-gray-500">Pending</span>
                      ) : (
                        <ProgressBar 
                          progress={runStatus.progress}
                          status={runStatus.status}
                          className="w-24"
                        />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium min-w-[200px]">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleViewDetails(run.id || run._id)}
                          className="inline-flex items-center px-2 py-1 text-xs font-medium text-primary-600 hover:text-primary-900 bg-primary-50 hover:bg-primary-100 rounded"
                          title="View Insights"
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          Insights
                        </button>
                        {run.status === 'completed' && (
                          <button 
                            onClick={() => handleDownloadReport(run.id || run._id)}
                            className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 hover:text-gray-900 bg-gray-50 hover:bg-gray-100 rounded"
                            title="Download Report"
                          >
                            <Download className="h-3 w-3 mr-1" />
                            Download
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteRun(run.id || run._id)}
                          className="inline-flex items-center px-2 py-1 text-xs font-medium text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 rounded"
                          title="Delete Run"
                        >
                          <Trash2 className="h-3 w-3 mr-1" />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <Activity className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No analysis runs</h3>
          <p className="mt-1 text-sm text-gray-500">
            {appId ? 'Start your first analysis to see results here.' : 'No analysis runs found.'}
          </p>
          {appId && (
            <div className="mt-6">
              <button
                onClick={handleStartAnalysis}
                className="btn btn-primary"
              >
                <Activity className="h-4 w-4 mr-2" />
                Start Analysis
              </button>
            </div>
          )}
        </div>
      )}

      {/* Run Details Modal */}
      {showDetailsModal && selectedRun && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowDetailsModal(false)} />
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  Analysis Run Details
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Run Info */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">Run Information</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Status:</span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedRun.run.status)}`}>
                          {selectedRun.run.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Started:</span>
                        <span>{formatDate(selectedRun.run.started_at || selectedRun.run.created_at)}</span>
                      </div>
                      {selectedRun.run.completed_at && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">Completed:</span>
                          <span>{formatDate(selectedRun.run.completed_at)}</span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-gray-500">Pages Analyzed:</span>
                        <span>{selectedRun.run.total_pages_analyzed || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Overall Score:</span>
                        <span>{selectedRun.run.overall_score || 0}/100</span>
                      </div>
                    </div>
                  </div>

                  {/* Results Summary */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">Results Summary</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Content Pages:</span>
                        <span>{selectedRun.run.content_pages_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Blank Pages:</span>
                        <span>{selectedRun.run.blank_pages_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Broken Links:</span>
                        <span>{selectedRun.run.broken_links_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Total Links:</span>
                        <span>{selectedRun.run.total_links_found || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Error Message */}
                {selectedRun.run.error_message && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-800">
                      <strong>Error:</strong> {selectedRun.run.error_message}
                    </p>
                  </div>
                )}
              </div>
              
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => setShowDetailsModal(false)}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisRuns;
