#!/usr/bin/env python3
"""
Download Real LANDFIRE Data - Interactive Script
Quickly download LANDFIRE data for testing and analysis
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from real_data_downloader import LANDFIREDataDownloader


def main():
    print("\n" + "=" * 70)
    print("LANDFIRE DATA DOWNLOAD - INTERACTIVE MODE")
    print("=" * 70)
    print()
    
    downloader = LANDFIREDataDownloader()
    locations = downloader.get_popular_locations()
    
    print("Select a location to download sample data:")
    print("-" * 70)
    
    location_list = list(locations.items())
    for i, (key, loc) in enumerate(location_list, 1):
        print(f"{i}. {loc['name']}")
        print(f"   {loc['description']}")
    
    print(f"{len(location_list) + 1}. Custom coordinates")
    print("-" * 70)
    
    while True:
        try:
            choice = input(f"\nSelect location (1-{len(location_list) + 1}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(location_list):
                key = location_list[choice_num - 1][0]
                loc = locations[key]
                center_lat = loc['lat']
                center_lon = loc['lon']
                location_name = loc['name']
                break
            elif choice_num == len(location_list) + 1:
                center_lat = float(input("Enter latitude: ").strip())
                center_lon = float(input("Enter longitude: ").strip())
                location_name = "Custom location"
                break
            else:
                print(f"Please enter a number between 1 and {len(location_list) + 1}")
        except ValueError:
            print("Please enter a valid number")
    
    # Ask for area size
    print(f"\nSelected: {location_name}")
    print(f"Coordinates: {center_lat:.4f}, {center_lon:.4f}")
    
    while True:
        try:
            size_input = input("\nArea size in miles (default: 5): ").strip()
            size_miles = float(size_input) if size_input else 5.0
            if 1 <= size_miles <= 50:
                break
            else:
                print("Size must be between 1 and 50 miles")
        except ValueError:
            print("Please enter a valid number")
    
    # Select products
    print("\nAvailable products:")
    all_products = ['FBFM40', 'CBH', 'CBD', 'CC', 'CH', 'SLPD', 'ASPD', 'ELEV']
    for i, prod in enumerate(all_products, 1):
        print(f"  {i}. {prod}")
    
    print("\nPress Enter for essential products (FBFM40, CBH, CBD, SLPD, ASPD)")
    print("Or enter product numbers separated by commas (e.g., 1,2,3):")
    
    prod_input = input("Products: ").strip()
    
    if not prod_input:
        products = ['FBFM40', 'CBH', 'CBD', 'SLPD', 'ASPD']
    else:
        try:
            indices = [int(x.strip()) - 1 for x in prod_input.split(',')]
            products = [all_products[i] for i in indices if 0 <= i < len(all_products)]
        except:
            print("Invalid input, using essential products")
            products = ['FBFM40', 'CBH', 'CBD', 'SLPD', 'ASPD']
    
    # Confirm download
    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"Location: {location_name}")
    print(f"Center: {center_lat:.4f}, {center_lon:.4f}")
    print(f"Area: {size_miles} x {size_miles} miles")
    print(f"Products: {', '.join(products)}")
    print(f"Estimated size: ~{len(products) * 2}MB")
    print("=" * 70)
    
    confirm = input("\nProceed with download? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        print("\nStarting download...")
        files = downloader.download_sample_area(
            center_lat=center_lat,
            center_lon=center_lon,
            size_miles=size_miles,
            products=products
        )
        
        if files:
            print("\n" + "=" * 70)
            print("SUCCESS! Downloaded files:")
            print("=" * 70)
            for product, filepath in files.items():
                print(f"  {product}: {filepath}")
            
            print("\n" + "=" * 70)
            print("NEXT STEPS")
            print("=" * 70)
            print("1. Examine the downloaded GeoTIFF files")
            print("2. Use scripts/07_process_landfire_data.py to extract and visualize")
            print("3. Run fire behavior analysis on real data")
            print("=" * 70)
        else:
            print("\nDownload failed or incomplete. Check error messages above.")
    else:
        print("\nDownload cancelled.")
    
    print()


if __name__ == "__main__":
    main()
