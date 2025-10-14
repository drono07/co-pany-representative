# Technical Documentation - Website Analysis Platform

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Background Tasks](#background-tasks)
9. [Web Scraping Implementation](#web-scraping-implementation)
10. [Link Validation System](#link-validation-system)
11. [Source Code Management](#source-code-management)
12. [Deployment & Scripts](#deployment--scripts)
13. [Configuration](#configuration)

---

## 🏗️ Architecture Overview

The Website Analysis Platform is a comprehensive system for analyzing websites, detecting broken links, and providing insights. It follows a microservices architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI Backend │    │   Celery Workers │
│   (Port 3000)   │◄──►│   (Port 8000)    │◄──►│   (Background)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   MongoDB       │
                       │   (Port 27017)  │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis         │
                       │   (Port 6379)   │
                       └─────────────────┘
```

### Key Design Principles:
- **Separation of Concerns**: Clear separation between API, business logic, and data layers
- **Asynchronous Processing**: Heavy tasks run in background via Celery
- **Scalable Architecture**: Can handle multiple concurrent analyses
- **Hierarchical Optimization**: Smart source code storage to avoid duplication

---

## 🛠️ Technology Stack

### Backend Technologies:
- **FastAPI**: Modern Python web framework for APIs
  - *Why*: High performance, automatic API documentation, type hints support
- **Celery**: Distributed task queue for background processing
  - *Why*: Handles long-running analysis tasks without blocking API
- **Redis**: Message broker for Celery
  - *Why*: Fast, reliable, and simple compared to RabbitMQ
- **MongoDB**: NoSQL database for flexible data storage
  - *Why*: Handles complex nested data structures from web analysis
- **Motor**: Async MongoDB driver
  - *Why*: Non-blocking database operations for FastAPI

### Web Scraping & Parsing:
- **aiohttp**: Async HTTP client for web requests
  - *Why*: Non-blocking HTTP requests, handles thousands of concurrent requests
- **BeautifulSoup4**: HTML parsing library
  - *Why*: Robust HTML parsing, handles malformed HTML gracefully
- **tqdm**: Progress bars for long-running operations
  - *Why*: User feedback during analysis progress

### Frontend:
- **React**: Modern JavaScript framework
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API calls

---

## 📁 Project Structure

```
website-insights/
├── backend/                    # Backend Python code
│   ├── api/                   # FastAPI application layer
│   │   ├── fastapi_app.py     # Main API server with all endpoints
│   │   └── api_models.py      # Pydantic models for request/response validation
│   ├── core/                  # Core business logic
│   │   ├── analysis_engine.py # Orchestrates the entire analysis process
│   │   ├── crawler.py         # Web scraping and link extraction
│   │   ├── main.py           # Legacy analysis platform (used by analysis_engine)
│   │   ├── validators.py     # Link validation and broken link detection
│   │   ├── content_processor.py # Content analysis and processing
│   │   ├── change_detector.py # Detects changes between analysis runs
│   │   ├── evaluation_system.py # AI-powered content evaluation
│   │   ├── html_structure_extractor.py # Extracts HTML structure
│   │   └── path_tracker.py   # Tracks parent-child relationships
│   ├── database/              # Database layer
│   │   ├── database_schema.py # MongoDB operations and schema
│   │   └── setup_mongodb.py   # Database initialization
│   ├── tasks/                 # Background task processing
│   │   ├── celery_app.py      # Celery configuration
│   │   ├── celery_tasks.py    # Task definitions
│   │   ├── celery_worker.py   # Worker process script
│   │   ├── celery_beat.py     # Task scheduler script
│   │   └── scheduler.py       # Scheduling logic
│   └── utils/                 # Shared utilities
│       ├── models.py          # Data models and enums
│       └── config.py          # Configuration management
├── scripts/                   # Platform management scripts
│   ├── start_backend.sh       # Start backend services
│   ├── start_frontend_react.sh # Start React frontend
│   ├── start_full_platform.sh # Start entire platform
│   └── stop.sh               # Stop all services
├── frontend/                  # React frontend application
└── docs/                      # Documentation
```

---

## 🔧 Core Components

### 1. Analysis Engine (`backend/core/analysis_engine.py`)
**Purpose**: Orchestrates the entire website analysis process

**Key Methods**:
- `analyze_website()`: Main entry point for analysis
- `save_results_to_db()`: Saves analysis results with hierarchical optimization

**Process Flow**:
1. Receives analysis request with configuration
2. Calls legacy `main.py` platform for crawling
3. Processes results and saves to database
4. Implements hierarchical source code storage optimization

### 2. Web Crawler (`backend/core/crawler.py`)
**Purpose**: Scrapes websites and extracts links/content

**Key Features**:
- **Configurable Link Extraction**: Separate static HTML vs dynamic JavaScript links
- **Adaptive Batch Processing**: Adjusts batch size based on performance
- **Concurrent Processing**: Uses asyncio for parallel requests
- **Smart Link Discovery**: Finds links in HTML, JavaScript, and data attributes

**Link Extraction Types**:
```python
class LinkType(str, Enum):
    STATIC_HTML = "static_html"   # From <a>, <link>, <area> tags
    DYNAMIC_JS = "dynamic_js"     # From JavaScript (onclick, data attributes)
    RESOURCE = "resource"         # Images, CSS, JS files
    EXTERNAL = "external"         # Links to external domains
```

**Configuration**:
- `extract_static_links`: Default True (HTML links)
- `extract_dynamic_links`: Default False (JavaScript links)
- `extract_resource_links`: Default False (resource files)
- `extract_external_links`: Default False (external domains)

### 3. Link Validator (`backend/core/validators.py`)
**Purpose**: Validates links and detects broken links

**Validation Process**:
1. **Concurrent Validation**: Uses asyncio for parallel link checking
2. **Status Code Analysis**: Categorizes links by HTTP status
3. **Error Detection**: Identifies broken, redirected, and timeout links
4. **Performance Metrics**: Tracks response times

**Link Status Categories**:
- `VALID`: 200 status code
- `BROKEN`: 404, 500, etc.
- `REDIRECT`: 301, 302, etc.
- `TIMEOUT`: Request timeout
- `RATE_LIMITED`: 429 status code

### 4. Content Processor (`backend/core/content_processor.py`)
**Purpose**: Processes and analyzes page content

**Features**:
- **HTML to Markdown**: Converts HTML to markdown for analysis
- **Content Chunking**: Splits content into manageable chunks
- **Structure Analysis**: Detects headers, footers, navigation
- **Word Count**: Calculates content metrics

---

## 🔄 Data Flow

### Analysis Request Flow:
```
1. User submits analysis request via React frontend
2. FastAPI receives request and validates data
3. Celery task is queued for background processing
4. Analysis Engine orchestrates the process:
   a. Web Crawler scrapes the website
   b. Link Validator checks all discovered links
   c. Content Processor analyzes page content
   d. Results are saved to MongoDB with hierarchical optimization
5. Frontend polls for results and displays them
```

### Hierarchical Source Code Storage:
```
Traditional Approach:
├── Page A (source code stored)
├── Page B (source code stored) ← Duplicate
├── Page C (source code stored) ← Duplicate
└── Page D (source code stored) ← Duplicate

Optimized Approach:
├── Page A (source code stored) ← Parent
│   ├── Page B (no storage, uses parent's source)
│   ├── Page C (no storage, uses parent's source)
│   └── Page D (no storage, uses parent's source)
```

**Benefits**:
- **Storage Efficiency**: Reduces database size by 60-80%
- **Faster Retrieval**: Less data to transfer
- **Cost Optimization**: Lower storage costs

---

## 🗄️ Database Schema

### MongoDB Collections:

#### 1. `analysis_runs`
```javascript
{
  "_id": ObjectId,
  "application_id": ObjectId,
  "status": "pending|running|completed|failed",
  "task_id": String,
  "created_at": Date,
  "updated_at": Date,
  "started_at": Date,
  "completed_at": Date
}
```

#### 2. `analysis_results`
```javascript
{
  "_id": ObjectId,
  "run_id": String,
  "total_pages": Number,
  "total_links": Number,
  "broken_links": Number,
  "valid_links": Number,
  "redirect_links": Number,
  "timeout_links": Number,
  "analysis_summary": Object,
  "created_at": Date
}
```

#### 3. `link_validations`
```javascript
{
  "_id": ObjectId,
  "run_id": String,
  "url": String,
  "status": "valid|broken|redirect|timeout|rate_limited|unknown",
  "status_code": Number,
  "response_time": Number,
  "error_message": String,
  "parent_url": String,
  "discovered_at": Date
}
```

#### 4. `parent_child_relationships`
```javascript
{
  "_id": ObjectId,
  "run_id": String,
  "start_url": String,
  "parent_map": Object,      // child_url -> parent_url
  "children_map": Object,    // parent_url -> [child_urls]
  "path_map": Object,        // url -> [path_to_root]
  "created_at": Date
}
```

#### 5. `page_source_codes` (Hierarchical Storage)
```javascript
{
  "_id": ObjectId,
  "run_id": String,
  "page_url": String,
  "source_code": String,     // Only stored for parent pages
  "parent_url": String,
  "created_at": Date
}
```

#### 6. `applications`
```javascript
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "name": String,
  "description": String,
  "website_url": String,
  "max_crawl_depth": Number,
  "max_pages_to_crawl": Number,
  "max_links_to_validate": Number,
  "enable_ai_evaluation": Boolean,
  "max_ai_evaluation_pages": Number,
  "extract_static_links": Boolean,
  "extract_dynamic_links": Boolean,
  "extract_resource_links": Boolean,
  "extract_external_links": Boolean,
  "created_at": Date,
  "updated_at": Date,
  "is_active": Boolean
}
```

---

## 🌐 API Endpoints

### Authentication Endpoints:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token

### Application Management:
- `GET /applications` - List user applications
- `POST /applications` - Create new application
- `GET /applications/{app_id}` - Get application details
- `PUT /applications/{app_id}` - Update application
- `DELETE /applications/{app_id}` - Delete application

### Analysis Management:
- `POST /applications/{app_id}/runs` - Start analysis run
- `GET /applications/{app_id}/runs` - List analysis runs
- `GET /runs/{run_id}` - Get analysis results
- `DELETE /runs/{run_id}` - Delete analysis run

### Data Retrieval:
- `GET /runs/{run_id}/source-code` - Get page source code (with hierarchical optimization)
- `GET /runs/{run_id}/parent-child-relationships` - Get URL relationships
- `GET /runs/{run_id}/broken-links` - Get broken links with parent info

### Utility Endpoints:
- `GET /health` - Health check
- `GET /dashboard` - Dashboard statistics
- `POST /runs/{run_id}/export-json` - Export analysis results

---

## ⚙️ Background Tasks

### Celery Configuration (`backend/tasks/celery_app.py`):
```python
celery_app = Celery(
    "website_analysis",
    broker="redis://localhost:6379/0",
    backend=None,  # Disabled to avoid Redis issues
    include=["celery_tasks"]
)
```

### Task Queues:
- `analysis`: Main analysis tasks
- `notifications`: Email notifications
- `maintenance`: Cleanup tasks

### Scheduled Tasks (Celery Beat):
```python
beat_schedule={
    "run-scheduled-analyses": {
        "task": "celery_tasks.process_scheduled_analyses",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "cleanup-old-results": {
        "task": "celery_tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "health-check": {
        "task": "celery_tasks.health_check",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
}
```

### Main Analysis Task (`celery_tasks.run_website_analysis`):
1. **Task Initialization**: Sets up progress tracking
2. **Analysis Execution**: Calls Analysis Engine
3. **Result Processing**: Saves results to database
4. **JSON Export**: Automatically exports results
5. **Cleanup**: Handles errors and cleanup

---

## 🕷️ Web Scraping Implementation

### Crawler Architecture (`backend/core/crawler.py`):

#### 1. **Adaptive Batch Processing**:
```python
def get_adaptive_batch_size(self) -> int:
    """Dynamically adjusts batch size based on performance"""
    if self.error_rate > 0.1:  # High error rate
        return max(5, self.batch_size // 2)
    elif self.error_rate < 0.05:  # Low error rate
        return min(50, self.batch_size * 2)
    return self.batch_size
```

#### 2. **Concurrent Request Handling**:
```python
async def _fetch_page_with_semaphore(self, url: str, semaphore: asyncio.Semaphore):
    """Controls concurrency to avoid overwhelming target servers"""
    async with semaphore:
        return await self.fetch_page(url)
```

#### 3. **Smart Link Extraction**:
```python
def extract_links(self, html_content: str, base_url: str, 
                 extract_static: bool = True, 
                 extract_dynamic: bool = False, 
                 extract_resources: bool = False, 
                 extract_external: bool = False):
    """Configurable link extraction with multiple strategies"""
```

**Static HTML Links**:
- Extracts from `<a>`, `<link>`, `<area>` tags
- Converts relative URLs to absolute URLs
- Validates URL format

**Dynamic JavaScript Links**:
- Parses `onclick` handlers for URLs
- Extracts from `data-url` attributes
- Uses regex to find URLs in JavaScript code blocks

**Resource Links**:
- Identifies images, CSS, JS files
- Filters by file extensions
- Categorizes by resource type

#### 4. **Rate Limiting & Respect**:
- **Respectful Crawling**: Configurable delays between requests
- **User-Agent Rotation**: Uses realistic browser user agents
- **Error Handling**: Graceful handling of timeouts and errors
- **Retry Logic**: Automatic retry for transient failures

### Content Processing:
1. **HTML Parsing**: BeautifulSoup4 for robust parsing
2. **Content Extraction**: Removes scripts, styles, comments
3. **Structure Analysis**: Identifies headers, footers, navigation
4. **Markdown Conversion**: Converts HTML to markdown for analysis

---

## 🔗 Link Validation System

### Validation Process (`backend/core/validators.py`):

#### 1. **Concurrent Validation**:
```python
async def validate_links(self, links: List[Link]) -> List[Link]:
    """Validates multiple links concurrently"""
    semaphore = asyncio.Semaphore(50)  # Limit concurrent requests
    tasks = [self._validate_single_link(link, semaphore) for link in links]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

#### 2. **HTTP Status Analysis**:
- **200**: Valid link
- **301/302**: Redirect (follows redirects)
- **404**: Broken link
- **500**: Server error
- **Timeout**: Network timeout
- **429**: Rate limited

#### 3. **Performance Metrics**:
- **Response Time**: Tracks how long each request takes
- **Error Rate**: Monitors validation success rate
- **Timeout Handling**: Configurable timeout settings

#### 4. **Parent-Child Tracking**:
- **Relationship Mapping**: Tracks which page discovered each link
- **Broken Link Context**: Shows where broken links were found
- **Navigation Paths**: Builds complete site structure

---

## 💾 Source Code Management

### Hierarchical Storage Optimization:

#### Problem:
Traditional approach stores HTML source code for every page, leading to massive duplication since many pages share identical HTML structure.

#### Solution:
Only store source code for **parent pages** (pages that have children). Leaf pages retrieve source code from their nearest parent via hierarchical traversal.

#### Implementation (`backend/database/database_schema.py`):
```python
async def get_page_source_code(self, run_id: str, page_url: str) -> Optional[dict]:
    """Get source code with hierarchical parent traversal"""
    # 1. Try direct lookup first
    result = await self.db.page_source_codes.find_one({
        "run_id": run_id,
        "page_url": page_url
    })
    
    if result:
        return result
    
    # 2. If not found, traverse up parent hierarchy
    relationships = await self.get_parent_child_relationships(run_id)
    current_url = page_url
    traversal_path = [current_url]
    depth = 0
    
    while current_url in relationships.get("parent_map", {}):
        parent_url = relationships["parent_map"][current_url]
        traversal_path.append(parent_url)
        depth += 1
        
        # Check if parent has source code
        parent_result = await self.db.page_source_codes.find_one({
            "run_id": run_id,
            "page_url": parent_url
        })
        
        if parent_result:
            return {
                **parent_result,
                "page_url": page_url,  # Override with requested URL
                "actual_source_page": parent_url,
                "traversal_path": traversal_path,
                "hierarchy_depth": depth
            }
        
        current_url = parent_url
    
    return None
```

#### Benefits:
- **60-80% Storage Reduction**: Eliminates duplicate source code
- **Faster Retrieval**: Less data to transfer
- **Transparent API**: Same response format regardless of storage method
- **Traversal Tracking**: Shows path taken to find source code

---

## 🚀 Deployment & Scripts

### Platform Scripts (`scripts/`):

#### 1. **Full Platform Startup** (`start_full_platform.sh`):
```bash
# Starts all services in correct order:
# 1. Redis check
# 2. Celery Worker
# 3. Celery Beat (scheduler)
# 4. FastAPI server
# 5. React frontend
```

#### 2. **Backend Only** (`start_backend.sh`):
```bash
# Starts backend services:
# - Celery Worker (background tasks)
# - Celery Beat (task scheduler)
# - FastAPI (API server)
```

#### 3. **Frontend Only** (`start_frontend_react.sh`):
```bash
# Starts React development server:
# - Installs dependencies if needed
# - Sets environment variables
# - Starts development server
```

#### 4. **Platform Shutdown** (`stop.sh`):
```bash
# Gracefully stops all services:
# - Kills processes by PID
# - Cleans up PID files
# - Ensures clean shutdown
```

### Service Dependencies:
1. **Redis**: Must be running (message broker for Celery)
2. **MongoDB**: Must be running (data storage)
3. **Node.js**: Required for React frontend
4. **Python 3.8+**: Required for backend

---

## ⚙️ Configuration

### Environment Variables (`backend/utils/config.py`):
```python
class Settings(BaseSettings):
    # Database
    mongodb_uri: str = "mongodb://localhost:27017/website_analysis_platform"
    enable_mongodb_storage: bool = True
    
    # Crawler Settings
    max_crawl_depth: int = 2
    max_pages_to_crawl: int = 500
    max_links_to_validate: int = 1500
    
    # Link Extraction (New Feature)
    extract_static_links: bool = True      # HTML links
    extract_dynamic_links: bool = False    # JavaScript links
    extract_resource_links: bool = False   # Resource files
    extract_external_links: bool = False   # External domains
    
    # Analysis Features
    enable_link_validation: bool = True
    enable_blank_page_detection: bool = True
    enable_content_analysis: bool = True
    enable_ai_evaluation: bool = False
    
    # Performance
    request_timeout: int = 30
    max_concurrent_requests: int = 50
    retry_attempts: int = 3
```

### Celery Configuration:
```python
# Redis as message broker
REDIS_URL = "redis://localhost:6379/0"

# Task routing
task_routes = {
    "celery_tasks.run_website_analysis": {"queue": "analysis"},
    "celery_tasks.send_notification": {"queue": "notifications"},
    "celery_tasks.cleanup_old_data": {"queue": "maintenance"},
}

# Worker settings
worker_prefetch_multiplier = 1
task_acks_late = True
worker_disable_rate_limits = True
```

---

## 🔧 Development Setup

### Prerequisites:
```bash
# Install Redis
brew install redis  # macOS
# or
sudo apt-get install redis-server  # Ubuntu

# Install MongoDB
brew install mongodb-community  # macOS
# or
sudo apt-get install mongodb  # Ubuntu

# Install Node.js
brew install node  # macOS
# or download from nodejs.org
```

### Starting Required Services:

**Redis:**
```bash
# macOS
brew services start redis

# Or using Docker
docker run -d -p 6379:6379 redis:alpine
```

**MongoDB:**
```bash
# macOS (recommended)
brew services start mongodb-community

# Or use our helper script
./scripts/start_mongodb.sh

# Or manually
mongod --dbpath /opt/homebrew/var/mongodb --logpath /opt/homebrew/var/log/mongodb/mongo.log --fork
```

### Installation:
```bash
# Clone repository
git clone <repository-url>
cd website-insights

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Start the platform
./scripts/start_full_platform.sh
```

### Development Workflow:
1. **Backend Changes**: Modify files in `backend/` directory
2. **Frontend Changes**: Modify files in `frontend/src/` directory
3. **Database Changes**: Update `backend/database/database_schema.py`
4. **API Changes**: Update `backend/api/` files
5. **Testing**: Use the platform's built-in analysis features

---

## 📊 Performance Considerations

### Scalability:
- **Horizontal Scaling**: Multiple Celery workers can be added
- **Database Optimization**: MongoDB indexes on frequently queried fields
- **Caching**: Redis can be used for caching frequently accessed data
- **Load Balancing**: Multiple FastAPI instances can be deployed

### Monitoring:
- **Health Checks**: Built-in health check endpoints
- **Task Monitoring**: Celery Flower for task monitoring
- **Database Monitoring**: MongoDB Compass for database inspection
- **Logging**: Comprehensive logging throughout the system

### Optimization Features:
- **Hierarchical Source Storage**: Reduces storage by 60-80%
- **Configurable Link Extraction**: Only extract needed link types
- **Adaptive Batch Processing**: Adjusts to server performance
- **Concurrent Processing**: Parallel request handling
- **Smart Caching**: Avoids duplicate work

---

## 🐛 Troubleshooting

### Common Issues:

#### 1. **Redis Connection Error**:
```bash
# Check if Redis is running
redis-cli ping
# Should return "PONG"

# Start Redis if not running
brew services start redis  # macOS
sudo systemctl start redis  # Ubuntu
```

#### 2. **MongoDB Connection Error**:
```bash
# Check if MongoDB is running
mongosh --eval "db.runCommand('ping')"
# Should return "ok": 1

# Start MongoDB if not running
brew services start mongodb-community  # macOS
sudo systemctl start mongod  # Ubuntu
```

#### 3. **Celery Worker Not Processing Tasks**:
```bash
# Check worker status
celery -A backend.tasks.celery_app inspect active

# Restart worker
pkill -f celery_worker
python3 backend/tasks/celery_worker.py
```

#### 4. **Import Errors After Reorganization**:
- Ensure all `__init__.py` files are present
- Check import paths in moved files
- Verify Python path includes project root

### Debug Mode:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./scripts/start_full_platform.sh
```

---

## 📈 Future Enhancements

### Planned Features:
1. **Real-time WebSocket Updates**: Live progress updates
2. **Advanced Caching**: Redis-based result caching
3. **API Rate Limiting**: Protect against abuse
4. **Multi-tenant Support**: Support multiple organizations
5. **Advanced Analytics**: More detailed insights and reporting
6. **Export Formats**: PDF, Excel, CSV export options
7. **Scheduled Reports**: Automated report generation
8. **Integration APIs**: Webhook support for external systems

### Performance Improvements:
1. **Database Sharding**: Distribute data across multiple MongoDB instances
2. **CDN Integration**: Serve static assets via CDN
3. **Microservices**: Split into smaller, focused services
4. **Container Deployment**: Docker and Kubernetes support
5. **Auto-scaling**: Dynamic resource allocation based on load

---

This technical documentation provides a comprehensive overview of the Website Analysis Platform's architecture, implementation, and operation. For specific implementation details, refer to the source code in the respective modules.
