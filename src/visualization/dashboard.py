#!/usr/bin/env python3
"""
Apple Health Dashboard Visualization

Generates visualizations and HTML dashboard from parsed health data.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter

from data_processing.health_parser import HealthRecord
from data_storage.health_database import HealthDatabase
from typing import Union
from .interactive_dashboard import generate_interactive_dashboard

def generate_dashboard(health_data: Union[List[HealthRecord], HealthDatabase], config: Dict[str, Any]) -> None:
    """Generate a comprehensive health dashboard from health data.
    
    Args:
        health_data: Either a list of HealthRecord objects or a HealthDatabase instance
        config: Configuration dictionary
    """
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Handle both old and new data formats
    if isinstance(health_data, HealthDatabase):
        print(f"📊 Processing data from database...")
        db = health_data
        
        # Generate both traditional and interactive dashboards
        _generate_database_dashboard(db, output_dir, config)
        generate_interactive_dashboard(db, output_dir)
    else:
        # Legacy support for old format
        print(f"📊 Processing {len(health_data)} health records (legacy format)...")
        df = _records_to_dataframe(health_data)
        
        if df.empty:
            print("⚠️ No health data found to visualize")
            return
        
        # Generate summary statistics
        _generate_summary_stats(df, output_dir)
        
        # Generate time series visualizations for key metrics
        _generate_time_series_plots(df, output_dir)
        
        # Generate category distributions
        _generate_category_distributions(df, output_dir)
        
        # Generate HTML dashboard
        _generate_html_dashboard(output_dir)
    
    print(f"✅ Dashboard generated in: {output_dir.absolute()}")

def _records_to_dataframe(records: List[HealthRecord]) -> pd.DataFrame:
    """Convert health records to pandas DataFrame."""
    if not records:
        return pd.DataFrame()
    
    data = []
    for record in records:
        data.append({
            'type': record.record_type,
            'source': record.source,
            'unit': record.unit,
            'value': record.value,
            'start_date': record.start_date,
            'end_date': record.end_date,
            **record.metadata
        })
    
    return pd.DataFrame(data)

def _generate_summary_stats(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate summary statistics for the health data."""
    stats = {
        'total_records': len(df),
        'date_range': {
            'start': df['start_date'].min(),
            'end': df['start_date'].max()
        },
        'unique_types': df['type'].nunique(),
        'sources': df['source'].value_counts().to_dict(),
        'records_by_type': df['type'].value_counts().head(20).to_dict()
    }
    
    # Save stats as JSON
    stats_file = output_dir / "summary_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    print(f"📈 Generated summary statistics: {stats_file}")

