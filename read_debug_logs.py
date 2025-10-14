#!/usr/bin/env python3
"""
Script to read and display analysis debug logs
"""

import os
import sys
from datetime import datetime

def read_debug_logs():
    """Read and display the latest debug logs"""
    log_file = "analysis_debug.log"
    
    if not os.path.exists(log_file):
        print("❌ No debug log file found: analysis_debug.log")
        print("Please run an analysis first to generate debug logs.")
        return
    
    print("🔍 Reading Analysis Debug Logs")
    print("=" * 50)
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            print("📝 Debug log file is empty")
            return
        
        print(f"📊 Total log entries: {len(lines)}")
        print(f"📅 Last updated: {datetime.fromtimestamp(os.path.getmtime(log_file))}")
        print()
        
        # Show last 50 lines (most recent)
        recent_lines = lines[-50:] if len(lines) > 50 else lines
        
        print("📋 Recent Debug Log Entries:")
        print("-" * 50)
        
        for line in recent_lines:
            line = line.strip()
            if line:
                # Color code different log levels
                if "ERROR" in line:
                    print(f"🔴 {line}")
                elif "WARNING" in line:
                    print(f"🟡 {line}")
                elif "INFO" in line:
                    print(f"🔵 {line}")
                else:
                    print(f"⚪ {line}")
        
        print()
        print("=" * 50)
        
        # Summary statistics
        error_count = sum(1 for line in lines if "ERROR" in line)
        warning_count = sum(1 for line in lines if "WARNING" in line)
        info_count = sum(1 for line in lines if "INFO" in line)
        
        print("📈 Summary:")
        print(f"   🔴 Errors: {error_count}")
        print(f"   🟡 Warnings: {warning_count}")
        print(f"   🔵 Info: {info_count}")
        
        # Look for specific patterns
        print()
        print("🔍 Key Patterns Found:")
        
        if any("Starting save_results_to_db" in line for line in lines):
            print("   ✅ save_results_to_db was called")
        else:
            print("   ❌ save_results_to_db was NOT called")
        
        if any("Starting source code saving process" in line for line in lines):
            print("   ✅ Source code saving process started")
        else:
            print("   ❌ Source code saving process did NOT start")
        
        if any("Saving source code for START URL" in line for line in lines):
            print("   ✅ Start URL source code was saved")
        else:
            print("   ❌ Start URL source code was NOT saved")
        
        if any("CRITICAL: No source codes were saved" in line for line in lines):
            print("   🚨 CRITICAL: No source codes were saved!")
        
        if any("start_url is None" in line for line in lines):
            print("   🚨 CRITICAL: start_url is None!")
        
    except Exception as e:
        print(f"❌ Error reading debug log: {e}")

if __name__ == "__main__":
    read_debug_logs()
