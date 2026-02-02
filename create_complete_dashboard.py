#!/usr/bin/env python3
"""
Create the complete working dashboard with all features
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path('.') / 'src'))

import xml.etree.ElementTree as ET
import zipfile
import tempfile
import shutil
from datetime import datetime
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter

def create_complete_dashboard():
    """Create the complete working dashboard."""
    
    print("🍏 Creating Complete Dashboard")
    print("=" * 40)
    print("This may take a minute for large datasets...")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Parse data
    records = []
    
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
                
                # Parse records with progress updates
                for i, child in enumerate(root):
                    if child.tag == 'Record':
                        try:
                            records.append({
                                'date': child.get('startDate'),
                                'type': child.get('type', 'Unknown'),
                                'source': child.get('sourceName', 'Unknown'),
                                'value': float(child.get('value', '0')),
                                'unit': child.get('unit', '')
                            })
                            
                            # Show progress every 100k records
                            if len(records) % 100000 == 0:
                                print(f"  Parsed {len(records):,} records...")
                            
                        except:
                            continue
                
                print(f"✅ Parsed {len(records):,} records")
            
        finally:
            shutil.rmtree(temp_dir)
    
    if not records:
        print("❌ No records found")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    df['date_parsed'] = pd.to_datetime(df['date'].str.split(' ').str[0])
    
    print("📊 Generating visualizations...")
    
    # Create directories
    (output_dir / "time_series").mkdir(exist_ok=True)
    (output_dir / "distributions").mkdir(exist_ok=True)
    
    # 1. Summary statistics
    summary = {
        'total_records': len(df),
        'date_range': {
            'start': df['date_parsed'].min().strftime('%Y-%m-%d'),
            'end': df['date_parsed'].max().strftime('%Y-%m-%d')
        },
        'unique_types': df['type'].nunique(),
        'unique_sources': df['source'].nunique(),
        'records_by_type': df['type'].value_counts().head(20).to_dict(),
        'records_by_source': df['source'].value_counts().head(10).to_dict()
    }
    
    with open(output_dir / "summary_stats.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("  ✅ Generated summary statistics")
    
    # 2. Time series plots for top metrics
    top_types = df['type'].value_counts().head(5).index.tolist()
    
    for record_type in top_types:
        try:
            type_df = df[df['type'] == record_type].copy()
            
            # Daily aggregation
            daily_df = type_df.groupby('date_parsed')['value'].agg(['mean', 'count']).reset_index()
            
            if len(daily_df) > 1:
                plt.figure(figsize=(12, 6))
                plt.plot(daily_df['date_parsed'], daily_df['mean'], 'o-', alpha=0.7, label='Mean')
                plt.fill_between(daily_df['date_parsed'], 
                                daily_df['mean'] - 0.5, 
                                daily_df['mean'] + 0.5, 
                                alpha=0.2)
                
                plt.title(f'{record_type} - Time Series')
                plt.xlabel('Date')
                plt.ylabel(f'Value ({type_df["unit"].iloc[0]})')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save with safe filename
                safe_type = record_type.replace('/', '_').replace(' ', '_')[:50]
                plt.savefig(output_dir / "time_series" / f"{safe_type}_timeseries.png", dpi=150)
                plt.close()
                
                print(f"  ✅ Created time series for {record_type}")
        except Exception as e:
            print(f"  ⚠️  Could not create chart for {record_type}: {e}")
            continue
    
    # 3. Distribution charts
    try:
        plt.figure(figsize=(12, 8))
        type_counts = df['type'].value_counts().head(20)
        sns.barplot(x=type_counts.values, y=type_counts.index, palette='viridis')
        plt.title('Health Record Types Distribution')
        plt.tight_layout()
        plt.savefig(output_dir / "distributions" / "record_types_distribution.png", dpi=150)
        plt.close()
        print("  ✅ Created record types distribution")
    except:
        print("  ⚠️  Could not create record types chart")
    
    try:
        plt.figure(figsize=(10, 6))
        source_counts = df['source'].value_counts().head(10)
        sns.barplot(x=source_counts.values, y=source_counts.index, palette='rocket')
        plt.title('Data Sources Distribution')
        plt.tight_layout()
        plt.savefig(output_dir / "distributions" / "sources_distribution.png", dpi=150)
        plt.close()
        print("  ✅ Created sources distribution")
    except:
        print("  ⚠️  Could not create sources chart")
    
    # Create HTML dashboard
    print("🌐 Generating HTML dashboard...")
    
    # Get list of actual chart files
    time_series_files = []
    if (output_dir / "time_series").exists():
        for file in (output_dir / "time_series").glob("*.png"):
            time_series_files.append(file.name)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apple Health Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        h1 {{
            color: #007AFF;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .section {{
            margin-bottom: 40px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #007AFF;
            margin-top: 0;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .gallery-item {{
            background-color: white;
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
            background-color: white;
            padding: 20px;
            border-radius: 6px;
            margin-top: 20px;
        }}
        
        .stats pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            max-height: 400px;
        }}
        
        footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #999;
            font-size: 0.9em;
        }}
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
"""
    
    # Add time series charts
    for chart_file in time_series_files:
        chart_name = chart_file.replace('_timeseries.png', '').replace('_', ' ')
        html_content += f"""
            <div class="gallery-item">
                <figure>
                    <img src="time_series/{chart_file}" alt="{chart_name} Time Series">
                    <figcaption>{chart_name} Time Series</figcaption>
                </figure>
            </div>
        """
    
    html_content += """
        </div>
    </div>
    
    <div class="section">
        <h2>📊 Data Distributions</h2>
        <div class="gallery" id="distributions-gallery">
            <div class="gallery-item">
                <figure>
                    <img src="distributions/record_types_distribution.png" alt="Record Types Distribution">
                    <figcaption>Record Types Distribution</figcaption>
                </figure>
            </div>
            <div class="gallery-item">
                <figure>
                    <img src="distributions/sources_distribution.png" alt="Data Sources Distribution">
                    <figcaption>Data Sources Distribution</figcaption>
                </figure>
            </div>
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
                    'Statistics will appear here when loaded.';
            });
    </script>
</body>
</html>
"""
    
    # Save HTML
    with open(output_dir / "dashboard.html", 'w') as f:
        f.write(html_content)
    
    # Save data
    df.to_json(output_dir / "data.json", orient='records', indent=2)
    
    print(f"✅ Complete dashboard created")
    print(f"📁 Location: {output_dir.absolute()}")
    print(f"🌐 Open: file://{output_dir.absolute()}/dashboard.html")
    print(f"📊 Data: {output_dir.absolute()}/data.json")
    
    return True

if __name__ == "__main__":
    create_complete_dashboard()