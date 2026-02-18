#!/usr/bin/env python3
"""
Health Database Module

SQLite-based storage for Apple Health data with optimized queries for dashboard generation.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import json
from contextlib import contextmanager

class HealthDatabase:
    """SQLite database for storing and querying Apple Health data."""
    
    def __init__(self, db_path: Union[str, Path] = "data/processed/health_data.db"):
        """Initialize the health database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._ensure_data_directory()
        self._initialize_database()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Main health records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    unit TEXT,
                    value REAL,
                    start_date DATETIME NOT NULL,
                    end_date DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    UNIQUE(record_type, source, start_date, end_date)
                )
            """)
            
            # Workouts table (specialized records)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY,
                    workout_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    duration REAL NOT NULL,
                    duration_unit TEXT DEFAULT 'min',
                    start_date DATETIME NOT NULL,
                    end_date DATETIME NOT NULL,
                    total_distance REAL,
                    total_distance_unit TEXT,
                    total_energy_burned REAL,
                    total_energy_burned_unit TEXT,
                    metadata_json TEXT,
                    FOREIGN KEY (id) REFERENCES health_records(id) ON DELETE CASCADE
                )
            """)
            
            # Sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    version TEXT,
                    device TEXT,
                    first_seen DATETIME,
                    last_seen DATETIME
                )
            """)
            
            # Record types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS record_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    category TEXT,
                    default_unit TEXT
                )
            """)
            
            # Create indexes for performance
            self._create_indexes(conn)
            
            conn.commit()
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create performance indexes."""
        cursor = conn.cursor()
        
        # Indexes for health_records
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_records_type 
            ON health_records(record_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_records_date 
            ON health_records(start_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_records_source 
            ON health_records(source)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_records_type_date 
            ON health_records(record_type, start_date)
        """)
        
        # Indexes for workouts
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workouts_type 
            ON workouts(workout_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workouts_date 
            ON workouts(start_date)
        """)
    
    @contextmanager
    def _get_connection(self) -> sqlite3.Connection:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def insert_health_record(self, record: Dict[str, Any]) -> int:
        """Insert a single health record.
        
        Args:
            record: Health record dictionary
            
        Returns:
            ID of the inserted record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Handle both datetime objects and ISO strings
            start_date_iso = record['start_date']
            if hasattr(record['start_date'], 'isoformat'):
                start_date_iso = record['start_date'].isoformat()
            
            end_date_iso = None
            if record.get('end_date'):
                if hasattr(record['end_date'], 'isoformat'):
                    end_date_iso = record['end_date'].isoformat()
                else:
                    end_date_iso = record['end_date']
            
            cursor.execute("""
                INSERT OR IGNORE INTO health_records 
                (record_type, source, unit, value, start_date, end_date, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record['record_type'],
                record['source'],
                record.get('unit'),
                record['value'],
                start_date_iso,
                end_date_iso,
                json.dumps(record.get('metadata', {}))
            ))
            
            record_id = cursor.lastrowid
            
            # Update sources table
            self._update_source_info(conn, record['source'], record.get('metadata', {}))
            
            # Update record_types table
            self._update_record_type_info(conn, record['record_type'])
            
            conn.commit()
            return record_id
    
    def insert_workout(self, workout: Dict[str, Any]) -> int:
        """Insert a workout record.
        
        Args:
            workout: Workout record dictionary
            
        Returns:
            ID of the inserted workout
        """
        # First insert as a health record
        health_record = {
            'record_type': f"Workout:{workout['workout_type']}",
            'source': workout['source'],
            'unit': workout.get('duration_unit', 'min'),
            'value': workout['duration'],
            'start_date': workout['start_date'],
            'end_date': workout['end_date'],
            'metadata': workout.get('metadata', {})
        }
        
        record_id = self.insert_health_record(health_record)
        
        # Then insert workout-specific data
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Handle both datetime objects and ISO strings
            start_date_iso = workout['start_date']
            if hasattr(workout['start_date'], 'isoformat'):
                start_date_iso = workout['start_date'].isoformat()
            
            end_date_iso = workout['end_date']
            if hasattr(workout['end_date'], 'isoformat'):
                end_date_iso = workout['end_date'].isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO workouts 
                (id, workout_type, source, duration, duration_unit, 
                 start_date, end_date, total_distance, total_distance_unit,
                 total_energy_burned, total_energy_burned_unit, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                workout['workout_type'],
                workout['source'],
                workout['duration'],
                workout.get('duration_unit', 'min'),
                start_date_iso,
                end_date_iso,
                workout.get('total_distance'),
                workout.get('total_distance_unit'),
                workout.get('total_energy_burned'),
                workout.get('total_energy_burned_unit'),
                json.dumps(workout.get('metadata', {}))
            ))
            
            conn.commit()
            return record_id
    
    def _update_source_info(self, conn: sqlite3.Connection, source_name: str, metadata: Dict[str, Any]):
        """Update source information in the sources table."""
        cursor = conn.cursor()
        
        # Get current timestamp
        now = datetime.now().isoformat()
        
        # Check if source exists
        cursor.execute("SELECT id FROM sources WHERE name = ?", (source_name,))
        source_row = cursor.fetchone()
        
        if source_row:
            # Update existing source
            cursor.execute("""
                UPDATE sources 
                SET 
                    version = COALESCE(?, version),
                    device = COALESCE(?, device),
                    last_seen = ?
                WHERE name = ?
            """, (
                metadata.get('sourceVersion'),
                metadata.get('device'),
                now,
                source_name
            ))
        else:
            # Insert new source
            cursor.execute("""
                INSERT INTO sources 
                (name, version, device, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (
                source_name,
                metadata.get('sourceVersion'),
                metadata.get('device'),
                now,
                now
            ))
    
    def _update_record_type_info(self, conn: sqlite3.Connection, record_type: str):
        """Update record type information."""
        cursor = conn.cursor()
        
        # Check if record type exists
        cursor.execute("SELECT id FROM record_types WHERE type_name = ?", (record_type,))
        
        if not cursor.fetchone():
            # Insert new record type
            category = self._infer_category_from_type(record_type)
            cursor.execute("""
                INSERT INTO record_types 
                (type_name, category)
                VALUES (?, ?)
            """, (record_type, category))
    
    def _infer_category_from_type(self, record_type: str) -> str:
        """Infer category from record type name."""
        record_type_lower = record_type.lower()
        
        if any(keyword in record_type_lower for keyword in ['heart', 'pulse', 'blood']):
            return 'Vital Signs'
        elif any(keyword in record_type_lower for keyword in ['step', 'walk', 'run', 'distance']):
            return 'Activity'
        elif any(keyword in record_type_lower for keyword in ['workout', 'exercise']):
            return 'Fitness'
        elif any(keyword in record_type_lower for keyword in ['sleep', 'rest']):
            return 'Sleep'
        elif any(keyword in record_type_lower for keyword in ['nutrition', 'food', 'water']):
            return 'Nutrition'
        else:
            return 'Other'
    
    # Query Methods for Dashboard
    
    def get_records_by_type(self, record_type: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get records by type with pagination.
        
        Args:
            record_type: Type of health record
            limit: Maximum number of records to return
            
        Returns:
            List of health records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM health_records
                WHERE record_type = ?
                ORDER BY start_date DESC
                LIMIT ?
            """, (record_type, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_records_by_date_range(self, start_date: datetime, end_date: datetime,
                                 record_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get records within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            record_type: Optional record type filter
            
        Returns:
            List of health records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if record_type:
                cursor.execute("""
                    SELECT * FROM health_records
                    WHERE record_type = ? AND start_date BETWEEN ? AND ?
                    ORDER BY start_date
                """, (record_type, start_date.isoformat(), end_date.isoformat()))
            else:
                cursor.execute("""
                    SELECT * FROM health_records
                    WHERE start_date BETWEEN ? AND ?
                    ORDER BY start_date
                """, (start_date.isoformat(), end_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_aggregates(self, record_type: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily aggregates for a record type.
        
        Args:
            record_type: Type of health record
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of daily aggregates
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    DATE(start_date) as date,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    COUNT(*) as count
                FROM health_records
                WHERE record_type = ? AND start_date BETWEEN ? AND ?
                GROUP BY DATE(start_date)
                ORDER BY date
            """, (record_type, start_date.isoformat(), end_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_workouts_by_type(self, workout_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get workouts by type.
        
        Args:
            workout_type: Type of workout
            limit: Maximum number of workouts to return
            
        Returns:
            List of workout records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT w.*, hr.unit, hr.value
                FROM workouts w
                JOIN health_records hr ON w.id = hr.id
                WHERE w.workout_type = ?
                ORDER BY w.start_date DESC
                LIMIT ?
            """, (workout_type, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_record_types_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all record types.
        
        Returns:
            List of record type summaries with counts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    rt.type_name,
                    rt.category,
                    COUNT(hr.id) as record_count,
                    MIN(hr.start_date) as first_record,
                    MAX(hr.start_date) as last_record
                FROM record_types rt
                LEFT JOIN health_records hr ON rt.type_name = hr.record_type
                GROUP BY rt.type_name
                ORDER BY record_count DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sources_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all data sources.
        
        Returns:
            List of source summaries with counts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    s.name,
                    s.device,
                    COUNT(hr.id) as record_count,
                    s.first_seen,
                    s.last_seen
                FROM sources s
                LEFT JOIN health_records hr ON s.name = hr.source
                GROUP BY s.name
                ORDER BY record_count DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics.
        
        Returns:
            Dictionary of database statistics
        """
        stats = {
            'total_records': 0,
            'total_workouts': 0,
            'total_sources': 0,
            'total_record_types': 0,
            'date_range': {'start': None, 'end': None}
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get record counts
            cursor.execute("SELECT COUNT(*) FROM health_records")
            stats['total_records'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM workouts")
            stats['total_workouts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sources")
            stats['total_sources'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM record_types")
            stats['total_record_types'] = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute("SELECT MIN(start_date), MAX(start_date) FROM health_records")
            date_range = cursor.fetchone()
            if date_range[0] and date_range[1]:
                stats['date_range'] = {
                    'start': date_range[0],
                    'end': date_range[1]
                }
        
        return stats
    
    def clear_database(self):
        """Clear all data from the database (for testing)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Disable foreign key constraints temporarily
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Delete all data
            cursor.execute("DELETE FROM workouts")
            cursor.execute("DELETE FROM health_records")
            cursor.execute("DELETE FROM sources")
            cursor.execute("DELETE FROM record_types")
            
            # Re-enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            conn.commit()
    
    def backup_database(self, backup_path: Union[str, Path]):
        """Create a backup of the database.
        
        Args:
            backup_path: Path to backup file
        """
        import shutil
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, backup_path)
    
    def restore_database(self, backup_path: Union[str, Path]):
        """Restore database from backup.
        
        Args:
            backup_path: Path to backup file
        """
        import shutil
        backup_path = Path(backup_path)
        if backup_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, self.db_path)