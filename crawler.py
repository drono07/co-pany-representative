import asyncio
import aiohttp
import time
import random
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from typing import Set, List, Dict, Optional
import logging
from tqdm import tqdm

from models import Link, LinkStatus, PageContent, PageType
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteCrawler:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.pending_urls: Set[str] = set()
        self.links: List[Link] = []
        self.pages: List[PageContent] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
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
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid and belongs to the same domain"""
        try:
            parsed = urlparse(url)
            base_parsed = urlparse(base_domain)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
                
            # Must be same domain
            if parsed.netloc != base_parsed.netloc:
                return False
                
            # Skip common non-content URLs
            skip_patterns = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.rar', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif',
                '.svg', '.ico', '.css', '.js', '.xml', '.json', '.txt'
            ]
            
            path_lower = parsed.path.lower()
            if any(path_lower.endswith(pattern) for pattern in skip_patterns):
                return False
                
            return True
        except Exception:
            return False
    
    async def fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a single page with smart retry strategy for rate limiting"""
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
    
    
    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract all links from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # Extract from various tag types
            for tag in soup.find_all(['a', 'link', 'area']):
                href = tag.get('href')
                if href:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(base_url, href)
                    links.append(absolute_url)
            
            # Also check for onclick handlers and data attributes that might contain URLs
            for tag in soup.find_all(attrs={'onclick': True}):
                onclick = tag.get('onclick', '')
                # Look for URLs in onclick handlers
                import re
                url_pattern = r'https?://[^\s\'"]+'
                urls = re.findall(url_pattern, onclick)
                for url in urls:
                    links.append(url)
            
            # Check for data attributes that might contain URLs
            for tag in soup.find_all(attrs={'data-url': True}):
                data_url = tag.get('data-url')
                if data_url:
                    absolute_url = urljoin(base_url, data_url)
                    links.append(absolute_url)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            logger.debug(f"Extracted {len(unique_links)} links from {base_url}")
            return unique_links
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {str(e)}")
            return []
    
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
    
    async def crawl_website(self, start_url: str, max_depth: int = None) -> Dict:
        """Main crawling function"""
        if max_depth is None:
            max_depth = settings.max_crawl_depth
            
        base_domain = urlparse(start_url).netloc
        self.pending_urls.add(start_url)
        
        logger.info(f"Starting crawl of {start_url} with max depth {max_depth}")
        logger.info(f"Page crawl limit: {settings.max_pages_to_crawl} pages")
        
        with tqdm(desc="Crawling pages") as pbar:
            while self.pending_urls and len(self.visited_urls) < settings.max_pages_to_crawl:  # Configurable limit
                # Process URLs one by one to avoid rate limiting
                current_url = list(self.pending_urls)[0]
                self.pending_urls.remove(current_url)
                
                # Fetch page sequentially (no concurrency)
                result = await self.fetch_page(current_url)
                
                if not result:
                    continue
                
                url = current_url
                self.visited_urls.add(url)
                
                # Create link record
                link = Link(
                    url=url,
                    status_code=result.get('status_code'),
                    status=self._determine_link_status(result.get('status_code')),
                    response_time=result.get('response_time'),
                    error_message=result.get('error')
                )
                self.links.append(link)
                
                # Process page content if successful
                if result.get('status_code') == 200 and result.get('html_content'):
                    page_content = self.extract_page_content(result['html_content'], url)
                    self.pages.append(page_content)
                    
                    # Extract new links if we haven't reached max depth
                    current_depth = self._get_url_depth(url, start_url)
                    if current_depth < max_depth:
                        new_links = self.extract_links(result['html_content'], url)
                        for new_link in new_links:
                            if (self.is_valid_url(new_link, start_url) and 
                                new_link not in self.visited_urls and 
                                    new_link not in self.pending_urls):
                                self.pending_urls.add(new_link)
                
                pbar.update(1)  # Update progress by 1 since we processed 1 URL
                pbar.set_postfix({
                    'visited': len(self.visited_urls),
                    'pending': len(self.pending_urls),
                    'pages': len(self.pages)
                })
        
        if len(self.visited_urls) >= settings.max_pages_to_crawl:
            logger.info(f"Crawl completed (hit page limit). Visited {len(self.visited_urls)} URLs, found {len(self.pages)} pages")
            logger.info(f"Remaining pending URLs: {len(self.pending_urls)}")
        else:
            logger.info(f"Crawl completed. Visited {len(self.visited_urls)} URLs, found {len(self.pages)} pages")
        
        return {
            'links': self.links,
            'pages': self.pages,
            'total_visited': len(self.visited_urls),
            'total_pages': len(self.pages)
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
