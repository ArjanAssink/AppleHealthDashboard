#!/usr/bin/env python3
"""
Quick Database Test

A simple test to verify the database system works with sample data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_storage.health_database import HealthDatabase
from data_storage.schema_validator import SchemaValidator

def create_sample_data():
    """Create sample health data for testing."""
    sample_records = []
    
    # Create sample records for the last 7 days
    for days_ago in range(7):
        date = datetime.now() - timedelta(days=days_ago)
        
        # Heart rate data
        sample_records.append({
            'record_type': 'HeartRate',
            'source': 'Apple Watch',
            'unit': 'count/min',
            'value': 65 + (days_ago * 2),
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'metadata': {'device': 'Watch6,1'}
        })
        
        # Step count data
        sample_records.append({
            'record_type': 'StepCount',
            'source': 'iPhone',
            'unit': 'count',
            'value': 5000 + (days_ago * 1000),
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'metadata': {'device': 'iPhone13,2'}
        })
        
        # Active energy
        sample_records.append({
            'record_type': 'ActiveEnergy',
            'source': 'Apple Watch',
            'unit': 'kcal',
            'value': 200 + (days_ago * 50),
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'metadata': {'device': 'Watch6,1'}
        })
    
    # Sample workouts
    sample_workouts = [
        {
            'workout_type': 'Running',
            'source': 'Apple Watch',
            'duration': 30.5,
            'duration_unit': 'min',
            'start_date': (datetime.now() - timedelta(days=1)).isoformat(),
            'end_date': (datetime.now() - timedelta(minutes=30)).isoformat(),
            'total_distance': 5.2,
            'total_distance_unit': 'km',
            'total_energy_burned': 350,
            'total_energy_burned_unit': 'kcal',
            'metadata': {'device': 'Watch6,1'}
        },
        {
            'workout_type': 'Cycling',
            'source': 'Apple Watch',
            'duration': 45.0,
            'duration_unit': 'min',
            'start_date': (datetime.now() - timedelta(days=2)).isoformat(),
            'end_date': (datetime.now() - timedelta(hours=1, minutes=15)).isoformat(),
            'total_distance': 12.5,
            'total_distance_unit': 'km',
            'total_energy_burned': 420,
            'total_energy_burned_unit': 'kcal',
            'metadata': {'device': 'Watch6,1'}
        }
    ]
    
    return sample_records, sample_workouts

def test_database_with_sample_data():
    """Test the database with sample health data."""
    print("🍏 Quick Database Test with Sample Data")
    print("=" * 45)
    
    # Initialize database and validator
    db = HealthDatabase()
    validator = SchemaValidator()
    
    # Clear existing data
    db.clear_database()
    print("🧹 Cleared existing database")
    
    # Create sample data
    sample_records, sample_workouts = create_sample_data()
    print(f"📊 Created {len(sample_records)} sample health records")
    print(f"🏋️ Created {len(sample_workouts)} sample workouts")
    
    # Insert sample records
    records_inserted = 0
    for record in sample_records:
        if validator.validate_health_record(record):
            db.insert_health_record(record)
            records_inserted += 1
    
    print(f"✅ Inserted {records_inserted} health records")
    
    # Insert sample workouts
    workouts_inserted = 0
    for workout in sample_workouts:
        if validator.validate_workout(workout):
            db.insert_workout(workout)
            workouts_inserted += 1
    
    print(f"✅ Inserted {workouts_inserted} workouts")
    
    # Get database statistics
    stats = db.get_database_stats()
    print(f"\n📊 Database Statistics:")
    print(f"   Total Records: {stats['total_records']}")
    print(f"   Total Workouts: {stats['total_workouts']}")
    print(f"   Total Sources: {stats['total_sources']}")
    print(f"   Total Record Types: {stats['total_record_types']}")
    
    if stats['date_range']['start']:
        print(f"   Date Range: {stats['date_range']['start']} to {stats['date_range']['end']}")
    
    # Test queries
    print(f"\n🔍 Testing Database Queries:")
    
    # Get record types
    record_types = db.get_record_types_summary()
    if record_types:
        print(f"   Record Types:")
        for rt in record_types:
            print(f"     • {rt['type_name']}: {rt['record_count']} records ({rt['category']})")
    
    # Get sources
    sources = db.get_sources_summary()
    if sources:
        print(f"   Data Sources:")
        for source in sources:
            print(f"     • {source['name']}: {source['record_count']} records")
    
    # Test time series queries
    print(f"\n📈 Testing Time Series Queries:")
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    for record_type in ['HeartRate', 'StepCount', 'ActiveEnergy']:
        daily_data = db.get_daily_aggregates(record_type, start_date, end_date)
        if daily_data:
            print(f"   • {record_type}: {len(daily_data)} days of data")
            # Show a sample day
            if daily_data:
                sample = daily_data[0]
                print(f"     Sample: {sample['date']} - Avg: {sample['avg_value']:.1f}, Min: {sample['min_value']:.1f}, Max: {sample['max_value']:.1f}")
    
    # Test workout queries
    print(f"\n🏋️ Testing Workout Queries:")
    
    for workout_type in ['Running', 'Cycling']:
        workouts = db.get_workouts_by_type(workout_type)
        if workouts:
            print(f"   • {workout_type}: {len(workouts)} workouts")
            for workout in workouts:
                duration = workout['duration']
                distance = workout.get('total_distance', 'N/A')
                energy = workout.get('total_energy_burned', 'N/A')
                print(f"     - Duration: {duration} min, Distance: {distance}, Energy: {energy} kcal")
    
    # Test date range queries
    print(f"\n📅 Testing Date Range Queries:")
    
    date_range_records = db.get_records_by_date_range(start_date, end_date, 'HeartRate')
    print(f"   • HeartRate records in last 7 days: {len(date_range_records)}")
    
    # Test backup/restore
    print(f"\n💾 Testing Backup/Restore:")
    
    backup_path = Path("test_backup.db")
    db.backup_database(backup_path)
    print(f"   ✅ Backup created")
    
    # Verify backup
    if backup_path.exists():
        print(f"   ✅ Backup file exists: {backup_path.stat().st_size / 1024:.1f} KB")
    
    # Cleanup
    if backup_path.exists():
        backup_path.unlink()
    
    print(f"\n🎉 Database test completed successfully!")
    print(f"💾 Sample data stored in: data/processed/health_data.db")
    
    # Save schema
    validator.save_schema(Path("data/processed/schema.json"))
    print(f"📋 Schema saved to: data/processed/schema.json")
    
    return True

def main():
    """Main test function."""
    try:
        success = test_database_with_sample_data()
        if success:
            print(f"\n✅ Quick database test completed successfully!")
            print(f"🚀 The database system is working perfectly!")
            print(f"\n📊 You can now:")
            print(f"   • Run the full migration: python3 migrate_to_database.py")
            print(f"   • Use the updated dashboard: python3 main.py")
            print(f"   • Explore the database: data/processed/health_data.db")
        else:
            print(f"\n❌ Quick database test failed!")
        
        return success
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)