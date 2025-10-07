# Fire Analysis Toolkit

Python-based wildfire modeling toolkit for fire behavior analysis, LANDFIRE data integration, and risk assessment.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run demo with synthetic data
python scripts/04_demo_analysis.py

# 3. Download real LANDFIRE data
python scripts/05_interactive_region_selector.py
python download_healdsburg.py

# 4. Visualize fuel models on interactive map
python scripts/06_healdsburg_visualization.py

# 5. Interactive fire calculator
python fire_calc.py
```

## 🌐 Live Demo

**[View Interactive Fire Map](https://tbryant.github.io/fire-behavior-analysis/)** - Explore fire behavior analysis for Healdsburg, CA (no installation required!)

## Features

- **Fire Behavior Modeling**: Rothermel fire spread calculations with 5 fuel models (GR1, GR2, SH5, TU1, TL5)
- **LANDFIRE Integration**: Download and process real geospatial fuel data from USGS
- **Interactive Tools**: Web-based region selector and CLI calculator
- **Risk Analysis**: Landscape-scale fire risk assessment and spread simulation
- **ArcGIS Workflows**: Complexity analysis for project bidding
- **GitHub Pages**: Share interactive visualizations online

## Project Structure

```
fire-analysis/
├── scripts/
│   ├── 01_landfire_downloader.py    # LANDFIRE data catalog
│   ├── 02_fire_behavior_calc.py     # Rothermel fire model
│   ├── 03_arcgis_integration.py     # ArcGIS workflows
│   ├── 04_demo_analysis.py          # Complete demo with synthetic data
│   ├── 05_interactive_region_selector.py  # Web map for region selection
│   ├── 06_healdsburg_visualization.py     # Interactive fuel model visualization
│   └── real_data_downloader.py      # LANDFIRE data downloader
├── fire_calc.py                     # Interactive CLI calculator
├── download_healdsburg.py           # Example download script
├── data/landfire/                   # Downloaded raster data (not in git)
└── outputs/                         # Analysis results and maps
```

## 📤 Publishing to GitHub Pages

Update your hosted fire maps easily:

```bash
# Update main page with latest visualization
python update_pages.py

# Add a specific output file
python update_pages.py --source outputs/my_region_map.html --name my_region

# List all published pages
python update_pages.py --list

# Then commit and push
git add docs/
git commit -m "Update fire visualization"
git push
```

Your maps will be live at: `https://YOUR_USERNAME.github.io/fire-behavior-analysis/`

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

## Dependencies

Core packages:
- `numpy`, `pandas` - Data processing
- `requests` - LANDFIRE API calls
- `folium` - Interactive maps
- `geopandas`, `shapely` - Geospatial operations
- `arcgis` - ArcGIS integration (optional)

See `requirements.txt` for complete list.

---

## Geospatial and Wildfire Mitigation Software Ecosystem

This section outlines the broader software and data ecosystem for wildfire mitigation planning and operations.

### 1. Foundational Data (Input for all Models)

* **Tool:** LANDFIRE (Landscape Fire and Resource Management Planning Tools)
* **Website:** [https://landfire.gov/](https://landfire.gov/)
* **Action:**
    * Use the website's data portal to download key geospatial layers for your Area of Interest (AOI).
    * **Primary Layers for Analysis:** Fuel Buffer Model (FBFM40), Canopy Base Height (CBH), Canopy Bulk Density (CBD).
    * **Coding Task:** Use Python libraries like `gdal` and `rasterio` to automate the downloading, clipping, and re-projecting of LANDFIRE data to match your project's coordinate system. This is a common preparatory step before loading data into ArcGIS or another model.

    ```python
    # Example pseudocode for data prep
    # import gdal
    #
    # aoi_shapefile = 'path/to/my_project_boundary.shp'
    # landfire_fuel_model_tif = 'path/to/downloaded_landfire_fuel.tif'
    # output_clipped_tif = 'path/to/project_fuel_model.tif'
    #
    # # Use gdal.Warp to clip the raster to the shapefile boundary
    # gdal.Warp(output_clipped_tif, landfire_fuel_model_tif, cutlineDSName=aoi_shapefile, cropToCutline=True)
    ```

### 2. Core Analysis and Planning Platforms (Commercial & Governmental)

These systems are typically desktop or enterprise applications and are not installed via `pip` or `git`. The coding tasks involve data preparation *for* them or analysis of their *outputs*.

* **Tool:** ESRI ArcGIS Pro
* **Role:** Central hub for data management, visualization, and custom analysis (e.g., complexity analysis).
* **Action:**
    * **Coding Task:** Automate your "complexity analysis" using `arcpy`, ESRI's Python site-package. A script could take your prepared LANDFIRE layers (fuel, slope, canopy) and access data as inputs, then run a series of geoprocessing tools (e.g., Reclassify, Weighted Overlay) to produce a final complexity map. This standardizes your bidding process.

* **Tool:** U.S. Forest Service FSIM (Large Fire Simulator)
* **Website:** [https://www.firelab.org/project/fire-simulation-fsim-system](https://www.firelab.org/project/fire-simulation-fsim-system)
* **Role:** Strategic, landscape-scale probabilistic risk assessment.
* **Action:**
    * Installation involves downloading the application and a large amount of specific data from the Forest Service.
    * **Coding Task:** FSIM inputs are highly structured text files (`.lcp`, `.fmd`, etc.) and spatial data. A key coding task is writing Python scripts to convert your standard GIS data (like LANDFIRE TIFs) into the specific formats required by FSIM. Use `gdal` and `numpy` for this.

* **Tool:** Technosylva Suite (Wildfire Analyst, FireSim)
* **Website:** [https://www.technosylva.com/](https://www.technosylva.com/)
* **Role:** Commercial, operational fire spread forecasting and risk analysis.
* **Action:**
    * This is licensed enterprise software. You cannot install it from a public repo.
    * **Coding Task:** If Technosylva provides an API, you could write Python scripts to pull simulation results or risk data into your own systems for custom analysis or dashboarding.

### 3. Open Source Simulators (For Research & Customization)

These are tools you can install and run directly. They are best for specific, targeted research questions that fall outside the scope of the major platforms.

* **Project:** ELMFIRE
* **Repository:** `https://github.com/elmfire/elmfire`
* **Primary Language:** C++
* **Installation:** Follow build instructions in the repository. Requires a C++ compilation environment.
    ```bash
    git clone [https://github.com/elmfire/elmfire.git](https://github.com/elmfire/elmfire.git)
    cd elmfire
    # Follow makefile instructions
    ```
* **Use Case:** Test specific fire spread hypotheses or compare a different model's output against your standard tools for a specific area.

* **Project:** ForeFire
* **Repository:** `https://github.com/forefireAPI/forefire`
* **Primary Language:** C++ with Python bindings
* **Installation:** Follow detailed instructions from their documentation at `https://forefire.readthedocs.io/`.
* **Use Case:** Highly scriptable. Excellent for batch processing many fire simulations under slightly different fuel or weather conditions to perform a sensitivity analysis.