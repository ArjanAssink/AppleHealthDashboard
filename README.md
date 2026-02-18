# Apple Health Dashboard

A Python-based dashboard for locally analyzing and visualizing your Apple Health data. Converts Apple Health `.zip` exports into an interactive HTML dashboard powered by Apache ECharts.

## Quick Start

### 1. Export Your Apple Health Data

1. **On iPhone/iPad:**
   - Open the **Health app**
   - Tap your **profile picture** (top right)
   - Scroll down and tap **Export All Health Data**
   - Save the `.zip` file

2. **On Mac:**
   - Open the **Health app**
   - Click your **profile picture** (top right)
   - Click **Export Health Data**
   - Save the `.zip` file

### 2. Set Up the Project

```bash
git clone https://github.com/ArjanAssink/AppleHealthDashboard.git
cd AppleHealthDashboard

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Add Your Health Data

Place your Apple Health export `.zip` file in the `data/health_exports/` directory:

```bash
cp ~/Downloads/apple_health_export.zip data/health_exports/
```

### 4. Run the Pipeline

```bash
python3 main.py
```

This will parse your health data, export structured JSON files, and generate an interactive HTML dashboard in the `output/` directory.

### 5. View Your Dashboard

The dashboard loads data via `fetch()`, so you need to serve it over HTTP:

```bash
python3 -m http.server 8000 --directory output
```

Then open http://localhost:8000 in your browser.

## Project Structure

```
AppleHealthDashboard/
├── data/
│   └── health_exports/          # Place your .zip files here (gitignored)
├── output/                      # Generated dashboard and JSON data (gitignored)
│   ├── index.html               # Interactive ECharts dashboard
│   └── data/                    # Pre-aggregated JSON time series
├── config/
│   └── config.json              # Optional configuration
├── src/
│   ├── data_processing/         # Health data parsing and JSON export
│   ├── visualization/           # HTML dashboard generation
│   └── utils/                   # Configuration management
├── tests/
├── main.py                      # Main entry point
└── requirements.txt
```

## Features

- **Interactive charts** — time series with pan/zoom, daily/weekly/monthly granularity
- **Workout tracking** — calendar heatmaps, weekly frequency, type filtering
- **100+ metric types** — steps, heart rate, sleep, nutrition, body measurements, and more
- **Category-grouped sidebar** with search
- **Privacy first** — all processing is local, health data is gitignored

## Configuration

The dashboard uses an optional config file at `config/config.json`. You can customize visualization theme, timezone, excluded sources/types, and dashboard behavior.

## Development

```bash
# Type checking
mypy src/

# Tests
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
