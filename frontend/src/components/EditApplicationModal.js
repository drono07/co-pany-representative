import React, { useState, useEffect } from 'react';
import { X, Save, Globe, Settings, Bot } from 'lucide-react';
import { applicationService } from '../services/api';
import toast from 'react-hot-toast';

const EditApplicationModal = ({ 
  isOpen, 
  onClose, 
  application, 
  onApplicationUpdated 
}) => {
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
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  // Initialize form data when application changes
  useEffect(() => {
    if (application && isOpen) {
      setFormData({
        name: application.name || '',
        description: application.description || '',
        website_url: application.website_url || '',
        max_crawl_depth: application.max_crawl_depth || 1,
        max_pages_to_crawl: application.max_pages_to_crawl || 500,
        max_links_to_validate: application.max_links_to_validate || 1500,
        enable_ai_evaluation: application.enable_ai_evaluation || false,
        max_ai_evaluation_pages: application.max_ai_evaluation_pages || 10
      });
      setErrors({});
    }
  }, [application, isOpen]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Application name is required';
    }

    if (!formData.website_url.trim()) {
      newErrors.website_url = 'Website URL is required';
    } else {
      try {
        new URL(formData.website_url);
      } catch {
        newErrors.website_url = 'Please enter a valid URL';
      }
    }

    if (formData.max_crawl_depth < 1 || formData.max_crawl_depth > 5) {
      newErrors.max_crawl_depth = 'Crawl depth must be between 1 and 5';
    }

    if (formData.max_pages_to_crawl < 10 || formData.max_pages_to_crawl > 1000) {
      newErrors.max_pages_to_crawl = 'Pages to crawl must be between 10 and 1000';
    }

    if (formData.max_links_to_validate < 10 || formData.max_links_to_validate > 2000) {
      newErrors.max_links_to_validate = 'Links to validate must be between 10 and 2000';
    }

    if (formData.enable_ai_evaluation && (formData.max_ai_evaluation_pages < 1 || formData.max_ai_evaluation_pages > 50)) {
      newErrors.max_ai_evaluation_pages = 'AI evaluation pages must be between 1 and 50';
    }

    // Validate that max_links_to_validate is 2-3x max_pages_to_crawl
    const recommendedLinks = Math.ceil(formData.max_pages_to_crawl * 2.5);
    if (formData.max_links_to_validate < formData.max_pages_to_crawl * 2) {
      newErrors.max_links_to_validate = `Recommended: ${recommendedLinks} links (2-3x pages to crawl)`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const updateData = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        website_url: formData.website_url.trim(),
        max_crawl_depth: parseInt(formData.max_crawl_depth),
        max_pages_to_crawl: parseInt(formData.max_pages_to_crawl),
        max_links_to_validate: parseInt(formData.max_links_to_validate),
        enable_ai_evaluation: formData.enable_ai_evaluation,
        max_ai_evaluation_pages: formData.enable_ai_evaluation ? parseInt(formData.max_ai_evaluation_pages) : null
      };

      await applicationService.partialUpdateApplication(application._id, updateData);
      toast.success('Application updated successfully');
      onApplicationUpdated();
      onClose();
    } catch (error) {
      console.error('Update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update application');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
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
    setErrors({});
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center">
            <Settings className="h-6 w-6 text-blue-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Edit Application</h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-auto p-6">
          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Globe className="h-5 w-5 mr-2" />
                Basic Information
              </h3>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Application Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.name ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Enter application name"
                  />
                  {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Website URL *
                  </label>
                  <input
                    type="url"
                    name="website_url"
                    value={formData.website_url}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.website_url ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="https://example.com"
                  />
                  {errors.website_url && <p className="text-red-500 text-sm mt-1">{errors.website_url}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Optional description of your application"
                  />
                </div>
              </div>
            </div>

            {/* Crawling Configuration */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                Crawling Configuration
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Crawl Depth
                  </label>
                  <input
                    type="number"
                    name="max_crawl_depth"
                    value={formData.max_crawl_depth}
                    onChange={handleInputChange}
                    min="1"
                    max="5"
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.max_crawl_depth ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.max_crawl_depth && <p className="text-red-500 text-sm mt-1">{errors.max_crawl_depth}</p>}
                  <p className="text-xs text-gray-500 mt-1">1-5 levels deep</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Pages to Crawl
                  </label>
                  <input
                    type="number"
                    name="max_pages_to_crawl"
                    value={formData.max_pages_to_crawl}
                    onChange={handleInputChange}
                    min="10"
                    max="1000"
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.max_pages_to_crawl ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.max_pages_to_crawl && <p className="text-red-500 text-sm mt-1">{errors.max_pages_to_crawl}</p>}
                  <p className="text-xs text-gray-500 mt-1">10-1000 pages</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Links to Validate
                  </label>
                  <input
                    type="number"
                    name="max_links_to_validate"
                    value={formData.max_links_to_validate}
                    onChange={handleInputChange}
                    min="10"
                    max="2000"
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.max_links_to_validate ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.max_links_to_validate && <p className="text-red-500 text-sm mt-1">{errors.max_links_to_validate}</p>}
                  <p className="text-xs text-gray-500 mt-1">2-3x pages to crawl</p>
                </div>
              </div>
            </div>

            {/* AI Configuration */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Bot className="h-5 w-5 mr-2" />
                AI Configuration
              </h3>
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="enable_ai_evaluation"
                    checked={formData.enable_ai_evaluation}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm font-medium text-gray-700">
                    Enable AI Content Evaluation
                  </label>
                </div>

                {formData.enable_ai_evaluation && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max AI Evaluation Pages
                    </label>
                    <input
                      type="number"
                      name="max_ai_evaluation_pages"
                      value={formData.max_ai_evaluation_pages}
                      onChange={handleInputChange}
                      min="1"
                      max="50"
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        errors.max_ai_evaluation_pages ? 'border-red-500' : 'border-gray-300'
                      }`}
                    />
                    {errors.max_ai_evaluation_pages && <p className="text-red-500 text-sm mt-1">{errors.max_ai_evaluation_pages}</p>}
                    <p className="text-xs text-gray-500 mt-1">1-50 pages for AI analysis</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50">
          <div className="flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              onClick={handleSubmit}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              {loading ? 'Updating...' : 'Update Application'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditApplicationModal;
