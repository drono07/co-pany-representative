import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, FileText, Eye, Users } from 'lucide-react';

const LinkInfoDropdown = ({ 
  link, 
  parentInfo, 
  navigationPath, 
  onViewSource, 
  onViewLink,
  results 
}) => {
  const [showParentDropdown, setShowParentDropdown] = useState(false);
  const [showSourceDropdown, setShowSourceDropdown] = useState(false);

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
    <div className="flex items-center space-x-2">
      {/* Parent Information Dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowParentDropdown(!showParentDropdown)}
          className="flex items-center px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          <Users className="h-3 w-3 mr-1" />
          Parent Info
          {showParentDropdown ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
        </button>
        
        {showParentDropdown && (
          <div className="absolute right-0 mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Parent Chain</h4>
              
              {parentInfo && parentInfo.isRootUrl ? (
                <div className="text-center py-4">
                  <div className="flex items-center justify-center mb-2">
                    <Users className="h-6 w-6 text-green-500" />
                  </div>
                  <p className="text-sm font-medium text-gray-900">Main Parent URL</p>
                  <p className="text-xs text-gray-500 mt-1">
                    This is the starting URL for the analysis
                  </p>
                </div>
              ) : parentChain.length > 0 ? (
                <div className="space-y-2">
                  {parentChain.map((parent, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-xs font-medium text-blue-600">{index + 1}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <a
                          href={parent.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                        >
                          {parent.title}
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                        <p className="text-xs text-gray-500 truncate">{parent.url}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No parent information available</p>
              )}
              
              {/* Navigation Path */}
              {navigationPath && navigationPath.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-200">
                  <h5 className="text-xs font-medium text-gray-700 mb-2">Navigation Path:</h5>
                  <div className="text-xs text-gray-600">
                    {navigationPath.map((pathUrl, pathIndex) => {
                      const pageTitle = results?.pages?.find(page => page.page_url === pathUrl)?.page_title || 'Unknown Page';
                      return (
                        <span key={pathIndex}>
                          {pathIndex > 0 && ' → '}
                          <a
                            href={pathUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800"
                          >
                            {pageTitle}
                          </a>
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Source Code Dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowSourceDropdown(!showSourceDropdown)}
          className="flex items-center px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
        >
          <FileText className="h-3 w-3 mr-1" />
          Source Code
          {showSourceDropdown ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
        </button>
        
        {showSourceDropdown && (
          <div className="absolute right-0 mt-1 w-96 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Source Code Options</h4>
              
              <div className="space-y-2">
                {parentInfo && (
                  <button
                    onClick={() => {
                      onViewSource(link.url, parentInfo.url);
                      setShowSourceDropdown(false);
                    }}
                    className="w-full flex items-center px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 rounded border border-blue-200 transition-colors"
                  >
                    <FileText className="h-4 w-4 mr-2 text-blue-600" />
                    <div className="text-left">
                      <div className="font-medium text-blue-900">View Parent Source</div>
                      <div className="text-xs text-blue-700">Show HTML source of parent page</div>
                    </div>
                  </button>
                )}
                
                <button
                  onClick={() => {
                    onViewSource(link.url);
                    setShowSourceDropdown(false);
                  }}
                  className="w-full flex items-center px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded border border-gray-200 transition-colors"
                >
                  <Eye className="h-4 w-4 mr-2 text-gray-600" />
                  <div className="text-left">
                    <div className="font-medium text-gray-900">View Link Source</div>
                    <div className="text-xs text-gray-700">Show HTML source of the link page</div>
                  </div>
                </button>
              </div>
              
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-500">
                  Source code will show highlighted links and their locations in the HTML.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LinkInfoDropdown;