def _generate_time_series_plots(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate time series plots for key health metrics."""
    
    # Create time series directory
    ts_dir = output_dir / "time_series"
    ts_dir.mkdir(exist_ok=True)
    
    # Group by date and type
    df['date'] = df['start_date'].dt.date
    
    # Get top 10 most frequent record types for visualization
    top_types = df['type'].value_counts().head(10).index.tolist()
    
    for record_type in top_types:
        try:
            type_df = df[df['type'] == record_type].copy()
            
            # Daily aggregation
            daily_df = type_df.groupby('date')['value'].agg(['mean', 'count', 'min', 'max']).reset_index()
            
            if len(daily_df) < 2:
                continue
            
            plt.figure(figsize=(12, 6))
            
            # Plot mean values
            sns.lineplot(data=daily_df, x='date', y='mean', label='Mean', color='blue')
            
            # Add confidence interval
            plt.fill_between(
                daily_df['date'],
                daily_df['min'],
                daily_df['max'],
                alpha=0.2,
                color='blue',
                label='Range'
            )
            
            # Format plot
            plt.title(f'{record_type} - Time Series')
            plt.xlabel('Date')
            plt.ylabel(f'Value ({type_df["unit"].iloc[0] if "unit" in type_df.columns else ""})')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Format x-axis dates
            ax = plt.gca()
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
            
            # Save plot
            safe_type = record_type.replace('/', '_').replace(' ', '_')
            plot_file = ts_dir / f"{safe_type}_timeseries.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"📊 Generated time series for {record_type}")
            
        except Exception as e:
            print(f"⚠️ Could not generate plot for {record_type}: {e}")
            continue

def _generate_category_distributions(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate distribution plots for health data categories."""
    
    dist_dir = output_dir / "distributions"
    dist_dir.mkdir(exist_ok=True)
    
    # Record types distribution
    plt.figure(figsize=(12, 8))
    type_counts = df['type'].value_counts().head(20)
    sns.barplot(x=type_counts.values, y=type_counts.index, palette='viridis')
    plt.title('Health Record Types Distribution')
    plt.xlabel('Count')
    plt.ylabel('Record Type')
    plt.tight_layout()
    
    dist_file = dist_dir / "record_types_distribution.png"
    plt.savefig(dist_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Generated record types distribution")
    
    # Sources distribution
    plt.figure(figsize=(10, 6))
    source_counts = df['source'].value_counts().head(10)
    sns.barplot(x=source_counts.values, y=source_counts.index, palette='rocket')
    plt.title('Data Sources Distribution')
    plt.xlabel('Count')
    plt.ylabel('Source')
    plt.tight_layout()
    
    source_file = dist_dir / "sources_distribution.png"
    plt.savefig(source_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Generated sources distribution")

def _generate_database_dashboard(db: HealthDatabase, output_dir: Path, config: Dict[str, Any]) -> None:
    """Generate dashboard visualizations using database queries."""
    
    # Generate database-based summary statistics
    _generate_database_summary_stats(db, output_dir)
    
    # Generate time series visualizations using database queries
    _generate_database_time_series(db, output_dir)
    
    # Generate category distributions from database
    _generate_database_distributions(db, output_dir)
    
    # Generate HTML dashboard
    _generate_html_dashboard(output_dir)


def _generate_database_summary_stats(db: HealthDatabase, output_dir: Path) -> None:
    """Generate summary statistics from database."""
    stats = db.get_database_stats()
    
    # Get record types summary
    record_types = db.get_record_types_summary()
    
    # Get sources summary
    sources = db.get_sources_summary()
    
    summary_data = {
        'total_records': stats['total_records'],
        'total_workouts': stats['total_workouts'],
        'total_sources': stats['total_sources'],
        'total_record_types': stats['total_record_types'],
        'date_range': stats['date_range'],
        'record_types_by_category': {},
        'top_sources': sources[:5]
    }
    
    # Group record types by category
    for record_type in record_types:
        category = record_type['category']
        if category not in summary_data['record_types_by_category']:
            summary_data['record_types_by_category'][category] = []
        summary_data['record_types_by_category'][category].append({
            'type': record_type['type_name'],
            'count': record_type['record_count']
        })
    
    # Save stats as JSON
    stats_file = output_dir / "summary_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(summary_data, f, indent=2, default=str)
    
    print(f"📈 Generated database summary statistics: {stats_file}")


def _generate_database_time_series(db: HealthDatabase, output_dir: Path) -> None:
    """Generate time series plots using database queries."""
    
    # Create time series directory
    ts_dir = output_dir / "time_series"
    ts_dir.mkdir(exist_ok=True)
    
    # Get top record types by count
    record_types = db.get_record_types_summary()
    top_types = [rt['type_name'] for rt in record_types if rt['record_count'] >= 10][:10]
    
    # Get overall date range
    stats = db.get_database_stats()
    if not stats['date_range']['start'] or not stats['date_range']['end']:
        print("⚠️ No date range available for time series")
        return
    
    start_date = datetime.fromisoformat(stats['date_range']['start'])
    end_date = datetime.fromisoformat(stats['date_range']['end'])
    
    for record_type in top_types:
        try:
            # Get daily aggregates from database
            daily_data = db.get_daily_aggregates(record_type, start_date, end_date)
            
            if len(daily_data) < 2:
                continue
            
            # Convert to DataFrame for plotting
            df = pd.DataFrame(daily_data)
            df['date'] = pd.to_datetime(df['date'])
            
            plt.figure(figsize=(12, 6))
            
            # Plot mean values
            sns.lineplot(data=df, x='date', y='avg_value', label='Mean', color='blue')
            
            # Add confidence interval
            plt.fill_between(
                df['date'],
                df['min_value'],
                df['max_value'],
                alpha=0.2,
                color='blue',
                label='Range'
            )
            
            # Format plot
            plt.title(f'{record_type} - Time Series')
            plt.xlabel('Date')
            plt.ylabel(f'Value')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Format x-axis dates
            ax = plt.gca()
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
            
            # Save plot
            safe_type = record_type.replace('/', '_').replace(' ', '_')
            plot_file = ts_dir / f"{safe_type}_timeseries.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"📊 Generated time series for {record_type}")
            
        except Exception as e:
            print(f"⚠️ Could not generate plot for {record_type}: {e}")
            continue


def _generate_database_distributions(db: HealthDatabase, output_dir: Path) -> None:
    """Generate distribution plots from database data."""
    
    dist_dir = output_dir / "distributions"
    dist_dir.mkdir(exist_ok=True)
    
    # Get record types distribution
    record_types = db.get_record_types_summary()
    
    if record_types:
        plt.figure(figsize=(12, 8))
        type_counts = pd.DataFrame(record_types)
        type_counts = type_counts.sort_values('record_count', ascending=False).head(20)
        
        sns.barplot(x='record_count', y='type_name', data=type_counts, palette='viridis')
        plt.title('Health Record Types Distribution')
        plt.xlabel('Count')
        plt.ylabel('Record Type')
        plt.tight_layout()
        
        dist_file = dist_dir / "record_types_distribution.png"
        plt.savefig(dist_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Generated record types distribution")
    
    # Get sources distribution
    sources = db.get_sources_summary()
    
    if sources:
        plt.figure(figsize=(10, 6))
        source_counts = pd.DataFrame(sources)
        source_counts = source_counts.sort_values('record_count', ascending=False).head(10)
        
        sns.barplot(x='record_count', y='name', data=source_counts, palette='rocket')
        plt.title('Data Sources Distribution')
        plt.xlabel('Count')
        plt.ylabel('Source')
        plt.tight_layout()
        
        source_file = dist_dir / "sources_distribution.png"
        plt.savefig(source_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Generated sources distribution")


def _generate_html_dashboard(output_dir: Path) -> None:
    """Generate an HTML dashboard that ties all visualizations together."""
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apple Health Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        h1 {
            color: #007AFF;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .section {
            margin-bottom: 40px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #007AFF;
            margin-top: 0;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 10px;
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .gallery-item {
            background-color: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .gallery-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .gallery-item img {
            width: 100%;
            height: auto;
            display: block;
        }
        
        .gallery-item figcaption {
            padding: 10px;
            text-align: center;
            font-size: 0.9em;
            color: #666;
        }
        
        .stats {
            background-color: white;
            padding: 20px;
            border-radius: 6px;
            margin-top: 20px;
        }
        
        .stats pre {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            max-height: 400px;
        }
        
        footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <header>
        <h1>🍏 Apple Health Dashboard</h1>
        <p class="subtitle">Your personal health data visualization</p>
    </header>
    
    <div class="section">
        <h2>📊 Summary Statistics</h2>
        <div class="stats">
            <pre id="stats-content">Loading statistics...</pre>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Time Series Analysis</h2>
        <div class="gallery" id="time-series-gallery">
            <!-- Time series plots will be loaded here -->
        </div>
    </div>
    
    <div class="section">
        <h2>📊 Data Distributions</h2>
        <div class="gallery" id="distributions-gallery">
            <!-- Distribution plots will be loaded here -->
        </div>
    </div>
    
    <footer>
        <p>Generated by Apple Health Dashboard | Data from Apple Health app</p>
    </footer>
    
    <script>
        // Load statistics
        fetch('summary_stats.json')
            .then(response => response.json())
            .then(data => {
                document.getElementById('stats-content').textContent = 
                    JSON.stringify(data, null, 2);
            })
            .catch(error => {
                console.error('Error loading statistics:', error);
                document.getElementById('stats-content').textContent = 
                    'Error loading statistics: ' + error.message;
            });
        
        // Load time series images
        const timeSeriesGallery = document.getElementById('time-series-gallery');
        const timeSeriesDir = 'time_series/';
        
        // This would be dynamically generated in a real implementation
        // For now, we'll show a placeholder
        const tsPlaceholder = document.createElement('div');
        tsPlaceholder.className = 'gallery-item';
        tsPlaceholder.innerHTML = `
            <figure>
                <img src="time_series/HeartRate_timeseries.png" alt="Heart Rate Time Series" onerror="this.src='https://via.placeholder.com/500x300?text=No+data+available'">
                <figcaption>Heart Rate Time Series</figcaption>
            </figure>
        `;
        timeSeriesGallery.appendChild(tsPlaceholder);
        
        // Load distribution images
        const distGallery = document.getElementById('distributions-gallery');
        
        const distItems = [
            {src: 'distributions/record_types_distribution.png', caption: 'Record Types Distribution'},
            {src: 'distributions/sources_distribution.png', caption: 'Data Sources Distribution'}
        ];
        
        distItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'gallery-item';
            div.innerHTML = `
                <figure>
                    <img src="${item.src}" alt="${item.caption}" onerror="this.src='https://via.placeholder.com/500x300?text=No+data+available'">
                    <figcaption>${item.caption}</figcaption>
                </figure>
            `;
            distGallery.appendChild(div);
        });
    </script>
</body>
</html>
"""
    
    # Write HTML file
    html_file = output_dir / "dashboard.html"
    with open(html_file, 'w') as f:
        f.write(html_content)
    
    print("🌐 Generated HTML dashboard:", html_file)