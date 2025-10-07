#!/usr/bin/env python3
"""
Download LANDFIRE data for Healdsburg, CA area
Example: Download ~100 sq mi area for fire analysis
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from real_data_downloader import LANDFIREDataDownloader


def main():
    print("\n" + "=" * 70)
    print("DOWNLOADING LANDFIRE DATA FOR HEALDSBURG, CA")
    print("=" * 70)
    
    # Healdsburg, CA coordinates
    healdsburg_lat = 38.6102
    healdsburg_lon = -122.8694
    
    # For 100 sq mi, we need approximately 10 x 10 mile square
    area_size_miles = 10
    
    print(f"\nLocation: Healdsburg, CA")
    print(f"Coordinates: {healdsburg_lat}, {healdsburg_lon}")
    print(f"Area: {area_size_miles} x {area_size_miles} miles (~{area_size_miles**2} sq mi)")
    print(f"\nThis area includes:")
    print("  - Healdsburg and surrounding wine country")
    print("  - Russian River Valley")
    print("  - Mixed oak woodlands and grasslands")
    print("  - Urban-wildland interface")
    
    # Essential products for fire analysis
    products = ['FBFM40', 'CBH', 'CBD', 'CC', 'SLPD', 'ASPD']
    
    print(f"\nProducts to download:")
    product_descriptions = {
        'FBFM40': 'Fire Behavior Fuel Model (40 models)',
        'CBH': 'Canopy Base Height',
        'CBD': 'Canopy Bulk Density',
        'CC': 'Canopy Cover',
        'SLPD': 'Slope (degrees)',
        'ASPD': 'Aspect (degrees)'
    }
    
    for prod in products:
        print(f"  • {prod}: {product_descriptions[prod]}")
    
    print("\n" + "=" * 70)
    proceed = input("Proceed with download? (yes/no): ").strip().lower()
    
    if proceed not in ['yes', 'y']:
        print("Download cancelled.")
        return
    
    # Initialize downloader
    downloader = LANDFIREDataDownloader()
    
    # Download the data
    print("\nStarting download...")
    print("=" * 70)
    
    files = downloader.download_sample_area(
        center_lat=healdsburg_lat,
        center_lon=healdsburg_lon,
        size_miles=area_size_miles,
        products=products
    )
    
    if files:
        print("\n" + "=" * 70)
        print("DOWNLOAD SUCCESSFUL!")
        print("=" * 70)
        print("\nDownloaded files:")
        for product, filepath in files.items():
            print(f"  ✓ {product}: {filepath}")
        
        print("\n" + "=" * 70)
        print("COMMAND TO REPEAT THIS DOWNLOAD:")
        print("=" * 70)
        print(f"""
python download_healdsburg.py

# Or use this Python code:
from scripts.real_data_downloader import LANDFIREDataDownloader

downloader = LANDFIREDataDownloader()
files = downloader.download_sample_area(
    center_lat={healdsburg_lat},
    center_lon={healdsburg_lon},
    size_miles={area_size_miles},
    products={products}
)
        """)
        
        print("\n" + "=" * 70)
        print("NEXT STEPS:")
        print("=" * 70)
        print("1. Examine the downloaded GeoTIFF files in data/landfire/")
        print("2. Create processing script to extract and visualize data")
        print("3. Run fire behavior analysis on real fuel models")
        print("4. Generate fire risk maps for the Healdsburg area")
        print("=" * 70 + "\n")
    else:
        print("\n" + "=" * 70)
        print("DOWNLOAD FAILED")
        print("=" * 70)
        print("Check the error messages above.")
        print("Common issues:")
        print("  - Internet connection problems")
        print("  - LANDFIRE services temporarily unavailable")
        print("  - Invalid bounding box coordinates")
        print("\nTry again in a few minutes.")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
