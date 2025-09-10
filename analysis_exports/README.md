# Analysis Exports Directory

This directory contains JSON exports of analysis results for debugging and verification purposes.

## 📁 File Naming Convention

Files are named using the following pattern:
```
analysis_export_{run_id}_{timestamp}.json
```

Example:
```
analysis_export_68c09399ba11031ffd966a94_20250910_062822.json
```

## 📊 What's Included in Each Export

Each JSON file contains complete analysis results:

### 🔍 **Analysis Run Data**
- Run ID, status, timestamps
- Total pages analyzed, links found
- Broken links count, blank pages count
- Overall website score

### 📄 **Page Analysis Results**
- All analyzed pages with metadata
- Page titles, word counts, page types
- HTML structure information
- Navigation paths

### 🔗 **Link Validations**
- All discovered links with status codes
- Response times and error messages
- Broken links, valid links, redirects
- Timeout and rate-limited links

### 🌐 **Parent-Child Relationships**
- Complete navigation mapping
- Parent-child URL relationships
- Navigation paths from root to each page
- Start URL information

### 📈 **Statistics & Breakdowns**
- Page types breakdown (content/blank/error/redirect)
- Link status breakdown (valid/broken/redirect/timeout)
- Overall website health metrics

## 🚀 **How to Use**

### Automatic Export
JSON files are automatically created when analysis runs complete successfully.

### Manual Export via API
```bash
POST /runs/{run_id}/export-json
```

### Manual Export via Script
```bash
python -c "
import asyncio
from database_schema import DatabaseManager

async def export():
    db = DatabaseManager()
    await db.connect()
    filepath = await db.export_analysis_results_to_json('your_run_id')
    print(f'Exported to: {filepath}')
    await db.disconnect()

asyncio.run(export())
"
```

## 🔧 **Debugging Use Cases**

1. **Verify Backend Data**: Check if all expected data is being saved correctly
2. **Frontend Issues**: Compare JSON data with what frontend displays
3. **Data Validation**: Ensure broken links, blank pages are correctly identified
4. **Performance Analysis**: Review analysis results and statistics
5. **API Testing**: Use as reference data for API endpoint testing

## 📋 **File Structure Example**

```json
{
  "export_info": {
    "run_id": "68c09399ba11031ffd966a94",
    "exported_at": "2025-01-10T10:30:00Z",
    "export_version": "1.0",
    "description": "Complete analysis results export for debugging and verification"
  },
  "analysis_run": { /* Run metadata */ },
  "application": { /* Application details */ },
  "analysis_results": { /* All pages analyzed */ },
  "link_validations": { /* All link validations */ },
  "parent_child_relationships": { /* Navigation mapping */ },
  "change_detection": { /* Change detection data */ },
  "statistics": { /* Overall statistics */ },
  "page_types_breakdown": { /* Pages by type */ },
  "link_status_breakdown": { /* Links by status */ }
}
```

## 🧹 **Cleanup**

Old export files can be safely deleted to save disk space. The system will create new exports for each analysis run.

## 📝 **Notes**

- Files are created in UTF-8 encoding
- Large websites may generate large JSON files (several MB)
- Files include all data needed for complete analysis verification
- Use these files to debug discrepancies between backend and frontend
