import asyncio
import aiohttp
import random
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
import logging
from datetime import datetime

from models import Link, LinkStatus, PageContent, PageType, WebsiteAnalysis
from config import settings

logger = logging.getLogger(__name__)

class LinkValidator:
    """Validates links and detects broken links"""
    
    def __init__(self):
        self.session: aiohttp.ClientSession = None
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=settings.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': settings.user_agent}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def validate_links(self, links: List[Link]) -> List[Link]:
        """Validate a list of links and update their status with parallel processing"""
        logger.info(f"Validating {len(links)} links with parallel processing...")
        
        # Filter out resource files that we don't need to validate
        page_links = [link for link in links if self._is_page_link(link.url)]
        resource_links = [link for link in links if not self._is_page_link(link.url)]
        
        logger.info(f"Found {len(page_links)} page links and {len(resource_links)} resource links")
        
        # Mark resource links as valid (we don't validate them)
        for link in resource_links:
            link.status = LinkStatus.VALID
            link.status_code = 200
            link.response_time = 0.0
        
        # Apply link validation limit
        if len(page_links) > settings.max_links_to_validate:
            logger.info(f"Limiting link validation to {settings.max_links_to_validate} links (found {len(page_links)} total)")
            page_links = page_links[:settings.max_links_to_validate]
        
        # Process page links in parallel batches
        batch_size = 3  # Reduced from 20 to 3 to avoid rate limiting
        rate_limited_links = []
        
        for i in range(0, len(page_links), batch_size):
            batch = page_links[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(page_links) + batch_size - 1)//batch_size} ({len(batch)} links)")
            
            # Process batch in parallel
            batch_tasks = [self._validate_single_link(link) for link in batch if link.status == LinkStatus.UNKNOWN]
            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Update links with results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error validating link {batch[j].url}: {result}")
                    else:
                        link = batch[j]
                        if result.status_code == 429:
                            rate_limited_links.append(result)
                            logger.warning(f"Rate limited: {link.url} - will retry later")
                        else:
                            # Find the original link in the full list and update it
                            original_index = links.index(link)
                            links[original_index] = result
            
            # Random delay between batches to avoid detection
            if i + batch_size < len(page_links):
                delay = random.uniform(2.0, 4.0)  # Increased delay between 2-4 seconds
                await asyncio.sleep(delay)
        
        # Retry rate-limited links with smart retry strategy
        if rate_limited_links:
            logger.info(f"Retrying {len(rate_limited_links)} rate-limited links with smart retry strategy...")
            
            # Process rate-limited links in parallel batches
            retry_batch_size = 2  # Reduced from 15 to 2 for retries
            max_retry_attempts = 10  # Reasonable limit
            
            for retry_round in range(max_retry_attempts):
                if not rate_limited_links:
                    break
                    
                logger.info(f"Retry round {retry_round + 1}/{max_retry_attempts}: {len(rate_limited_links)} links remaining")
                
                # Process current batch in parallel
                current_batch = rate_limited_links[:retry_batch_size]
                remaining_links = rate_limited_links[retry_batch_size:]
                
                # Create retry tasks with exponential backoff
                base_delay = 2
                retry_delay = min(base_delay * (2 ** retry_round), 15)  # 2s, 4s, 8s, 15s max
                retry_tasks = [self._retry_single_link(link, retry_delay) for link in current_batch]
                retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
                
                # Process results
                new_rate_limited = []
                for j, result in enumerate(retry_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error retrying link {current_batch[j].url}: {result}")
                        new_rate_limited.append(current_batch[j])
                    else:
                        link = current_batch[j]
                        if result.status_code == 429:
                            new_rate_limited.append(result)
                            logger.warning(f"⏳ Still rate limited: {link.url} - will retry again")
                        else:
                            logger.info(f"✅ Got definitive response for {link.url}: {result.status_code}")
                            # Find the original link in the full list and update it
                            original_index = links.index(link)
                            links[original_index] = result
                
                # Update rate_limited_links for next iteration
                rate_limited_links = new_rate_limited + remaining_links
                
                # Wait before next retry batch
                if rate_limited_links and retry_round < max_retry_attempts - 1:
                    logger.info(f"Waiting {retry_delay} seconds before next retry batch...")
                    await asyncio.sleep(retry_delay)
            
            # Mark remaining rate-limited links as rate limited
            if rate_limited_links:
                logger.warning(f"Marking {len(rate_limited_links)} links as rate limited after {max_retry_attempts} attempts")
                for link in rate_limited_links:
                    link.status = LinkStatus.RATE_LIMITED
                    link.status_code = 429
                    link.error_message = f"Rate limited after {max_retry_attempts} retry attempts"
                    original_index = links.index(link)
                    links[original_index] = link
        
        return links
    
    async def _retry_single_link(self, link: Link, retry_delay: int) -> Link:
        """Retry a single rate-limited link"""
        try:
            retried_link = await self._validate_single_link(link)
            return retried_link
        except Exception as e:
            logger.error(f"Error retrying link {link.url}: {e}")
            return link
    
    async def _validate_single_link(self, link: Link) -> Link:
        """Validate a single link"""
        try:
            # Add small random delay before each request to avoid rate limiting
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            start_time = datetime.now()
            async with self.session.head(link.url, allow_redirects=True) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                
                link.status_code = response.status
                link.response_time = response_time
                link.status = self._categorize_status_code(response.status)
                
                # Get title if available
                if response.status == 200:
                    try:
                        async with self.session.get(link.url) as full_response:
                            if full_response.status == 200:
                                html = await full_response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                title_tag = soup.find('title')
                                if title_tag:
                                    link.title = title_tag.get_text().strip()
                    except Exception:
                        pass  # Title extraction is optional
                
        except asyncio.TimeoutError:
            link.status = LinkStatus.TIMEOUT
            link.error_message = "Request timeout"
        except Exception as e:
            link.status = LinkStatus.BROKEN
            link.error_message = str(e)
        
        return link
    
    def _is_page_link(self, url: str) -> bool:
        """Check if a URL is a page link (not a resource file)"""
        # Resource file extensions to exclude
        resource_extensions = [
            '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
            '.woff', '.woff2', '.ttf', '.eot', '.otf',  # Fonts
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Documents
            '.zip', '.rar', '.tar', '.gz',  # Archives
            '.mp3', '.mp4', '.avi', '.mov', '.wmv',  # Media
            '.xml', '.json', '.txt', '.csv'  # Data files
        ]
        
        # Check if URL ends with resource extension
        url_lower = url.lower()
        for ext in resource_extensions:
            if url_lower.endswith(ext):
                return False
        
        # Check for common resource paths
        resource_paths = [
            '/cdn/', '/assets/', '/static/', '/images/', '/img/', '/css/', '/js/',
            '/fonts/', '/media/', '/uploads/', '/files/', '/downloads/'
        ]
        
        for path in resource_paths:
            if path in url_lower:
                return False
        
        # If it doesn't match resource patterns, it's likely a page
        return True
    
    def _categorize_status_code(self, status_code: int) -> LinkStatus:
        """Categorize HTTP status code into link status"""
        if 200 <= status_code < 300:
            return LinkStatus.VALID
        elif 300 <= status_code < 400:
            return LinkStatus.REDIRECT
        elif status_code == 429:  # Rate limited - need to retry
            return LinkStatus.RATE_LIMITED
        elif 400 <= status_code < 500:
            return LinkStatus.BROKEN
        elif 500 <= status_code < 600:
            return LinkStatus.BROKEN
        else:
            return LinkStatus.UNKNOWN

class BlankPageDetector:
    """Detects blank or low-content pages"""
    
    def __init__(self):
        self.min_content_threshold = 50   # Minimum words for content page (reduced for product pages)
        self.min_meaningful_content = 100  # Minimum words for meaningful content (reduced)
        self.header_footer_threshold = 50  # If page has header+footer but less than this, likely blank
        
    def detect_blank_pages(self, pages: List[PageContent]) -> List[PageContent]:
        """Analyze pages and identify blank or low-content pages"""
        logger.info(f"Analyzing {len(pages)} pages for blank content...")
        
        for page in pages:
            page.page_type = self._analyze_page_content(page)
        
        return pages
    
    def _analyze_page_content(self, page: PageContent) -> PageType:
        """Analyze page content and determine if it's blank or has meaningful content"""
        
        # Check word count
        if page.word_count < self.min_content_threshold:
            return PageType.BLANK
        
        # Check for common blank page indicators
        if self._has_only_boilerplate_content(page):
            return PageType.BLANK
        
        # Check for error pages
        if self._is_error_page(page):
            return PageType.ERROR
        
        # Check for redirect pages
        if self._is_redirect_page(page):
            return PageType.REDIRECT
        
        return PageType.CONTENT
    
    def _has_only_boilerplate_content(self, page: PageContent) -> bool:
        """Check if page has only header/footer/navigation content by analyzing HTML structure"""
        try:
            from bs4 import BeautifulSoup
            
            # Parse the HTML content
            soup = BeautifulSoup(page.html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract header content
            header_content = self._extract_section_content(soup, ['header', 'nav'])
            
            # Extract footer content
            footer_content = self._extract_section_content(soup, ['footer'])
            
            # Extract main content (everything else)
            main_content = self._extract_main_content(soup)
            
            # Calculate word counts for each section
            header_words = len(header_content.split()) if header_content else 0
            footer_words = len(footer_content.split()) if footer_content else 0
            main_words = len(main_content.split()) if main_content else 0
            
            total_words = page.word_count
            
            # If there's no main content at all, it's definitely blank
            if main_words == 0:
                return True
            
            # If main content is very minimal compared to header/footer
            if main_words < 20 and (header_words + footer_words) > main_words * 2:
                return True
            
            # If main content is less than 10% of total content, likely blank
            if total_words > 0 and main_words < (total_words * 0.1):
                return True
            
            # Check if main content is just navigation or boilerplate
            if self._is_main_content_boilerplate(main_content):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error analyzing HTML structure for {page.url}: {str(e)}")
            # Fallback to simple word count check
            return page.word_count < 50
    
    def _extract_section_content(self, soup, tag_names):
        """Extract text content from specific HTML sections"""
        content_parts = []
        
        for tag_name in tag_names:
            # Find elements by tag name
            elements = soup.find_all(tag_name)
            for element in elements:
                content_parts.append(element.get_text())
            
            # Also find elements by class/id that might contain these sections
            for element in soup.find_all(['div', 'section'], class_=lambda x: x and any(
                word in x.lower() for word in [tag_name, 'top', 'bottom', 'menu', 'navigation']
            )):
                content_parts.append(element.get_text())
        
        return ' '.join(content_parts)
    
    def _extract_main_content(self, soup):
        """Extract main content by removing header, footer, and navigation"""
        # Create a copy to avoid modifying the original
        soup_copy = BeautifulSoup(str(soup), 'html.parser')
        
        # Remove header, footer, nav elements
        for tag in soup_copy.find_all(['header', 'footer', 'nav']):
            tag.decompose()
        
        # Remove elements with header/footer/nav classes or IDs
        for element in soup_copy.find_all(['div', 'section'], class_=lambda x: x and any(
            word in x.lower() for word in ['header', 'footer', 'nav', 'navigation', 'menu', 'top', 'bottom']
        )):
            element.decompose()
        
        for element in soup_copy.find_all(['div', 'section'], id=lambda x: x and any(
            word in x.lower() for word in ['header', 'footer', 'nav', 'navigation', 'menu', 'top', 'bottom']
        )):
            element.decompose()
        
        # Remove common navigation patterns
        for element in soup_copy.find_all(['ul', 'ol'], class_=lambda x: x and any(
            word in x.lower() for word in ['nav', 'menu', 'navigation']
        )):
            element.decompose()
        
        return soup_copy.get_text()
    
    def _is_main_content_boilerplate(self, main_content):
        """Check if main content is just boilerplate text"""
        content_lower = main_content.lower().strip()
        
        # Common boilerplate phrases that might appear in main content
        boilerplate_phrases = [
            "coming soon", "under construction", "page not found", "404", "error",
            "loading", "please wait", "redirecting", "this page has moved",
            "access denied", "forbidden", "internal server error", "500", "502", "503",
            "click here if you are not redirected", "you will be redirected",
            "this content is not available", "content coming soon", "stay tuned"
        ]
        
        # If main content is just boilerplate phrases
        for phrase in boilerplate_phrases:
            if content_lower == phrase or content_lower.startswith(phrase):
                return True
        
        # If main content is very short and contains mostly boilerplate
        words = main_content.split()
        if len(words) < 10:
            boilerplate_count = sum(1 for phrase in boilerplate_phrases if phrase in content_lower)
            if boilerplate_count > 0:
                return True
        
        return False
    
    def _is_error_page(self, page: PageContent) -> bool:
        """Check if page is an error page"""
        text = page.text_content.lower()
        title = (page.title or "").lower()
        
        error_indicators = [
            "404", "not found", "page not found", "error", "oops",
            "something went wrong", "access denied", "forbidden",
            "internal server error", "500", "502", "503", "504"
        ]
        
        return any(indicator in text or indicator in title for indicator in error_indicators)
    
    def _is_redirect_page(self, page: PageContent) -> bool:
        """Check if page is a redirect page"""
        text = page.text_content.lower()
        
        redirect_indicators = [
            "redirecting", "you will be redirected", "please wait",
            "this page has moved", "redirecting to", "click here if"
        ]
        
        return any(indicator in text for indicator in redirect_indicators)

class ContentAnalyzer:
    """Analyzes content quality and structure"""
    
    def __init__(self):
        self.min_heading_structure = 2  # Minimum number of headings for good structure
        self.min_paragraph_count = 3    # Minimum paragraphs for good content
        
    def analyze_content_quality(self, pages: List[PageContent]) -> Dict[str, any]:
        """Analyze content quality across all pages"""
        logger.info(f"Analyzing content quality for {len(pages)} pages...")
        
        analysis = {
            'total_pages': len(pages),
            'content_pages': 0,
            'blank_pages': 0,
            'error_pages': 0,
            'redirect_pages': 0,
            'avg_word_count': 0,
            'pages_with_headers': 0,
            'pages_with_footers': 0,
            'pages_with_navigation': 0,
            'well_structured_pages': 0,
            'content_quality_issues': []
        }
        
        total_words = 0
        
        for page in pages:
            # Count page types
            if page.page_type == PageType.CONTENT:
                analysis['content_pages'] += 1
            elif page.page_type == PageType.BLANK:
                analysis['blank_pages'] += 1
            elif page.page_type == PageType.ERROR:
                analysis['error_pages'] += 1
            elif page.page_type == PageType.REDIRECT:
                analysis['redirect_pages'] += 1
            
            # Count structural elements
            if page.has_header:
                analysis['pages_with_headers'] += 1
            if page.has_footer:
                analysis['pages_with_footers'] += 1
            if page.has_navigation:
                analysis['pages_with_navigation'] += 1
            
            # Analyze content structure
            if self._has_good_structure(page):
                analysis['well_structured_pages'] += 1
            
            total_words += page.word_count
            
            # Identify content quality issues
            issues = self._identify_content_issues(page)
            if issues:
                analysis['content_quality_issues'].extend(issues)
        
        # Calculate averages
        if analysis['total_pages'] > 0:
            analysis['avg_word_count'] = total_words / analysis['total_pages']
        
        return analysis
    
    def _has_good_structure(self, page: PageContent) -> bool:
        """Check if page has good content structure"""
        if page.page_type != PageType.CONTENT:
            return False
        
        # Check for headings
        soup = BeautifulSoup(page.html_content, 'html.parser')
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        # Check for paragraphs
        paragraphs = soup.find_all('p')
        
        return (len(headings) >= self.min_heading_structure and 
                len(paragraphs) >= self.min_paragraph_count)
    
    def _identify_content_issues(self, page: PageContent) -> List[str]:
        """Identify specific content quality issues"""
        issues = []
        
        if page.page_type == PageType.CONTENT:
            # Check for very short content
            if page.word_count < 100:
                issues.append(f"Page '{page.url}' has very short content ({page.word_count} words)")
            
            # Check for missing title
            if not page.title or page.title.strip() == "":
                issues.append(f"Page '{page.url}' is missing a title")
            
            # Check for duplicate titles
            if page.title and len(page.title) > 60:
                issues.append(f"Page '{page.url}' has a very long title")
        
        return issues
