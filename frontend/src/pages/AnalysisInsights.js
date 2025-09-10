import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft,
  ExternalLink,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  Link,
  Eye,
  Download,
  TrendingUp,
  Target,
  Zap,
  MapPin,
  ArrowRight
} from 'lucide-react';
import { analysisService, applicationService } from '../services/api';
import SourceCodeViewer from '../components/SourceCodeViewer';
import LinkInfoModal from '../components/LinkInfoModal';
import toast from 'react-hot-toast';

const AnalysisInsights = () => {
  const { runId } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState(null);
  const [results, setResults] = useState(null);
  const [linkValidations, setLinkValidations] = useState([]);
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [contentAnalysisTask, setContentAnalysisTask] = useState(null);
  const [contentAnalysisResults, setContentAnalysisResults] = useState(null);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [availableRuns, setAvailableRuns] = useState([]);
  const [selectedRunForComparison, setSelectedRunForComparison] = useState(null);
  const [sourceViewerOpen, setSourceViewerOpen] = useState(false);
  const [sourceViewerData, setSourceViewerData] = useState(null);
  const [parentChildRelationships, setParentChildRelationships] = useState(null);
  const [linkInfoModalOpen, setLinkInfoModalOpen] = useState(false);
  const [selectedLink, setSelectedLink] = useState(null);

  const loadAnalysisData = useCallback(async () => {
    try {
      console.log('Loading analysis data for runId:', runId);
      console.log('RunId type:', typeof runId);
      console.log('RunId value:', runId);
      
      if (!runId) {
        console.error('No runId provided');
        toast.error('No analysis run ID provided');
        setLoading(false);
        return;
      }
      
      const data = await analysisService.getAnalysisRun(runId);
      console.log('Analysis data loaded:', data);
      
      if (!data || !data.run) {
        console.error('No run data in response:', data);
        toast.error('Analysis run data not found');
        setLoading(false);
        return;
      }
      
      setRun(data.run);
      setResults(data.results);
      console.log('Link validations from API:', data.link_validations);
      console.log('Link validations length:', data.link_validations?.length || 0);
      setLinkValidations(data.link_validations || []);
      
      // Load application data to get website URL
      if (data.run.application_id) {
        console.log('Loading application data for appId:', data.run.application_id);
        const appData = await applicationService.getApplication(data.run.application_id);
        console.log('Application data loaded:', appData);
        setApplication(appData);
      }
    } catch (error) {
      console.error('Analysis data error details:', error);
      console.error('Error response:', error.response?.data);
      toast.error(`Failed to load analysis data: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  }, [runId]);

  const loadParentChildRelationships = async () => {
    try {
      console.log('Loading parent-child relationships for runId:', runId);
      const relationships = await analysisService.getParentChildRelationships(runId);
      console.log('Parent-child relationships loaded:', relationships);
      setParentChildRelationships(relationships);
    } catch (error) {
      console.error('Error loading parent-child relationships:', error);
      console.error('Error details:', error.response?.data);
    }
  };

  const handleViewSource = async (brokenUrl, parentUrl = null) => {
    try {
      setLoading(true);
      console.log('Loading source code for:', parentUrl || brokenUrl);
      
      // Get source code data
      const sourceData = await analysisService.getPageSourceCode(runId, parentUrl || brokenUrl);
      console.log('Source code data received:', sourceData);
      
      if (sourceData) {
        setSourceViewerData({
          ...sourceData,
          brokenUrl: brokenUrl
        });
        setSourceViewerOpen(true);
      } else {
        toast.error('Source code not available for this page');
      }
    } catch (error) {
      console.error('Error loading source code:', error);
      console.error('Error details:', error.response?.data);
      toast.error('Failed to load source code');
    } finally {
      setLoading(false);
    }
  };

  const getParentInfo = (brokenUrl) => {
    console.log('getParentInfo called with:', brokenUrl);
    console.log('parentChildRelationships:', parentChildRelationships);
    
    if (!parentChildRelationships || !parentChildRelationships.parent_map) {
      console.log('No parent-child relationships data available');
      return null;
    }
    
    const parentUrl = parentChildRelationships.parent_map[brokenUrl];
    const startUrl = parentChildRelationships.start_url;
    console.log('Parent URL for', brokenUrl, ':', parentUrl);
    console.log('Start URL:', startUrl);
    
    // If no parent URL, check if this is the start URL
    if (!parentUrl) {
      if (startUrl && brokenUrl === startUrl) {
        return {
          url: null,
          title: null,
          isRootUrl: true
        };
      }
      return null;
    }
    
    // Find parent page title from results
    const parentPage = results?.pages?.find(page => page.page_url === parentUrl);
    
    // If parent page not found in results, try to get title from link validations
    let parentTitle = parentPage?.page_title;
    if (!parentTitle) {
      const parentLink = linkValidations?.find(link => link.url === parentUrl);
      parentTitle = parentLink?.page_title;
    }
    
    // If still no title, use a fallback based on the URL
    if (!parentTitle || parentTitle === 'Unknown') {
      if (parentUrl.includes('/collections/')) {
        parentTitle = 'Collections Page';
      } else if (parentUrl.includes('/products/')) {
        parentTitle = 'Product Page';
      } else if (parentUrl.includes('/pages/')) {
        parentTitle = 'Page';
      } else {
        parentTitle = 'Parent Page';
      }
    }
    
    const result = {
      url: parentUrl,
      title: parentTitle || 'Unknown Page',
      isRootUrl: false
    };
    console.log('getParentInfo returning:', result);
    return result;
  };

  const getNavigationPath = (brokenUrl) => {
    if (!parentChildRelationships || !parentChildRelationships.path_map) {
      return [];
    }
    
    return parentChildRelationships.path_map[brokenUrl] || [];
  };

  const formatParentChildPath = (pathArray) => {
    if (!Array.isArray(pathArray) || pathArray.length === 0) {
      return 'No path available';
    }
    
    return pathArray.map(item => {
      if (typeof item === 'string') {
        return item;
      } else if (item && typeof item === 'object' && item.title) {
        return item.title;
      }
      return 'Unknown Page';
    }).join(' → ');
  };

  const handleOpenLinkInfo = (link) => {
    setSelectedLink(link);
    setLinkInfoModalOpen(true);
  };

  useEffect(() => {
    if (runId) {
      loadAnalysisData();
      loadParentChildRelationships();
    }
  }, [runId, loadAnalysisData]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <Clock className="h-5 w-5 text-blue-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getBrokenLinks = () => {
    return linkValidations.filter(link => 
      link.status === 'broken' || 
      (link.status_code && link.status_code >= 400) ||
      link.status === 'error' ||
      link.status === 'timeout'
    );
  };

  const getWorkingLinks = () => {
    // Debug: log the link validations to see what we have
    console.log('Link validations:', linkValidations);
    console.log('Link validations length:', linkValidations.length);
    
    if (!linkValidations || linkValidations.length === 0) {
      console.log('No link validations data available');
      
      // Fallback: if no link validations but we have run data, calculate from totals
      if (run && run.total_links_found && run.broken_links_count) {
        const workingCount = run.total_links_found - run.broken_links_count;
        console.log(`Fallback: calculated ${workingCount} working links from run totals`);
        
        // Return a mock array with the calculated count for display purposes
        return Array(workingCount).fill(null).map((_, index) => ({
          id: `fallback-${index}`,
          url: `Working link ${index + 1}`,
          status: 'valid',
          status_code: 200,
          isFallback: true
        }));
      }
      
      return [];
    }
    
    const working = linkValidations.filter(link => {
      console.log('Checking link:', link);
      
      // Check if it's explicitly marked as working/valid
      const isExplicitlyWorking = link.status === 'valid' || 
                                 link.status === 'working' || 
                                 link.status === 'success' ||
                                 link.status === 'ok';
      
      // Check if status code indicates success (200-299)
      const hasSuccessStatusCode = link.status_code && 
                                  link.status_code >= 200 && 
                                  link.status_code < 300;
      
      // Check if it's NOT explicitly broken
      const isNotBroken = link.status !== 'broken' && 
                         link.status !== 'error' && 
                         link.status !== 'timeout' &&
                         link.status !== 'failed';
      
      // Check if status code is NOT an error (not 400+)
      const isNotErrorStatusCode = !link.status_code || 
                                  link.status_code < 400;
      
      const isValid = (isExplicitlyWorking || hasSuccessStatusCode) && 
                     isNotBroken && 
                     isNotErrorStatusCode;
      
      if (isValid) {
        console.log('Working link found:', link);
      } else {
        console.log('Link not working:', link, {
          isExplicitlyWorking,
          hasSuccessStatusCode,
          isNotBroken,
          isNotErrorStatusCode
        });
      }
      
      return isValid;
    });
    
    console.log('Working links count:', working.length);
    
    // If no working links found but we have link validations, try alternative approach
    if (working.length === 0 && linkValidations.length > 0) {
      console.log('No working links found with current logic, trying alternative approach...');
      
      // Alternative: assume all links that are not explicitly broken are working
      const alternativeWorking = linkValidations.filter(link => {
        const isExplicitlyBroken = link.status === 'broken' || 
                                  link.status === 'error' || 
                                  link.status === 'timeout' ||
                                  link.status === 'failed' ||
                                  (link.status_code && link.status_code >= 400);
        
        return !isExplicitlyBroken;
      });
      
      console.log('Alternative working links count:', alternativeWorking.length);
      return alternativeWorking;
    }
    
    return working;
  };

  const getRedirectLinks = () => {
    return linkValidations.filter(link => 
      link.status_code && link.status_code >= 300 && link.status_code < 400
    );
  };

  const getBlankPages = () => {
    return results?.filter(result => result.page_type === 'blank') || [];
  };

  const getContentPages = () => {
    return results?.filter(result => result.page_type === 'content') || [];
  };

  const getParentChildPath = (url) => {
    // Use actual parent-child relationships data from API
    console.log('getParentChildPath called with URL:', url);
    console.log('parentChildRelationships:', parentChildRelationships);
    
    if (!parentChildRelationships || !parentChildRelationships.path_map || !url) {
      console.log('No parent-child relationships data available');
      return [];
    }
    
    // Get the navigation path from the API data
    const navigationPath = parentChildRelationships.path_map[url] || [];
    console.log('Navigation path for', url, ':', navigationPath);
    
    // Convert URLs to page titles if possible
    const result = navigationPath.map(pathUrl => {
      // Try to find the page title from results
      const page = results?.pages?.find(p => p.page_url === pathUrl);
      if (page?.page_title) {
        return page.page_title;
      }
      
      // If no page title found, try to get a meaningful title from the URL
      if (pathUrl.includes('/collections/')) {
        return 'Collections Page';
      } else if (pathUrl.includes('/products/')) {
        return 'Product Page';
      } else if (pathUrl.includes('/pages/')) {
        return 'Page';
      } else if (pathUrl.includes('/recommendations/')) {
        return 'Recommendations Page';
      } else {
        return pathUrl;
      }
    });
    
    console.log('Formatted path result:', result);
    return result;
  };


  const handleDownloadReport = () => {
    if (!run || !results) {
      toast.error('No data available for download');
      return;
    }

    const reportData = {
      run: run,
      results: results,
      linkValidations: linkValidations,
      summary: {
        totalPages: run.total_pages_analyzed || 0,
        totalLinks: run.total_links_found || 0,
        brokenLinks: run.broken_links_count || 0,
        blankPages: run.blank_pages_count || 0,
        overallScore: run.overall_score || 0
      },
      generatedAt: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis-report-${run.id}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    toast.success('Report downloaded successfully');
  };

  const handleRunContentAnalysis = async () => {
    try {
      const result = await analysisService.runContentAnalysis(runId);
      setContentAnalysisTask({
        taskId: result.task_id,
        status: 'PENDING',
        progress: 0
      });
      toast.success('Content analysis started!');
      
      // Start polling for status
      pollContentAnalysisStatus(result.task_id);
    } catch (error) {
      toast.error('Failed to start content analysis');
      console.error('Content analysis error:', error);
    }
  };

  const pollContentAnalysisStatus = async (taskId) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await analysisService.getContentAnalysisStatus(runId, taskId);
        setContentAnalysisTask(prev => ({
          ...prev,
          status: status.status,
          progress: status.result?.progress || 0
        }));
        
        if (status.ready) {
          clearInterval(pollInterval);
          if (status.status === 'SUCCESS') {
            setContentAnalysisResults(status.result);
            toast.success('Content analysis completed!');
          } else {
            toast.error('Content analysis failed');
          }
        }
      } catch (error) {
        console.error('Error polling content analysis status:', error);
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  const loadAvailableRuns = async () => {
    try {
      if (application && application.id) {
        const runs = await analysisService.getAnalysisRuns(application.id);
        // Filter out the current run and only show completed runs
        const filteredRuns = runs.filter(run => 
          run.id !== runId && 
          run._id !== runId && 
          run.status === 'completed'
        );
        setAvailableRuns(filteredRuns);
      }
    } catch (error) {
      console.error('Error loading available runs:', error);
      toast.error('Failed to load available runs for comparison');
    }
  };

  const handleOpenComparisonModal = () => {
    setShowComparisonModal(true);
    loadAvailableRuns();
  };

  const handleCompareRuns = () => {
    if (selectedRunForComparison) {
      const comparisonUrl = `/content-comparison/${runId}/${selectedRunForComparison.id || selectedRunForComparison._id}`;
      navigate(comparisonUrl);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="text-center py-12">
        <XCircle className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Analysis not found</h3>
        <p className="mt-1 text-sm text-gray-500">The requested analysis run could not be found.</p>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 btn btn-primary"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go Back
        </button>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: TrendingUp },
    { id: 'links', name: 'Link Analysis', icon: Link },
    { id: 'pages', name: 'Page Analysis', icon: FileText },
    { id: 'issues', name: 'Issues & Recommendations', icon: AlertTriangle },
    { id: 'navigation', name: 'Navigation Paths', icon: MapPin },
    { id: 'context', name: 'Content Context', icon: Eye },
    { id: 'ai-analysis', name: 'AI Analysis', icon: Zap }
  ];

  // Debug logging
  console.log('AnalysisInsights render - run:', run);
  console.log('AnalysisInsights render - loading:', loading);
  console.log('AnalysisInsights render - runId:', runId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate(-1)}
              className="text-gray-400 hover:text-gray-600"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
                Analysis Insights
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Detailed analysis results for run {run.id}
              </p>
            </div>
          </div>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0 space-x-3">
          <button 
            onClick={handleDownloadReport}
            className="btn btn-secondary"
          >
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </button>
          <button 
            onClick={handleOpenComparisonModal}
            className="btn btn-secondary"
          >
            <Target className="h-4 w-4 mr-2" />
            Compare Runs
          </button>
          <button 
            onClick={handleRunContentAnalysis}
            disabled={contentAnalysisTask && contentAnalysisTask.status === 'PENDING'}
            className="btn btn-primary"
          >
            {contentAnalysisTask && contentAnalysisTask.status === 'PENDING' ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Analyzing...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4 mr-2" />
                AI Content Analysis
              </>
            )}
          </button>
        </div>
      </div>

      {/* Run Status Card */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {getStatusIcon(run.status)}
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Analysis Status
              </h3>
              <p className="text-sm text-gray-500">
                Started: {formatDate(run.started_at || run.created_at)}
                {run.completed_at && ` • Completed: ${formatDate(run.completed_at)}`}
              </p>
            </div>
          </div>
          <div className="text-right">
            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(run.status)}`}>
              {run.status}
            </span>
            {run.overall_score && (
              <p className="mt-1 text-sm text-gray-500">
                Overall Score: {run.overall_score}/100
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-blue-100">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Pages Analyzed
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {run.total_pages_analyzed || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-green-100">
              <Link className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Links Found
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {run.total_links_found || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-red-100">
              <XCircle className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Broken Links
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {run.broken_links_count || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-yellow-100">
              <AlertTriangle className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Blank Pages
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {run.blank_pages_count || 0}
                </dd>
              </dl>
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
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
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
          {activeTab === 'ai-analysis' && (
            <div className="space-y-6">
              {/* AI Analysis Header */}
              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">AI Content Analysis</h3>
                    <p className="text-sm text-gray-500">
                      Deep AI-powered analysis of your website content
                    </p>
                  </div>
                  <div className="flex space-x-3">
                    {!contentAnalysisTask && (
                      <button 
                        onClick={handleRunContentAnalysis}
                        className="btn btn-primary"
                      >
                        <Zap className="h-4 w-4 mr-2" />
                        Run AI Analysis
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Content Analysis Status */}
              {contentAnalysisTask && (
                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-md font-medium text-gray-900">Analysis Status</h4>
                      <p className="text-sm text-gray-500">
                        Status: {contentAnalysisTask.status}
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${contentAnalysisTask.progress}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600">
                        {contentAnalysisTask.progress}%
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Analysis Results */}
              {contentAnalysisResults && (
                <div className="space-y-6">
                  <div className="card">
                    <h4 className="text-lg font-medium text-gray-900 mb-4">Analysis Summary</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {contentAnalysisResults.total_pages_analyzed}
                        </div>
                        <div className="text-sm text-blue-800">Pages Analyzed</div>
                      </div>
                      <div className="bg-green-50 p-4 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {contentAnalysisResults.status}
                        </div>
                        <div className="text-sm text-green-800">Status</div>
                      </div>
                      <div className="bg-purple-50 p-4 rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          GPT-3.5
                        </div>
                        <div className="text-sm text-purple-800">AI Model</div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h4 className="text-lg font-medium text-gray-900 mb-4">AI Insights</h4>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-start">
                        <div className="flex-shrink-0">
                          <Zap className="h-5 w-5 text-yellow-600" />
                        </div>
                        <div className="ml-3">
                          <h5 className="text-sm font-medium text-yellow-800">
                            AI Analysis Complete
                          </h5>
                          <p className="text-sm text-yellow-700 mt-1">
                            Your content has been analyzed by AI. Detailed insights are available in the analysis results.
                            This includes content quality scores, SEO recommendations, user experience insights, and technical analysis.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h4 className="text-lg font-medium text-gray-900 mb-4">Next Steps</h4>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center">
                            <span className="text-xs font-medium text-primary-600">1</span>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Review AI Recommendations</p>
                          <p className="text-sm text-gray-500">Check the detailed analysis for actionable insights</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center">
                            <span className="text-xs font-medium text-primary-600">2</span>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Compare with Previous Runs</p>
                          <p className="text-sm text-gray-500">Use the comparison feature to track content changes over time</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center">
                            <span className="text-xs font-medium text-primary-600">3</span>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Implement Improvements</p>
                          <p className="text-sm text-gray-500">Apply the AI recommendations to improve your content</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* No Analysis State */}
              {!contentAnalysisTask && !contentAnalysisResults && (
                <div className="card">
                  <div className="text-center py-12">
                    <Zap className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No AI Analysis Yet</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Run AI content analysis to get deep insights into your website content quality, SEO, and user experience.
                    </p>
                    <div className="mt-6">
                      <button 
                        onClick={handleRunContentAnalysis}
                        className="btn btn-primary"
                      >
                        <Zap className="h-4 w-4 mr-2" />
                        Start AI Analysis
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Analysis Summary</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Website URL</h4>
                  <p className="mt-1 text-sm text-gray-900">{application?.website_url || 'N/A'}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Analysis Date</h4>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(run.created_at)}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Total Pages</h4>
                  <p className="mt-1 text-sm text-gray-900">{run.total_pages_analyzed || 0}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Total Links</h4>
                  <p className="mt-1 text-sm text-gray-900">{run.total_links_found || 0}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'links' && (
          <div className="space-y-6">
            {/* Broken Links */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <XCircle className="h-5 w-5 text-red-500 mr-2" />
                Broken Links ({getBrokenLinks().length})
              </h3>
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        URL
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status Code
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Parent Page
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {getBrokenLinks().map((link) => (
                      <tr key={link.id || link._id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <span className="truncate max-w-xs">{link.url}</span>
                            <button
                              onClick={() => window.open(link.url, '_blank')}
                              className="ml-2 text-gray-400 hover:text-gray-600"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            link.status_code >= 500 ? 'bg-red-100 text-red-800' :
                            link.status_code >= 400 ? 'bg-orange-100 text-orange-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {link.status_code}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatParentChildPath(getParentChildPath(link.parent_url || 'N/A'))}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => window.open(link.url, '_blank')}
                            className="text-primary-600 hover:text-primary-900"
                          >
                            Test Link
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Working Links */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                Working Links ({getWorkingLinks().length})
              </h3>
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        URL
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status Code
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Response Time
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {getWorkingLinks().slice(0, 10).map((link) => (
                      <tr key={link.id || link._id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <span className="truncate max-w-xs">
                              {link.isFallback ? 'Working link (calculated from totals)' : link.url}
                            </span>
                            {!link.isFallback && (
                              <button
                                onClick={() => window.open(link.url, '_blank')}
                                className="ml-2 text-gray-400 hover:text-gray-600"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            {link.status_code || '200'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {link.response_time ? `${link.response_time}ms` : (link.isFallback ? 'N/A' : 'N/A')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {getWorkingLinks().length > 10 && (
                  <div className="px-6 py-3 bg-gray-50 text-sm text-gray-500">
                    Showing 10 of {getWorkingLinks().length} working links
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'pages' && (
          <div className="space-y-6">
            {/* Blank Pages */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
                Blank Pages ({getBlankPages().length})
              </h3>
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        URL
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Title
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Content Length
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {getBlankPages().map((page) => (
                      <tr key={page.id || page._id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <span className="truncate max-w-xs">{page.page_url}</span>
                            <button
                              onClick={() => window.open(page.page_url, '_blank')}
                              className="ml-2 text-gray-400 hover:text-gray-600"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {page.page_title || 'No title'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {page.word_count || 0} words
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => handleOpenLinkInfo({ url: page.page_url, status_code: 200, type: 'blank' })}
                            className="flex items-center px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                          >
                            <FileText className="h-3 w-3 mr-1" />
                            View Info
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Content Pages */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <FileText className="h-5 w-5 text-blue-500 mr-2" />
                Content Pages ({getContentPages().length})
              </h3>
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        URL
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Title
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Content Length
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Score
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {getContentPages().slice(0, 10).map((page) => (
                      <tr key={page.id || page._id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <span className="truncate max-w-xs">{page.page_url}</span>
                            <button
                              onClick={() => window.open(page.page_url, '_blank')}
                              className="ml-2 text-gray-400 hover:text-gray-600"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {page.page_title || 'No title'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {page.word_count || 0} words
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {page.quality_score ? `${page.quality_score}/100` : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => handleOpenLinkInfo({ url: page.page_url, status_code: 200, type: 'content' })}
                            className="flex items-center px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                          >
                            <FileText className="h-3 w-3 mr-1" />
                            View Info
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {getContentPages().length > 10 && (
                  <div className="px-6 py-3 bg-gray-50 text-sm text-gray-500">
                    Showing 10 of {getContentPages().length} content pages
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'issues' && (
          <div className="space-y-6">
            {/* Critical Issues */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Critical Issues</h3>
              <div className="space-y-4">
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <XCircle className="h-5 w-5 text-red-400" />
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-red-800">Broken Links ({run.broken_links_count || 0})</h4>
                      <div className="mt-2 text-sm text-red-700">
                        <p>These links return error status codes and need immediate attention:</p>
                        <ul className="list-disc list-inside space-y-1 mt-2">
                          {getBrokenLinks().slice(0, 3).map((link, index) => (
                            <li key={index}>
                              <strong>{link.status_code}</strong> - {link.url}
                              <br />
                              <span className="text-xs text-gray-600">
                                Found on: {formatParentChildPath(getParentChildPath(link.parent_url || link.url))}
                              </span>
                            </li>
                          ))}
                          {getBrokenLinks().length > 3 && (
                            <li className="text-xs text-gray-600">
                              ... and {getBrokenLinks().length - 3} more broken links
                            </li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <AlertTriangle className="h-5 w-5 text-yellow-400" />
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-yellow-800">Blank Pages ({run.blank_pages_count || 0})</h4>
                      <div className="mt-2 text-sm text-yellow-700">
                        <p>These pages have minimal content and may hurt SEO:</p>
                        <ul className="list-disc list-inside space-y-1 mt-2">
                          {getBlankPages().slice(0, 3).map((page, index) => (
                            <li key={index}>
                              <strong>{page.page_title || 'Untitled'}</strong>
                              <br />
                              <span className="text-xs text-gray-600">
                                {page.page_url} ({page.word_count || 0} words)
                              </span>
                            </li>
                          ))}
                          {getBlankPages().length > 3 && (
                            <li className="text-xs text-gray-600">
                              ... and {getBlankPages().length - 3} more blank pages
                            </li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Recommendations</h3>
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <Target className="h-5 w-5 text-blue-400" />
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-blue-800">Immediate Actions</h4>
                      <div className="mt-2 text-sm text-blue-700">
                        <ul className="list-disc list-inside space-y-1">
                          <li><strong>Fix {run.broken_links_count || 0} broken links</strong> - Update URLs or remove dead links</li>
                          <li><strong>Address {run.blank_pages_count || 0} blank pages</strong> - Add content or implement redirects</li>
                          <li><strong>Optimize page titles</strong> - Ensure all pages have descriptive titles</li>
                          <li><strong>Improve navigation structure</strong> - Ensure all pages are reachable within 3 clicks</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-5 w-5 text-green-400" />
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-green-800">Performance Improvements</h4>
                      <div className="mt-2 text-sm text-green-700">
                        <ul className="list-disc list-inside space-y-1">
                          <li><strong>Content Quality</strong> - {getContentPages().length} pages have good content, maintain this standard</li>
                          <li><strong>Link Health</strong> - {getWorkingLinks().length} working links, keep monitoring for changes</li>
                          <li><strong>Site Structure</strong> - Consider implementing breadcrumb navigation</li>
                          <li><strong>SEO Optimization</strong> - Add meta descriptions to pages missing them</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <Zap className="h-5 w-5 text-purple-400" />
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-purple-800">Long-term Strategy</h4>
                      <div className="mt-2 text-sm text-purple-700">
                        <ul className="list-disc list-inside space-y-1">
                          <li><strong>Regular Monitoring</strong> - Set up automated link checking</li>
                          <li><strong>Content Audit</strong> - Review and update content quarterly</li>
                          <li><strong>User Experience</strong> - Implement user feedback collection</li>
                          <li><strong>Analytics Integration</strong> - Track user behavior and page performance</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Status Code Analysis */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Status Code Analysis</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="bg-green-100 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-800">{getWorkingLinks().length}</div>
                  <div className="text-sm text-green-600">2xx Success</div>
                </div>
                <div className="bg-yellow-100 rounded-lg p-4">
                  <div className="text-2xl font-bold text-yellow-800">{getRedirectLinks().length}</div>
                  <div className="text-sm text-yellow-600">3xx Redirects</div>
                </div>
                <div className="bg-red-100 rounded-lg p-4">
                  <div className="text-2xl font-bold text-red-800">{getBrokenLinks().length}</div>
                  <div className="text-sm text-red-600">4xx/5xx Errors</div>
                </div>
                <div className="bg-blue-100 rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-800">{linkValidations.length}</div>
                  <div className="text-sm text-blue-600">Total Links</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'navigation' && (
          <div className="space-y-6">
            {/* Navigation Path Analysis Header */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Navigation Path Analysis</h3>
              <p className="text-sm text-gray-600 mb-4">
                Track the navigation paths to broken links and understand the user journey to problematic pages.
              </p>
            </div>

            {/* Broken Links with Navigation Paths */}
            {getBrokenLinks().length > 0 && (
              <div className="card">
                <h4 className="text-md font-medium text-gray-900 mb-4">Broken Links & Navigation Paths</h4>
                <div className="space-y-6">
                  {getBrokenLinks().map((link, index) => {
                    const parentInfo = getParentInfo(link.url);
                    const navigationPath = getNavigationPath(link.url);
                    
                    return (
                      <div key={index} className="border border-red-200 rounded-lg p-4 bg-red-50">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center mb-2">
                              <XCircle className="h-4 w-4 text-red-500 mr-2" />
                              <span className="text-sm font-medium text-red-800">Broken Link</span>
                            </div>
                            <a 
                              href={link.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-sm text-red-700 hover:text-red-900 break-all"
                            >
                              {link.url}
                            </a>
                            <div className="mt-1 text-xs text-red-600">
                              Status: {link.status_code || 'Unknown'} | Found on: {parentInfo?.title || 'Unknown'}
                            </div>
                          </div>
                          
                          {/* Action Button */}
                          <div className="ml-4">
                            <button
                              onClick={() => handleOpenLinkInfo(link)}
                              className="flex items-center px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                            >
                              <FileText className="h-3 w-3 mr-1" />
                              View Info
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Page Hierarchy Analysis */}
            <div className="card">
              <h4 className="text-md font-medium text-gray-900 mb-4">Page Hierarchy & Relationships</h4>
              <div className="space-y-4">
                {results && results.slice(0, 10).map((page, index) => {
                  const parentChildPath = getParentChildPath(page.page_url);
                  return (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center mb-2">
                            <FileText className="h-4 w-4 text-blue-500 mr-2" />
                            <span className="text-sm font-medium text-gray-900">{page.page_title}</span>
                          </div>
                          <a 
                            href={page.page_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-blue-700 hover:text-blue-900 break-all"
                          >
                            {page.page_url}
                          </a>
                          <div className="mt-1 text-xs text-gray-600">
                            {page.word_count} words | {page.page_type}
                          </div>
                        </div>
                        
                        {/* View Info Button */}
                        <div className="ml-4">
                          <button
                            onClick={() => handleOpenLinkInfo({ 
                              url: page.page_url, 
                              status_code: 200, 
                              type: 'content' 
                            })}
                            className="flex items-center px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                          >
                            <FileText className="h-3 w-3 mr-1" />
                            View Info
                          </button>
                        </div>
                      </div>

                      {/* Parent-Child Relationships */}
                      {parentChildPath && parentChildPath.length > 0 && (
                        <div className="mt-3">
                          <h6 className="text-xs font-medium text-gray-700 mb-2">Parent-Child Path:</h6>
                          <div className="text-xs text-gray-600">
                            {formatParentChildPath(parentChildPath)}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              
              {results && results.length > 10 && (
                <div className="mt-4 text-center">
                  <p className="text-sm text-gray-500">
                    Showing 10 of {results.length} pages. Use the Page Analysis tab to see all pages.
                  </p>
                </div>
              )}
            </div>

            {/* Navigation Statistics */}
            <div className="card">
              <h4 className="text-md font-medium text-gray-900 mb-4">Navigation Statistics</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{getBrokenLinks().length}</div>
                  <div className="text-sm text-red-800">Broken Links</div>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{results ? results.length : 0}</div>
                  <div className="text-sm text-blue-800">Total Pages</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{getWorkingLinks().length}</div>
                  <div className="text-sm text-green-800">Working Links</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'context' && (
          <div className="space-y-6">
            {/* Content Overview */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Content Overview</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-800">{getContentPages().length}</div>
                  <div className="text-sm text-blue-600">Content Pages</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Average: {getContentPages().length > 0 ? Math.round(getContentPages().reduce((sum, page) => sum + (page.word_count || 0), 0) / getContentPages().length) : 0} words
                  </div>
                </div>
                <div className="bg-yellow-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-yellow-800">{getBlankPages().length}</div>
                  <div className="text-sm text-yellow-600">Blank Pages</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Need content or removal
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-800">
                    {results?.filter(r => r.has_header && r.has_footer && r.has_navigation).length || 0}
                  </div>
                  <div className="text-sm text-green-600">Complete Pages</div>
                  <div className="text-xs text-gray-500 mt-1">
                    With header, footer & navigation
                  </div>
                </div>
              </div>
            </div>

            {/* Page Structure Analysis */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Page Structure Analysis</h3>
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Page
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Structure
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Content
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quality
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {results?.slice(0, 10).map((page) => (
                      <tr key={page.id || page._id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <span className="truncate max-w-xs">{page.page_title || 'Untitled'}</span>
                            <button
                              onClick={() => window.open(page.page_url, '_blank')}
                              className="ml-2 text-gray-400 hover:text-gray-600"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex space-x-1">
                            {page.has_header && <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Header</span>}
                            {page.has_footer && <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">Footer</span>}
                            {page.has_navigation && <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">Nav</span>}
                            {!page.has_header && !page.has_footer && !page.has_navigation && (
                              <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">Minimal</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            (page.word_count || 0) > 1000 ? 'bg-green-100 text-green-800' :
                            (page.word_count || 0) > 500 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {page.word_count || 0} words
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            page.page_type === 'content' ? 'bg-green-100 text-green-800' :
                            page.page_type === 'blank' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {page.page_type}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {results && results.length > 10 && (
                  <div className="px-6 py-3 bg-gray-50 text-sm text-gray-500">
                    Showing 10 of {results.length} pages
                  </div>
                )}
              </div>
            </div>


            {/* Content Quality Metrics */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Content Quality Metrics</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Content Distribution</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>High Content (1000+ words)</span>
                      <span className="font-medium">
                        {results?.filter(r => (r.word_count || 0) > 1000).length || 0}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Medium Content (500-1000 words)</span>
                      <span className="font-medium">
                        {results?.filter(r => (r.word_count || 0) >= 500 && (r.word_count || 0) <= 1000).length || 0}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Low Content (100-500 words)</span>
                      <span className="font-medium">
                        {results?.filter(r => (r.word_count || 0) >= 100 && (r.word_count || 0) < 500).length || 0}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Minimal Content (&lt;100 words)</span>
                      <span className="font-medium">
                        {results?.filter(r => (r.word_count || 0) < 100).length || 0}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Structure Completeness</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Complete Structure</span>
                      <span className="font-medium">
                        {results?.filter(r => r.has_header && r.has_footer && r.has_navigation).length || 0}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Partial Structure</span>
                      <span className="font-medium">
                        {results?.filter(r => (r.has_header || r.has_footer || r.has_navigation) && !(r.has_header && r.has_footer && r.has_navigation)).length || 0}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Minimal Structure</span>
                      <span className="font-medium">
                        {results?.filter(r => !r.has_header && !r.has_footer && !r.has_navigation).length || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Comparison Modal */}
      {showComparisonModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Compare Analysis Runs</h3>
                <button
                  onClick={() => setShowComparisonModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>
              
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  Select a previous run to compare with the current run:
                </p>
                <p className="text-xs text-gray-500 mb-4">
                  Current Run: {run?.started_at ? new Date(run.started_at).toLocaleString() : 'Unknown'}
                </p>
              </div>

              {availableRuns.length > 0 ? (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {availableRuns.map((run) => (
                    <div
                      key={run.id || run._id}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedRunForComparison?.id === run.id || selectedRunForComparison?._id === run._id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedRunForComparison(run)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {run.started_at ? new Date(run.started_at).toLocaleString() : 'Unknown Date'}
                          </div>
                          <div className="text-xs text-gray-500">
                            Pages: {run.total_pages_analyzed || 0} | Score: {run.overall_score || 0}/100
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">
                          {run.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Target className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No runs available</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    No other completed runs found for this application.
                  </p>
                </div>
              )}

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowComparisonModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCompareRuns}
                  disabled={!selectedRunForComparison}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Compare Runs
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Source Code Viewer Modal */}
      <SourceCodeViewer
        isOpen={sourceViewerOpen}
        onClose={() => {
          setSourceViewerOpen(false);
          setSourceViewerData(null);
        }}
        sourceData={sourceViewerData}
        brokenUrl={sourceViewerData?.brokenUrl}
      />

      {/* Link Info Modal */}
      {selectedLink && (
        <LinkInfoModal
          isOpen={linkInfoModalOpen}
          onClose={() => {
            setLinkInfoModalOpen(false);
            setSelectedLink(null);
          }}
          link={selectedLink}
          parentInfo={getParentInfo(selectedLink.url)}
          navigationPath={getNavigationPath(selectedLink.url)}
          onViewSource={handleViewSource}
          onViewLink={handleViewSource}
          results={results}
        />
      )}
    </div>
  );
};

export default AnalysisInsights;
