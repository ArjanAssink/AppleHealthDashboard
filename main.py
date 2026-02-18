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
from data_processing.health_exporter import HealthDataExporter
from visualization.html_dashboard import generate_html_dashboard
from utils.config_manager import load_config, save_config

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
        # Parse the health data
        print("🔍 Parsing health data...")
        parser = AppleHealthParser(export_file)
        health_data = parser.parse()
        
        # Export structured JSON data files for the HTML dashboard
        output_dir = Path("output")
        print("📦 Exporting structured JSON data files...")
        exporter = HealthDataExporter(health_data, output_dir)
        exporter.export()

        # Generate the interactive HTML dashboard
        print("🌐 Generating interactive HTML dashboard...")
        dashboard_path = generate_html_dashboard(output_dir)

        print("✅ Dashboard generation complete!")
        print(f"📈 Open {dashboard_path} in your browser to view your health data.")
        
    except Exception as e:
        print(f"❌ Error processing health data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()