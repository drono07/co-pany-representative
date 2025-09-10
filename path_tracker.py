"""
Path tracking system for website crawling
Tracks the click path (parent-child relationships) to reach each page
"""

from typing import Dict, List, Optional, Set
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class PathTracker:
    """Tracks navigation paths during website crawling"""
    
    def __init__(self):
        # Maps each URL to its parent URL (how we reached it)
        self.parent_map: Dict[str, str] = {}
        
        # Maps each URL to its children (pages discovered from it)
        self.children_map: Dict[str, Set[str]] = {}
        
        # Tracks the full path to each URL
        self.path_map: Dict[str, List[str]] = {}
        
        # Starting URL
        self.start_url: Optional[str] = None
    
    def set_start_url(self, url: str):
        """Set the starting URL for path tracking"""
        self.start_url = url
        self.parent_map[url] = None  # No parent for start URL
        self.path_map[url] = [url]   # Path is just the start URL
        self.children_map[url] = set()
        logger.info(f"Started path tracking from: {url}")
    
    def add_page_relationship(self, parent_url: str, child_url: str):
        """Add a parent-child relationship between two URLs"""
        try:
            # Normalize URLs
            parent_normalized = self._normalize_url(parent_url)
            child_normalized = self._normalize_url(child_url)
            
            # Skip if it's the same URL
            if parent_normalized == child_normalized:
                return
            
            # Set parent relationship
            self.parent_map[child_normalized] = parent_normalized
            
            # Add to children map
            if parent_normalized not in self.children_map:
                self.children_map[parent_normalized] = set()
            self.children_map[parent_normalized].add(child_normalized)
            
            # Build path for child URL
            if parent_normalized in self.path_map:
                self.path_map[child_normalized] = self.path_map[parent_normalized] + [child_normalized]
            else:
                self.path_map[child_normalized] = [child_normalized]
            
            logger.debug(f"Added path: {parent_normalized} → {child_normalized}")
            
        except Exception as e:
            logger.error(f"Failed to add page relationship: {e}")
    
    def get_path_to_url(self, url: str) -> List[str]:
        """Get the full click path to reach a specific URL"""
        normalized_url = self._normalize_url(url)
        return self.path_map.get(normalized_url, [normalized_url])
    
    def get_parent_url(self, url: str) -> Optional[str]:
        """Get the parent URL that led to this URL"""
        normalized_url = self._normalize_url(url)
        return self.parent_map.get(normalized_url)
    
    def get_children_urls(self, url: str) -> List[str]:
        """Get all child URLs discovered from this URL"""
        normalized_url = self._normalize_url(url)
        return list(self.children_map.get(normalized_url, set()))
    
    def get_path_depth(self, url: str) -> int:
        """Get the depth of a URL (how many clicks from start)"""
        path = self.get_path_to_url(url)
        return len(path) - 1  # Subtract 1 because start URL is depth 0
    
    def get_all_paths(self) -> Dict[str, List[str]]:
        """Get all tracked paths"""
        return self.path_map.copy()
    
    def get_path_statistics(self) -> Dict[str, any]:
        """Get statistics about the tracked paths"""
        total_pages = len(self.path_map)
        max_depth = max([len(path) - 1 for path in self.path_map.values()]) if self.path_map else 0
        
        # Count pages by depth
        depth_counts = {}
        for path in self.path_map.values():
            depth = len(path) - 1
            depth_counts[depth] = depth_counts.get(depth, 0) + 1
        
        return {
            "total_pages": total_pages,
            "max_depth": max_depth,
            "pages_by_depth": {str(k): v for k, v in depth_counts.items()},
            "start_url": self.start_url
        }
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized
        except Exception:
            return url
    
    def export_path_data(self) -> Dict[str, any]:
        """Export path tracking data for storage"""
        return {
            "start_url": self.start_url,
            "parent_map": self.parent_map,
            "children_map": {k: list(v) for k, v in self.children_map.items()},
            "path_map": self.path_map,
            "statistics": self.get_path_statistics()
        }
    
    def import_path_data(self, data: Dict[str, any]):
        """Import path tracking data from storage"""
        self.start_url = data.get("start_url")
        self.parent_map = data.get("parent_map", {})
        self.children_map = {k: set(v) for k, v in data.get("children_map", {}).items()}
        self.path_map = data.get("path_map", {})
        logger.info(f"Imported path data for {len(self.path_map)} pages")
