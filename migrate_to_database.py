#!/usr/bin/env python3
"""
Migration Script: Convert Existing Health Data to Database Format

This script migrates existing health data from the old in-memory format to the new SQLite database format.
"""

import sys
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_processing.health_parser import HealthRecord, AppleHealthParser
from data_storage.health_database import HealthDatabase
from data_storage.schema_validator import SchemaValidator

def migrate_existing_data():
    """Migrate existing health data to database format."""
    print("🚀 Starting migration to database format...")
    
    # Check if we have existing export files
    data_dir = Path("data/health_exports")
    if not data_dir.exists():
        print("❌ No health exports directory found. Nothing to migrate.")
        return False
    
    export_files = list(data_dir.glob("*.zip"))
    if not export_files:
        print("❌ No Apple Health export files found. Nothing to migrate.")
        return False
    
    print(f"📁 Found {len(export_files)} export files to migrate")
    
    # Initialize database and validator
    db = HealthDatabase()
    validator = SchemaValidator()
    
    # Clear existing database (start fresh)
    db.clear_database()
    print("🧹 Cleared existing database")
    
    # Process each export file
    for i, export_file in enumerate(export_files, 1):
        print(f"📊 Processing file {i}/{len(export_files)}: {export_file.name}")
        
        try:
            # Use the old parser to get HealthRecord objects
            parser = AppleHealthParser(export_file)
            
            # We need to access the internal parsing method to get records
            # This is a bit hacky but necessary for migration
            temp_dir = None
            try:
                import zipfile
                import tempfile
                import shutil
                import xml.etree.ElementTree as ET
                
                # Extract the zip file
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(export_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find the main export.xml file
                xml_file = None
                for file in Path(temp_dir).rglob('*.xml'):
                    if 'export' in file.name.lower():
                        xml_file = file
                        break
                
                if not xml_file:
                    print(f"⚠️ Could not find export.xml in {export_file.name}")
                    continue
                
                # Parse XML and store records
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                records_processed = 0
                workouts_processed = 0
                
                # Process Record elements
                for record_elem in root.findall('.//Record'):
                    try:
                        record = parser._parse_record_element(record_elem)
                        if record:
                            # Convert to dict and validate
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
                        print(f"⚠️ Error processing record: {e}")
                        continue
                
                # Process Workout elements
                for workout_elem in root.findall('.//Workout'):
                    try:
                        workout_record = parser._parse_workout_element(workout_elem)
                        if workout_record:
                            # Convert to dict and validate
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
                        print(f"⚠️ Error processing workout: {e}")
                        continue
                
                print(f"✅ Processed {records_processed} records and {workouts_processed} workouts from {export_file.name}")
                
            finally:
                # Clean up temporary directory
                if temp_dir and Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            print(f"❌ Error processing {export_file.name}: {e}")
            continue
    
    # Get final statistics
    stats = db.get_database_stats()
    print(f"🎉 Migration complete!")
    print(f"📊 Final database stats:")
    print(f"   - Total records: {stats['total_records']}")
    print(f"   - Total workouts: {stats['total_workouts']}")
    print(f"   - Total sources: {stats['total_sources']}")
    print(f"   - Total record types: {stats['total_record_types']}")
    print(f"   - Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")
    
    # Save schema for reference
    validator.save_schema(Path("data/processed/schema.json"))
    
    return True

def main():
    """Main migration function."""
    print("🍏 Apple Health Data Migration Tool")
    print("=" * 50)
    
    try:
        success = migrate_existing_data()
        if success:
            print("\n✅ Migration completed successfully!")
            print("💾 Your health data is now stored in: data/processed/health_data.db")
            print("📋 Schema saved to: data/processed/schema.json")
            print("\n🚀 You can now use the updated dashboard with database support!")
        else:
            print("❌ Migration completed with no data processed.")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()