"""
Change Detection System
Compares current crawl with previous crawl to detect changes
"""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChangeDetector:
    """Detects changes between website crawl sessions"""
    
    def __init__(self):
        self.current_pages: Dict[str, Dict] = {}
        self.previous_pages: Dict[str, Dict] = {}
        self.changes: Dict[str, Any] = {}
    
    def set_current_pages(self, pages: List[Dict[str, Any]]):
        """Set current crawl pages"""
        self.current_pages = {page["url"]: page for page in pages}
        logger.info(f"Set {len(self.current_pages)} current pages")
    
    def set_previous_pages(self, pages: List[Dict[str, Any]]):
        """Set previous crawl pages"""
        self.previous_pages = {page["url"]: page for page in pages}
        logger.info(f"Set {len(self.previous_pages)} previous pages")
    
    def detect_changes(self) -> Dict[str, Any]:
        """Detect all types of changes between current and previous crawl"""
        if not self.previous_pages:
            logger.info("No previous pages to compare with")
            return {
                "status": "no_previous_data",
                "message": "No previous crawl data available for comparison",
                "current_pages_count": len(self.current_pages)
            }
        
        changes = {
            "detection_timestamp": datetime.now().isoformat(),
            "current_pages_count": len(self.current_pages),
            "previous_pages_count": len(self.previous_pages),
            "new_pages": [],
            "removed_pages": [],
            "modified_pages": [],
            "unchanged_pages": [],
            "path_changes": [],
            "content_changes": [],
            "summary": {}
        }
        
        # Get URL sets
        current_urls = set(self.current_pages.keys())
        previous_urls = set(self.previous_pages.keys())
        
        # Detect new pages
        new_urls = current_urls - previous_urls
        for url in new_urls:
            changes["new_pages"].append({
                "url": url,
                "title": self.current_pages[url].get("title", ""),
                "word_count": self.current_pages[url].get("word_count", 0),
                "path": self.current_pages[url].get("path", []),
                "discovered_at": self.current_pages[url].get("crawled_at", "")
            })
        
        # Detect removed pages
        removed_urls = previous_urls - current_urls
        for url in removed_urls:
            changes["removed_pages"].append({
                "url": url,
                "title": self.previous_pages[url].get("title", ""),
                "word_count": self.previous_pages[url].get("word_count", 0),
                "last_seen": self.previous_pages[url].get("crawled_at", "")
            })
        
        # Detect modified pages
        common_urls = current_urls & previous_urls
        for url in common_urls:
            current_page = self.current_pages[url]
            previous_page = self.previous_pages[url]
            
            page_changes = self._detect_page_changes(current_page, previous_page)
            if page_changes:
                changes["modified_pages"].append({
                    "url": url,
                    "changes": page_changes
                })
            else:
                changes["unchanged_pages"].append(url)
        
        # Detect path changes
        path_changes = self._detect_path_changes()
        changes["path_changes"] = path_changes
        
        # Generate summary
        changes["summary"] = self._generate_summary(changes)
        
        logger.info(f"Change detection completed: {len(changes['new_pages'])} new, "
                   f"{len(changes['removed_pages'])} removed, "
                   f"{len(changes['modified_pages'])} modified")
        
        return changes
    
    def _detect_page_changes(self, current_page: Dict, previous_page: Dict) -> List[Dict]:
        """Detect changes in a specific page"""
        changes = []
        
        # Compare basic page info
        if current_page.get("title") != previous_page.get("title"):
            changes.append({
                "type": "title_change",
                "old_value": previous_page.get("title"),
                "new_value": current_page.get("title")
            })
        
        if current_page.get("word_count") != previous_page.get("word_count"):
            changes.append({
                "type": "content_change",
                "old_word_count": previous_page.get("word_count"),
                "new_word_count": current_page.get("word_count"),
                "word_count_difference": current_page.get("word_count", 0) - previous_page.get("word_count", 0)
            })
        
        # Compare page type
        if current_page.get("page_type") != previous_page.get("page_type"):
            changes.append({
                "type": "page_type_change",
                "old_type": previous_page.get("page_type"),
                "new_type": current_page.get("page_type")
            })
        
        # Compare HTML structure if available
        if "html_structure" in current_page and "html_structure" in previous_page:
            if current_page["html_structure"] != previous_page["html_structure"]:
                changes.append({
                    "type": "html_structure_change",
                    "description": "HTML structure has been modified"
                })
        
        # Compare path
        current_path = current_page.get("path", [])
        previous_path = previous_page.get("path", [])
        if current_path != previous_path:
            changes.append({
                "type": "path_change",
                "old_path": previous_path,
                "new_path": current_path
            })
        
        return changes
    
    def _detect_path_changes(self) -> List[Dict]:
        """Detect changes in navigation paths"""
        path_changes = []
        
        # Compare paths for common URLs
        common_urls = set(self.current_pages.keys()) & set(self.previous_pages.keys())
        
        for url in common_urls:
            current_path = self.current_pages[url].get("path", [])
            previous_path = self.previous_pages[url].get("path", [])
            
            if current_path != previous_path:
                path_changes.append({
                    "url": url,
                    "old_path": previous_path,
                    "new_path": current_path,
                    "path_depth_change": len(current_path) - len(previous_path)
                })
        
        return path_changes
    
    def _generate_summary(self, changes: Dict) -> Dict[str, Any]:
        """Generate a summary of all changes"""
        summary = {
            "total_changes": 0,
            "change_types": {},
            "impact_assessment": "low"
        }
        
        # Count changes by type
        change_counts = {
            "new_pages": len(changes["new_pages"]),
            "removed_pages": len(changes["removed_pages"]),
            "modified_pages": len(changes["modified_pages"]),
            "path_changes": len(changes["path_changes"])
        }
        
        summary["change_types"] = change_counts
        summary["total_changes"] = sum(change_counts.values())
        
        # Assess impact
        total_pages = changes["current_pages_count"]
        if total_pages > 0:
            change_percentage = (summary["total_changes"] / total_pages) * 100
            
            if change_percentage > 20:
                summary["impact_assessment"] = "high"
            elif change_percentage > 10:
                summary["impact_assessment"] = "medium"
            else:
                summary["impact_assessment"] = "low"
        
        return summary
    
    def get_change_report(self) -> str:
        """Generate a human-readable change report"""
        if not self.changes:
            return "No changes detected or change detection not run."
        
        report = []
        report.append("=== WEBSITE CHANGE DETECTION REPORT ===")
        report.append(f"Detection Time: {self.changes.get('detection_timestamp', 'Unknown')}")
        report.append(f"Current Pages: {self.changes.get('current_pages_count', 0)}")
        report.append(f"Previous Pages: {self.changes.get('previous_pages_count', 0)}")
        report.append("")
        
        # New pages
        new_pages = self.changes.get("new_pages", [])
        if new_pages:
            report.append(f"🆕 NEW PAGES ({len(new_pages)}):")
            for page in new_pages[:10]:  # Show first 10
                report.append(f"  - {page['url']} ({page.get('word_count', 0)} words)")
            if len(new_pages) > 10:
                report.append(f"  ... and {len(new_pages) - 10} more")
            report.append("")
        
        # Removed pages
        removed_pages = self.changes.get("removed_pages", [])
        if removed_pages:
            report.append(f"❌ REMOVED PAGES ({len(removed_pages)}):")
            for page in removed_pages[:10]:  # Show first 10
                report.append(f"  - {page['url']}")
            if len(removed_pages) > 10:
                report.append(f"  ... and {len(removed_pages) - 10} more")
            report.append("")
        
        # Modified pages
        modified_pages = self.changes.get("modified_pages", [])
        if modified_pages:
            report.append(f"📝 MODIFIED PAGES ({len(modified_pages)}):")
            for page in modified_pages[:5]:  # Show first 5
                report.append(f"  - {page['url']}")
                for change in page.get("changes", []):
                    report.append(f"    • {change['type']}")
            if len(modified_pages) > 5:
                report.append(f"  ... and {len(modified_pages) - 5} more")
            report.append("")
        
        # Summary
        summary = self.changes.get("summary", {})
        report.append("📊 SUMMARY:")
        report.append(f"  Total Changes: {summary.get('total_changes', 0)}")
        report.append(f"  Impact Level: {summary.get('impact_assessment', 'unknown').upper()}")
        
        return "\n".join(report)
    
    def export_changes(self) -> Dict[str, Any]:
        """Export change detection results"""
        return self.changes.copy()
