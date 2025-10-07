#!/usr/bin/env python3
"""
LANDFIRE Data Downloader - Real Implementation
Downloads actual LANDFIRE data using their web services
"""

import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
from datetime import datetime


class LANDFIREDataDownloader:
    """
    Download real LANDFIRE data for specified geographic areas
    
    Note: LANDFIRE provides data through:
    1. Direct download portal (manual)
    2. LandfireProductService (web service - requires specific requests)
    3. Bulk download by state/zone
    """
    
    # LANDFIRE web service endpoints
    LANDFIRE_BASE_URL = "https://lfps.usgs.gov/arcgis/rest/services"
    
    # Product codes for LF 2022 (most recent complete version for CONUS)
    # Format: Landfire_LF220/US_220<PRODUCT>_22
    LF220_PRODUCTS = {
        'FBFM40': 'Landfire_LF220/US_220F40_22',  # 40 Fire Behavior Fuel Models
        'FBFM13': 'Landfire_LF220/US_220F13_22',  # 13 Fire Behavior Fuel Models
        'CBH': 'Landfire_LF220/US_220CBH_22',
        'CBD': 'Landfire_LF220/US_220CBD_22',
        'CC': 'Landfire_LF220/US_220CC_22',
        'CH': 'Landfire_LF220/US_220CH_22',
        'SLPD': 'Landfire_LF220/US_SLPD2020',
        'ASPD': 'Landfire_LF220/US_ASP2020',
        'ELEV': 'Landfire_LF220/US_ELEV2020',
        'EVC': 'Landfire_LF220/US_220EVC_22',
        'EVH': 'Landfire_LF220/US_220EVH_22',
    }
    
    # State FIPS codes for LANDFIRE downloads
    STATE_CODES = {
        'CA': {'name': 'California', 'fips': '06'},
        'OR': {'name': 'Oregon', 'fips': '41'},
        'WA': {'name': 'Washington', 'fips': '53'},
        'MT': {'name': 'Montana', 'fips': '30'},
        'ID': {'name': 'Idaho', 'fips': '16'},
        'WY': {'name': 'Wyoming', 'fips': '56'},
        'AZ': {'name': 'Arizona', 'fips': '04'},
        'NM': {'name': 'New Mexico', 'fips': '35'},
        'NV': {'name': 'Nevada', 'fips': '32'},
        'UT': {'name': 'Utah', 'fips': '49'},
        'CO': {'name': 'Colorado', 'fips': '08'},
        'TX': {'name': 'Texas', 'fips': '48'},
        'OK': {'name': 'Oklahoma', 'fips': '40'},
        'KS': {'name': 'Kansas', 'fips': '20'},
    }
    
    def __init__(self, output_dir: str = "data/landfire"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LANDFIRE-Fire-Analysis-Tool/1.0'
        })
    
    def get_service_info(self, product: str) -> Optional[Dict]:
        """
        Get information about a LANDFIRE product service
        """
        if product not in self.LF220_PRODUCTS:
            print(f"Unknown product: {product}")
            return None
        
        service_name = self.LF220_PRODUCTS[product]
        url = f"{self.LANDFIRE_BASE_URL}/{service_name}/ImageServer?f=json"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Service not available: {url}")
                return None
        except Exception as e:
            print(f"Error accessing service: {e}")
            return None
    
    def download_by_bbox(
        self,
        product: str,
        bbox: Tuple[float, float, float, float],
        output_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Download LANDFIRE data for a bounding box
        
        Args:
            product: Product code (e.g., 'FBFM40')
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
            output_filename: Optional custom filename
        
        Returns:
            Path to downloaded file or None if failed
        """
        if product not in self.LF220_PRODUCTS:
            print(f"Unknown product: {product}")
            return None
        
        service_name = self.LF220_PRODUCTS[product]
        
        # LANDFIRE uses ArcGIS Image Service export
        export_url = f"{self.LANDFIRE_BASE_URL}/{service_name}/ImageServer/exportImage"
        
        # Create bounding box string
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        
        # Request parameters
        params = {
            'bbox': bbox_str,
            'bboxSR': '4326',  # WGS84
            'size': '2000,2000',  # Max reasonable size
            'imageSR': '4326',
            'format': 'tiff',
            'pixelType': 'S16',
            'noData': '-9999',
            'interpolation': 'RSP_NearestNeighbor',
            'f': 'image'
        }
        
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{product}_{timestamp}.tif"
        
        output_path = self.output_dir / output_filename
        
        print(f"\nDownloading {product} data...")
        print(f"  Bounding box: {bbox}")
        print(f"  Output: {output_path}")
        
        try:
            response = self.session.get(export_url, params=params, timeout=60, stream=True)
            
            if response.status_code == 200:
                # Save the file
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = output_path.stat().st_size
                print(f"  ✓ Downloaded: {file_size:,} bytes")
                return str(output_path)
            else:
                print(f"  ✗ Download failed: HTTP {response.status_code}")
                print(f"    Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"  ✗ Error downloading: {e}")
            return None
    
    def download_sample_area(
        self,
        center_lat: float,
        center_lon: float,
        size_miles: float = 10,
        products: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Download a sample area around a center point
        
        Args:
            center_lat: Latitude of center point
            center_lon: Longitude of center point  
            size_miles: Size of area in miles (creates square)
            products: List of products to download (default: essential products)
        
        Returns:
            Dictionary mapping product codes to file paths
        """
        if products is None:
            products = ['FBFM40', 'CBH', 'CBD', 'CC', 'SLPD', 'ASPD']
        
        # Calculate bounding box
        # Rough conversion: 1 degree latitude ≈ 69 miles
        # 1 degree longitude varies by latitude
        lat_offset = size_miles / 69.0 / 2
        lon_offset = size_miles / (69.0 * abs(0.99 * center_lat)) / 2
        
        bbox = (
            center_lon - lon_offset,  # min_lon
            center_lat - lat_offset,  # min_lat
            center_lon + lon_offset,  # max_lon
            center_lat + lat_offset   # max_lat
        )
        
        print("\n" + "=" * 70)
        print(f"DOWNLOADING SAMPLE AREA")
        print("=" * 70)
        print(f"Center: {center_lat:.4f}, {center_lon:.4f}")
        print(f"Size: {size_miles} miles x {size_miles} miles")
        print(f"Bounding Box: {bbox}")
        print(f"Products: {', '.join(products)}")
        print("=" * 70)
        
        downloaded_files = {}
        
        for product in products:
            file_path = self.download_by_bbox(product, bbox)
            if file_path:
                downloaded_files[product] = file_path
            time.sleep(1)  # Be nice to the server
        
        print("\n" + "=" * 70)
        print(f"DOWNLOAD COMPLETE: {len(downloaded_files)}/{len(products)} files")
        print("=" * 70)
        
        for product, path in downloaded_files.items():
            print(f"  ✓ {product}: {path}")
        
        # Save metadata
        metadata = {
            'download_time': datetime.now().isoformat(),
            'center': {'lat': center_lat, 'lon': center_lon},
            'bbox': bbox,
            'size_miles': size_miles,
            'products': products,
            'files': downloaded_files
        }
        
        metadata_file = self.output_dir / f"download_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✓ Metadata saved: {metadata_file}")
        
        return downloaded_files
    
    def get_popular_locations(self) -> Dict[str, Dict]:
        """
        Get some popular/interesting locations for fire analysis
        """
        return {
            'Yosemite_CA': {
                'name': 'Yosemite National Park, CA',
                'lat': 37.8651,
                'lon': -119.5383,
                'description': 'Sierra Nevada, mixed conifer forests'
            },
            'Portland_OR': {
                'name': 'Portland, OR area',
                'lat': 45.5152,
                'lon': -122.6784,
                'description': 'Pacific Northwest, Douglas-fir forests'
            },
            'Boulder_CO': {
                'name': 'Boulder, CO area',
                'lat': 40.0150,
                'lon': -105.2705,
                'description': 'Front Range, ponderosa pine and grasslands'
            },
            'Flagstaff_AZ': {
                'name': 'Flagstaff, AZ area',
                'lat': 35.1983,
                'lon': -111.6513,
                'description': 'Southwest, ponderosa pine forests'
            },
            'Boise_ID': {
                'name': 'Boise, ID area',
                'lat': 43.6150,
                'lon': -116.2023,
                'description': 'Intermountain West, sagebrush and forests'
            },
        }


