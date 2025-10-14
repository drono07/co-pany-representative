#!/usr/bin/env python3
"""
Celery worker startup script
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.tasks.celery_app import celery_app

if __name__ == "__main__":
    # Start Celery worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=2",  # Reduced concurrency for better asyncio compatibility
        "--pool=threads",  # Use threads instead of processes for better asyncio support
        "--queues=celery,analysis,notifications,maintenance",  # Queue names
        "--hostname=worker@%h"  # Worker hostname
    ])
