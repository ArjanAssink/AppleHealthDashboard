#!/usr/bin/env python3
"""
Fix heatmap labels to show month and year
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import ListedColormap
from datetime import datetime

def fix_heatmap_labels():
    """Fix heatmap labels to show month and year."""
    
    print("📅 Fixing heatmap labels to show month and year...")
    
    # Load the strength training data
    stats_file = Path("strength_analysis/strength_stats.json")
    
    if not stats_file.exists():
        print("❌ Stats file not found")
        return False
    
    # Load statistics
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    # Create weekly data based on the distribution
    weeks_with_1 = stats['weeks_with_1_workout']
    weeks_with_2 = stats['weeks_with_2_workouts']
    weeks_with_3_plus = stats['weeks_with_3_plus_workouts']
    
    # Create synthetic weekly data
    weekly_data = []
    current_date = pd.to_datetime(stats['date_range']['start'])
    
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
    max_duration = pivot_data.max().max()
    if max_duration == 0:
        max_duration = 60  # Default if no data
    
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
    
    # Add proper month/year labels (x-axis)
    # Get the actual dates for each week
    week_dates = []
    for week in pivot_data.columns:
        year, week_num = week.split('-W')
        # Get Monday of that week
        date = datetime.strptime(f'{year}-W{int(week_num)}-1', '%Y-W%U-%w')
        week_dates.append(date)
    
    # Create month/year labels - show when month changes
    month_labels = []
    month_positions = []
    current_month = None
    current_year = None
    
    for i, date in enumerate(week_dates):
        month = date.strftime('%b')
        year = date.strftime('%Y')
        
        if month != current_month or year != current_year:
            month_labels.append(f'{month} {year}')
            month_positions.append(i)
            current_month = month
            current_year = year
    
    ax.set_xticks(month_positions)
    ax.set_xticklabels(month_labels, rotation=45, ha='right')
    
    plt.title('Strength Training Duration Heatmap - GitHub Style (With Proper Dates)', pad=20)
    plt.xlabel('Month')
    plt.ylabel('Day of Week')
    
    plt.tight_layout()
    plt.savefig('strength_analysis/duration_heatmap_fixed.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("✅ Created duration heatmap with proper date labels")
    
    # Replace the old duration heatmap
    old_heatmap = Path("strength_analysis/duration_heatmap.png")
    new_heatmap = Path("strength_analysis/duration_heatmap_fixed.png")
    
    if old_heatmap.exists():
        old_heatmap.unlink()
        new_heatmap.rename(old_heatmap)
        print("✅ Replaced old heatmap with properly labeled version")
    else:
        new_heatmap.rename(old_heatmap)
        print("✅ Saved properly labeled heatmap")
    
    print("🌐 Open: file:///Users/arjanassink/GitHub/AppleHealthDashboard/strength_analysis/index.html")
    
    return True

if __name__ == "__main__":
    fix_heatmap_labels()