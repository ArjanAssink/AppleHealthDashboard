#!/usr/bin/env python3
"""
JSON Schema Validator for Health Data

Validates Apple Health data against JSON schema to ensure data quality and consistency.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from jsonschema import validate, ValidationError, Draft7Validator

class SchemaValidator:
    """Validator for Apple Health data using JSON Schema."""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize the schema validator.
        
        Args:
            schema_path: Path to JSON schema file. If None, uses default schema.
        """
        if schema_path and schema_path.exists():
            with open(schema_path) as f:
                self.schema = json.load(f)
        else:
            self.schema = self._get_default_schema()
        
        self.validator = Draft7Validator(self.schema)
    
    def _get_default_schema(self) -> Dict[str, Any]:
        """Get the default JSON schema for health data."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Apple Health Data Schema",
            "description": "Schema for validating Apple Health export data",
            "type": "object",
            "properties": {
                "health_records": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "record_type": {"type": "string", "minLength": 1},
                            "source": {"type": "string", "minLength": 1},
                            "unit": {"type": ["string", "null"]},
                            "value": {"type": "number"},
                            "start_date": {"type": "string", "format": "date-time"},
                            "end_date": {"type": ["string", "null"], "format": "date-time"},
                            "metadata": {"type": "object"}
                        },
                        "required": ["record_type", "source", "value", "start_date"]
                    }
                },
                "workouts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "workout_type": {"type": "string", "minLength": 1},
                            "source": {"type": "string", "minLength": 1},
                            "duration": {"type": "number", "minimum": 0},
                            "duration_unit": {"type": "string", "default": "min"},
                            "start_date": {"type": "string", "format": "date-time"},
                            "end_date": {"type": "string", "format": "date-time"},
                            "total_distance": {"type": ["number", "null"]},
                            "total_distance_unit": {"type": ["string", "null"]},
                            "total_energy_burned": {"type": ["number", "null"]},
                            "total_energy_burned_unit": {"type": ["string", "null"]},
                            "metadata": {"type": "object"}
                        },
                        "required": ["workout_type", "source", "duration", "start_date", "end_date"]
                    }
                }
            },
            "additionalProperties": False
        }
    
    def validate_health_record(self, record: Dict[str, Any]) -> bool:
        """Validate a single health record.
        
        Args:
            record: Health record dictionary
            
        Returns:
            True if valid, False if invalid
        """
        try:
            validate(instance=record, schema=self.schema["properties"]["health_records"]["items"])
            return True
        except ValidationError as e:
            print(f"❌ Health record validation error: {e.message}")
            return False
    
    def validate_workout(self, workout: Dict[str, Any]) -> bool:
        """Validate a single workout record.
        
        Args:
            workout: Workout record dictionary
            
        Returns:
            True if valid, False if invalid
        """
        try:
            validate(instance=workout, schema=self.schema["properties"]["workouts"]["items"])
            return True
        except ValidationError as e:
            print(f"❌ Workout validation error: {e.message}")
            return False
    
    def validate_batch(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a batch of health data.
        
        Args:
            data: Dictionary containing health_records and/or workouts arrays
            
        Returns:
            Dictionary with validation results and error details
        """
        results = {
            'valid': True,
            'health_records': {'valid': 0, 'invalid': 0, 'errors': []},
            'workouts': {'valid': 0, 'invalid': 0, 'errors': []}
        }
        
        # Validate health records
        if 'health_records' in data:
            for i, record in enumerate(data['health_records']):
                if self.validate_health_record(record):
                    results['health_records']['valid'] += 1
                else:
                    results['health_records']['invalid'] += 1
                    results['valid'] = False
        
        # Validate workouts
        if 'workouts' in data:
            for i, workout in enumerate(data['workouts']):
                if self.validate_workout(workout):
                    results['workouts']['valid'] += 1
                else:
                    results['workouts']['invalid'] += 1
                    results['valid'] = False
        
        return results
    
    def get_validation_errors(self, data: Dict[str, Any]) -> List[str]:
        """Get detailed validation errors for a data batch.
        
        Args:
            data: Dictionary containing health data
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate health records
        if 'health_records' in data:
            for i, record in enumerate(data['health_records']):
                try:
                    validate(instance=record, schema=self.schema["properties"]["health_records"]["items"])
                except ValidationError as e:
                    errors.append(f"Health record {i}: {e.message} (path: {e.path})")
        
        # Validate workouts
        if 'workouts' in data:
            for i, workout in enumerate(data['workouts']):
                try:
                    validate(instance=workout, schema=self.schema["properties"]["workouts"]["items"])
                except ValidationError as e:
                    errors.append(f"Workout {i}: {e.message} (path: {e.path})")
        
        return errors
    
    def save_schema(self, schema_path: Path):
        """Save the current schema to a file.
        
        Args:
            schema_path: Path to save the schema
        """
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        with open(schema_path, 'w') as f:
            json.dump(self.schema, f, indent=2)
        print(f"✅ Schema saved to {schema_path}")
    
    def update_schema(self, new_schema: Dict[str, Any]):
        """Update the current schema.
        
        Args:
            new_schema: New schema dictionary
        """
        self.schema = new_schema
        self.validator = Draft7Validator(self.schema)
        print("✅ Schema updated")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the current schema.
        
        Returns:
            Current JSON schema
        """
        return self.schema