# Website Analysis Platform - API Endpoints Documentation

## Overview
This document provides comprehensive documentation for all API endpoints in the Website Analysis Platform. The API is built with FastAPI and provides endpoints for website analysis, broken link detection, content analysis, and more.

## Base URL
```
http://localhost:8000
```

## Authentication
Most endpoints require Bearer token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

---

## 🔐 Authentication Endpoints

### Register User
```http
POST /auth/register
```
**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword",
  "role": "user"
}
```

### Login User
```http
POST /auth/login
```
**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```
**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

### Get Current User Info
```http
GET /auth/me
```
**Headers:** `Authorization: Bearer <token>`

---

## 📱 Application Management

### Create Application
```http
POST /applications
```
**Request Body:**
```json
{
  "name": "My Website Analysis",
  "description": "Analysis for my main website",
  "website_url": "https://example.com",
  "max_crawl_depth": 2,
  "max_pages_to_crawl": 500,
  "max_links_to_validate": 1500,
  "enable_ai_evaluation": false,
  "max_ai_evaluation_pages": 10
}
```

### Get All Applications
```http
GET /applications
```

### Get Specific Application
```http
GET /applications/{app_id}
```

### Update Application
```http
PUT /applications/{app_id}
PATCH /applications/{app_id}
```

### Delete Application
```http
DELETE /applications/{app_id}
```

---

## 🔍 Analysis Run Endpoints

### Start Analysis Run
```http
POST /applications/{app_id}/runs
```
**Response:**
```json
{
  "message": "Analysis started",
  "run_id": "run_id_here",
  "task_id": "celery_task_id"
}
```

### Get Analysis Runs for Application
```http
GET /applications/{app_id}/runs?limit=10
```

### Get All Analysis Runs (User)
```http
GET /runs?limit=50
```

### Get Specific Analysis Run with Results ⭐ **MAIN ENDPOINT**
```http
GET /runs/{run_id}
```
**Response:**
```json
{
  "run": {
    "id": "run_id",
    "application_id": "app_id",
    "status": "completed",
    "total_pages_analyzed": 45,
    "total_links_found": 234,
    "broken_links_count": 12,
    "blank_pages_count": 3,
    "content_pages_count": 42,
    "overall_score": 85.5
  },
  "results": [
    {
      "id": "result_id",
      "run_id": "run_id",
      "page_url": "https://example.com/page1",
      "page_title": "Page Title",
      "word_count": 1250,
      "page_type": "content",
      "has_header": true,
      "has_footer": true,
      "has_navigation": true,
      "html_structure": {...},
      "path": ["https://example.com", "https://example.com/page1"],
      "crawled_at": "2025-01-10T10:30:00Z"
    }
  ],
  "link_validations": [
    {
      "id": "link_id",
      "run_id": "run_id",
      "url": "https://example.com/broken-link",
      "status_code": 404,
      "status": "broken",
      "response_time": 1.2,
      "error_message": "Not Found"
    }
  ],
  "change_detection": {
    "id": "change_id",
    "run_id": "run_id",
    "previous_run_id": "previous_run_id",
    "new_pages_count": 5,
    "removed_pages_count": 2,
    "modified_pages_count": 8,
    "unchanged_pages_count": 30,
    "changes_summary": {...}
  }
}
```

### Delete Analysis Run
```http
DELETE /runs/{run_id}
```

---

## 🔗 Broken Links & Link Analysis

### Get Broken Link Details ⭐ **BROKEN LINKS ENDPOINT**
```http
GET /runs/{run_id}/broken-links/details?broken_url={url_encoded_broken_url}
```
**Response:**
```json
{
  "url": "https://example.com/broken-link",
  "status": "broken",
  "status_code": 404,
  "parent_url": "https://example.com/parent-page",
  "parent_title": "Parent Page Title",
  "navigation_path": [
    "https://example.com",
    "https://example.com/parent-page",
    "https://example.com/broken-link"
  ],
  "error_message": "Not Found",
  "response_time": 1.2
}
```

