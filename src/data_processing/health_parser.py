#!/usr/bin/env python3
"""
Apple Health Data Parser

Parses Apple Health export .zip files and extracts health data into structured format.
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import tempfile
import shutil

@dataclass
class HealthRecord:
    """Represents a single health data record."""
    record_type: str
    source: str
    unit: Optional[str]
    value: float
    start_date: datetime
    end_date: Optional[datetime]
    metadata: Dict[str, Any]

class AppleHealthParser:
    """Parser for Apple Health export files."""
    
    def __init__(self, zip_file_path: Path):
        self.zip_file_path = zip_file_path
        self.temp_dir = None
        
    def parse(self) -> List[HealthRecord]:
        """Parse the Apple Health export file and return structured health data."""
        if not self.zip_file_path.exists():
            raise FileNotFoundError(f"Health export file not found: {self.zip_file_path}")
        
        # Extract the zip file to a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        try:
            with zipfile.ZipFile(self.zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # Find the main export.xml file
            xml_file = None
            for file in Path(self.temp_dir).rglob('*.xml'):
                if 'export' in file.name.lower():
                    xml_file = file
                    break
            
            if not xml_file:
                raise FileNotFoundError("Could not find export.xml in the health data archive")
            
            return self._parse_xml(xml_file)
            
        finally:
            # Clean up temporary directory
            if self.temp_dir and Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
    
    def _parse_xml(self, xml_file: Path) -> List[HealthRecord]:
        """Parse the Apple Health XML export file."""
        records = []
        
        try:
            # Parse the XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Find all Record elements - handle both direct children and nested records
            for record_elem in root.findall('.//Record'):
                record = self._parse_record_element(record_elem)
                if record:
                    records.append(record)
            
            # Also look for Workout elements which contain valuable workout data
            for workout_elem in root.findall('.//Workout'):
                workout_record = self._parse_workout_element(workout_elem)
                if workout_record:
                    records.append(workout_record)
            
            return records
            
        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML file: {e}")
    
    def _parse_record_element(self, record_elem) -> Optional[HealthRecord]:
        """Parse a single Record element from the XML."""
        try:
            record_type = record_elem.get('type')
            source = record_elem.get('sourceName', 'Unknown')
            unit = record_elem.get('unit')
            
            # Parse value - try both attribute and child element
            value = None
            value_elem = record_elem.find('Value')
            if value_elem is not None:
                value = float(value_elem.text)
            else:
                # Try to get value from attribute
                value_text = record_elem.get('value')
                if value_text:
                    value = float(value_text)
                else:
                    return None
            
            # Parse dates - try both attributes and child elements
            start_date = None
            end_date = None
            
            # Try child elements first
            start_date_elem = record_elem.find('StartDate')
            end_date_elem = record_elem.find('EndDate')
            
            if start_date_elem is not None:
                start_date = self._parse_apple_date(start_date_elem.text)
                if end_date_elem is not None:
                    end_date = self._parse_apple_date(end_date_elem.text)
            else:
                # Try attributes
                start_date_text = record_elem.get('startDate')
                end_date_text = record_elem.get('endDate')
                
                if start_date_text:
                    start_date = self._parse_apple_date(start_date_text)
                    if end_date_text:
                        end_date = self._parse_apple_date(end_date_text)
                else:
                    return None
            
            # Extract metadata from child elements
            metadata = {}
            for child in record_elem:
                if child.tag not in ['Value', 'StartDate', 'EndDate']:
                    metadata[child.tag] = child.text
            
            # Add source version to metadata if available
            source_version = record_elem.get('sourceVersion')
            if source_version:
                metadata['sourceVersion'] = source_version
            
            # Add device info if available
            device = record_elem.get('device')
            if device:
                metadata['device'] = device
            
            return HealthRecord(
                record_type=record_type,
                source=source,
                unit=unit,
                value=value,
                start_date=start_date,
                end_date=end_date,
                metadata=metadata
            )
            
        except (ValueError, AttributeError) as e:
            # Skip malformed records
            return None
    
    def _parse_workout_element(self, workout_elem) -> Optional[HealthRecord]:
        """Parse a Workout element from the XML."""
        try:
            workout_type = workout_elem.get('workoutActivityType', 'UnknownWorkout')
            source = workout_elem.get('sourceName', 'Unknown')
            
            # Get duration
            duration = float(workout_elem.get('duration', '0'))
            
            # Get start and end dates
            start_date = self._parse_apple_date(workout_elem.get('startDate'))
            end_date = self._parse_apple_date(workout_elem.get('endDate'))
            
            # Create metadata with workout details
            metadata = {
                'workout_type': workout_type,
                'duration': duration,
                'duration_unit': workout_elem.get('durationUnit', 'min'),
                'total_distance': workout_elem.get('totalDistance'),
                'total_distance_unit': workout_elem.get('totalDistanceUnit'),
                'total_energy_burned': workout_elem.get('totalEnergyBurned'),
                'total_energy_burned_unit': workout_elem.get('totalEnergyBurnedUnit')
            }
            
            return HealthRecord(
                record_type=f"Workout:{workout_type}",
                source=source,
                unit=workout_elem.get('durationUnit', 'min'),
                value=duration,
                start_date=start_date,
                end_date=end_date,
                metadata=metadata
            )
            
        except (ValueError, AttributeError) as e:
            # Skip malformed workout records
            return None
    
    def _parse_apple_date(self, date_str: str) -> datetime:
        """Parse Apple's date format into datetime object."""
        # Apple uses ISO 8601 format: YYYY-MM-DD HH:MM:SS ±HH:MM
        try:
            # Remove timezone info for simplicity (we'll handle it properly later)
            clean_date = date_str.split(' ')[0] + ' ' + date_str.split(' ')[1]
            return datetime.strptime(clean_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Fallback to more robust parsing
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))