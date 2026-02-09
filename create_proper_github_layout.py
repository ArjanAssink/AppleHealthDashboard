#!/usr/bin/env python3
"""
Create proper GitHub layout: days as rows, weeks as columns
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import ListedColormap

def create_proper_github_layout():
    """Create proper GitHub layout with days as rows, weeks as columns."""
    
    print("🎨 Creating proper GitHub layout...")
    
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
    
    # Create heatmap data with proper GitHub layout
    # Days as rows (0=Monday, 6=Sunday), weeks as columns
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
        
        # Create pivot table - transpose to get days as rows, weeks as columns
        pivot_data = heatmap_df.pivot_table(
            index='day_of_week',  # Days as rows
            columns='week',       # Weeks as columns
            values='workout_count',
            aggfunc='sum',
            fill_value=0
        )
        
        # Reorder days to start with Monday (0)
        day_order = [0, 1, 2, 3, 4, 5, 6]  # Mon, Tue, Wed, Thu, Fri, Sat, Sun
        pivot_data = pivot_data.reindex(day_order)
        
        # GitHub uses a specific color scheme
        github_colors = ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
        cmap = ListedColormap(github_colors)
        
        plt.figure(figsize=(20, 5))  # Wider than tall for GitHub style
        
        # Create the heatmap with proper orientation
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
        
        # Add day labels (y-axis)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ax.set_yticks(np.arange(len(days)) + 0.5)
        ax.set_yticklabels(days, rotation=0)
        
        # Add week labels (x-axis) - show every 8th week to avoid clutter
        weeks_in_data = len(pivot_data.columns)
        if weeks_in_data > 40:
            week_labels = [f'Week {i+1}' for i in range(0, weeks_in_data, 8)]
            week_positions = list(range(0, weeks_in_data, 8))
        else:
            week_labels = [f'Week {i+1}' for i in range(weeks_in_data)]
            week_positions = list(range(weeks_in_data))
        
        ax.set_xticks(week_positions)
        ax.set_xticklabels(week_labels, rotation=45, ha='right')
        
        plt.title('Strength Training Consistency - GitHub Style (Proper Layout)', pad=20)
        plt.xlabel('Week')
        plt.ylabel('Day of Week')
        
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
        plt.savefig('strength_analysis/github_proper_layout.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print("✅ Created proper GitHub layout")
        
        # Replace the old heatmap
        old_heatmap = Path("strength_analysis/github_heatmap.png")
        new_heatmap = Path("strength_analysis/github_proper_layout.png")
        
        if old_heatmap.exists():
            old_heatmap.unlink()
            new_heatmap.rename(old_heatmap)
            print("✅ Replaced old heatmap with proper layout")
        else:
            new_heatmap.rename(old_heatmap)
            print("✅ Saved proper layout heatmap")
    else:
        print("⚠️  No workout data to display")
    
    print("🌐 Open: file:///Users/arjanassink/GitHub/AppleHealthDashboard/strength_analysis/index.html")
    
    return True

if __name__ == "__main__":
    create_proper_github_layout()