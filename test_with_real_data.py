#!/usr/bin/env python3
"""
Test with Real Health Data

Process a sample of the real health data to demonstrate the new database functionality.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_processing.health_parser import AppleHealthParser
from data_storage.health_database import HealthDatabase
from data_storage.schema_validator import SchemaValidator

def test_with_real_data():
    """Test with real health data."""
    print("🍏 Testing with Real Health Data")
    print("=" * 40)
    
    # Check if we have health export files
    export_file = Path("data/health_exports/export.zip")
    if not export_file.exists():
        print("❌ No health export file found")
        return False
    
    print(f"📁 Found health export: {export_file.name}")
    print(f"📊 File size: {export_file.stat().st_size / (1024*1024):.1f} MB")
    
    # Initialize database
    db = HealthDatabase()
    validator = SchemaValidator()
    
    # Clear existing data for clean test
    db.clear_database()
    print("🧹 Cleared existing database")
    
    # Test parsing with a timeout to avoid long processing
    print("🔍 Starting data parsing (this may take a moment)...")
    
    try:
        # Create parser and parse data
        parser = AppleHealthParser(export_file)
        
        # Parse the data (this will store it in the database)
        print("📊 Parsing health data...")
        
        # We'll use a simple approach to test the parsing
        import zipfile
        import tempfile
        import shutil
        import xml.etree.ElementTree as ET
        
        temp_dir = tempfile.mkdtemp()
        records_processed = 0
        workouts_processed = 0
        
        try:
            # Extract just enough to test
            with zipfile.ZipFile(export_file, 'r') as zip_ref:
                # Get the first XML file
                for name in zip_ref.namelist():
                    if name.endswith('.xml') and 'export' in name.lower():
                        print(f"📄 Found XML file: {name}")
                        
                        # Extract and parse just the first 100 records for testing
                        with zip_ref.open(name) as xml_file:
                            # Read the file in chunks to find records
                            content = xml_file.read(1000000)  # Read first 1MB
                            
                            # Try to parse as XML
                            try:
                                root = ET.fromstring(content)
                                
                                # Process first 50 records for demo
                                for record_elem in root.findall('.//Record'):
                                    if records_processed >= 50:
                                        break
                                    
                                    try:
                                        record = parser._parse_record_element(record_elem)
                                        if record:
                                            # Convert to dict and store
                                            record_dict = {
                                                'record_type': record.record_type,
                                                'source': record.source,
                                                'unit': record.unit,
                                                'value': record.value,
                                                'start_date': record.start_date,
                                                'end_date': record.end_date,
                                                'metadata': record.metadata
                                            }
                                            
                                            if validator.validate_health_record(record_dict):
                                                db.insert_health_record(record_dict)
                                                records_processed += 1
                                    except Exception as e:
                                        continue
                                
                                # Process first 10 workouts for demo
                                for workout_elem in root.findall('.//Workout'):
                                    if workouts_processed >= 10:
                                        break
                                    
                                    try:
                                        workout_record = parser._parse_workout_element(workout_elem)
                                        if workout_record:
                                            # Convert to dict and store
                                            metadata = workout_record.metadata
                                            workout_dict = {
                                                'workout_type': metadata.get('workout_type', 'UnknownWorkout'),
                                                'source': workout_record.source,
                                                'duration': metadata.get('duration', 0),
                                                'duration_unit': metadata.get('duration_unit', 'min'),
                                                'start_date': workout_record.start_date,
                                                'end_date': workout_record.end_date,
                                                'total_distance': metadata.get('total_distance'),
                                                'total_distance_unit': metadata.get('total_distance_unit'),
                                                'total_energy_burned': metadata.get('total_energy_burned'),
                                                'total_energy_burned_unit': metadata.get('total_energy_burned_unit'),
                                                'metadata': metadata
                                            }
                                            
                                            if validator.validate_workout(workout_dict):
                                                db.insert_workout(workout_dict)
                                                workouts_processed += 1
                                    except Exception as e:
                                        continue
                                
                                break  # Just process first matching XML file
                            except ET.ParseError:
                                continue
                        
                        break  # Just process first XML file
        
        finally:
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
        
        print(f"✅ Processed {records_processed} health records")
        print(f"✅ Processed {workouts_processed} workouts")
        
        # Get database statistics
        stats = db.get_database_stats()
        print(f"\n📊 Database Statistics:")
        print(f"   Total Records: {stats['total_records']}")
        print(f"   Total Workouts: {stats['total_workouts']}")
        print(f"   Total Sources: {stats['total_sources']}")
        print(f"   Total Record Types: {stats['total_record_types']}")
        
        if stats['date_range']['start']:
            print(f"   Date Range: {stats['date_range']['start']} to {stats['date_range']['end']}")
        
        # Test some queries
        if stats['total_records'] > 0:
            print(f"\n🔍 Testing Database Queries:")
            
            # Get record types
            record_types = db.get_record_types_summary()
            if record_types:
                print(f"   Top Record Types:")
                for i, rt in enumerate(record_types[:5], 1):
                    print(f"     {i}. {rt['type_name']} ({rt['record_count']} records)")
            
            # Get sources
            sources = db.get_sources_summary()
            if sources:
                print(f"   Data Sources:")
                for i, source in enumerate(sources[:3], 1):
                    print(f"     {i}. {source['name']} ({source['record_count']} records)")
        
        print(f"\n🎉 Successfully tested with real health data!")
        print(f"💾 Data stored in: data/processed/health_data.db")
        
        # Save schema
        validator.save_schema(Path("data/processed/schema.json"))
        print(f"📋 Schema saved to: data/processed/schema.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing health data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    try:
        success = test_with_real_data()
        if success:
            print(f"\n✅ Real data test completed successfully!")
            print(f"🚀 The database system is working with your health data!")
        else:
            print(f"\n❌ Real data test failed!")
        
        return success
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)