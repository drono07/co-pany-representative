import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Plus, 
  Globe, 
  Play, 
  Trash2, 
  ExternalLink,
  Activity,
  Target,
  Edit
} from 'lucide-react';
import { applicationService, analysisService } from '../services/api';
import EditApplicationModal from '../components/EditApplicationModal';
import toast from 'react-hot-toast';

const Applications = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [startingAnalysis, setStartingAnalysis] = useState(new Set()); // Track which apps are starting analysis
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingApplication, setEditingApplication] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    website_url: '',
    max_crawl_depth: 1,
    max_pages_to_crawl: 500,
    max_links_to_validate: 1500,
    enable_ai_evaluation: false,
    max_ai_evaluation_pages: 10
  });

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    try {
      const data = await applicationService.getApplications();
      setApplications(data);
    } catch (error) {
      toast.error('Failed to load applications');
      console.error('Applications error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApplication = async (e) => {
    e.preventDefault();
    setCreateLoading(true);

    try {
      await applicationService.createApplication(formData);
      toast.success('Application created successfully!');
      setShowCreateModal(false);
      setFormData({
        name: '',
        description: '',
        website_url: '',
        max_crawl_depth: 1,
        max_pages_to_crawl: 500,
        max_links_to_validate: 1500,
        enable_ai_evaluation: false,
        max_ai_evaluation_pages: 10
      });
      loadApplications();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create application');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteApplication = async (id) => {
    if (!window.confirm('Are you sure you want to delete this application?')) {
      return;
    }

    try {
      await applicationService.deleteApplication(id);
      toast.success('Application deleted successfully!');
      loadApplications();
    } catch (error) {
      toast.error('Failed to delete application');
    }
  };

  const handleEditApplication = (application) => {
    setEditingApplication(application);
    setShowEditModal(true);
  };

  const handleApplicationUpdated = () => {
    loadApplications();
  };

  const handleStartAnalysis = async (appId) => {
    setStartingAnalysis(prev => new Set(prev).add(appId));
    try {
      await analysisService.startAnalysis(appId);
      toast.success('Analysis started successfully!');
      // You could navigate to the runs page or show a modal with task details
    } catch (error) {
      toast.error('Failed to start analysis');
    } finally {
      setStartingAnalysis(prev => {
        const newSet = new Set(prev);
        newSet.delete(appId);
        return newSet;
      });
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Auto-adjust max_links_to_validate when max_pages_to_crawl changes
    if (name === 'max_pages_to_crawl') {
      const pages = parseInt(value) || 500;
      setFormData(prev => ({
        ...prev,
        max_links_to_validate: Math.max(pages * 2, 1000) // At least 2x pages
      }));
    }
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
            Applications
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage your website analysis applications
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Application
          </button>
        </div>
      </div>

      {/* Applications Grid */}
      {applications.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
          {applications.map((app) => (
            <div key={app._id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Globe className="h-8 w-8 text-primary-600" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900">{app.name}</h3>
                    <p className="text-sm text-gray-500">{app.website_url}</p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleStartAnalysis(app._id)}
                    disabled={startingAnalysis.has(app._id)}
                    className="text-primary-600 hover:text-primary-900 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Start Analysis"
                  >
                    {startingAnalysis.has(app._id) ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    onClick={() => handleEditApplication(app)}
                    className="text-blue-600 hover:text-blue-900"
                    title="Edit Application"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteApplication(app._id)}
                    className="text-red-600 hover:text-red-900"
                    title="Delete Application"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              
              {app.description && (
                <p className="mt-3 text-sm text-gray-600">{app.description}</p>
              )}
              
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Max Pages:</span>
                  <span className="ml-1 font-medium">{app.max_pages_to_crawl}</span>
                </div>
                <div>
                  <span className="text-gray-500">Max Links:</span>
                  <span className="ml-1 font-medium">{app.max_links_to_validate}</span>
                </div>
                <div>
                  <span className="text-gray-500">Depth:</span>
                  <span className="ml-1 font-medium">{app.max_crawl_depth}</span>
                </div>
                <div>
                  <span className="text-gray-500">AI Eval:</span>
                  <span className="ml-1 font-medium">{app.enable_ai_evaluation ? 'Yes' : 'No'}</span>
                </div>
              </div>
              
              <div className="mt-4 flex space-x-2">
                <Link
                  to={`/runs/${app._id}`}
                  className="flex-1 btn btn-secondary text-center"
                >
                  <Activity className="h-4 w-4 mr-2" />
                  View Runs
                </Link>
                <Link
                  to={`/context-analysis/${app._id}`}
                  className="flex-1 btn btn-primary text-center"
                >
                  <Target className="h-4 w-4 mr-2" />
                  Context Analysis
                </Link>
                <a
                  href={app.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Globe className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No applications</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating a new application.</p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Application
            </button>
          </div>
        </div>
      )}

      {/* Create Application Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowCreateModal(false)} />
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleCreateApplication}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                    Create New Application
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="label">Application Name</label>
                      <input
                        type="text"
                        name="name"
                        required
                        value={formData.name}
                        onChange={handleChange}
                        className="input"
                        placeholder="My Website Analysis"
                      />
                    </div>
                    
                    <div>
                      <label className="label">Description</label>
                      <textarea
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        className="input"
                        rows="3"
                        placeholder="Brief description of this application"
                      />
                    </div>
                    
                    <div>
                      <label className="label">Website URL</label>
                      <input
                        type="url"
                        name="website_url"
                        required
                        value={formData.website_url}
                        onChange={handleChange}
                        className="input"
                        placeholder="https://example.com"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="label">Max Pages to Crawl</label>
                        <input
                          type="number"
                          name="max_pages_to_crawl"
                          min="10"
                          max="1000"
                          value={formData.max_pages_to_crawl}
                          onChange={handleChange}
                          className="input"
                        />
                      </div>
                      
                      <div>
                        <label className="label">Max Links to Validate</label>
                        <input
                          type="number"
                          name="max_links_to_validate"
                          min="10"
                          max="2000"
                          value={formData.max_links_to_validate}
                          onChange={handleChange}
                          className="input"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Should be 2-3x pages for comprehensive validation
                        </p>
                      </div>
                    </div>
                    
                    <div>
                      <label className="label">Max Crawl Depth</label>
                      <select
                        name="max_crawl_depth"
                        value={formData.max_crawl_depth}
                        onChange={handleChange}
                        className="input"
                      >
                        <option value={1}>1 (Shallow)</option>
                        <option value={2}>2 (Medium)</option>
                        <option value={3}>3 (Deep)</option>
                        <option value={4}>4 (Very Deep)</option>
                        <option value={5}>5 (Maximum)</option>
                      </select>
                    </div>
                    
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        name="enable_ai_evaluation"
                        checked={formData.enable_ai_evaluation}
                        onChange={handleChange}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label className="ml-2 text-sm text-gray-700">
                        Enable AI Evaluation
                      </label>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    disabled={createLoading}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                  >
                    {createLoading ? 'Creating...' : 'Create Application'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Application Modal */}
      <EditApplicationModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setEditingApplication(null);
        }}
        application={editingApplication}
        onApplicationUpdated={handleApplicationUpdated}
      />
    </div>
  );
};

export default Applications;
