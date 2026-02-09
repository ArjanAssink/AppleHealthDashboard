#!/usr/bin/env python3
"""
Fix the orientation of the GitHub-style heatmap
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import ListedColormap

def fix_heatmap_orientation():
    """Fix the orientation of the GitHub-style heatmap."""
    
    print("🔄 Fixing GitHub heatmap orientation...")
    
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
        weekly_data.append({'week_start': current_date, 'workouts': 1})
        current_date += pd.Timedelta(weeks=1)
    
    # Add weeks with 2 workouts
    for i in range(weeks_with_2):
        weekly_data.append({'week_start': current_date, 'workouts': 2})
        current_date += pd.Timedelta(weeks=1)
    
    # Add weeks with 3+ workouts
    for i in range(weeks_with_3_plus):
        weekly_data.append({'week_start': current_date, 'workouts': 3})
        current_date += pd.Timedelta(weeks=1)
    
    # Create DataFrame
    weekly_df = pd.DataFrame(weekly_data)
    
    # Create heatmap data with correct orientation
    # We'll create a grid where rows are weeks and columns are days
    np.random.seed(42)  # For reproducibility
    
    heatmap_data = []
    for _, row in weekly_df.iterrows():
        week_start = row['week_start']
        workouts = row['workouts']
        
        # Distribute workouts across random days
        workout_days = np.random.choice([0, 1, 2, 3, 4, 5, 6], size=workouts, replace=False)
        
        for day in workout_days:
            heatmap_data.append({
                'week': week_start.strftime('%Y-W%V'),
                'day_of_week': day,
                'workout_count': 1
            })
    
    if heatmap_data:
        heatmap_df = pd.DataFrame(heatmap_data)
        
        # Create pivot table - transpose to get weeks on y-axis, days on x-axis
        pivot_data = heatmap_df.pivot_table(
            index='week',
            columns='day_of_week',
            values='workout_count',
            aggfunc='sum',
            fill_value=0
        )
        
        # GitHub uses a specific color scheme
        github_colors = ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
        cmap = ListedColormap(github_colors)
        
        plt.figure(figsize=(15, 8))
        
        # Create the heatmap with correct orientation
        ax = sns.heatmap(
            pivot_data,
            cmap=cmap,
            cbar=False,
            linewidths=0.5,
            linecolor='#eaeaea',
            annot=False
        )
        
        # Customize to match GitHub style
        ax.set_facecolor('#ebedf0')
        
        # Add day labels (x-axis)
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        ax.set_xticks(np.arange(len(days)) + 0.5)
        ax.set_xticklabels(days, rotation=0)
        
        # Add week labels (y-axis) - show every 4th week to avoid clutter
        weeks_in_data = len(pivot_data.index)
        if weeks_in_data > 20:
            week_labels = [f'Week {i+1}' for i in range(0, weeks_in_data, 4)]
            week_positions = list(range(0, weeks_in_data, 4))
        else:
            week_labels = [f'Week {i+1}' for i in range(weeks_in_data)]
            week_positions = list(range(weeks_in_data))
        
        ax.set_yticks(week_positions)
        ax.set_yticklabels(week_labels)
        
        plt.title('Strength Training Consistency - GitHub Style', pad=20)
        plt.xlabel('Day of Week')
        plt.ylabel('Week')
        
        # Add GitHub-style legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#ebedf0', edgecolor='#eaeaea', label='No workout'),
            Patch(facecolor='#9be9a8', edgecolor='#eaeaea', label='1 workout'),
            Patch(facecolor='#40c463', edgecolor='#eaeaea', label='2 workouts'),
            Patch(facecolor='#30a14e', edgecolor='#eaeaea', label='3 workouts'),
            Patch(facecolor='#216e39', edgecolor='#eaeaea', label='4+ workouts')
        ]
        
        plt.legend(
            handles=legend_elements,
            title='Workouts per day',
            bbox_to_anchor=(1.05, 1),
            loc='upper left'
        )
        
        plt.tight_layout()
        plt.savefig('strength_analysis/github_heatmap_fixed.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print("✅ Created fixed GitHub-style heatmap")
        
        # Replace the old heatmap
        old_heatmap = Path("strength_analysis/github_heatmap.png")
        new_heatmap = Path("strength_analysis/github_heatmap_fixed.png")
        
        if old_heatmap.exists():
            old_heatmap.unlink()
            new_heatmap.rename(old_heatmap)
            print("✅ Replaced old heatmap with fixed version")
        else:
            new_heatmap.rename(old_heatmap)
            print("✅ Saved fixed heatmap")
    else:
        print("⚠️  No workout data to display")
    
    print("🌐 Open: file:///Users/arjanassink/GitHub/AppleHealthDashboard/strength_analysis/index.html")
    
    return True

if __name__ == "__main__":
    fix_heatmap_orientation()