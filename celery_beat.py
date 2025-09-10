#!/usr/bin/env python3
"""
Celery beat scheduler startup script
"""

import os
import sys
from celery import Celery
from celery_app import celery_app

if __name__ == "__main__":
    # Start Celery beat scheduler
    import subprocess
    import sys
    
    # Run celery beat command directly
    subprocess.run([
        sys.executable, "-m", "celery",
        "-A", "celery_app",
        "beat",
        "--loglevel=info",
        "--schedule=/tmp/celerybeat-schedule",
        "--pidfile=/tmp/celerybeat.pid"
    ])
