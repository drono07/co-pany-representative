import React, { useState } from 'react';
import { X, ExternalLink, Copy, Check } from 'lucide-react';
import toast from 'react-hot-toast';

const SourceCodeViewer = ({ isOpen, onClose, sourceData, brokenUrl }) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !sourceData) return null;

  const { 
    source_code, 
    page_url, 
    parent_url, 
    highlighted_links,
    actual_source_page,
    is_source_from_parent,
    traversal_path,
    hierarchy_depth
  } = sourceData;
  
  // Debug logging
  console.log('SourceCodeViewer props:', {
    source_code_length: source_code?.length || 0,
    page_url,
    parent_url,
    highlighted_links_count: highlighted_links?.length || 0,
    brokenUrl,
    actual_source_page,
    is_source_from_parent,
    traversal_path,
    hierarchy_depth
  });

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(source_code);
      setCopied(true);
      toast.success('Source code copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error('Failed to copy source code');
    }
  };

  const highlightLinks = (code) => {
    // If no code provided, return empty string
    if (!code || code.trim() === '') {
      console.warn('SourceCodeViewer: No source code provided');
      return '';
    }

    // If no highlighted links, return the code as-is
    if (!highlighted_links || highlighted_links.length === 0) {
      return code;
    }

    try {
      let highlightedCode = code;
      let offset = 0;

      // Sort by position to avoid offset issues
      const sortedLinks = highlighted_links.sort((a, b) => a.start - b.start);

      sortedLinks.forEach(link => {
        const start = link.start + offset;
        const end = link.end + offset;
        
        // Validate bounds
        if (start < 0 || end > highlightedCode.length || start >= end) {
          console.warn('SourceCodeViewer: Invalid link bounds', { start, end, length: highlightedCode.length });
          return;
        }
        
        const before = highlightedCode.substring(0, start);
        const linkText = highlightedCode.substring(start, end);
        const after = highlightedCode.substring(end);

        // Different highlighting based on link type
        let highlightStyle = '';
        if (link.type === 'broken') {
          highlightStyle = 'background-color: #fef2f2; padding: 2px 4px; border-radius: 3px; border: 1px solid #f87171; color: #dc2626 !important; font-weight: bold;';
        } else if (link.type === 'working') {
          highlightStyle = 'background-color: #f0fdf4; padding: 2px 4px; border-radius: 3px; border: 1px solid #4ade80; color: #16a34a !important; font-weight: bold;';
        } else {
          highlightStyle = 'background-color: #fef3c7; padding: 2px 4px; border-radius: 3px; border: 1px solid #f59e0b; color: #d97706 !important; font-weight: bold;';
        }

        highlightedCode = before + 
          `<mark style="${highlightStyle}" title="${link.url} (${link.status_code || 'Unknown'})">${linkText}</mark>` + 
          after;
        
        // Update offset for next replacement (approximate length of the mark tag)
        offset += 60; // Approximate length of the mark tag with styling
      });

      return highlightedCode;
    } catch (error) {
      console.error('SourceCodeViewer: Error highlighting links', error);
      return code; // Return original code if highlighting fails
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Source Code Viewer</h2>
            <p className="text-sm text-gray-600 mt-1">
              {brokenUrl && brokenUrl !== page_url ? `Link: ${brokenUrl}` : `Page: ${page_url}`}
            </p>
            {parent_url && (
              <p className="text-sm text-blue-600 mt-1">
                Parent page: <a href={parent_url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                  {parent_url} <ExternalLink className="inline w-3 h-3" />
                </a>
              </p>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={copyToClipboard}
              className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-md transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-auto p-6">
            <pre className="text-sm text-gray-900 whitespace-pre-wrap font-mono bg-gray-50 p-4 rounded-lg border">
              <code 
                className="text-gray-900"
                style={{ color: '#111827' }}
                dangerouslySetInnerHTML={{ 
                  __html: highlightLinks(source_code) || source_code || 'No source code available'
                }}
              />
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {highlighted_links && highlighted_links.length > 0 && (
                <div className="flex items-center space-x-2">
                  {(() => {
                    const brokenCount = highlighted_links.filter(link => link.type === 'broken').length;
                    const workingCount = highlighted_links.filter(link => link.type === 'working').length;
                    
                    return (
                      <>
                        {brokenCount > 0 && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
                            {brokenCount} broken link{brokenCount !== 1 ? 's' : ''}
                          </span>
                        )}
                        {workingCount > 0 && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                            {workingCount} working link{workingCount !== 1 ? 's' : ''}
                          </span>
                        )}
                      </>
                    );
                  })()}
                </div>
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

export default SourceCodeViewer;