### Get Page Source Code ⭐ **HTML PARSED CONTENT ENDPOINT** (HIERARCHICAL OPTIMIZATION)
```http
GET /runs/{run_id}/source-code?page_url={url_encoded_page_url}
```
**Response:**
```json
{
  "page_url": "https://example.com/deep/page",
  "source_code": "<html><head><title>Page Title</title></head><body>...</body></html>",
  "parent_url": "https://example.com/deep",
  "highlighted_links": [
    {
      "url": "https://example.com/broken-link",
      "start": 1250,
      "end": 1285,
      "type": "broken",
      "status_code": 404,
      "status": "broken"
    }
  ],
  "created_at": "2025-01-10T10:30:00Z",
  "actual_source_page": "https://example.com/parent",
  "is_source_from_parent": true,
  "traversal_path": [
    "https://example.com/deep/page",
    "https://example.com/deep",
    "https://example.com/parent"
  ],
  "hierarchy_depth": 2
}
```

**Hierarchical Optimization Notes:**
- ✅ **Smart Storage**: HTML source code is stored only for pages that have children (at any depth)
- ✅ **Hierarchical Retrieval**: Leaf pages automatically get source code from their nearest parent via traversal
- ✅ **Multi-Level Support**: Handles complex hierarchies (depth 2, 3, 4, 5, 6+)
- ✅ **No Duplication**: Eliminates redundant storage of identical HTML content across the entire hierarchy
- ✅ **Transparent**: API returns the same data structure regardless of storage optimization
- ✅ **Traversal Tracking**: Shows the path taken to find source code and hierarchy depth

### Get Parent-Child Relationships ⭐ **PARENT LINK FETCH ENDPOINT**
```http
GET /runs/{run_id}/parent-child-relationships
```
**Response:**
```json
{
  "parent_map": {
    "https://example.com/page1": "https://example.com",
    "https://example.com/page2": "https://example.com/page1"
  },
  "children_map": {
    "https://example.com": [
      "https://example.com/page1",
      "https://example.com/page2"
    ]
  },
  "path_map": {
    "https://example.com/page1": [
      "https://example.com",
      "https://example.com/page1"
    ]
  },
  "start_url": "https://example.com",
  "statistics": {
    "total_pages": 45,
    "total_relationships": 89
  }
}
```

---

## 📊 Dashboard & Statistics

### Get Dashboard Stats
```http
GET /dashboard
```
**Response:**
```json
{
  "total_applications": 5,
  "total_runs": 25,
  "active_schedules": 3,
  "recent_runs": [...],
  "top_issues": {
    "broken_links": 45,
    "blank_pages": 12,
    "slow_pages": 8
  }
}
```

---

## 🔄 Content Analysis & Comparison

### Run Content Analysis
```http
POST /runs/{run_id}/content-analysis
```

### Get Content Analysis Status
```http
GET /runs/{run_id}/content-analysis/{task_id}
```

### Get Context Comparison
```http
GET /runs/{run_id}/context-comparison
```

### Get Content Comparison Between Runs
```http
GET /runs/{run_id}/content-comparison/{previous_run_id}
```

### Export Analysis Results to JSON ⭐ **DEBUGGING ENDPOINT**
```http
POST /runs/{run_id}/export-json
```
**Provides:** Complete analysis results exported to JSON file for debugging and verification

**Response:**
```json
{
  "message": "Analysis results exported successfully",
  "filepath": "analysis_exports/analysis_export_68c09399ba11031ffd966a94_20250910_062822.json",
  "run_id": "68c09399ba11031ffd966a94",
  "exported_at": "2025-01-10T10:30:00Z"
}
```

**JSON Export Contents:**
- ✅ Complete analysis run data
- ✅ All analyzed pages with metadata
- ✅ All link validations (broken/valid)
- ✅ Parent-child relationships
- ✅ Change detection data
- ✅ **HTML source codes for all pages** (raw HTML content) - **HIERARCHICAL OPTIMIZATION**: Only stored for pages with children, leaf pages get source via parent traversal
- ✅ Statistics and breakdowns
- ✅ Page types breakdown (content/blank/error)
- ✅ Link status breakdown (valid/broken/redirect)

---

## ⏰ Scheduling

### Create Schedule
```http
POST /applications/{app_id}/schedules
```
**Request Body:**
```json
{
  "frequency": "daily",
  "cron_expression": "0 9 * * *",
  "is_active": true,
  "next_run": "2025-01-11T09:00:00Z"
}
```

