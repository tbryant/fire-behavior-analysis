# Fire Analysis Scripts

This directory contains Python scripts for fire modeling and analysis workflows.

## Scripts Overview

### 1. `01_landfire_downloader.py`
Downloads and catalogs LANDFIRE datasets for fire modeling.

**Key Datasets:**
- FBFM40 - Fire Behavior Fuel Models (40 models)
- CBH - Canopy Base Height
- CBD - Canopy Bulk Density
- CC - Canopy Cover
- Elevation, Slope, Aspect

**Usage:**
```bash
python 01_landfire_downloader.py
```

### 2. `02_fire_behavior_calc.py`
Calculates fire behavior using simplified Rothermel model.

**Calculates:**
- Rate of spread (chains/hr, ft/min)
- Flame length
- Fireline intensity
- Fire type classification

**Usage:**
```bash
python 02_fire_behavior_calc.py
```

**Example scenarios included:**
- Grassland (mild and moderate conditions)
- Shrubland (extreme conditions)
- Timber (moderate conditions)

### 3. `03_arcgis_integration.py`
Demonstrates ArcGIS workflows for complexity analysis.

**Features:**
- Terrain complexity calculation
- Fuel complexity analysis
- Project complexity mapping for sales bids
- Integration with ArcGIS Field Maps

**Note:** Requires ArcGIS Pro and arcpy

**Usage:**
```bash
python 03_arcgis_integration.py
```

### 4. `04_demo_analysis.py` ⭐ **Start Here!**
Complete demonstration using synthetic data - no external data required.

**Demonstrates:**
- Landscape generation (terrain, fuels)
- Fire risk analysis
- Fire spread simulation
- Report generation

**Usage:**
```bash
python 04_demo_analysis.py
```

### 5. `05_interactive_region_selector.py`
Interactive web-based map for selecting and downloading LANDFIRE data regions.

**Features:**
- Draw custom regions on interactive map
- Automatically calculates download specifications
- Generates download configuration

**Usage:**
```bash
python 05_interactive_region_selector.py
# Opens browser at http://localhost:8000/outputs/landfire_selector.html
```

### 6. `06_healdsburg_visualization.py`
Creates interactive visualization of LANDFIRE data for Healdsburg, CA.

**Features:**
- Fuel model raster overlays (FBFM40)
- Canopy cover and slope layers
- Multiple base maps (satellite, topographic)
- Interactive legend and measurement tools

**Usage:**
```bash
python 06_healdsburg_visualization.py
```

### 7. `07_healdsburg_fire_predictions.py` ⭐ **NEW**
Landscape-scale fire behavior predictions using real LANDFIRE data.

**Calculates:**
- Fire spread rates across entire landscape
- Flame length predictions for each pixel
- Fireline intensity mapping
- Statistics for multiple weather scenarios

**Features:**
- Uses actual LANDFIRE fuel and terrain data
- Applies Rothermel fire spread model pixel-by-pixel
- Compares multiple weather scenarios
- Generates color-coded prediction maps

**Usage:**
```python
from scripts.healdsburg_fire_predictions import HealdsburgFirePredictor

predictor = HealdsburgFirePredictor()
predictor.load_data()

scenarios = [
    {
        'scenario_name': 'Red Flag Warning',
        'wind_speed': 25,
        'fuel_moisture': 5,
        'temperature': 95,
        'relative_humidity': 15,
    }
]

predictor.create_prediction_map(scenarios)
```

Or run the example:
```bash
python examples/healdsburg_fire_predictions.py
```

## Installation

### Basic Setup (Required)
```bash
# Install Python dependencies
pip install -r ../requirements.txt
```

### ArcGIS Setup (Optional)
For ArcGIS scripts, you need:
1. ArcGIS Pro installed
2. Use the Python environment that comes with ArcGIS Pro

## Quick Start

Run the demo to see everything in action:
```bash
python 04_demo_analysis.py
```

This will:
1. Create a synthetic landscape with varied terrain and fuels
2. Analyze fire risk under specified weather conditions
3. Simulate fire spread for 6 hours
4. Generate a JSON report in the `outputs/` directory

## Fire Modeling Tools Context

These scripts demonstrate concepts used in professional tools:

**Commercial/Governmental:**
- **Technosylva** - Fire spread forecasting and risk analysis
- **Xyloplan** - Forest management planning
- **FSIM** - USFS Large Fire Simulator
- **ESRI ArcGIS** - Spatial analysis and field operations

**Data Sources:**
- **LANDFIRE** - Fuel, vegetation, and terrain data
- **Vibrant Planet** - Land management platform

**Open Source:**
- **BehavePlus** - Fire behavior predictions
- **FlamMap** - Fire behavior mapping
- **FARSITE** - Fire area simulation

## Workflow Example

Typical fire analysis workflow:

1. **Data Acquisition** (`01_landfire_downloader.py`)
   - Download LANDFIRE data for your area
   - Organize into project structure

2. **Fire Behavior Analysis** (`02_fire_behavior_calc.py`)
   - Calculate fire behavior for different scenarios
   - Understand spread rates and intensity

3. **Complexity Mapping** (`03_arcgis_integration.py`)
   - Analyze terrain and fuel complexity
   - Support sales bids and project planning

4. **Operational Planning**
   - Export maps to ArcGIS Field Maps
   - Support field operations teams

## Output Files

Scripts generate outputs in `../outputs/`:
- JSON reports with analysis results
- Fire behavior predictions
- Risk statistics

## Notes

- Scripts use simplified models for demonstration
- For operational use, consult professional tools
- Real LANDFIRE data requires manual download from https://landfire.gov
- ArcGIS scripts require valid ArcGIS Pro license

## Resources

- **LANDFIRE**: https://landfire.gov/
- **FSIM**: https://www.firelab.org/project/fire-simulation-fsim-system
- **Technosylva**: https://www.technosylva.com/
- **ArcGIS Pro**: https://pro.arcgis.com/
- **Vibrant Planet**: https://www.vibrantplanet.net/
