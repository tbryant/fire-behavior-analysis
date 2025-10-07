# Fire Behavior Analysis

Python toolkit for wildfire modeling, LANDFIRE data integration, and interactive visualization.

🌐 **[Live Demo](https://tbryant.github.io/fire-behavior-analysis/)** - Interactive fire map for Healdsburg, CA

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run demo with synthetic data
python scripts/04_demo_analysis.py

# Select region and download LANDFIRE data
python scripts/05_interactive_region_selector.py

# Generate interactive fire behavior map
python scripts/06_healdsburg_visualization.py

# Run fire behavior predictions
python examples/healdsburg_fire_predictions.py

# Publish to GitHub Pages
python update_pages.py
```

## Features

- **Fire Behavior Modeling**: Rothermel surface fire spread and Van Wagner crown fire models
- **Fire Predictions**: Landscape-scale fire behavior predictions under multiple weather scenarios
- **LANDFIRE Integration**: Download and process real geospatial fuel data from USGS
- **Interactive Visualizations**: Web maps showing fire spread rates, flame lengths, crown fire potential
- **Risk Analysis**: Landscape-scale fire behavior assessment across different conditions
- **GitHub Pages Publishing**: One-command deployment of interactive maps

## Project Structure

```
fire-behavior-analysis/
├── scripts/              # Core analysis modules
│   ├── 01_landfire_downloader.py
│   ├── 02_fire_behavior_calc.py
│   ├── 03_arcgis_integration.py
│   ├── 04_demo_analysis.py
│   ├── 05_interactive_region_selector.py
│   ├── 06_healdsburg_visualization.py
│   ├── 07_healdsburg_fire_predictions.py
│   └── real_data_downloader.py
├── examples/             # Example scripts and tools
│   ├── download_healdsburg.py
│   ├── download_landfire.py
│   ├── fire_calc.py
│   ├── healdsburg_fire_predictions.py
│   └── check_status.py
├── update_pages.py       # Publish to GitHub Pages
├── docs/                 # GitHub Pages site
├── data/landfire/        # Downloaded raster data (not in git)
└── outputs/              # Generated maps and reports
```

## Publishing to GitHub Pages

Share your fire maps online with one command:

```bash
# Generate visualization
python scripts/06_healdsburg_visualization.py

# Publish to GitHub Pages
python update_pages.py

# Commit and push
git add docs/ && git commit -m "Update fire map" && git push
```

Your map will be live at `https://YOUR_USERNAME.github.io/fire-behavior-analysis/` in 1-2 minutes.

**Additional options:**
```bash
# Publish specific file
python update_pages.py --source outputs/my_map.html --name my_region

# List published pages
python update_pages.py --list

# Create index for multiple maps
python update_pages.py --create-index
```

## Working with LANDFIRE Data

### Select Region Interactively
```bash
python scripts/05_interactive_region_selector.py
# Opens interactive map at http://localhost:8000/outputs/landfire_selector.html
```

### Download Data
```python
from scripts.real_data_downloader import LANDFIREDataDownloader

downloader = LANDFIREDataDownloader()
files = downloader.download_sample_area(
    center_lat=38.6102,    # Healdsburg, CA
    center_lon=-122.8694,
    size_miles=10,         # ~100 sq mi
    products=['FBFM40', 'CBH', 'CBD', 'CC', 'SLPD', 'ASPD']
)
```

### Available Products
- **FBFM40**: Fire Behavior Fuel Model (40 Scott & Burgan models)
- **CBH**: Canopy Base Height
- **CBD**: Canopy Bulk Density
- **CC**: Canopy Cover
- **SLPD**: Slope Degrees
- **ASPD**: Aspect Degrees

## Fire Behavior Analysis

### Healdsburg Fire Predictions Example

Generate landscape-scale fire behavior predictions under different weather scenarios:

```bash
# Download LANDFIRE data for Healdsburg (if not already done)
python examples/download_healdsburg.py

# Run fire predictions for multiple weather scenarios
python examples/healdsburg_fire_predictions.py
```

This creates an interactive map showing:
- **Flame length predictions** across the landscape (color-coded)
- **Rate of spread** predictions for each fuel type
- **Multiple weather scenarios**: Typical summer, Red Flag Warning, Extreme conditions
- **Interactive layer control** to compare scenarios

**Example scenarios analyzed:**
1. **Typical Summer Day**: 8 mph winds, 80°F, 35% RH
2. **Red Flag Warning**: 25 mph winds, 95°F, 15% RH  
3. **Extreme Fire Weather (Diablo Winds)**: 40 mph winds, 105°F, 8% RH

Output files:
- `outputs/healdsburg_fire_predictions.html` - Interactive map
- `outputs/healdsburg_fire_predictions_statistics.json` - Statistics for each scenario

### Calculate Fire Spread
```python
from scripts.fire_behavior_calc import FireBehaviorCalculator

calc = FireBehaviorCalculator()
result = calc.calculate_fire_behavior(
    fuel_model='GR2',        # Short grass
    moisture_1hr=6,          # 6% fuel moisture
    moisture_10hr=7,
    moisture_100hr=8,
    wind_speed=15,           # mph
    slope=20,                # degrees
    aspect=180               # south-facing
)

print(f"Rate of spread: {result['rate_of_spread_ch_hr']:.1f} chains/hr")
print(f"Flame length: {result['flame_length_ft']:.1f} feet")
```

## Fire Behavior Models

**Rothermel Surface Fire Spread Model**
- Calculates rate of spread based on fuel, weather, and topography
- Outputs: spread rate, flame length, fireline intensity

**Van Wagner Crown Fire Model**
- Determines crown fire initiation and spread potential
- Outputs: critical wind speeds, crown fire type (surface/passive/active)

## Dependencies

See `requirements.txt` for complete list. Key packages:
- `numpy`, `pandas` - Data processing
- `requests` - LANDFIRE API
- `folium` - Interactive maps
- `geopandas`, `rasterio`, `shapely` - Geospatial operations

## Data Sources

- **LANDFIRE**: [landfire.gov](https://landfire.gov/) - Landscape fire and resource management tools
- **Fire Models**: Scott & Burgan (2005) Standard Fire Behavior Fuel Models

## References

- Rothermel, R.C. (1972). A mathematical model for predicting fire spread in wildland fuels
- Scott, J.H. & Burgan, R.E. (2005). Standard fire behavior fuel models
- Van Wagner, C.E. (1977). Conditions for the start and spread of crown fire

## License

MIT License
    ```
* **Use Case:** Test specific fire spread hypotheses or compare a different model's output against your standard tools for a specific area.

* **Project:** ForeFire
* **Repository:** `https://github.com/forefireAPI/forefire`
* **Primary Language:** C++ with Python bindings
* **Installation:** Follow detailed instructions from their documentation at `https://forefire.readthedocs.io/`.
* **Use Case:** Highly scriptable. Excellent for batch processing many fire simulations under slightly different fuel or weather conditions to perform a sensitivity analysis.