### Get Application Schedules
```http
GET /applications/{app_id}/schedules
```

---

## 🔧 Task Management

### Get Task Status
```http
GET /tasks/{task_id}/status
```
**Response:**
```json
{
  "task_id": "task_id",
  "status": "SUCCESS",
  "result": {...},
  "info": {...},
  "ready": true,
  "successful": true,
  "failed": false
}
```

### Get Worker Statistics
```http
GET /tasks/workers/stats
```

---

## 🏥 Health & System

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T10:30:00Z"
}
```

### API Documentation
```http
GET /docs
```
Interactive Swagger UI documentation

```http
GET /redoc
```
Alternative ReDoc documentation

---

## 🎯 **RECOMMENDED ENDPOINTS FOR FRONTEND**

Based on your requirements, here are the **key endpoints** that provide maximum information:

### 1. **Main Analysis Results** ⭐
```http
GET /runs/{run_id}
```
**Provides:** Complete analysis results including:
- Broken links count and details
- Blank pages count and details  
- HTML parsed content for all pages
- Parent-child relationships
- Link validations with status codes

### 2. **Broken Links Details** ⭐
```http
GET /runs/{run_id}/broken-links/details?broken_url={url}
```
**Provides:** Detailed broken link information including parent page and navigation path

### 3. **Source Code with Highlighted Links** ⭐
```http
GET /runs/{run_id}/source-code?page_url={url}
```
**Provides:** Raw HTML source code with broken links highlighted

### 4. **Parent-Child Relationships** ⭐
```http
GET /runs/{run_id}/parent-child-relationships
```
**Provides:** Complete parent-child mapping and navigation paths

---

## 📝 **Data Structure Summary**

### Broken Links
- **Status:** `broken`, `valid`, `redirect`, `timeout`, `rate_limited`, `unknown`
- **Status Codes:** HTTP response codes (404, 500, etc.)
- **Parent Information:** Which page contains the broken link
- **Navigation Path:** Full path from root to the broken link

### Blank Pages
- **Page Type:** `blank`, `content`, `error`, `redirect`
- **Word Count:** Number of words on the page
- **HTML Structure:** Parsed HTML structure information

### HTML Parsed Content
- **Raw Source Code:** Complete HTML source
- **Highlighted Links:** Broken links highlighted in the source
- **Parent URL:** Source page where the link was found
- **Metadata:** Creation timestamp and other details

### Parent Link Information
- **Parent Map:** Direct parent for each URL
- **Children Map:** All children for each parent URL
- **Path Map:** Complete navigation path for each URL
- **Start URL:** Root URL of the analysis

---

## 🔧 **Usage Examples**

### Get All Broken Links for a Run
```javascript
// 1. Get main analysis results
const response = await fetch(`/runs/${runId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// 2. Filter broken links
const brokenLinks = data.link_validations.filter(link => link.status === 'broken');

// 3. Get details for each broken link
for (const link of brokenLinks) {
  const details = await fetch(`/runs/${runId}/broken-links/details?broken_url=${encodeURIComponent(link.url)}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const linkDetails = await details.json();
  console.log(linkDetails);
}
```

### Get Source Code for a Page
```javascript
const sourceResponse = await fetch(`/runs/${runId}/source-code?page_url=${encodeURIComponent(pageUrl)}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const sourceData = await sourceResponse.json();
console.log(sourceData.source_code); // Raw HTML
console.log(sourceData.highlighted_links); // Broken links highlighted
```

### Get Parent-Child Relationships
```javascript
const relationshipsResponse = await fetch(`/runs/${runId}/parent-child-relationships`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const relationships = await relationshipsResponse.json();
console.log(relationships.parent_map); // Direct parents
console.log(relationships.children_map); // All children
console.log(relationships.path_map); // Navigation paths
```

---

## 🚀 **Quick Start**

1. **Register/Login** to get access token
2. **Create Application** for your website
3. **Start Analysis Run** to begin crawling
4. **Get Results** using the main endpoint
5. **Drill Down** into specific broken links, source code, or relationships

The API provides comprehensive website analysis data with a focus on broken links, blank pages, HTML content, and parent-child relationships as requested.
