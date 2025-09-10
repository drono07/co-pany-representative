"""
HTML Structure Extractor
Extracts and cleans HTML structure without CSS, images, or other resources
"""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Comment
import logging

logger = logging.getLogger(__name__)

class HTMLStructureExtractor:
    """Extracts clean HTML structure for storage and comparison"""
    
    def __init__(self):
        # Elements to remove completely
        self.remove_elements = [
            'script', 'style', 'noscript', 'iframe', 'embed', 'object',
            'link', 'meta', 'title'  # Keep title for reference but remove from structure
        ]
        
        # Attributes to remove from all elements
        self.remove_attributes = [
            'style', 'class', 'id', 'onclick', 'onload', 'onerror',
            'src', 'href', 'data-*', 'aria-*', 'role', 'tabindex'
        ]
        
        # Attributes to keep (minimal set for structure)
        self.keep_attributes = [
            'type', 'name', 'value', 'placeholder', 'alt', 'title'
        ]
    
    def extract_structure(self, html_content: str, url: str) -> Dict[str, any]:
        """Extract clean HTML structure from content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic page info
            page_info = self._extract_page_info(soup, url)
            
            # Clean the HTML
            cleaned_html = self._clean_html(soup)
            
            # Extract structure elements
            structure_elements = self._extract_structure_elements(soup)
            
            # Extract form information
            forms = self._extract_forms(soup)
            
            # Extract navigation structure
            navigation = self._extract_navigation(soup)
            
            return {
                "url": url,
                "page_info": page_info,
                "html_structure": cleaned_html,
                "structure_elements": structure_elements,
                "forms": forms,
                "navigation": navigation,
                "extracted_at": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Failed to extract HTML structure for {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "extracted_at": self._get_timestamp()
            }
    
    def _extract_page_info(self, soup: BeautifulSoup, url: str) -> Dict[str, any]:
        """Extract basic page information"""
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Extract meta information
        meta_description = ""
        meta_keywords = ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_description = meta_desc.get('content', '')
        
        meta_key = soup.find('meta', attrs={'name': 'keywords'})
        if meta_key:
            meta_keywords = meta_key.get('content', '')
        
        return {
            "title": title,
            "meta_description": meta_description,
            "meta_keywords": meta_keywords,
            "url": url
        }
    
    def _clean_html(self, soup: BeautifulSoup) -> str:
        """Clean HTML by removing unwanted elements and attributes"""
        # Remove unwanted elements
        for element in self.remove_elements:
            for tag in soup.find_all(element):
                tag.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Clean attributes from all remaining elements
        for tag in soup.find_all():
            self._clean_attributes(tag)
        
        return str(soup)
    
    def _clean_attributes(self, tag):
        """Remove unwanted attributes from a tag"""
        if not tag.attrs:
            return
        
        # Get list of attributes to remove
        attrs_to_remove = []
        for attr in tag.attrs:
            # Remove if it's in the remove list
            if attr in self.remove_attributes:
                attrs_to_remove.append(attr)
            # Remove data-* and aria-* attributes
            elif attr.startswith('data-') or attr.startswith('aria-'):
                attrs_to_remove.append(attr)
            # Remove if not in keep list and not a structural attribute
            elif attr not in self.keep_attributes and not self._is_structural_attribute(attr):
                attrs_to_remove.append(attr)
        
        # Remove the attributes
        for attr in attrs_to_remove:
            del tag.attrs[attr]
    
    def _is_structural_attribute(self, attr: str) -> bool:
        """Check if an attribute is structural (should be kept)"""
        structural_attrs = [
            'type', 'name', 'value', 'placeholder', 'alt', 'title',
            'colspan', 'rowspan', 'scope', 'headers', 'for', 'method',
            'action', 'enctype', 'target', 'rel', 'media'
        ]
        return attr in structural_attrs
    
    def _extract_structure_elements(self, soup: BeautifulSoup) -> Dict[str, List[Dict]]:
        """Extract key structural elements"""
        elements = {
            "headings": [],
            "links": [],
            "images": [],
            "buttons": [],
            "inputs": [],
            "lists": []
        }
        
        # Extract headings
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                elements["headings"].append({
                    "level": i,
                    "text": heading.get_text().strip(),
                    "tag": f"h{i}"
                })
        
        # Extract links (without href values)
        for link in soup.find_all('a'):
            elements["links"].append({
                "text": link.get_text().strip(),
                "tag": "a"
            })
        
        # Extract images (without src values)
        for img in soup.find_all('img'):
            elements["images"].append({
                "alt": img.get('alt', ''),
                "tag": "img"
            })
        
        # Extract buttons
        for button in soup.find_all(['button', 'input']):
            if button.name == 'input' and button.get('type') in ['button', 'submit', 'reset']:
                elements["buttons"].append({
                    "text": button.get('value', ''),
                    "type": button.get('type', 'button'),
                    "tag": "input"
                })
            elif button.name == 'button':
                elements["buttons"].append({
                    "text": button.get_text().strip(),
                    "type": "button",
                    "tag": "button"
                })
        
        # Extract form inputs
        for input_tag in soup.find_all('input'):
            elements["inputs"].append({
                "type": input_tag.get('type', 'text'),
                "name": input_tag.get('name', ''),
                "placeholder": input_tag.get('placeholder', ''),
                "tag": "input"
            })
        
        # Extract lists
        for list_tag in soup.find_all(['ul', 'ol']):
            items = []
            for li in list_tag.find_all('li'):
                items.append(li.get_text().strip())
            elements["lists"].append({
                "type": list_tag.name,
                "items": items,
                "item_count": len(items)
            })
        
        return elements
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract form information"""
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                "action": form.get('action', ''),
                "method": form.get('method', 'get'),
                "inputs": []
            }
            
            for input_tag in form.find_all('input'):
                form_data["inputs"].append({
                    "type": input_tag.get('type', 'text'),
                    "name": input_tag.get('name', ''),
                    "required": input_tag.has_attr('required')
                })
            
            for select in form.find_all('select'):
                options = []
                for option in select.find_all('option'):
                    options.append({
                        "value": option.get('value', ''),
                        "text": option.get_text().strip()
                    })
                form_data["inputs"].append({
                    "type": "select",
                    "name": select.get('name', ''),
                    "options": options
                })
            
            forms.append(form_data)
        
        return forms
    
    def _extract_navigation(self, soup: BeautifulSoup) -> Dict[str, List]:
        """Extract navigation structure"""
        navigation = {
            "nav_links": [],
            "breadcrumbs": [],
            "menus": []
        }
        
        # Extract navigation links
        for nav in soup.find_all('nav'):
            links = []
            for link in nav.find_all('a'):
                links.append({
                    "text": link.get_text().strip(),
                    "tag": "a"
                })
            navigation["nav_links"].extend(links)
        
        # Extract breadcrumbs
        for breadcrumb in soup.find_all(class_=re.compile(r'breadcrumb', re.I)):
            items = []
            for item in breadcrumb.find_all(['a', 'span']):
                items.append({
                    "text": item.get_text().strip(),
                    "tag": item.name
                })
            navigation["breadcrumbs"].extend(items)
        
        # Extract menu structures
        for menu in soup.find_all(['ul', 'ol'], class_=re.compile(r'menu|nav', re.I)):
            items = []
            for item in menu.find_all('li'):
                items.append({
                    "text": item.get_text().strip(),
                    "tag": "li"
                })
            navigation["menus"].append({
                "type": menu.name,
                "items": items
            })
        
        return navigation
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def compare_structures(self, structure1: Dict, structure2: Dict) -> Dict[str, any]:
        """Compare two HTML structures and detect changes"""
        changes = {
            "page_info_changes": [],
            "structure_changes": [],
            "element_changes": [],
            "form_changes": [],
            "navigation_changes": []
        }
        
        # Compare page info
        info1 = structure1.get("page_info", {})
        info2 = structure2.get("page_info", {})
        
        for key in ["title", "meta_description", "meta_keywords"]:
            if info1.get(key) != info2.get(key):
                changes["page_info_changes"].append({
                    "field": key,
                    "old_value": info1.get(key),
                    "new_value": info2.get(key)
                })
        
        # Compare HTML structure (simplified comparison)
        html1 = structure1.get("html_structure", "")
        html2 = structure2.get("html_structure", "")
        
        if html1 != html2:
            changes["structure_changes"].append({
                "type": "html_structure",
                "description": "HTML structure has changed"
            })
        
        # Compare structural elements
        elements1 = structure1.get("structure_elements", {})
        elements2 = structure2.get("structure_elements", {})
        
        for element_type in ["headings", "links", "images", "buttons", "inputs", "lists"]:
            if elements1.get(element_type) != elements2.get(element_type):
                changes["element_changes"].append({
                    "type": element_type,
                    "old_count": len(elements1.get(element_type, [])),
                    "new_count": len(elements2.get(element_type, []))
                })
        
        return changes
