#!/usr/bin/env python3
"""
Test Script for Database Functionality

Tests the new SQLite database storage system for Apple Health data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_storage.health_database import HealthDatabase
from data_storage.schema_validator import SchemaValidator

def test_database_functionality():
    """Test the database functionality."""
    print("🧪 Testing Database Functionality...")
    
    # Create a test database
    test_db_path = Path("test_health_data.db")
    if test_db_path.exists():
        test_db_path.unlink()
    
    db = HealthDatabase(test_db_path)
    validator = SchemaValidator()
    
    # Test 1: Insert health records
    print("📊 Test 1: Inserting health records...")
    
    test_records = [
        {
            'record_type': 'HeartRate',
            'source': 'Apple Watch',
            'unit': 'count/min',
            'value': 72.0,
            'start_date': datetime.now() - timedelta(days=1),
            'end_date': datetime.now() - timedelta(days=1),
            'metadata': {'device': 'Watch6,1', 'sourceVersion': '1.0'}
        },
        {
            'record_type': 'StepCount',
            'source': 'iPhone',
            'unit': 'count',
            'value': 5000.0,
            'start_date': datetime.now() - timedelta(days=1),
            'end_date': datetime.now() - timedelta(days=1),
            'metadata': {'device': 'iPhone13,2', 'sourceVersion': '2.0'}
        }
    ]
    
    for record in test_records:
        if validator.validate_health_record(record):
            db.insert_health_record(record)
            print(f"✅ Inserted {record['record_type']} record")
        else:
            print(f"❌ Failed to validate {record['record_type']} record")
    
    # Test 2: Insert workout
    print("🏋️ Test 2: Inserting workout...")
    
    test_workout = {
        'workout_type': 'Running',
        'source': 'Apple Watch',
        'duration': 30.5,
        'duration_unit': 'min',
        'start_date': datetime.now() - timedelta(hours=2),
        'end_date': datetime.now() - timedelta(hours=1, minutes=30),
        'total_distance': 5.2,
        'total_distance_unit': 'km',
        'total_energy_burned': 350,
        'total_energy_burned_unit': 'kcal',
        'metadata': {'device': 'Watch6,1'}
    }
    
    if validator.validate_workout(test_workout):
        db.insert_workout(test_workout)
        print("✅ Inserted workout record")
    else:
        print("❌ Failed to validate workout record")
    
    # Test 3: Query data
    print("🔍 Test 3: Querying data...")
    
    # Get database stats
    stats = db.get_database_stats()
    print(f"📊 Database stats: {stats['total_records']} records, {stats['total_workouts']} workouts")
    
    # Get records by type
    heart_rate_records = db.get_records_by_type('HeartRate')
    print(f"💓 Found {len(heart_rate_records)} HeartRate records")
    
    # Get record types summary
    record_types = db.get_record_types_summary()
    print(f"📋 Found {len(record_types)} record types")
    
    # Get sources summary
    sources = db.get_sources_summary()
    print(f"📱 Found {len(sources)} data sources")
    
    # Test 4: Date range queries
    print("📅 Test 4: Date range queries...")
    
    start_date = datetime.now() - timedelta(days=2)
    end_date = datetime.now()
    
    date_range_records = db.get_records_by_date_range(start_date, end_date)
    print(f"🗓️ Found {len(date_range_records)} records in date range")
    
    # Test 5: Daily aggregates
    print("📈 Test 5: Daily aggregates...")
    
    if record_types:
        sample_type = record_types[0]['type_name']
        daily_agg = db.get_daily_aggregates(sample_type, start_date, end_date)
        print(f"📊 Found {len(daily_agg)} daily aggregates for {sample_type}")
    
    # Test 6: Backup and restore
    print("💾 Test 6: Backup and restore...")
    
    backup_path = Path("test_backup.db")
    db.backup_database(backup_path)
    print("✅ Database backup created")
    
    # Clear and restore
    db.clear_database()
    print("🧹 Database cleared")
    
    db.restore_database(backup_path)
    print("🔄 Database restored")
    
    # Verify restore
    restored_stats = db.get_database_stats()
    if restored_stats['total_records'] == stats['total_records']:
        print("✅ Restore successful - record count matches")
    else:
        print("❌ Restore failed - record count mismatch")
    
    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()
    if backup_path.exists():
        backup_path.unlink()
    
    print("🎉 All database tests completed!")
    return True

def test_schema_validation():
    """Test schema validation functionality."""
    print("📋 Testing Schema Validation...")
    
    validator = SchemaValidator()
    
    # Test valid record
    valid_record = {
        'record_type': 'HeartRate',
        'source': 'Apple Watch',
        'unit': 'count/min',
        'value': 72.0,
        'start_date': datetime.now().isoformat(),
        'metadata': {}
    }
    
    if validator.validate_health_record(valid_record):
        print("✅ Valid record passed validation")
    else:
        print("❌ Valid record failed validation")
    
    # Test invalid record (missing required field)
    invalid_record = {
        'source': 'Apple Watch',
        'value': 72.0,
        'start_date': datetime.now().isoformat()
        # Missing record_type
    }
    
    if not validator.validate_health_record(invalid_record):
        print("✅ Invalid record correctly failed validation")
    else:
        print("❌ Invalid record incorrectly passed validation")
    
    # Test batch validation
    batch_data = {
        'health_records': [valid_record, invalid_record]
    }
    
    results = validator.validate_batch(batch_data)
    print(f"📊 Batch validation: {results['health_records']['valid']} valid, {results['health_records']['invalid']} invalid")
    
    # Save schema
    validator.save_schema(Path("test_schema.json"))
    print("✅ Schema saved successfully")
    
    # Cleanup
    Path("test_schema.json").unlink()
    
    print("🎉 Schema validation tests completed!")
    return True

def main():
    """Run all tests."""
    print("🍏 Apple Health Database Functionality Tests")
    print("=" * 50)
    
    try:
        # Test database functionality
        if test_database_functionality():
            print("\n✅ Database functionality tests passed!")
        else:
            print("\n❌ Database functionality tests failed!")
            return False
        
        # Test schema validation
        if test_schema_validation():
            print("\n✅ Schema validation tests passed!")
        else:
            print("\n❌ Schema validation tests failed!")
            return False
        
        print("\n🎉 All tests passed successfully!")
        print("🚀 The database storage system is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)