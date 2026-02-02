#!/usr/bin/env python3
"""
Analyze strength training patterns and create visualizations
"""

import xml.etree.ElementTree as ET
import zipfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def analyze_strength_training():
    """Analyze strength training patterns and create visualizations."""
    
    print("🏋️‍♂️ Analyzing Strength Training Patterns")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("strength_analysis")
    output_dir.mkdir(exist_ok=True)
    
    # Parse workout data
    workouts = []
    
    with zipfile.ZipFile('data/health_exports/export.zip', 'r') as zip_ref:
        temp_dir = tempfile.mkdtemp()
        try:
            zip_ref.extractall(temp_dir)
            
            # Find export.xml
            xml_file = None
            for file in Path(temp_dir).rglob('*.xml'):
                if 'export' in file.name.lower():
                    xml_file = file
                    break
            
            if xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Parse all workouts
                for child in root:
                    if child.tag == 'Workout':
                        try:
                            workout_type = child.get('workoutActivityType', 'Unknown')
                            
                            # Filter for strength training workouts
                            if 'Strength' in workout_type or 'Weight' in workout_type:
                                workouts.append({
                                    'date': child.get('startDate'),
                                    'type': workout_type,
                                    'duration': float(child.get('duration', '0')),
                                    'duration_unit': child.get('durationUnit', 'min'),
                                    'total_distance': child.get('totalDistance'),
                                    'total_energy': child.get('totalEnergyBurned'),
                                    'source': child.get('sourceName', 'Unknown')
                                })
                        except:
                            continue
                
                print(f"✅ Found {len(workouts)} strength training workouts")
            
        finally:
            shutil.rmtree(temp_dir)
    
    if not workouts:
        print("❌ No strength training workouts found")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(workouts)
    df['date_parsed'] = pd.to_datetime(df['date'].str.split(' ').str[0])
    df['week'] = df['date_parsed'].dt.to_period('W')
    df['year'] = df['date_parsed'].dt.year
    
    print("📊 Generating strength training analysis...")
    
    # 1. Weekly frequency analysis
    weekly_counts = df.groupby('week').size().reset_index(name='count')
    weekly_counts['week_start'] = weekly_counts['week'].dt.start_time
    
    plt.figure(figsize=(15, 6))
    plt.bar(weekly_counts['week_start'], weekly_counts['count'], width=5)
    plt.title('Strength Training Frequency by Week')
    plt.xlabel('Week')
    plt.ylabel('Number of Workouts')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "weekly_frequency.png", dpi=150)
    plt.close()
    print("  ✅ Created weekly frequency chart")
    
    # 2. Frequency distribution (0, 1, 2, 3+ workouts per week)
    weekly_dist = weekly_counts['count'].value_counts().sort_index()
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=weekly_dist.index, y=weekly_dist.values, palette='viridis')
    plt.title('Distribution of Weekly Strength Training Frequency')
    plt.xlabel('Workouts per Week')
    plt.ylabel('Number of Weeks')
    plt.tight_layout()
    plt.savefig(output_dir / "frequency_distribution.png", dpi=150)
    plt.close()
    print("  ✅ Created frequency distribution chart")
    
    # 3. Time between workouts
    df_sorted = df.sort_values('date_parsed')
    df_sorted['time_since_last'] = df_sorted['date_parsed'].diff().dt.total_seconds() / (24*3600)  # days
    
    plt.figure(figsize=(12, 6))
    plt.hist(df_sorted['time_since_last'].dropna(), bins=30, edgecolor='black')
    plt.title('Days Between Strength Training Workouts')
    plt.xlabel('Days')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(output_dir / "time_between_workouts.png", dpi=150)
    plt.close()
    print("  ✅ Created time between workouts chart")
    
    # 4. Workout duration analysis
    plt.figure(figsize=(12, 6))
    sns.histplot(df['duration'], bins=30, kde=True)
    plt.title('Strength Training Workout Duration Distribution')
    plt.xlabel(f'Duration ({df["duration_unit"].iloc[0]})')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(output_dir / "workout_duration.png", dpi=150)
    plt.close()
    print("  ✅ Created workout duration chart")
    
    # 5. Weekly heatmap
    weekly_pivot = df.groupby(['year', 'week'])['duration'].mean().unstack()
    
    plt.figure(figsize=(15, 8))
    sns.heatmap(weekly_pivot, cmap='YlOrRd', cbar_kws={'label': 'Avg Duration (min)'})
    plt.title('Strength Training Heatmap (Average Duration by Week)')
    plt.xlabel('Week of Year')
    plt.ylabel('Year')
    plt.tight_layout()
    plt.savefig(output_dir / "weekly_heatmap.png", dpi=150)
    plt.close()
    print("  ✅ Created weekly heatmap")
    
    # 6. Statistics
    stats = {
        'total_workouts': len(df),
        'date_range': {
            'start': df['date_parsed'].min().strftime('%Y-%m-%d'),
            'end': df['date_parsed'].max().strftime('%Y-%m-%d')
        },
        'average_workouts_per_week': weekly_counts['count'].mean(),
        'median_workouts_per_week': weekly_counts['count'].median(),
        'weeks_with_no_workouts': len(weekly_counts[weekly_counts['count'] == 0]),
        'weeks_with_1_workout': len(weekly_counts[weekly_counts['count'] == 1]),
        'weeks_with_2_workouts': len(weekly_counts[weekly_counts['count'] == 2]),
        'weeks_with_3_plus_workouts': len(weekly_counts[weekly_counts['count'] >= 3]),
        'average_days_between_workouts': df_sorted['time_since_last'].mean(),
        'median_days_between_workouts': df_sorted['time_since_last'].median(),
        'average_workout_duration': df['duration'].mean(),
        'median_workout_duration': df['duration'].median(),
        'total_workout_time': df['duration'].sum()
    }
    
    with open(output_dir / "strength_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("📈 Generated strength training statistics")
    
    # Create HTML dashboard
    print("🌐 Generating HTML dashboard...")
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Strength Training Analysis</title>
    <style>
        body {{
            font-family: -apple-system, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        
        header {{
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        h1 {{
            margin: 0;
            font-size: 2em;
        }}
        
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #ff6b6b;
            margin-top: 0;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .gallery-item {{
            background-color: #f8f8f8;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .gallery-item img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        
        .gallery-item figcaption {{
            padding: 10px;
            text-align: center;
            font-size: 0.9em;
            color: #666;
        }}
        
        .stats {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        
        .stats pre {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        
        footer {{
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🏋️‍♂️ Strength Training Analysis</h1>
        <p>Detailed analysis of your strength training patterns</p>
    </header>
    
    <div class="section">
        <h2>📊 Summary Statistics</h2>
        <div class="stats">
            <pre>{json.dumps(stats, indent=2, default=str)}</pre>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Visualizations</h2>
        <div class="gallery">
            <div class="gallery-item">
                <figure>
                    <img src="weekly_frequency.png" alt="Weekly Frequency">
                    <figcaption>Strength Training Frequency by Week</figcaption>
                </figure>
            </div>
            
            <div class="gallery-item">
                <figure>
                    <img src="frequency_distribution.png" alt="Frequency Distribution">
                    <figcaption>Weekly Workout Frequency Distribution</figcaption>
                </figure>
            </div>
            
            <div class="gallery-item">
                <figure>
                    <img src="time_between_workouts.png" alt="Time Between Workouts">
                    <figcaption>Days Between Strength Training Workouts</figcaption>
                </figure>
            </div>
            
            <div class="gallery-item">
                <figure>
                    <img src="workout_duration.png" alt="Workout Duration">
                    <figcaption>Workout Duration Distribution</figcaption>
                </figure>
            </div>
            
            <div class="gallery-item">
                <figure>
                    <img src="weekly_heatmap.png" alt="Weekly Heatmap">
                    <figcaption>Weekly Heatmap (Average Duration)</figcaption>
                </figure>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Strength Training Analysis | Generated from Apple Health Data</p>
    </footer>
</body>
</html>
"""
    
    # Save HTML
    with open(output_dir / "index.html", 'w') as f:
        f.write(html_content)
    
    # Save data
    df.to_json(output_dir / "workouts.json", orient='records', indent=2)
    
    print(f"✅ Strength training analysis complete")
    print(f"📁 Location: {output_dir.absolute()}")
    print(f"🌐 Open: file://{output_dir.absolute()}/index.html")
    print(f"📊 Data: {output_dir.absolute()}/workouts.json")
    
    return True

if __name__ == "__main__":
    analyze_strength_training()