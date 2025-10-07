# LANDFIRE Data Directory

This directory contains downloaded LANDFIRE geospatial data files.

## Current Downloads

Run `python download_healdsburg.py` to download data for Healdsburg, CA area.

Downloaded files for this project (not in git):
- FBFM40_*.tif - Fire Behavior Fuel Model (40 models)
- CBH_*.tif - Canopy Base Height
- CBD_*.tif - Canopy Bulk Density  
- CC_*.tif - Canopy Cover
- SLPD_*.tif - Slope Degrees
- ASPD_*.tif - Aspect Degrees

## File Formats

All files are GeoTIFF format:
- Coordinate System: WGS84 (EPSG:4326)
- Resolution: 30 meters
- Data Type: 16-bit signed integer
- NoData Value: -9999

## Metadata

Download metadata is saved in `download_metadata_*.json` files.

## Downloading Your Own Data

Use the download scripts:
```bash
# Download for Healdsburg area
python download_healdsburg.py

# Download custom area
python download_landfire.py

# Or use Python directly
from scripts.real_data_downloader import LANDFIREDataDownloader
downloader = LANDFIREDataDownloader()
files = downloader.download_sample_area(
    center_lat=YOUR_LAT,
    center_lon=YOUR_LON,
    size_miles=10
)
```

## Data Not Committed to Git

LANDFIRE data files are large (8-10MB each) and are excluded from git via `.gitignore`.
You need to download them yourself using the scripts provided.

## More Information

- LANDFIRE Website: https://landfire.gov/
- Data Documentation: https://landfire.gov/documents.php
- Service Status: https://lfps.usgs.gov/arcgis/rest/services
