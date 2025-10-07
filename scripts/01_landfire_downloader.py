#!/usr/bin/env python3
"""
LANDFIRE Data Downloader
Downloads key fire modeling datasets from LANDFIRE
"""

import os
import requests
from pathlib import Path
from typing import List, Dict

class LandfireDownloader:
    """
    Download LANDFIRE datasets for fire modeling
    
    Key datasets:
    - FBFM40: 40 Scott and Burgan Fire Behavior Fuel Models
    - CBH: Canopy Base Height
    - CBD: Canopy Bulk Density
    - CC: Canopy Cover
    - CH: Canopy Height
    - DEM: Elevation
    - Slope: Slope Degrees
    - Aspect: Aspect Degrees
    """
    
    BASE_URL = "https://landfire.gov/bulk/downloadfile.php"
    
    # Common LANDFIRE products (2020 version - LF 2020)
    PRODUCTS = {
        'FBFM40': '200FBFM40',     # Fire Behavior Fuel Model 40
        'CBH': '200CBH',            # Canopy Base Height
        'CBD': '200CBD',            # Canopy Bulk Density
        'CC': '200CC',              # Canopy Cover
        'CH': '200CH',              # Canopy Height
        'EVC': '200EVC',            # Existing Vegetation Cover
        'EVH': '200EVH',            # Existing Vegetation Height
        'EVT': '200EVT',            # Existing Vegetation Type
        'ELEV': '200ELEV',          # Elevation
        'SLOPE': '200SLPD',         # Slope Degrees
        'ASPECT': '200ASPD',        # Aspect Degrees
    }
    
    def __init__(self, output_dir: str = "data/landfire"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def get_available_products(self) -> Dict[str, str]:
        """Return available LANDFIRE products"""
        return self.PRODUCTS.copy()
    
    def list_products(self):
        """Print available products"""
        print("Available LANDFIRE Products:")
        print("-" * 60)
        for key, code in self.PRODUCTS.items():
            print(f"{key:12} - {code:12} - {self._get_description(key)}")
    
    def _get_description(self, product: str) -> str:
        """Get product description"""
        descriptions = {
            'FBFM40': 'Fire Behavior Fuel Model (40 models)',
            'CBH': 'Canopy Base Height (meters * 10)',
            'CBD': 'Canopy Bulk Density (kg/m³ * 100)',
            'CC': 'Canopy Cover (percent)',
            'CH': 'Canopy Height (meters * 10)',
            'EVC': 'Existing Vegetation Cover (%)',
            'EVH': 'Existing Vegetation Height (m)',
            'EVT': 'Existing Vegetation Type',
            'ELEV': 'Elevation (meters)',
            'SLOPE': 'Slope (degrees)',
            'ASPECT': 'Aspect (degrees)',
        }
        return descriptions.get(product, 'Unknown product')
    
    def download_product(self, product: str, region: str = "US"):
        """
        Download a LANDFIRE product
        
        Args:
            product: Product code (e.g., 'FBFM40')
            region: Geographic region (default 'US' for CONUS)
        
        Note: This is a simplified example. Actual LANDFIRE downloads
        require specific region codes and may need authentication.
        """
        if product not in self.PRODUCTS:
            raise ValueError(f"Unknown product: {product}. Use list_products() to see available options.")
        
        product_code = self.PRODUCTS[product]
        output_file = self.output_dir / f"{product}_{region}.zip"
        
        print(f"Note: LANDFIRE downloads typically require using their web interface")
        print(f"Visit: https://landfire.gov/version_download.php")
        print(f"Product to download: {product_code}")
        print(f"Suggested output location: {output_file}")
        print()
        print("For automated downloads, you would need to:")
        print("1. Select your Area of Interest (state/region)")
        print("2. Choose the product version (LF 2020, 2022, etc.)")
        print("3. Download the zip file to the data directory")
        
        return output_file


def main():
    """Example usage"""
    print("=" * 70)
    print("LANDFIRE Data Downloader for Fire Analysis")
    print("=" * 70)
    print()
    
    downloader = LandfireDownloader()
    
    # List available products
    downloader.list_products()
    print()
    
    # Key products for fire modeling
    essential_products = ['FBFM40', 'CBH', 'CBD', 'CC', 'SLOPE', 'ASPECT']
    
    print("Essential Products for Fire Modeling:")
    print("-" * 60)
    for product in essential_products:
        print(f"  ✓ {product}")
    print()
    
    print("Next Steps:")
    print("1. Visit https://landfire.gov/version_download.php")
    print("2. Select your state/region of interest")
    print("3. Download the products listed above")
    print("4. Place zip files in the 'data/landfire' directory")
    print("5. Use 02_process_landfire.py to extract and process the data")
    print()


if __name__ == "__main__":
    main()
