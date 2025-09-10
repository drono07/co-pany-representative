import React, { useState } from 'react';
import { X, ExternalLink, FileText, Eye, Users, ChevronRight } from 'lucide-react';

const LinkInfoModal = ({ 
  isOpen, 
  onClose, 
  link, 
  parentInfo, 
  navigationPath, 
  onViewSource, 
  onViewLink,
  results 
}) => {
  const [activeTab, setActiveTab] = useState('parent');

  if (!isOpen) return null;

  const getParentChain = (url) => {
    if (!parentInfo) return [];
    
    // If this is a root URL, return empty chain
    if (parentInfo.isRootUrl) {
      return [];
    }
    
    const chain = [];
    let currentUrl = url;
    let currentParent = parentInfo;
    
    // Build parent chain
    while (currentParent && currentParent.url) {
      chain.push({
        url: currentParent.url,
        title: currentParent.title || 'Unknown Page'
      });
      
      // Find the parent of the current parent
      const parentPage = results?.pages?.find(page => page.page_url === currentParent.url);
      if (parentPage && parentPage.path && parentPage.path.length > 1) {
        const grandParentUrl = parentPage.path[parentPage.path.length - 2];
        const grandParentPage = results?.pages?.find(page => page.page_url === grandParentUrl);
        currentParent = grandParentPage ? {
          url: grandParentUrl,
          title: grandParentPage.page_title || 'Unknown Page'
        } : null;
      } else {
        break;
      }
    }
    
    return chain;
  };

  const parentChain = getParentChain(link.url);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Link Information</h2>
            <p className="text-sm text-gray-600 mt-1 break-all">
              {link.url}
            </p>
            <div className="mt-1 text-xs text-gray-500">
              Status: {link.status_code || 'Unknown'} | Type: {link.type || 'Link'}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('parent')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'parent'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Users className="h-4 w-4 inline mr-2" />
              Parent Information
            </button>
            <button
              onClick={() => setActiveTab('source')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'source'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <FileText className="h-4 w-4 inline mr-2" />
              Source Code
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'parent' && (
            <div className="space-y-6">
              {/* Parent Chain */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Parent Chain</h3>
                
                {parentInfo && parentInfo.isRootUrl ? (
                  <div className="text-center py-8 text-gray-500">
                    <Users className="mx-auto h-12 w-12 text-green-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">Main Parent URL</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      This is the starting URL for the website analysis. It serves as the main parent page from which other pages were discovered.
                    </p>
                  </div>
                ) : parentChain.length > 0 ? (
                  <div className="space-y-3">
                    {parentChain.map((parent, index) => (
                      <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">{index + 1}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <a
                            href={parent.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center"
                          >
                            {parent.title}
                            <ExternalLink className="h-3 w-3 ml-1" />
                          </a>
                          <p className="text-xs text-gray-500 truncate mt-1">{parent.url}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Users className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No parent information</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      No parent page information available for this link.
                    </p>
                  </div>
                )}
              </div>

              {/* Navigation Path */}
              {navigationPath && navigationPath.length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Navigation Path</h3>
                  <div className="flex flex-wrap items-center gap-2">
                    {navigationPath.map((pathUrl, pathIndex) => {
                      const pageTitle = results?.pages?.find(page => page.page_url === pathUrl)?.page_title || 'Unknown Page';
                      
                      return (
                        <React.Fragment key={pathIndex}>
                          {pathIndex > 0 && (
                            <ChevronRight className="h-4 w-4 text-gray-400" />
                          )}
                          <a
                            href={pathUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-700 bg-blue-100 rounded-lg hover:bg-blue-200 transition-colors"
                          >
                            <ExternalLink className="h-3 w-3 mr-1" />
                            {pageTitle}
                          </a>
                        </React.Fragment>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'source' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Source Code Options</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {parentInfo && (
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-3">
                      <FileText className="h-5 w-5 text-blue-600 mr-2" />
                      <h4 className="font-medium text-gray-900">Parent Page Source</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      View the HTML source code of the parent page that contains this link.
                    </p>
                    <button
                      onClick={() => {
                        onViewSource(link.url, parentInfo.url);
                        onClose();
                      }}
                      className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      View Parent Source
                    </button>
                  </div>
                )}
                
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <Eye className="h-5 w-5 text-gray-600 mr-2" />
                    <h4 className="font-medium text-gray-900">Link Page Source</h4>
                  </div>
                  <p className="text-sm text-gray-600 mb-4">
                    View the HTML source code of the actual link page.
                  </p>
                  <button
                    onClick={() => {
                      onViewSource(link.url);
                      onClose();
                    }}
                    className="w-full flex items-center justify-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View Link Source
                  </button>
                </div>
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">About Source Code Viewing</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• <strong>Red highlighting:</strong> Broken links (404, 500, etc.)</li>
                  <li>• <strong>Green highlighting:</strong> Working links (200, 301, etc.)</li>
                  <li>• <strong>Hover over links:</strong> See URL and status code</li>
                  <li>• <strong>Copy functionality:</strong> Copy source code to clipboard</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {parentInfo && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                  Parent: {parentInfo.title}
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LinkInfoModal;
