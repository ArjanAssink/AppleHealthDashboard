# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline (parse health data -> generate dashboards)
python3 main.py

# View the interactive dashboard
open output/index.html

# Type checking
mypy src/

# Tests
pytest
pytest tests/test_foo.py -v          # single test file
pytest tests/test_foo.py::test_bar   # single test
```

## Architecture

The project is a local-only pipeline that converts Apple Health `.zip` exports into interactive HTML dashboards. No cloud services or build tools required.

### Pipeline flow

```
.zip in data/health_exports/
  → AppleHealthParser (src/data_processing/health_parser.py)
    extracts zip, parses export.xml, returns List[HealthRecord]
  → HealthDataExporter (src/data_processing/health_exporter.py)
    converts to DataFrame, aggregates daily/weekly/monthly, writes JSON to output/data/
  → generate_html_dashboard (src/visualization/html_dashboard.py)
    writes standalone output/index.html that lazy-loads the JSON via fetch()
  → generate_dashboard (src/visualization/dashboard.py)
    legacy path: matplotlib/seaborn PNG charts + basic output/dashboard.html
```

`main.py` orchestrates this sequence. Both the legacy and modern dashboard paths run.

### Core data structure

`HealthRecord` (dataclass in `health_parser.py`): `record_type`, `source`, `unit`, `value` (float), `start_date`, `end_date`, `metadata` dict. The parser produces these from both `<Record>` and `<Workout>` XML elements.

### Exporter output structure

```
output/data/
├── manifest.json              # index of all metrics, date ranges, sources
├── workouts.json              # workout summaries by type
└── metrics/{metric_id}.json   # per-metric time series (daily/weekly/monthly)
```

Metric IDs are derived by stripping `HKQuantityTypeIdentifier`/`HKWorkoutActivityType` prefixes and converting CamelCase to snake_case.

### Aggregation convention

Extensive quantities (steps, calories, distance) use **sum**; intensive quantities (heart rate, weight) use **mean**. The mapping is defined in `METRIC_METADATA` in `health_exporter.py` (~100 Apple Health types). Unmapped types fall back to heuristics based on the unit string.

### Frontend

`html_dashboard.py` emits a single self-contained HTML file using Apache ECharts (loaded from CDN). It lazy-loads metric JSON files on navigation and caches them in `state.metricCache`. Features include category-grouped sidebar, daily/weekly/monthly tabs, GitHub-style workout calendar heatmaps, and responsive layout.

### Configuration

`config/config.json` (optional) — merged with defaults via `src/utils/config_manager.py`. Controls visualization theme, timezone, excluded sources/types, and dashboard behavior.

### Privacy

Health data (`data/health_exports/`) and generated output (`output/`) are gitignored. The parser extracts to a temp directory and cleans up automatically.
