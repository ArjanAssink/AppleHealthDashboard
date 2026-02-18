#!/usr/bin/env python3
"""
Interactive Dashboard Generator

Generates an interactive health dashboard using Chart.js and Plotly.js hybrid approach.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

from data_storage.health_database import HealthDatabase

def generate_interactive_dashboard(db: HealthDatabase, output_dir: Path = Path("output")) -> None:
    """Generate an interactive dashboard with Chart.js and Plotly.js.
    
    Args:
        db: HealthDatabase instance with health data
        output_dir: Output directory for dashboard files
    """
    print("🎨 Generating interactive dashboard...")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Generate all data files
    chart_data = _prepare_chart_data(db)
    stats_data = _prepare_stats_data(db)
    
    # Save data files
    _save_json_data(output_dir, chart_data, "chart_data.json")
    _save_json_data(output_dir, stats_data, "stats_data.json")
    
    # Generate HTML dashboard
    _generate_interactive_html(output_dir)
    
    print("✅ Interactive dashboard generated!")
    print(f"📊 Data files saved to: {output_dir}")

def _prepare_chart_data(db: HealthDatabase) -> Dict[str, Any]:
    """Prepare data for interactive charts."""
    chart_data = {
        'time_series': {},
        'distributions': {},
        'workouts': {},
        'correlations': {}
    }
    
    # Get overall date range
    stats = db.get_database_stats()
    if not stats['date_range']['start'] or not stats['date_range']['end']:
        return chart_data
    
    start_date = datetime.fromisoformat(stats['date_range']['start'])
    end_date = datetime.fromisoformat(stats['date_range']['end'])
    
    # Time series data for Chart.js
    record_types = db.get_record_types_summary()
    top_types = [rt['type_name'] for rt in record_types if rt['record_count'] >= 5][:6]
    
    for record_type in top_types:
        daily_data = db.get_daily_aggregates(record_type, start_date, end_date)
        if daily_data and len(daily_data) > 1:
            chart_data['time_series'][record_type] = {
                'dates': [d['date'] for d in daily_data],
                'avg_values': [d['avg_value'] for d in daily_data],
                'min_values': [d['min_value'] for d in daily_data],
                'max_values': [d['max_value'] for d in daily_data],
                'counts': [d['count'] for d in daily_data]
            }
    
    # Distribution data for Chart.js
    record_types_data = db.get_record_types_summary()
    chart_data['distributions']['record_types'] = {
        'types': [rt['type_name'] for rt in record_types_data],
        'counts': [rt['record_count'] for rt in record_types_data],
        'categories': [rt['category'] for rt in record_types_data]
    }
    
    sources_data = db.get_sources_summary()
    chart_data['distributions']['sources'] = {
        'names': [s['name'] for s in sources_data],
        'counts': [s['record_count'] for s in sources_data]
    }
    
    # Workout data for Plotly.js
    workout_types = ['Running', 'Cycling', 'Walking', 'Swimming', 'Yoga']
    for workout_type in workout_types:
        workouts = db.get_workouts_by_type(workout_type)
        if workouts:
            chart_data['workouts'][workout_type] = [{
                'date': w['start_date'],
                'duration': w['duration'],
                'distance': w.get('total_distance'),
                'energy': w.get('total_energy_burned'),
                'source': w['source']
            } for w in workouts]
    
    # Correlation data for Plotly.js (scientific views)
    _add_correlation_data(db, chart_data, start_date, end_date)
    
    return chart_data

def _add_correlation_data(db: HealthDatabase, chart_data: Dict[str, Any], 
                         start_date: datetime, end_date: datetime):
    """Add correlation data for scientific analysis."""
    # Get multiple record types for correlation
    record_types = ['HeartRate', 'StepCount', 'ActiveEnergy']
    correlation_data = {}
    
    for record_type in record_types:
        records = db.get_records_by_date_range(start_date, end_date, record_type)
        if records and len(records) > 10:
            correlation_data[record_type] = [{
                'date': r['start_date'],
                'value': r['value'],
                'source': r['source']
            } for r in records]
    
    if len(correlation_data) >= 2:
        chart_data['correlations'] = correlation_data

def _prepare_stats_data(db: HealthDatabase) -> Dict[str, Any]:
    """Prepare summary statistics data."""
    stats = db.get_database_stats()
    
    # Get detailed record types
    record_types = db.get_record_types_summary()
    record_types_by_category = {}
    
    for rt in record_types:
        category = rt['category']
        if category not in record_types_by_category:
            record_types_by_category[category] = []
        record_types_by_category[category].append({
            'type': rt['type_name'],
            'count': rt['record_count'],
            'first_record': rt['first_record'],
            'last_record': rt['last_record']
        })
    
    # Get sources
    sources = db.get_sources_summary()
    
    return {
        'total_records': stats['total_records'],
        'total_workouts': stats['total_workouts'],
        'total_sources': stats['total_sources'],
        'total_record_types': stats['total_record_types'],
        'date_range': stats['date_range'],
        'record_types_by_category': record_types_by_category,
        'sources': sources
    }

def _save_json_data(output_dir: Path, data: Dict[str, Any], filename: str):
    """Save data as JSON file."""
    file_path = output_dir / filename
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"📊 Saved {filename}")

def _generate_interactive_html(output_dir: Path):
    """Generate the interactive HTML dashboard."""
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apple Health Dashboard - Interactive</title>
    <style>
        :root {
            --primary-color: #007AFF;
            --secondary-color: #ff6b6b;
            --background-color: #f5f5f7;
            --card-color: #ffffff;
            --text-color: #1d1d1f;
            --light-text: #86868b;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: var(--card-color);
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: var(--primary-color);
            margin: 10px 0;
        }
        
        .stat-label {
            color: var(--light-text);
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .section {
            background: var(--card-color);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .section h2 {
            color: var(--primary-color);
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }
        
        .chart-container {
            margin: 20px 0;
            position: relative;
            height: 400px;
        }
        
        .chart-container.full-height {
            height: 500px;
        }
        
        .plotly-container {
            margin: 20px 0;
            min-height: 500px;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: var(--light-text);
        }
        
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top: 4px solid var(--primary-color);
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: var(--light-text);
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .grid-2, .grid-3 {
                grid-template-columns: 1fr;
            }
            
            .chart-container {
                height: 300px;
            }
        }
        
        /* Chart.js responsive fix */
        @media (max-width: 480px) {
            .chart-container {
                height: 250px;
            }
        }
    </style>
    
    <!-- Chart.js for most visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    <!-- Plotly.js for scientific visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/plotly.js@2.26.0/dist/plotly.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>🍏 Apple Health Dashboard</h1>
            <p class="subtitle">Interactive Health Analytics</p>
        </header>
        
        <div class="stats-grid" id="stats-grid">
            <div class="loading">
                <div class="spinner"></div>
                Loading statistics...
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Summary Statistics</h2>
            <div id="summary-stats"></div>
        </div>
        
        <div class="section">
            <h2>📈 Time Series Analysis</h2>
            <div class="grid-2">
                <div>
                    <h3>Heart Rate Trends</h3>
                    <div class="chart-container">
                        <canvas id="heartRateChart"></canvas>
                    </div>
                </div>
                <div>
                    <h3>Activity Levels</h3>
                    <div class="chart-container">
                        <canvas id="activityChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🏋️ Workout Analysis</h2>
            <div class="plotly-container">
                <div id="workoutChart"></div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Data Distributions</h2>
            <div class="grid-2">
                <div>
                    <h3>Record Types by Category</h3>
                    <div class="chart-container full-height">
                        <canvas id="recordTypesChart"></canvas>
                    </div>
                </div>
                <div>
                    <h3>Data Sources</h3>
                    <div class="chart-container full-height">
                        <canvas id="sourcesChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔬 Scientific Analysis</h2>
            <div class="plotly-container">
                <div id="correlationChart"></div>
            </div>
        </div>
        
        <footer>
            <p>Generated by Apple Health Dashboard | Data from Apple Health app</p>
            <p>Powered by Chart.js and Plotly.js</p>
        </footer>
    </div>
    
    <script>
        // Global variables
        let chartData = {};
        let statsData = {};
        let charts = {};
        
        // Load data
        async function loadData() {
            try {
                const [chartRes, statsRes] = await Promise.all([
                    fetch('chart_data.json'),
                    fetch('stats_data.json')
                ]);
                
                chartData = await chartRes.json();
                statsData = await statsRes.json();
                
                console.log('Data loaded successfully', {chartData, statsData});
                
                // Update stats grid
                updateStatsGrid();
                
                // Initialize charts
                initializeCharts();
                
            } catch (error) {
                console.error('Error loading data:', error);
                showError('Failed to load dashboard data. Please check the console for details.');
            }
        }
        
        function updateStatsGrid() {
            const statsGrid = document.getElementById('stats-grid');
            
            const stats = [
                { label: 'Total Records', value: statsData.total_records, icon: '📊' },
                { label: 'Workouts', value: statsData.total_workouts, icon: '🏋️' },
                { label: 'Data Sources', value: statsData.total_sources, icon: '📱' },
                { label: 'Record Types', value: statsData.total_record_types, icon: '📋' }
            ];
            
            statsGrid.innerHTML = stats.map(stat => `
                <div class="stat-card">
                    <div class="stat-icon">${stat.icon}</div>
                    <div class="stat-value">${stat.value.toLocaleString()}</div>
                    <div class="stat-label">${stat.label}</div>
                </div>
            `).join('');
        }
        
        function initializeCharts() {
            // Time series charts (Chart.js)
            createTimeSeriesCharts();
            
            // Distribution charts (Chart.js)
            createDistributionCharts();
            
            // Workout charts (Plotly.js)
            createWorkoutCharts();
            
            // Correlation charts (Plotly.js)
            createCorrelationCharts();
        }
        
        function createTimeSeriesCharts() {
            const timeSeries = chartData.time_series || {};
            
            // Heart Rate Chart
            if (timeSeries.HeartRate) {
                const ctx = document.getElementById('heartRateChart').getContext('2d');
                charts.heartRate = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: timeSeries.HeartRate.dates,
                        datasets: [
                            {
                                label: 'Average Heart Rate',
                                data: timeSeries.HeartRate.avg_values,
                                borderColor: '#ff6b6b',
                                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                                fill: true,
                                tension: 0.4,
                                pointRadius: 3,
                                pointHoverRadius: 6
                            },
                            {
                                label: 'Min Heart Rate',
                                data: timeSeries.HeartRate.min_values,
                                borderColor: 'rgba(255, 107, 107, 0.5)',
                                borderDash: [5, 5],
                                fill: false,
                                tension: 0.4,
                                pointRadius: 0
                            },
                            {
                                label: 'Max Heart Rate',
                                data: timeSeries.HeartRate.max_values,
                                borderColor: 'rgba(255, 107, 107, 0.5)',
                                borderDash: [5, 5],
                                fill: false,
                                tension: 0.4,
                                pointRadius: 0
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false
                        },
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: {
                                    padding: 15,
                                    font: { size: 12 }
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + ' bpm';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'Date' },
                                grid: { display: false }
                            },
                            y: {
                                title: { display: true, text: 'Beats Per Minute' },
                                beginAtZero: false
                            }
                        }
                    }
                });
            }
            
            // Activity Chart (StepCount or ActiveEnergy)
            const activityTypes = ['StepCount', 'ActiveEnergy'];
            for (const type of activityTypes) {
                if (timeSeries[type]) {
                    const ctx = document.getElementById('activityChart').getContext('2d');
                    const unit = type === 'StepCount' ? 'steps' : 'kcal';
                    const color = type === 'StepCount' ? '#4ecdc4' : '#ffe66d';
                    
                    charts.activity = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: timeSeries[type].dates,
                            datasets: [{
                                label: type === 'StepCount' ? 'Daily Steps' : 'Active Energy',
                                data: timeSeries[type].avg_values,
                                backgroundColor: color,
                                borderColor: color,
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'top',
                                    labels: { padding: 15, font: { size: 12 } }
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return context.parsed.y.toFixed(0) + ' ' + unit;
                                        }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    title: { display: true, text: 'Date' },
                                    grid: { display: false }
                                },
                                y: {
                                    title: { display: true, text: unit.charAt(0).toUpperCase() + unit.slice(1) },
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                    break;
                }
            }
        }
        
        function createDistributionCharts() {
            const dist = chartData.distributions || {};
            
            // Record Types Chart
            if (dist.record_types && dist.record_types.types.length > 0) {
                const ctx = document.getElementById('recordTypesChart').getContext('2d');
                
                // Group by category for better visualization
                const categories = {};
                dist.record_types.types.forEach((type, i) => {
                    const category = dist.record_types.categories[i];
                    if (!categories[category]) {
                        categories[category] = { labels: [], data: [], backgroundColors: [] };
                    }
                    categories[category].labels.push(type);
                    categories[category].data.push(dist.record_types.counts[i]);
                });
                
                const colors = {
                    'Vital Signs': '#ff6b6b',
                    'Activity': '#4ecdc4',
                    'Fitness': '#ffe66d',
                    'Sleep': '#a78bfa',
                    'Nutrition': '#fbbf24',
                    'Other': '#9ca3af'
                };
                
                charts.recordTypes = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: dist.record_types.types,
                        datasets: [{
                            label: 'Record Count',
                            data: dist.record_types.counts,
                            backgroundColor: dist.record_types.types.map(type => {
                                const category = dist.record_types.categories[dist.record_types.types.indexOf(type)];
                                return colors[category] || '#9ca3af';
                            }),
                            borderColor: '#ffffff',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.parsed.x + ' records';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'Number of Records' },
                                beginAtZero: true
                            },
                            y: {
                                title: { display: true, text: 'Record Type' }
                            }
                        }
                    }
                });
            }
            
            // Sources Chart
            if (dist.sources && dist.sources.names.length > 0) {
                const ctx = document.getElementById('sourcesChart').getContext('2d');
                
                charts.sources = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: dist.sources.names,
                        datasets: [{
                            data: dist.sources.counts,
                            backgroundColor: [
                                '#ff6b6b',
                                '#4ecdc4',
                                '#ffe66d',
                                '#a78bfa',
                                '#fbbf24'
                            ],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    padding: 20,
                                    font: { size: 12 }
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((context.parsed / total) * 100).toFixed(1);
                                        return context.label + ': ' + context.parsed + ' records (' + percentage + '%)';
                                    }
                                }
                            }
                        }
                    }
                });
            }
        }
        
        function createWorkoutCharts() {
            const workouts = chartData.workouts || {};
            const workoutTypes = Object.keys(workouts);
            
            if (workoutTypes.length === 0) {
                document.getElementById('workoutChart').innerHTML = 
                    '<p style="text-align: center; color: var(--light-text); padding: 40px;">No workout data available</p>';
                return;
            }
            
            // Prepare data for Plotly
            const traces = [];
            
            workoutTypes.forEach(type => {
                const workoutData = workouts[type];
                
                traces.push({
                    x: workoutData.map(w => w.date),
                    y: workoutData.map(w => w.duration),
                    name: type,
                    type: 'scatter',
                    mode: 'markers',
                    marker: {
                        size: workoutData.map(w => Math.max(8, w.duration / 2)),
                        color: workoutData.map(w => w.duration),
                        colorscale: 'Viridis',
                        showscale: true,
                        colorbar: { title: 'Duration (min)' }
                    },
                    text: workoutData.map(w => 
                        `Date: ${w.date}<br>Duration: ${w.duration} min<br>` +
                        (w.distance ? `Distance: ${w.distance} ${w.distance_unit || 'km'}<br>` : '') +
                        (w.energy ? `Energy: ${w.energy} kcal` : '')
                    ),
                    hovertemplate: '%{text}<extra></extra>'
                });
            });
            
            const layout = {
                title: 'Workout Analysis',
                xaxis: { title: 'Date' },
                yaxis: { title: 'Duration (minutes)' },
                hovermode: 'closest',
                showlegend: true,
                legend: { orientation: 'h', y: -0.2 },
                margin: { t: 40, b: 40, l: 50, r: 20 }
            };
            
            Plotly.newPlot('workoutChart', traces, layout, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d']
            });
        }
        
        function createCorrelationCharts() {
            const correlations = chartData.correlations || {};
            const correlationTypes = Object.keys(correlations);
            
            if (correlationTypes.length < 2) {
                document.getElementById('correlationChart').innerHTML = 
                    '<p style="text-align: center; color: var(--light-text); padding: 40px;">Insufficient data for correlation analysis</p>';
                return;
            }
            
            // Create subplots for each correlation
            const traces = [];
            
            correlationTypes.forEach((type, index) => {
                const data = correlations[type];
                
                traces.push({
                    x: data.map(d => d.date),
                    y: data.map(d => d.value),
                    name: type,
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { width: 2 },
                    marker: { size: 6 }
                });
            });
            
            const layout = {
                title: 'Health Metrics Correlation',
                xaxis: { title: 'Date' },
                yaxis: { title: 'Value' },
                hovermode: 'x unified',
                showlegend: true,
                legend: { orientation: 'h', y: -0.2 },
                margin: { t: 40, b: 40, l: 50, r: 20 }
            };
            
            Plotly.newPlot('correlationChart', traces, layout, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d']
            });
        }
        
        function showError(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.innerHTML = `<strong>Error:</strong> ${message}`;
            document.querySelector('.container').prepend(errorDiv);
        }
        
        // Initialize the dashboard
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Dashboard initialized, loading data...');
            loadData();
        });
        
        // Handle window resize for responsive charts
        window.addEventListener('resize', function() {
            Object.values(charts).forEach(chart => {
                if (chart && chart.resize) {
                    chart.resize();
                }
            });
        });
    </script>
</body>
</html>'''
    
    # Write HTML file
    html_file = output_dir / "interactive_dashboard.html"
    with open(html_file, 'w') as f:
        f.write(html_content)
    
    print(f"🌐 Generated interactive dashboard: {html_file}")