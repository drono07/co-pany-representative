#!/usr/bin/env python3
"""
Celery beat scheduler startup script
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.tasks.celery_app import celery_app

if __name__ == "__main__":
    # Start Celery beat scheduler
    import subprocess
    
    # Run celery beat command directly
    subprocess.run([
        sys.executable, "-m", "celery",
        "-A", "backend.tasks.celery_app",
        "beat",
        "--loglevel=info",
        "--schedule=/tmp/celerybeat-schedule",
        "--pidfile=/tmp/celerybeat.pid"
    ])