def main():
    """
    Main entry point - demonstrate data download
    """
    print("\n" + "=" * 70)
    print("LANDFIRE REAL DATA DOWNLOADER")
    print("=" * 70)
    print()
    
    downloader = LANDFIREDataDownloader()
    
    # Show popular locations
    print("Popular locations for fire analysis:")
    print("-" * 70)
    locations = downloader.get_popular_locations()
    for i, (key, loc) in enumerate(locations.items(), 1):
        print(f"{i}. {loc['name']}")
        print(f"   {loc['description']}")
        print(f"   Coordinates: {loc['lat']:.4f}, {loc['lon']:.4f}")
        print()
    
    print("-" * 70)
    print("\nExample: Download data for Yosemite area")
    print("-" * 70)
    
    # Example download (commented out to avoid automatic download)
    # Uncomment to actually download data:
    
    print("\nTo download data, use:")
    print("""
downloader = LANDFIREDataDownloader()

# Download a small area around Yosemite
files = downloader.download_sample_area(
    center_lat=37.8651,
    center_lon=-119.5383,
    size_miles=5,  # 5x5 mile area
    products=['FBFM40', 'CBH', 'CBD', 'SLPD']
)

# Or download by custom bounding box
file = downloader.download_by_bbox(
    product='FBFM40',
    bbox=(-119.6, 37.8, -119.4, 38.0)  # (min_lon, min_lat, max_lon, max_lat)
)
    """)
    
    print("\n" + "=" * 70)
    print("TESTING: Checking LANDFIRE service availability")
    print("=" * 70)
    
    # Test service availability
    for product in ['FBFM40', 'CBH', 'SLPD']:
        print(f"\nChecking {product} service...")
        info = downloader.get_service_info(product)
        if info:
            print(f"  ✓ Service available")
            if 'description' in info:
                print(f"    Description: {info['description'][:100]}...")
            if 'extent' in info:
                extent = info['extent']
                print(f"    Extent: {extent.get('xmin', 'N/A')} to {extent.get('xmax', 'N/A')}")
        else:
            print(f"  ✗ Service not available or error")
    
    print("\n" + "=" * 70)
    print("Ready to download real LANDFIRE data!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
