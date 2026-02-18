#!/usr/bin/env python3
"""
Apple Health Dashboard - Main Entry Point

This script processes Apple Health export data and generates a dashboard
with health metrics, trends, and insights.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_processing.health_parser import AppleHealthParser
from visualization.dashboard import generate_dashboard
from utils.config_manager import load_config, save_config
from data_storage.health_database import HealthDatabase

def main() -> None:
    """Main entry point for the Apple Health Dashboard."""
    print("🍏 Apple Health Dashboard")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    
    # Check if health data directory exists and has files
    data_dir = Path("data/health_exports")
    if not data_dir.exists():
        print(f"❌ Health data directory not found: {data_dir}")
        print("Please place your Apple Health export .zip file in this directory.")
        return
    
    # Find the most recent export file
    export_files = list(data_dir.glob("*.zip"))
    if not export_files:
        print("❌ No Apple Health export .zip files found in data/health_exports/")
        print("Please export your health data from the Apple Health app and place the .zip file here.")
        return
    
    # Use the most recent file
    export_file = max(export_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 Using health export: {export_file.name}")
    
    try:
        # Parse the health data and store in database
        print("🔍 Parsing health data...")
        parser = AppleHealthParser(export_file)
        health_db = parser.parse()
        
        # Show database stats
        stats = health_db.get_database_stats()
        print(f"📊 Database stats: {stats['total_records']} records, {stats['total_workouts']} workouts")
        
        # Generate dashboard using database
        print("📊 Generating dashboard...")
        generate_dashboard(health_db, config)
        
        print("✅ Dashboard generation complete!")
        print("📈 Open the generated HTML files in your browser to view your health data.")
        
    except Exception as e:
        print(f"❌ Error processing health data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()