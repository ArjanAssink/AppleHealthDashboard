# 🍏 Apple Health Dashboard

A Python-based dashboard for locally analyzing and visualizing your Apple Health data. This project allows you to explore your health metrics, trends, and insights from the Apple Health export files.

## 🚀 Quick Start

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
# Clone the repository
git clone https://github.com/your-username/AppleHealthDashboard.git
cd AppleHealthDashboard

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Add Your Health Data

Place your Apple Health export `.zip` file in the `data/health_exports/` directory:

```bash
# Copy your export file (replace with your actual filename)
cp ~/Downloads/apple_health_export.zip data/health_exports/
```

### 4. Run the Dashboard

```bash
python main.py
```

This will:
- Parse your health data
- Generate visualizations
- Create an interactive HTML dashboard
- Save all outputs in the `output/` directory

### 5. View Your Dashboard

Open the generated dashboard:

```bash
open output/dashboard.html
```

## 📁 Project Structure

```
AppleHealthDashboard/
├── data/
│   └── health_exports/          # Place your .zip files here (GIT IGNORED)
│       └── README.md            # Instructions for health exports
├── output/                      # Generated dashboards and visualizations (GIT IGNORED)
├── config/                      # Configuration files
│   └── config.json              # User configuration
├── src/
│   ├── data_processing/         # Data parsing and processing
│   ├── visualization/           # Dashboard generation and visualizations
│   └── utils/                   # Utility functions and config management
├── tests/                      # Test files
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
└── README.md                    # This file
```

## 🔧 Configuration

The dashboard uses a configuration file at `config/config.json`. You can customize:

- Visualization settings (themes, date formats)
- Data processing options (exclude sources/types)
- Dashboard behavior

## 📊 Features

### Data Processing
- ✅ Parse Apple Health XML export files
- ✅ Extract structured health records with metadata
- ✅ Handle various health data types (heart rate, steps, sleep, etc.)

### Visualizations
- ✅ Time series analysis for key metrics
- ✅ Statistical distributions and trends
- ✅ Interactive HTML dashboard
- ✅ Exportable charts and graphs

### Privacy
- 🔒 **Your health data stays local** - no cloud processing
- 🔒 **Git ignored** - health export files are never committed
- 🔒 **Temporary processing** - extracted data is cleaned up automatically

## 🛠️ Development

### Running Tests

```bash
pytest
```

### Adding New Visualizations

1. Add new visualization functions to `src/visualization/dashboard.py`
2. Update the HTML template to include the new visualizations
3. Add any new dependencies to `requirements.txt`

### Contributing

Contributions are welcome! Please open issues for bugs or feature requests, and submit pull requests for improvements.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Resources

- [Apple Health Export Format Documentation](https://developer.apple.com/documentation/healthkit)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Documentation](https://matplotlib.org/stable/contents.html)

---

**Note:** This project is designed to work with your personal health data. Always be cautious when handling sensitive health information and ensure you comply with all relevant privacy regulations.
