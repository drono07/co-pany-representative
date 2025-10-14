import asyncio
import aiohttp
import time
import random
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from typing import Set, List, Dict, Optional
import logging
from tqdm import tqdm
from datetime import datetime

from ..utils.models import Link, LinkStatus, LinkType, PageContent, PageType
from ..utils.config import settings
from .path_tracker import PathTracker
from .html_structure_extractor import HTMLStructureExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteCrawler:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.pending_urls: Set[str] = set()
        self.links: List[Link] = []
        self.pages: List[PageContent] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Adaptive crawling state
        self.rate_limit_detected = False
        self.slow_mode_pages_remaining = 0
        self.consecutive_429_count = 0
        self.total_429_errors = 0
        self.total_requests = 0
        
        # New features
        self.path_tracker = PathTracker()
        self.html_extractor = HTMLStructureExtractor()
        self.crawl_session_id: Optional[str] = None
        
    async def __aenter__(self):
        # Use very conservative connector settings for crawling
        connector = aiohttp.TCPConnector(limit=1)  # Only 1 concurrent connection
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': settings.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_adaptive_batch_size(self):
        """Get batch size based on current rate limiting status"""
        if self.rate_limit_detected and self.slow_mode_pages_remaining > 0:
            return 1  # Slow mode: 1 at a time
        elif self.consecutive_429_count > 2:
            return 1  # Recent 429s: be careful
        elif self.consecutive_429_count > 0:
            return 5  # Some 429s: reduce batch size
        else:
            return min(100, settings.max_concurrent_requests)  # Fast mode: up to 100 parallel

    def handle_429_detected(self):
        """Handle when 429 rate limiting is detected"""
        self.rate_limit_detected = True
        self.slow_mode_pages_remaining = 20  # Slow mode for next 20 pages
        self.consecutive_429_count += 1
        self.total_429_errors += 1
        logger.warning(f"🚨 Rate limiting detected! Switching to slow mode for next 20 pages")
        logger.warning(f"📊 Total 429 errors so far: {self.total_429_errors}")

    def update_adaptive_state(self, had_429):
        """Update adaptive state after each batch"""
        if had_429:
            self.handle_429_detected()
        else:
            # No 429 in this batch, gradually recover
            if self.slow_mode_pages_remaining > 0:
                self.slow_mode_pages_remaining -= 1
                if self.slow_mode_pages_remaining == 0:
                    logger.info("✅ Slow mode completed, gradually increasing speed")
            
            # Gradually reduce consecutive 429 count
            if self.consecutive_429_count > 0:
                self.consecutive_429_count = max(0, self.consecutive_429_count - 1)
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and other duplicate-causing elements"""
        try:
            parsed = urlparse(url)
            # Remove fragment (everything after #) to avoid duplicates
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized
        except Exception:
            return url
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid and belongs to the same domain"""
        try:
            parsed = urlparse(url)
            
            # Handle both full URLs and domain names for base_domain
            if base_domain.startswith(('http://', 'https://')):
                base_parsed = urlparse(base_domain)
            else:
                base_parsed = urlparse(f"https://{base_domain}")
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
                
            # Must be same domain
            if parsed.netloc != base_parsed.netloc:
                return False
                
            # Skip common non-content URLs
            skip_patterns = [
                # Documents
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                # Archives
                '.zip', '.rar', '.tar', '.gz',
                # Images
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp', '.bmp', '.tiff',
                # Media
                '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
                # Web resources
                '.css', '.js', '.xml', '.json', '.txt', '.csv',
                # Fonts
                '.woff', '.woff2', '.ttf', '.eot', '.otf',
                # Feeds and embeds
                '.atom', '.rss', '.oembed', '.embed',
                # Other
                '.map', '.min', '.bundle'
            ]
            
            path_lower = parsed.path.lower()
            
            # Skip files with resource extensions
            if any(path_lower.endswith(pattern) for pattern in skip_patterns):
                return False
            
            # Skip common resource paths
            resource_paths = [
                '/cdn/', '/assets/', '/static/', '/images/', '/img/', '/css/', '/js/',
                '/fonts/', '/media/', '/uploads/', '/files/', '/downloads/', '/public/',
                '/vendor/', '/node_modules/', '/dist/', '/build/', '/compiled/'
            ]
            
            if any(path in path_lower for path in resource_paths):
                return False
                
            return True
        except Exception:
            return False
    
    async def fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a single page with smart retry strategy for rate limiting"""
        self.total_requests += 1
        max_retries = 10  # Reduced from 15 to 10
        base_delay = 3  # Increased from 2 to 3 seconds
        attempt = 0
        
        # Add longer random delay before first request to avoid detection
        initial_delay = random.uniform(2.0, 4.0)  # Increased from 0.5-2.0 to 2.0-4.0
        await asyncio.sleep(initial_delay)
        
        while attempt < max_retries:
            try:
                attempt += 1
                start_time = time.time()
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    
                    # If rate limited, retry with exponential backoff
                    if response.status == 429:
                        self.total_429_errors += 1
                        if attempt < max_retries:
                            # Exponential backoff: 3s, 6s, 12s, 24s, max 60s
                            retry_delay = min(base_delay * (2 ** (attempt - 1)), 60)
                            logger.warning(f"Rate limited fetching {url} (attempt {attempt}/{max_retries}) - retrying in {retry_delay}s")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.warning(f"Rate limited fetching {url} after {max_retries} attempts - giving up")
                            return {
                                'url': url,
                                'status_code': 429,
                                'html_content': '',
                                'response_time': response_time,
                                'error': 'rate_limited_after_retries'
                            }
                    
                    html_content = await response.text()
                    
                    return {
                        'url': url,
                        'status_code': response.status,
                        'html_content': html_content,
                        'response_time': response_time,
                        'headers': dict(response.headers)
                    }
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url}")
                return {
                    'url': url,
                    'status_code': None,
                    'html_content': '',
                    'response_time': None,
                    'error': 'timeout'
                }
            except Exception as e:
                logger.warning(f"Error fetching {url}: {str(e)}")
                return {
                    'url': url,
                    'status_code': None,
                    'html_content': '',
                    'response_time': None,
                    'error': str(e)
                }
        
        # If we get here, all retries failed
        return {
            'url': url,
            'status_code': 429,
            'html_content': '',
            'response_time': None,
            'error': 'rate_limited_after_retries'
        }
    
    async def _fetch_page_with_semaphore(self, url: str, semaphore: asyncio.Semaphore) -> Optional[Dict]:
        """Fetch a single page with semaphore control for concurrency management"""
        async with semaphore:
            return await self.fetch_page(url)
    
    def extract_links(self, html_content: str, base_url: str, 
                     extract_static: bool = True, 
                     extract_dynamic: bool = False, 
                     extract_resources: bool = False, 
                     extract_external: bool = False) -> List[Dict[str, any]]:
        """Extract links from HTML content with configurable types"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # Extract static HTML links (default behavior)
            if extract_static:
                static_links = self._extract_static_links(soup, base_url)
                links.extend(static_links)
            
            # Extract dynamic JavaScript links
            if extract_dynamic:
                dynamic_links = self._extract_dynamic_links(soup, base_url)
                links.extend(dynamic_links)
            
            # Extract resource links
            if extract_resources:
                resource_links = self._extract_resource_links(soup, base_url)
                links.extend(resource_links)
            
            # Filter external links if not requested
            if not extract_external:
                base_domain = urlparse(base_url).netloc
                links = [link for link in links if self._is_same_domain(link['url'], base_domain)]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in links:
                if link['url'] not in seen:
                    seen.add(link['url'])
                    unique_links.append(link)
            
            logger.debug(f"Extracted {len(unique_links)} links from {base_url} (static: {extract_static}, dynamic: {extract_dynamic}, resources: {extract_resources})")
            return unique_links
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {str(e)}")
            return []
    
    def _extract_static_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, any]]:
        """Extract links from static HTML tags (a, link, area)"""
        links = []
        
        for tag in soup.find_all(['a', 'link', 'area']):
            href = tag.get('href')
            if href:
                absolute_url = urljoin(base_url, href)
                if self._is_valid_link(absolute_url):
                    links.append({
                        'url': absolute_url,
                        'type': LinkType.STATIC_HTML,
                        'context': f"HTML tag: {tag.name}",
                        'title': tag.get('title', '') or tag.get_text().strip()[:100]
                    })
        
        return links
    
    def _extract_dynamic_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, any]]:
        """Extract links from JavaScript and dynamic content"""
        links = []
        import re
        
        # Extract from onclick handlers
        for tag in soup.find_all(attrs={'onclick': True}):
            onclick = tag.get('onclick', '')
            url_pattern = r'https?://[^\s\'"]+'
            urls = re.findall(url_pattern, onclick)
            for url in urls:
                if self._is_valid_link(url):
                    links.append({
                        'url': url,
                        'type': LinkType.DYNAMIC_JS,
                        'context': f"onclick handler: {onclick[:100]}...",
                        'title': tag.get('title', '') or tag.get_text().strip()[:100]
                    })
        
        # Extract from data attributes
        for tag in soup.find_all(attrs={'data-url': True}):
            data_url = tag.get('data-url')
            if data_url:
                absolute_url = urljoin(base_url, data_url)
                if self._is_valid_link(absolute_url):
                    links.append({
                        'url': absolute_url,
                        'type': LinkType.DYNAMIC_JS,
                        'context': f"data-url attribute",
                        'title': tag.get('title', '') or tag.get_text().strip()[:100]
                    })
        
        # Extract from script content
        for script in soup.find_all('script'):
            if script.string:
                script_content = script.string
                url_pattern = r'https?://[^\s\'"]+'
                urls = re.findall(url_pattern, script_content)
                for url in urls:
                    if self._is_valid_link(url):
                        links.append({
                            'url': url,
                            'type': LinkType.DYNAMIC_JS,
                            'context': f"JavaScript content: {script_content[:100]}...",
                            'title': 'JavaScript-generated link'
                        })
        
        return links
    
    def _extract_resource_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, any]]:
        """Extract resource links (images, CSS, JS files)"""
        links = []
        
        # Extract from img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                if self._is_resource_link(absolute_url):
                    links.append({
                        'url': absolute_url,
                        'type': LinkType.RESOURCE,
                        'context': f"img src",
                        'title': img.get('alt', '') or 'Image'
                    })
        
        # Extract from link tags (CSS)
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(base_url, href)
                if self._is_resource_link(absolute_url):
                    links.append({
                        'url': absolute_url,
                        'type': LinkType.RESOURCE,
                        'context': f"CSS stylesheet",
                        'title': 'Stylesheet'
                    })
        
        # Extract from script tags (JS)
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                if self._is_resource_link(absolute_url):
                    links.append({
                        'url': absolute_url,
                        'type': LinkType.RESOURCE,
                        'context': f"JavaScript file",
                        'title': 'JavaScript'
                    })
        
        return links
    
    def _is_valid_link(self, url: str) -> bool:
        """Check if a URL is a valid page link (not a resource file)"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Skip resource files
            if self._is_resource_link(url):
                return False
            
            return True
        except Exception:
            return False
    
    def _is_resource_link(self, url: str) -> bool:
        """Check if a URL is a resource file"""
        resource_extensions = [
            '.css', '.js', '.xml', '.json', '.txt', '.csv',
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.tar', '.gz', '.mp4', '.mp3', '.wav'
        ]
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        return any(path.endswith(ext) for ext in resource_extensions)
    
    def _is_same_domain(self, url: str, base_domain: str) -> bool:
        """Check if URL belongs to the same domain"""
        try:
            parsed = urlparse(url)
            return parsed.netloc == base_domain
        except Exception:
            return False
    
    def extract_page_content(self, html_content: str, url: str) -> PageContent:
        """Extract and analyze page content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else None
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            text_content = ' '.join(text_content.split())  # Clean whitespace
            
            # Check for common page elements with more comprehensive detection
            has_header = bool(
                soup.find(['header', 'nav']) or 
                soup.find('div', class_=lambda x: x and any(word in x.lower() for word in ['header', 'top', 'banner', 'masthead'])) or
                soup.find('div', id=lambda x: x and any(word in x.lower() for word in ['header', 'top', 'banner', 'masthead']))
            )
            
            has_footer = bool(
                soup.find('footer') or 
                soup.find('div', class_=lambda x: x and any(word in x.lower() for word in ['footer', 'bottom', 'copyright'])) or
                soup.find('div', id=lambda x: x and any(word in x.lower() for word in ['footer', 'bottom', 'copyright']))
            )
            
            has_navigation = bool(
                soup.find('nav') or 
                soup.find('div', class_=lambda x: x and any(word in x.lower() for word in ['nav', 'menu', 'navigation', 'sidebar'])) or
                soup.find('div', id=lambda x: x and any(word in x.lower() for word in ['nav', 'menu', 'navigation', 'sidebar'])) or
                soup.find('ul', class_=lambda x: x and any(word in x.lower() for word in ['nav', 'menu', 'navigation']))
            )
            
            # Determine page type
            word_count = len(text_content.split())
            page_type = PageType.BLANK if word_count < 50 else PageType.CONTENT
            
            # Create content chunks (split by paragraphs or sections)
            chunks = self.create_content_chunks(text_content)
            
            return PageContent(
                url=url,
                title=title,
                html_content=html_content,
                text_content=text_content,
                word_count=word_count,
                page_type=page_type,
                has_header=has_header,
                has_footer=has_footer,
                has_navigation=has_navigation,
                content_chunks=chunks
            )
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return PageContent(
                url=url,
                html_content=html_content,
                text_content="",
                word_count=0,
                page_type=PageType.ERROR
            )
    
    def create_content_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into manageable chunks for AI processing"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    async def crawl_website(self, start_url: str, max_depth: int = None, max_pages_to_crawl: int = None, max_links_to_validate: int = None,
                           extract_static: bool = True, extract_dynamic: bool = False, extract_resources: bool = False, extract_external: bool = False) -> Dict:
        """Main crawling function with adaptive batch processing"""
        if max_depth is None:
            max_depth = settings.max_crawl_depth
        if max_pages_to_crawl is None:
            max_pages_to_crawl = settings.max_pages_to_crawl
        if max_links_to_validate is None:
            max_links_to_validate = settings.max_links_to_validate
            
        base_domain = urlparse(start_url).netloc
        normalized_start_url = self.normalize_url(start_url)
        self.pending_urls.add(normalized_start_url)
        
        # Initialize path tracking
        self.path_tracker.set_start_url(normalized_start_url)
        
        # Generate session ID
        self.crawl_session_id = f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting adaptive crawl of {start_url} with max depth {max_depth}")
        logger.info(f"Page crawl limit: {max_pages_to_crawl} pages")
        logger.info(f"Session ID: {self.crawl_session_id}")
        
        with tqdm(desc="Crawling pages") as pbar:
            while self.pending_urls and len(self.visited_urls) < max_pages_to_crawl:
                # Get adaptive batch size
                batch_size = self.get_adaptive_batch_size()
                
                # Get next batch
                current_batch = list(self.pending_urls)[:batch_size]
                self.pending_urls -= set(current_batch)
                
                logger.info(f"🔄 Processing batch of {len(current_batch)} pages (batch size: {batch_size})")
                logger.info(f"📈 Status: 429_count={self.consecutive_429_count}, slow_mode_pages={self.slow_mode_pages_remaining}")
                
                # Process batch based on size
                if batch_size == 1:
                    # Sequential processing for slow mode
                    results = []
                    for url in current_batch:
                        result = await self.fetch_page(url)
                        results.append(result)
                        self.visited_urls.add(self.normalize_url(url))
                        # Small delay between sequential requests
                        await asyncio.sleep(0.5)
                else:
                    # Parallel processing for fast mode
                    semaphore = asyncio.Semaphore(batch_size)
                    tasks = [self._fetch_page_with_semaphore(url, semaphore) for url in current_batch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if not isinstance(result, Exception) and result:
                            self.visited_urls.add(self.normalize_url(result['url']))
                
                # Check for 429 errors in this batch
                had_429 = any(
                    result.get('status_code') == 429 
                    for result in results 
                    if isinstance(result, dict) and result
                )
                
                # Update adaptive state
                self.update_adaptive_state(had_429)
                
                # Process results and extract new links
                for i, result in enumerate(results):
                    if isinstance(result, Exception) or not result:
                        continue
                        
                    url = current_batch[i]
                    self.visited_urls.add(url)
                    
                    # Create link record
                    link = Link(
                        url=url,
                        status_code=result.get('status_code'),
                        status=self._determine_link_status(result.get('status_code')),
                        link_type=LinkType.STATIC_HTML,  # Default for crawled pages
                        response_time=result.get('response_time'),
                        error_message=result.get('error')
                    )
                    self.links.append(link)
                    
                    # Process page content if successful
                    if result.get('status_code') == 200 and result.get('html_content'):
                        page_content = self.extract_page_content(result['html_content'], url)
                        
                        # Add path information to page content
                        page_content.path = self.path_tracker.get_path_to_url(url)
                        page_content.crawled_at = datetime.now().isoformat()
                        page_content.session_id = self.crawl_session_id
                        
                        # Extract HTML structure
                        html_structure = self.html_extractor.extract_structure(result['html_content'], url)
                        page_content.html_structure = html_structure
                        
                        self.pages.append(page_content)
                        
                        # Extract new links if we haven't reached max depth
                        current_depth = self._get_url_depth(url, start_url)
                        if current_depth < max_depth:
                            new_links_data = self.extract_links(result['html_content'], url, 
                                                               extract_static, extract_dynamic, extract_resources, extract_external)
                            for link_data in new_links_data:
                                new_link = link_data['url']
                                normalized_link = self.normalize_url(new_link)
                                if (self.is_valid_url(new_link, start_url) and 
                                    normalized_link not in self.visited_urls and 
                                    normalized_link not in self.pending_urls):
                                    self.pending_urls.add(normalized_link)
                                    # Track parent-child relationship
                                    self.path_tracker.add_page_relationship(url, normalized_link)
                
                pbar.update(len(current_batch))
                pbar.set_postfix({
                    'visited': len(self.visited_urls),
                    'pending': len(self.pending_urls),
                    '429_errors': self.total_429_errors
                })
                
                # Delay between batches
                if self.pending_urls:
                    delay = 2.0 if batch_size == 1 else 1.0
                    await asyncio.sleep(delay)
        
        # Final results
        if len(self.visited_urls) >= max_pages_to_crawl:
            logger.info(f"Crawl completed (hit page limit). Visited {len(self.visited_urls)} URLs, found {len(self.pages)} pages")
            logger.info(f"Remaining pending URLs: {len(self.pending_urls)}")
        else:
            logger.info(f"Crawl completed. Visited {len(self.visited_urls)} URLs, found {len(self.pages)} pages")
        
        logger.info(f"📊 Total 429 errors: {self.total_429_errors}")
        logger.info(f" 429 error rate: {(self.total_429_errors/self.total_requests)*100:.1f}%" if self.total_requests > 0 else " 429 error rate: 0.0%")
        
        return {
            'links': self.links,
            'pages': self.pages,
            'total_visited': len(self.visited_urls),
            'total_pages': len(self.pages),
            'total_429_errors': self.total_429_errors,
            'error_rate': (self.total_429_errors/self.total_requests)*100 if self.total_requests > 0 else 0,
            'session_id': self.crawl_session_id,
            'path_tracking': self.path_tracker.export_path_data(),
            'start_url': start_url
        }
    
    def _determine_link_status(self, status_code: Optional[int]) -> LinkStatus:
        """Determine link status based on HTTP status code"""
        if status_code is None:
            return LinkStatus.UNKNOWN
        
        if 200 <= status_code < 300:
            return LinkStatus.VALID
        elif 300 <= status_code < 400:
            return LinkStatus.REDIRECT
        elif 400 <= status_code < 500:
            return LinkStatus.BROKEN
        elif 500 <= status_code < 600:
            return LinkStatus.BROKEN
        else:
            return LinkStatus.UNKNOWN
    
    def _get_url_depth(self, url: str, base_url: str) -> int:
        """Calculate the depth of a URL relative to the base URL"""
        try:
            base_path = urlparse(base_url).path
            url_path = urlparse(url).path
            
            base_depth = len([p for p in base_path.split('/') if p])
            url_depth = len([p for p in url_path.split('/') if p])
            
            return max(0, url_depth - base_depth)
        except Exception:
            return 0
