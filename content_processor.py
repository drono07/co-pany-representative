import re
import tiktoken
from bs4 import BeautifulSoup
from markdownify import markdownify
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

from models import PageContent
from config import settings

logger = logging.getLogger(__name__)

class ContentProcessor:
    """Processes and chunks content for AI analysis"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
        self.encoding = tiktoken.encoding_for_model(model_name)
        self.max_tokens_per_chunk = 2000  # Leave room for context
        self.chunk_overlap = 200  # Overlap between chunks
        
    def process_page_content(self, page: PageContent) -> PageContent:
        """Process page content and create optimized chunks"""
        logger.info(f"Processing content for {page.url}")
        
        try:
            # Convert HTML to markdown
            markdown_content = self._html_to_markdown(page.html_content)
            page.markdown_content = markdown_content
            
            # Extract structured content
            structured_content = self._extract_structured_content(page.html_content)
            
            # Create semantic chunks
            chunks = self._create_semantic_chunks(markdown_content, structured_content)
            page.content_chunks = chunks
            
            # Update word count based on processed content
            page.word_count = len(page.text_content.split())
            
            logger.info(f"Successfully processed {page.url}: {len(chunks)} chunks, {page.word_count} words")
            
        except Exception as e:
            logger.error(f"Error processing content for {page.url}: {e}")
            # Set fallback values
            page.markdown_content = page.text_content
            page.content_chunks = [page.text_content[:2000]] if page.text_content else []
            page.word_count = len(page.text_content.split()) if page.text_content else 0
        
        return page
    
    def process_pages(self, pages: List[PageContent]) -> List[PageContent]:
        """Process multiple pages"""
        logger.info(f"Processing content for {len(pages)} pages...")
        
        processed_pages = []
        for page in pages:
            try:
                processed_page = self.process_page_content(page)
                processed_pages.append(processed_page)
            except Exception as e:
                logger.error(f"Failed to process page {page.url}: {e}")
                # Add page with minimal processing
                page.markdown_content = page.text_content or ""
                page.content_chunks = [page.text_content[:2000]] if page.text_content else []
                processed_pages.append(page)
        
        logger.info(f"Successfully processed {len(processed_pages)} pages")
        return processed_pages
    
    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to clean markdown"""
        try:
            # Clean HTML first
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Convert to markdown
            markdown = markdownify(str(soup), heading_style="ATX")
            
            # Clean up markdown
            markdown = self._clean_markdown(markdown)
            
            return markdown
        except Exception as e:
            logger.error(f"Error converting HTML to markdown: {e}")
            return ""
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean and normalize markdown content"""
        # Remove excessive whitespace
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
        
        # Remove empty lines at start and end
        markdown = markdown.strip()
        
        # Fix common markdown issues
        markdown = re.sub(r'#+\s*$', '', markdown, flags=re.MULTILINE)  # Remove empty headings
        markdown = re.sub(r'\*\s*\*', '', markdown)  # Remove empty bold
        markdown = re.sub(r'_\s*_', '', markdown)  # Remove empty italic
        
        return markdown
    
    def _extract_structured_content(self, html_content: str) -> Dict[str, List[str]]:
        """Extract structured content elements"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        structured = {
            'headings': [],
            'paragraphs': [],
            'lists': [],
            'links': [],
            'images': [],
            'tables': []
        }
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text().strip()
            if text:
                structured['headings'].append({
                    'level': int(heading.name[1]),
                    'text': text
                })
        
        # Extract paragraphs
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 20:  # Filter out very short paragraphs
                structured['paragraphs'].append(text)
        
        # Extract lists
        for ul in soup.find_all(['ul', 'ol']):
            items = [li.get_text().strip() for li in ul.find_all('li')]
            if items:
                structured['lists'].append({
                    'type': ul.name,
                    'items': items
                })
        
        # Extract links
        for a in soup.find_all('a', href=True):
            text = a.get_text().strip()
            href = a['href']
            if text and href:
                structured['links'].append({
                    'text': text,
                    'url': href
                })
        
        # Extract images
        for img in soup.find_all('img'):
            alt = img.get('alt', '')
            src = img.get('src', '')
            if src:
                structured['images'].append({
                    'alt': alt,
                    'src': src
                })
        
        # Extract tables
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                structured['tables'].append(rows)
        
        return structured
    
    def _create_semantic_chunks(self, markdown_content: str, structured_content: Dict) -> List[str]:
        """Create semantic chunks based on content structure"""
        chunks = []
        
        # Strategy 1: Split by headings
        heading_chunks = self._split_by_headings(markdown_content)
        
        # Strategy 2: Split by paragraphs
        paragraph_chunks = self._split_by_paragraphs(markdown_content)
        
        # Strategy 3: Split by token count
        token_chunks = self._split_by_tokens(markdown_content)
        
        # Combine and deduplicate chunks
        all_chunks = heading_chunks + paragraph_chunks + token_chunks
        chunks = self._deduplicate_chunks(all_chunks)
        
        # Ensure chunks are within token limits
        chunks = self._ensure_token_limits(chunks)
        
        return chunks
    
    def _split_by_headings(self, markdown: str) -> List[str]:
        """Split content by headings"""
        chunks = []
        lines = markdown.split('\n')
        current_chunk = []
        
        for line in lines:
            if line.startswith('#'):
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                    current_chunk = []
            current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
        
        return chunks
    
    def _split_by_paragraphs(self, markdown: str) -> List[str]:
        """Split content by paragraphs"""
        paragraphs = markdown.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            paragraph_length = len(self.encoding.encode(paragraph))
            
            if current_length + paragraph_length > self.max_tokens_per_chunk and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_length = paragraph_length
            else:
                current_chunk.append(paragraph)
                current_length += paragraph_length
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _split_by_tokens(self, markdown: str) -> List[str]:
        """Split content by token count"""
        tokens = self.encoding.encode(markdown)
        chunks = []
        
        for i in range(0, len(tokens), self.max_tokens_per_chunk - self.chunk_overlap):
            chunk_tokens = tokens[i:i + self.max_tokens_per_chunk]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
        
        return chunks
    
    def _deduplicate_chunks(self, chunks: List[str]) -> List[str]:
        """Remove duplicate and very similar chunks"""
        unique_chunks = []
        seen_chunks = set()
        
        for chunk in chunks:
            # Normalize chunk for comparison
            normalized = re.sub(r'\s+', ' ', chunk.strip().lower())
            
            if normalized not in seen_chunks and len(normalized) > 50:
                unique_chunks.append(chunk)
                seen_chunks.add(normalized)
        
        return unique_chunks
    
    def _ensure_token_limits(self, chunks: List[str]) -> List[str]:
        """Ensure all chunks are within token limits"""
        valid_chunks = []
        
        for chunk in chunks:
            tokens = self.encoding.encode(chunk)
            
            if len(tokens) <= self.max_tokens_per_chunk:
                valid_chunks.append(chunk)
            else:
                # Split oversized chunks
                sub_chunks = self._split_by_tokens(chunk)
                valid_chunks.extend(sub_chunks)
        
        return valid_chunks
    
    def create_context_for_ai(self, page: PageContent, chunk_index: int = 0) -> str:
        """Create context string for AI evaluation"""
        context_parts = []
        
        # Add page metadata
        context_parts.append(f"URL: {page.url}")
        if page.title:
            context_parts.append(f"Title: {page.title}")
        context_parts.append(f"Word Count: {page.word_count}")
        context_parts.append(f"Page Type: {page.page_type}")
        context_parts.append("")
        
        # Add content chunk
        if page.content_chunks and chunk_index < len(page.content_chunks):
            context_parts.append("Content:")
            context_parts.append(page.content_chunks[chunk_index])
        else:
            context_parts.append("Content:")
            context_parts.append(page.text_content[:2000])  # Fallback to first 2000 chars
        
        return "\n".join(context_parts)
    
    def get_chunk_summary(self, page: PageContent) -> Dict[str, any]:
        """Get summary of content chunks"""
        return {
            'total_chunks': len(page.content_chunks),
            'avg_chunk_size': sum(len(chunk) for chunk in page.content_chunks) / len(page.content_chunks) if page.content_chunks else 0,
            'total_tokens': sum(len(self.encoding.encode(chunk)) for chunk in page.content_chunks) if page.content_chunks else 0,
            'chunk_sizes': [len(chunk) for chunk in page.content_chunks]
        }
