#!/usr/bin/env python3
"""
Create a GitHub-style contribution heatmap for strength training
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import ListedColormap
import numpy as np

def create_github_style_heatmap():
    """Create a GitHub-style contribution heatmap."""
    
    print("🎨 Creating GitHub-style strength training heatmap...")
    
    # Load the strength training data
    workouts_file = Path("strength_analysis/workouts.json")
    stats_file = Path("strength_analysis/strength_stats.json")
    
    if not workouts_file.exists():
        print("❌ Workouts file not found")
        return False
    
    # Load data
    with open(workouts_file, 'r') as f:
        workouts = json.load(f)
    
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    df = pd.DataFrame(workouts)
    df['date_parsed'] = pd.to_datetime(df['date'])
    df['date_only'] = df['date_parsed'].dt.date
    
    # Create GitHub-style heatmap
    # Get all dates in range
    start_date = pd.to_datetime(stats['date_range']['start'])
    end_date = pd.to_datetime(stats['date_range']['end'])
    all_dates = pd.date_range(start_date, end_date, freq='D')
    
    # Create date grid
    date_grid = []
    for date in all_dates:
        day_of_week = date.dayofweek  # Monday=0, Sunday=6
        week = date.isocalendar()[1]
        year = date.year
        date_grid.append({
            'date': date,
            'day_of_week': day_of_week,
            'week': week,
            'year': year,
            'has_workout': date.date() in df['date_only'].values
        })
    
    grid_df = pd.DataFrame(date_grid)
    
    # Create pivot table for heatmap
    pivot_data = grid_df.pivot_table(
        index='week', 
        columns='day_of_week', 
        values='has_workout',
        aggfunc='sum',
        fill_value=0
    )
    
    # GitHub uses a specific color scheme
    github_colors = ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
    cmap = ListedColormap(github_colors)
    
    plt.figure(figsize=(15, 8))
    
    # Create the heatmap
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
    
    # Add day labels (GitHub uses 3-letter abbreviations)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    ax.set_xticks(np.arange(len(days)) + 0.5)
    ax.set_xticklabels(days, rotation=0)
    
    # Add month labels on the side
    months = []
    month_positions = []
    current_month = None
    
    for i, (week, row) in enumerate(pivot_data.iterrows()):
        # Get the date for this week (using Monday)
        year = all_dates[i].year
        month = all_dates[i].strftime('%b')
        
        if month != current_month:
            months.append(month)
            month_positions.append(i)
            current_month = month
    
    # Add month labels
    ax.set_yticks(month_positions)
    ax.set_yticklabels(months)
    
    plt.title('Strength Training Consistency - GitHub Style', pad=20)
    plt.xlabel('Day of Week')
    plt.ylabel('Month')
    
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
    plt.savefig('strength_analysis/github_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("✅ Created GitHub-style heatmap")
    
    # Add the new heatmap to the HTML dashboard
    print("🌐 Updating HTML dashboard with GitHub heatmap...")
    
    # Read the existing HTML
    html_file = Path("strength_analysis/index.html")
    with open(html_file, 'r') as f:
        html_content = f.read()
    
    # Add GitHub heatmap to the gallery
    github_heatmap_html = '''
            <div class="gallery-item">
                <figure>
                    <img src="github_heatmap.png" alt="GitHub Style Heatmap">
                    <figcaption>GitHub-Style Consistency Heatmap</figcaption>
                </figure>
            </div>
        '''
    
    # Insert before the closing div of the gallery
    html_content = html_content.replace(
        '</div>\n    </div>',
        f'{github_heatmap_html}</div>\n    </div>'
    )
    
    # Save the updated HTML
    with open(html_file, 'w') as f:
        f.write(html_content)
    
    print("✅ Updated dashboard with GitHub-style heatmap")
    print("🌐 Open: file:///Users/arjanassink/GitHub/AppleHealthDashboard/strength_analysis/index.html")
    
    return True

if __name__ == "__main__":
    create_github_style_heatmap()