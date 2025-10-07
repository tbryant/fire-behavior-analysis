# Fire Analysis Visualization

Interactive wildfire behavior analysis and prediction using LANDFIRE data and the Rothermel fire spread model.

## Interactive Map

**[View the Comprehensive Fire Map](index.html)**

### Features

- **Extreme Fire Conditions**: 70 mph NE winds, 2% fuel moisture, 95°F
- **48-Hour Fire Spread Simulation**: Time-to-arrival isochrones showing fire progression
- **Fuel Models Layer**: FBFM40 vegetation types (grass, shrub, timber)
- **Terrain Analysis**: Slope visualization
- **Satellite Imagery**: Toggleable aerial photography overlay
- **Predicted Burn Area**: 1,092 acres from NE grasslands ignition point

### Simulation Details

Based on extreme conditions similar to the 2017 Tubbs Fire:
- **Wind**: 70 mph from northeast (45°)
- **Fuel Moisture**: 2% (critically dry)
- **Temperature**: 95°F, 25% relative humidity
- **Ignition**: Northeast grasslands with continuous fuel
- **Duration**: 48-hour fire spread projection

The map includes toggleable layers and time-to-arrival isochrones color-coded from immediate threat (red) to distant (purple).

### Technical Details

- **Metadata**: [JSON output file](comprehensive_fire_map_data.json) contains all simulation parameters and results
- **Fire Model**: Rothermel (1972) surface fire spread equations
- **Fuel Models**: Scott & Burgan (2005) FBFM40 classification
- **Simulation**: Cellular wave propagation using Huygens' principle
- **Data**: LANDFIRE landscape data for Healdsburg, California

## Data Sources

- **LANDFIRE**: Landscape fire and resource management planning tools database
- **Analysis**: Fire behavior calculations based on crown fire initiation and spread models

## About

This analysis was generated using fire behavior modeling scripts available in the main repository.
