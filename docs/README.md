# Website Analysis Platform

A comprehensive FastAPI-based platform for automated website analysis with **Celery task queue**, **Redis broker**, **MongoDB storage**, and **automated scheduling**.

## 🚀 Features

### Core Features
- **Multi-User Support**: User registration, authentication, and role-based access
- **Application Management**: Create and manage multiple website analysis applications
- **Celery Task Queue**: Robust background task processing with Redis
- **Automated Scheduling**: Celery Beat for cron-based scheduling
- **Real-time Dashboard**: Visual dashboard with charts and statistics
- **API-First Design**: RESTful API for all operations
- **Context Comparison**: Compare analysis results between runs
- **Task Monitoring**: Real-time task status and worker monitoring

### Analysis Features
- **Website Crawling**: Recursive link discovery with configurable depth
- **Link Validation**: HTTP status checking with retry logic
- **Blank Page Detection**: Advanced HTML structure analysis
- **Change Detection**: Compare results between analysis runs
- **Path Tracking**: Track navigation paths to each page
- **HTML Structure Storage**: Store clean HTML structure for comparison

## 📋 Prerequisites

- Python 3.8+
- Redis (for Celery broker and result backend)
- MongoDB (for data storage)
- Docker (optional, for containerized deployment)

## 🛠️ Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Services
```bash
# Start Redis (choose one)
brew services start redis                    # macOS
docker run -d -p 6379:6379 redis:alpine     # Docker
sudo systemctl start redis-server           # Ubuntu/Debian

# Start the platform
./start.sh
```

### 3. Access the Platform
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard.html
- **API Docs**: http://localhost:8000/docs

## 🎯 Default Configuration

The platform comes with sensible defaults:

### Crawler Defaults
- **MAX_PAGES_TO_CRAWL**: 500 pages
- **MAX_LINKS_TO_VALIDATE**: 1500 links (3x pages for comprehensive validation)
- **MAX_CRAWL_DEPTH**: 1 (shallow crawl for performance)
- **ENABLE_AI_EVALUATION**: false (disabled by default)

### Validation Rules
- **MAX_LINKS_TO_VALIDATE** should be **2-3x** the value of **MAX_PAGES_TO_CRAWL**
- This ensures comprehensive link validation without overwhelming the system
- Frontend will show validation messages for proper configuration

## 📚 API Usage

### Authentication

#### Register User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "securepassword"
  }'
```

#### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

### Application Management

#### Create Application
```bash
curl -X POST "http://localhost:8000/applications" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Website",
    "description": "Main website analysis",
    "website_url": "https://example.com"
  }'
```

### Analysis with Celery Tasks

#### Start Analysis (Queued Task)
```bash
curl -X POST "http://localhost:8000/applications/{app_id}/runs" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response includes both `run_id` and `task_id`:
```json
{
  "message": "Analysis started",
  "run_id": "run_123",
  "task_id": "celery_task_456"
}
```

#### Monitor Task Status
```bash
curl -X GET "http://localhost:8000/tasks/{task_id}/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Scheduling

#### Create Schedule
```bash
curl -X POST "http://localhost:8000/applications/{app_id}/schedules" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "daily",
    "is_active": true
  }'
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/website_analysis_platform

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Authentication
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Website Analysis Settings (with defaults)
MAX_PAGES_TO_CRAWL=500
MAX_LINKS_TO_VALIDATE=1500
MAX_CRAWL_DEPTH=1
ENABLE_AI_EVALUATION=false
```

### Application Settings
```python
{
    "name": "Application Name",
    "description": "Description",
    "website_url": "https://example.com",
    "max_crawl_depth": 1,           # 1-5 (default: 1)
    "max_pages_to_crawl": 500,      # 10-1000 (default: 500)
    "max_links_to_validate": 1500,  # 10-2000 (default: 1500, should be 2-3x pages)
    "enable_ai_evaluation": false,  # true/false (default: false)
    "max_ai_evaluation_pages": 10   # 1-50 (default: 10)
}
```

### Validation Rules
- **MAX_LINKS_TO_VALIDATE** should be **2-3x** **MAX_PAGES_TO_CRAWL**
- Example: 500 pages → 1000-1500 links to validate
- Frontend will show validation messages for proper configuration

## 🚀 Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Manual Deployment
```bash
# Start Redis
redis-server

# Start Celery Worker
python celery_worker.py

# Start Celery Beat
python celery_beat.py

# Start FastAPI
python fastapi_app.py
```

## 📊 Monitoring

### Task Status Endpoints
- `GET /tasks/{task_id}/status` - Get task status
- `GET /tasks/workers/stats` - Get worker statistics
- `GET /health` - Platform health check

### Flower (Optional)
```bash
celery -A celery_app flower --port=5555
# Access at: http://localhost:5555
```

## 🧪 Testing

### Run Comprehensive Test
```bash
python test_celery_platform.py
```

### Test Individual Components
```bash
# Test API only
python test_platform.py

# Test Celery platform
python test_celery_platform.py
```

## 🗄️ Database Schema

### Collections
- **users**: User accounts and authentication
- **applications**: Website analysis applications
- **schedules**: Automated analysis schedules
- **analysis_runs**: Analysis execution records
- **analysis_results**: Page analysis results
- **link_validations**: Link validation results
- **change_detections**: Change comparison results

### Celery Integration
- **Task Results**: Stored in Redis with configurable expiration
- **Task Metadata**: Progress, status, and error information
- **Worker Stats**: Real-time worker performance metrics

## 🔒 Security

### Authentication
- JWT-based authentication with Redis session storage
- Password hashing with bcrypt
- Token expiration and refresh

### Task Security
- User-based task isolation
- Application ownership validation
- Secure task parameter passing

## 🎯 Use Cases

### 1. Website Monitoring
- **Automated Health Checks**: Schedule daily/weekly analysis runs
- **Issue Detection**: Monitor broken links, blank pages, and content quality
- **Trend Analysis**: Track website health over time

### 2. SEO Analysis
- **Site Structure Analysis**: Understand navigation depth and page relationships
- **Content Quality**: Identify pages with insufficient content
- **Link Health**: Monitor internal and external link status

### 3. Development Testing
- **Pre-deployment Checks**: Validate website before going live
- **Change Impact Analysis**: Compare before/after deployment results
- **Performance Monitoring**: Track analysis metrics over time

## 📈 Performance

### Scaling
- **Horizontal Scaling**: Add more Celery workers
- **Queue Separation**: Different queues for different task types
- **Load Balancing**: Distribute tasks across workers

### Optimization
- **Task Batching**: Group similar tasks together
- **Result Expiration**: Configure Redis result expiration
- **Worker Concurrency**: Tune worker concurrency settings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the API documentation at `/docs`
- Monitor Celery tasks with Flower
- Review the logs for error details
- Create an issue in the repository

## 🔄 Migration from Basic Version

To migrate from the basic website analysis tool:

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start Redis**: `brew services start redis` or `docker run -d -p 6379:6379 redis:alpine`
3. **Start platform**: `./start.sh`
4. **Create applications**: Use the API to create applications for your websites
5. **Setup schedules**: Configure automated analysis runs

The platform maintains backward compatibility with the existing analysis engine while adding robust task queue and scheduling capabilities with Celery and Redis.





# NOTE: 1. apply wait for lazy loading or page need to be load. 
        2. we need to identify parent link and store parent children relationship using list or mapping
        3. edit option enable in the application 