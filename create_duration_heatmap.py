#!/usr/bin/env python3
"""
Create heatmap with duration-based intensity
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import ListedColormap

def create_duration_heatmap():
    """Create heatmap with duration-based intensity."""
    
    print("🎨 Creating duration-based heatmap...")
    
    # Load the strength training data
    workouts_file = Path("strength_analysis/workouts.json")
    stats_file = Path("strength_analysis/strength_stats.json")
    
    if not workouts_file.exists():
        print("❌ Workouts file not found, using statistics only")
        workouts_file = None
    
    if not stats_file.exists():
        print("❌ Stats file not found")
        return False
    
    # Load statistics
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    # Try to load actual workout data if available
    if workouts_file and workouts_file.exists():
        with open(workouts_file, 'r') as f:
            workouts = json.load(f)
        df = pd.DataFrame(workouts)
        df['date_parsed'] = pd.to_datetime(df['date'])
        df['date_only'] = df['date_parsed'].dt.date
        df['week'] = df['date_parsed'].dt.to_period('W')
        df['day_of_week'] = df['date_parsed'].dt.dayofweek  # Monday=0, Sunday=6
    else:
        # Create synthetic data based on statistics
        print("📊 Using synthetic data based on statistics")
        weekly_data = []
        current_date = pd.to_datetime(stats['date_range']['start'])
        
        # Create weekly data based on the distribution
        weeks_with_1 = stats['weeks_with_1_workout']
        weeks_with_2 = stats['weeks_with_2_workouts']
        weeks_with_3_plus = stats['weeks_with_3_plus_workouts']
        
        # Add weeks with 1 workout
        for i in range(weeks_with_1):
            weekly_data.append({'week_start': current_date, 'workouts': 1, 'avg_duration': 30})
            current_date += pd.Timedelta(weeks=1)
        
        # Add weeks with 2 workouts
        for i in range(weeks_with_2):
            weekly_data.append({'week_start': current_date, 'workouts': 2, 'avg_duration': 35})
            current_date += pd.Timedelta(weeks=1)
        
        # Add weeks with 3+ workouts
        for i in range(weeks_with_3_plus):
            weekly_data.append({'week_start': current_date, 'workouts': 3, 'avg_duration': 40})
            current_date += pd.Timedelta(weeks=1)
        
        # Create DataFrame and expand to daily data
        weekly_df = pd.DataFrame(weekly_data)
        heatmap_data = []
        
        for _, row in weekly_df.iterrows():
            week_start = row['week_start']
            workouts = row['workouts']
            avg_duration = row['avg_duration']
            
            # Distribute workouts across random days
            workout_days = np.random.choice([0, 1, 2, 3, 4, 5, 6], size=workouts, replace=False)
            
            for day in workout_days:
                heatmap_data.append({
                    'week': week_start.strftime('%Y-W%V'),
                    'day_of_week': day,
                    'duration': avg_duration
                })
        
        df = pd.DataFrame(heatmap_data)
    
    # Create pivot table for heatmap
    pivot_data = df.pivot_table(
        index='day_of_week',
        columns='week',
        values='duration',
        aggfunc='sum',
        fill_value=0
    )
    
    # Reorder days to start with Monday (0)
    day_order = [0, 1, 2, 3, 4, 5, 6]  # Mon, Tue, Wed, Thu, Fri, Sat, Sun
    pivot_data = pivot_data.reindex(day_order)
    
    # Create custom color map based on duration
    # Use a gradient from light to dark green based on actual duration values
    max_duration = pivot_data.max().max()
    if max_duration == 0:
        max_duration = 60  # Default if no data
    
    # Create 5 color levels
    color_levels = [0, max_duration*0.25, max_duration*0.5, max_duration*0.75, max_duration]
    github_colors = ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
    cmap = ListedColormap(github_colors)
    norm = plt.Normalize(vmin=0, vmax=max_duration)
    
    plt.figure(figsize=(20, 5))
    
    # Create the heatmap
    ax = sns.heatmap(
        pivot_data,
        cmap=cmap,
        norm=norm,
        cbar=True,
        cbar_kws={'label': 'Total Duration (minutes)'},
        linewidths=0.5,
        linecolor='#eaeaea',
        annot=False
    )
    
    # Customize to match GitHub style
    ax.set_facecolor('#ebedf0')
    
    # Add day labels (y-axis)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ax.set_yticks(np.arange(len(days)) + 0.5)
    ax.set_yticklabels(days, rotation=0)
    
    # Add week labels (x-axis)
    weeks_in_data = len(pivot_data.columns)
    if weeks_in_data > 40:
        week_labels = [f'Week {i+1}' for i in range(0, weeks_in_data, 8)]
        week_positions = list(range(0, weeks_in_data, 8))
    else:
        week_labels = [f'Week {i+1}' for i in range(weeks_in_data)]
        week_positions = list(range(weeks_in_data))
    
    ax.set_xticks(week_positions)
    ax.set_xticklabels(week_labels, rotation=45, ha='right')
    
    plt.title('Strength Training Duration Heatmap - GitHub Style', pad=20)
    plt.xlabel('Week')
    plt.ylabel('Day of Week')
    
    plt.tight_layout()
    plt.savefig('strength_analysis/duration_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("✅ Created duration-based heatmap")
    
    # Add to HTML dashboard
    print("🌐 Updating HTML dashboard...")
    
    html_file = Path("strength_analysis/index.html")
    with open(html_file, 'r') as f:
        html_content = f.read()
    
    # Add duration heatmap to the gallery
    duration_html = '''            <div class="gallery-item">
                <figure>
                    <img src="duration_heatmap.png" alt="Duration Heatmap">
                    <figcaption>Duration-Based Heatmap (Minutes)</figcaption>
                </figure>
            </div>
        '''
    
    # Insert before the closing div of the gallery
    insert_point = html_content.find('</div>\n    </div>\n    <footer>')
    if insert_point != -1:
        html_content = html_content[:insert_point] + duration_html + html_content[insert_point+18:]
        
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print("✅ Updated dashboard with duration heatmap")
    else:
        print("⚠️  Could not find insertion point in HTML")
    
    print("🌐 Open: file:///Users/arjanassink/GitHub/AppleHealthDashboard/strength_analysis/index.html")
    
    return True

if __name__ == "__main__":
    create_duration_heatmap()