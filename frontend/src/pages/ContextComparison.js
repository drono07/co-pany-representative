import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft,
  GitCompare,
  FileText,
  Link,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  Eye,
  Download
} from 'lucide-react';
import { analysisService } from '../services/api';
import toast from 'react-hot-toast';

const ContextComparison = () => {
  const { appId } = useParams();
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [selectedRuns, setSelectedRuns] = useState({ run1: null, run2: null });
  const [run1Data, setRun1Data] = useState(null);
  const [run2Data, setRun2Data] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const loadRuns = useCallback(async () => {
    try {
      const data = await analysisService.getApplicationRuns(appId, 20);
      setRuns(data);
    } catch (error) {
      toast.error('Failed to load analysis runs');
      console.error('Runs error:', error);
    } finally {
      setLoading(false);
    }
  }, [appId]);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  const handleRunSelection = (runId, type) => {
    setSelectedRuns(prev => ({
      ...prev,
      [type]: runId
    }));
  };

  const compareRuns = async () => {
    if (!selectedRuns.run1 || !selectedRuns.run2) {
      toast.error('Please select both runs to compare');
      return;
    }

    if (selectedRuns.run1 === selectedRuns.run2) {
      toast.error('Please select different runs to compare');
      return;
    }

    setComparing(true);
    try {
      // Load both runs data
      const [data1, data2] = await Promise.all([
        analysisService.getAnalysisRun(selectedRuns.run1),
        analysisService.getAnalysisRun(selectedRuns.run2)
      ]);

      setRun1Data(data1);
      setRun2Data(data2);

      // Perform comparison
      const comparisonResult = performComparison(data1, data2);
      setComparison(comparisonResult);
      
      toast.success('Comparison completed successfully');
    } catch (error) {
      toast.error('Failed to compare runs');
      console.error('Comparison error:', error);
    } finally {
      setComparing(false);
    }
  };

  const performComparison = (data1, data2) => {
    const run1 = data1.run;
    const run2 = data2.run;
    const results1 = data1.results || [];
    const results2 = data2.results || [];
    const links1 = data1.link_validations || [];
    const links2 = data2.link_validations || [];

    // Compare basic metrics
    const metricsComparison = {
      pages: {
        run1: run1.total_pages_analyzed || 0,
        run2: run2.total_pages_analyzed || 0,
        change: (run2.total_pages_analyzed || 0) - (run1.total_pages_analyzed || 0)
      },
      links: {
        run1: run1.total_links_found || 0,
        run2: run2.total_links_found || 0,
        change: (run2.total_links_found || 0) - (run1.total_links_found || 0)
      },
      brokenLinks: {
        run1: run1.broken_links_count || 0,
        run2: run2.broken_links_count || 0,
        change: (run2.broken_links_count || 0) - (run1.broken_links_count || 0)
      },
      blankPages: {
        run1: run1.blank_pages_count || 0,
        run2: run2.blank_pages_count || 0,
        change: (run2.blank_pages_count || 0) - (run1.blank_pages_count || 0)
      },
      overallScore: {
        run1: run1.overall_score || 0,
        run2: run2.overall_score || 0,
        change: (run2.overall_score || 0) - (run1.overall_score || 0)
      }
    };

    // Compare pages
    const pages1 = new Map(results1.map(p => [p.page_url, p]));
    const pages2 = new Map(results2.map(p => [p.page_url, p]));
    
    const newPages = results2.filter(p => !pages1.has(p.page_url));
    const removedPages = results1.filter(p => !pages2.has(p.page_url));
    const commonPages = results1.filter(p => pages2.has(p.page_url));
    
    const changedPages = commonPages.filter(page1 => {
      const page2 = pages2.get(page1.page_url);
      return page1.content_length !== page2.content_length || 
             page1.page_type !== page2.page_type ||
             page1.quality_score !== page2.quality_score;
    });

    // Compare links
    const links1Map = new Map(links1.map(l => [l.url, l]));
    const links2Map = new Map(links2.map(l => [l.url, l]));
    
    const newLinks = links2.filter(l => !links1Map.has(l.url));
    const removedLinks = links1.filter(l => !links2Map.has(l.url));
    const commonLinks = links1.filter(l => links2Map.has(l.url));
    
    const fixedLinks = commonLinks.filter(link1 => {
      const link2 = links2Map.get(link1.url);
      return link1.status === 'broken' && link2.status === 'valid';
    });
    
    const brokenLinks = commonLinks.filter(link1 => {
      const link2 = links2Map.get(link1.url);
      return link1.status === 'valid' && link2.status === 'broken';
    });

    return {
      metrics: metricsComparison,
      pages: {
        new: newPages,
        removed: removedPages,
        changed: changedPages,
        total: {
          run1: results1.length,
          run2: results2.length
        }
      },
      links: {
        new: newLinks,
        removed: removedLinks,
        fixed: fixedLinks,
        broken: brokenLinks,
        total: {
          run1: links1.length,
          run2: links2.length
        }
      },
      run1: run1,
      run2: run2
    };
  };

  const getChangeIcon = (change) => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (change < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const handleDownloadComparison = () => {
    if (!comparison) {
      toast.error('No comparison data to download');
      return;
    }

    const reportData = {
      comparison: comparison,
      generatedAt: new Date().toISOString(),
      run1: run1Data,
      run2: run2Data
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `context-comparison-${selectedRuns.run1}-vs-${selectedRuns.run2}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    toast.success('Comparison report downloaded successfully');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: GitCompare },
    { id: 'pages', name: 'Page Changes', icon: FileText },
    { id: 'links', name: 'Link Changes', icon: Link },
    { id: 'content', name: 'Content Analysis', icon: Eye }
  ];

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
                Context Comparison
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Compare analysis runs to track changes over time
              </p>
            </div>
          </div>
        </div>
        {comparison && (
          <div className="mt-4 flex md:ml-4 md:mt-0 space-x-3">
            <button 
              onClick={handleDownloadComparison}
              className="btn btn-secondary"
            >
              <Download className="h-4 w-4 mr-2" />
              Export Comparison
            </button>
          </div>
        )}
      </div>

      {/* Run Selection */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Select Runs to Compare</h3>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              First Run (Baseline)
            </label>
            <select
              value={selectedRuns.run1 || ''}
              onChange={(e) => handleRunSelection(e.target.value, 'run1')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select a run...</option>
              {runs.map((run) => (
                <option key={run.id || run._id} value={run.id || run._id}>
                  {formatDate(run.created_at)} - {run.status} - {run.total_pages_analyzed || 0} pages
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Second Run (Comparison)
            </label>
            <select
              value={selectedRuns.run2 || ''}
              onChange={(e) => handleRunSelection(e.target.value, 'run2')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select a run...</option>
              {runs.map((run) => (
                <option key={run.id || run._id} value={run.id || run._id}>
                  {formatDate(run.created_at)} - {run.status} - {run.total_pages_analyzed || 0} pages
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={compareRuns}
            disabled={!selectedRuns.run1 || !selectedRuns.run2 || comparing}
            className="btn btn-primary"
          >
            {comparing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Comparing...
              </>
            ) : (
              <>
                <GitCompare className="h-4 w-4 mr-2" />
                Compare Runs
              </>
            )}
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {comparison && (
        <>
          {/* Metrics Overview */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
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
                    <dd className="flex items-center text-lg font-medium text-gray-900">
                      {comparison.metrics.pages.run2}
                      <span className={`ml-2 flex items-center ${getChangeColor(comparison.metrics.pages.change)}`}>
                        {getChangeIcon(comparison.metrics.pages.change)}
                        {comparison.metrics.pages.change > 0 ? '+' : ''}{comparison.metrics.pages.change}
                      </span>
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
                    <dd className="flex items-center text-lg font-medium text-gray-900">
                      {comparison.metrics.links.run2}
                      <span className={`ml-2 flex items-center ${getChangeColor(comparison.metrics.links.change)}`}>
                        {getChangeIcon(comparison.metrics.links.change)}
                        {comparison.metrics.links.change > 0 ? '+' : ''}{comparison.metrics.links.change}
                      </span>
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
                    <dd className="flex items-center text-lg font-medium text-gray-900">
                      {comparison.metrics.brokenLinks.run2}
                      <span className={`ml-2 flex items-center ${getChangeColor(-comparison.metrics.brokenLinks.change)}`}>
                        {getChangeIcon(-comparison.metrics.brokenLinks.change)}
                        {comparison.metrics.brokenLinks.change > 0 ? '+' : ''}{comparison.metrics.brokenLinks.change}
                      </span>
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
                    <dd className="flex items-center text-lg font-medium text-gray-900">
                      {comparison.metrics.blankPages.run2}
                      <span className={`ml-2 flex items-center ${getChangeColor(-comparison.metrics.blankPages.change)}`}>
                        {getChangeIcon(-comparison.metrics.blankPages.change)}
                        {comparison.metrics.blankPages.change > 0 ? '+' : ''}{comparison.metrics.blankPages.change}
                      </span>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0 rounded-md p-3 bg-purple-100">
                  <TrendingUp className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Overall Score
                    </dt>
                    <dd className="flex items-center text-lg font-medium text-gray-900">
                      {comparison.metrics.overallScore.run2}/100
                      <span className={`ml-2 flex items-center ${getChangeColor(comparison.metrics.overallScore.change)}`}>
                        {getChangeIcon(comparison.metrics.overallScore.change)}
                        {comparison.metrics.overallScore.change > 0 ? '+' : ''}{comparison.metrics.overallScore.change}
                      </span>
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
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div className="card">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Comparison Summary</h3>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700">Run 1 (Baseline)</h4>
                      <p className="mt-1 text-sm text-gray-900">
                        {formatDate(comparison.run1.created_at)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {comparison.run1.total_pages_analyzed || 0} pages, {comparison.run1.total_links_found || 0} links
                      </p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-700">Run 2 (Comparison)</h4>
                      <p className="mt-1 text-sm text-gray-900">
                        {formatDate(comparison.run2.created_at)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {comparison.run2.total_pages_analyzed || 0} pages, {comparison.run2.total_links_found || 0} links
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div className="card">
                    <h4 className="text-lg font-medium text-gray-900 mb-4">Page Changes</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">New Pages</span>
                        <span className="text-sm font-medium text-green-600">
                          +{comparison.pages.new.length}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Removed Pages</span>
                        <span className="text-sm font-medium text-red-600">
                          -{comparison.pages.removed.length}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Changed Pages</span>
                        <span className="text-sm font-medium text-yellow-600">
                          {comparison.pages.changed.length}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h4 className="text-lg font-medium text-gray-900 mb-4">Link Changes</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">New Links</span>
                        <span className="text-sm font-medium text-green-600">
                          +{comparison.links.new.length}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Removed Links</span>
                        <span className="text-sm font-medium text-red-600">
                          -{comparison.links.removed.length}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Fixed Links</span>
                        <span className="text-sm font-medium text-green-600">
                          +{comparison.links.fixed.length}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">New Broken Links</span>
                        <span className="text-sm font-medium text-red-600">
                          +{comparison.links.broken.length}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'pages' && (
              <div className="space-y-6">
                {/* New Pages */}
                {comparison.pages.new.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      New Pages ({comparison.pages.new.length})
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
                              Type
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {comparison.pages.new.map((page) => (
                            <tr key={page.id || page._id}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                <div className="flex items-center">
                                  <span className="truncate max-w-xs">{page.page_url}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {page.page_title || 'No title'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                  page.page_type === 'content' ? 'bg-green-100 text-green-800' :
                                  page.page_type === 'blank' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {page.page_type}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Removed Pages */}
                {comparison.pages.removed.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                      <XCircle className="h-5 w-5 text-red-500 mr-2" />
                      Removed Pages ({comparison.pages.removed.length})
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
                              Type
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {comparison.pages.removed.map((page) => (
                            <tr key={page.id || page._id}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                <div className="flex items-center">
                                  <span className="truncate max-w-xs">{page.page_url}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {page.page_title || 'No title'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                  page.page_type === 'content' ? 'bg-green-100 text-green-800' :
                                  page.page_type === 'blank' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {page.page_type}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Changed Pages */}
                {comparison.pages.changed.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                      <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
                      Changed Pages ({comparison.pages.changed.length})
                    </h3>
                    <div className="overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              URL
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Content Length Change
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Type Change
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {comparison.pages.changed.map((page1) => {
                            const page2 = run2Data.results.find(p => p.page_url === page1.page_url);
                            const contentChange = (page2?.content_length || 0) - (page1.content_length || 0);
                            return (
                              <tr key={page1.id || page1._id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  <div className="flex items-center">
                                    <span className="truncate max-w-xs">{page1.page_url}</span>
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  <span className={`flex items-center ${getChangeColor(contentChange)}`}>
                                    {getChangeIcon(contentChange)}
                                    {contentChange > 0 ? '+' : ''}{contentChange} chars
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {page1.page_type !== page2?.page_type && (
                                    <span className="text-yellow-600">
                                      {page1.page_type} → {page2?.page_type}
                                    </span>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'links' && (
              <div className="space-y-6">
                {/* Fixed Links */}
                {comparison.links.fixed.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      Fixed Links ({comparison.links.fixed.length})
                    </h3>
                    <div className="overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              URL
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Status Change
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Parent Page
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {comparison.links.fixed.map((link1) => {
                            const link2 = run2Data.link_validations.find(l => l.url === link1.url);
                            return (
                              <tr key={link1.id || link1._id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  <div className="flex items-center">
                                    <span className="truncate max-w-xs">{link1.url}</span>
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  <span className="text-green-600">
                                    {link1.status_code} → {link2?.status_code}
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {link1.parent_url || 'N/A'}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* New Broken Links */}
                {comparison.links.broken.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                      <XCircle className="h-5 w-5 text-red-500 mr-2" />
                      New Broken Links ({comparison.links.broken.length})
                    </h3>
                    <div className="overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              URL
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Status Change
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Parent Page
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {comparison.links.broken.map((link1) => {
                            const link2 = run2Data.link_validations.find(l => l.url === link1.url);
                            return (
                              <tr key={link1.id || link1._id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  <div className="flex items-center">
                                    <span className="truncate max-w-xs">{link1.url}</span>
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  <span className="text-red-600">
                                    {link1.status_code} → {link2?.status_code}
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {link1.parent_url || 'N/A'}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'content' && (
              <div className="space-y-6">
                <div className="card">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Content Analysis</h3>
                  <div className="bg-gray-50 rounded-md p-4">
                    <p className="text-sm text-gray-600">
                      Advanced content analysis features are being developed. This will include:
                    </p>
                    <ul className="mt-2 text-sm text-gray-600 list-disc list-inside space-y-1">
                      <li>Semantic content similarity analysis</li>
                      <li>Content quality changes over time</li>
                      <li>Keyword and topic analysis</li>
                      <li>Content structure comparison</li>
                      <li>SEO impact analysis</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ContextComparison;
