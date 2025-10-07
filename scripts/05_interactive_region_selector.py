#!/usr/bin/env python3
"""
Interactive LANDFIRE Region Selector
Uses Folium to create an interactive map for selecting LANDFIRE data regions
"""

import folium
from folium import plugins
import json
from pathlib import Path
import webbrowser
from typing import Dict, List, Tuple
import requests


class LANDFIRERegionSelector:
    """
    Interactive map-based selector for LANDFIRE data downloads
    """
    
    # LANDFIRE bounding boxes for major regions (simplified)
    # In a full implementation, these would come from LANDFIRE's API
    REGIONS = {
        'California': {
            'bounds': [[32.5, -124.5], [42.0, -114.0]],
            'center': [37.0, -119.5],
            'states': ['CA'],
            'landfire_zone': 'LF_Zone16'
        },
        'Pacific Northwest': {
            'bounds': [[42.0, -124.5], [49.0, -116.0]],
            'center': [45.5, -120.0],
            'states': ['OR', 'WA'],
            'landfire_zone': 'LF_Zone17'
        },
        'Northern Rockies': {
            'bounds': [[44.0, -116.0], [49.0, -104.0]],
            'center': [46.5, -110.0],
            'states': ['MT', 'ID', 'WY'],
            'landfire_zone': 'LF_Zone18'
        },
        'Southwest': {
            'bounds': [[31.0, -114.0], [37.0, -103.0]],
            'center': [34.0, -108.5],
            'states': ['AZ', 'NM', 'NV', 'UT'],
            'landfire_zone': 'LF_Zone19'
        },
        'Great Basin': {
            'bounds': [[37.0, -120.0], [42.0, -111.0]],
            'center': [39.5, -115.5],
            'states': ['NV', 'UT'],
            'landfire_zone': 'LF_Zone20'
        },
        'Southern Rockies': {
            'bounds': [[37.0, -109.0], [41.0, -102.0]],
            'center': [39.0, -105.5],
            'states': ['CO'],
            'landfire_zone': 'LF_Zone21'
        },
        'Southern Plains': {
            'bounds': [[25.0, -106.0], [37.0, -94.0]],
            'center': [31.0, -100.0],
            'states': ['TX', 'OK', 'KS'],
            'landfire_zone': 'LF_Zone22'
        },
    }
    
    # LANDFIRE products available for download
    PRODUCTS = {
        'FBFM40': {
            'name': 'Fire Behavior Fuel Model 40',
            'code': '200FBFM40',
            'description': 'Scott and Burgan 40 fuel models',
            'priority': 1
        },
        'CBH': {
            'name': 'Canopy Base Height',
            'code': '200CBH',
            'description': 'Height to live crown (m x 10)',
            'priority': 2
        },
        'CBD': {
            'name': 'Canopy Bulk Density',
            'code': '200CBD',
            'description': 'Crown fuel density (kg/m³ x 100)',
            'priority': 3
        },
        'CC': {
            'name': 'Canopy Cover',
            'code': '200CC',
            'description': 'Forest canopy cover (%)',
            'priority': 4
        },
        'CH': {
            'name': 'Canopy Height',
            'code': '200CH',
            'description': 'Average tree height (m x 10)',
            'priority': 5
        },
        'SLPD': {
            'name': 'Slope Degrees',
            'code': '200SLPD',
            'description': 'Terrain slope (degrees)',
            'priority': 6
        },
        'ASPD': {
            'name': 'Aspect Degrees',
            'code': '200ASPD',
            'description': 'Terrain aspect (degrees)',
            'priority': 7
        },
        'ELEV': {
            'name': 'Elevation',
            'code': '200ELEV',
            'description': 'Elevation (meters)',
            'priority': 8
        },
    }
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path("data/landfire")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def create_interactive_map(self, filename: str = "landfire_selector.html") -> str:
        """
        Create an interactive map for selecting LANDFIRE regions
        
        Returns:
            Path to the generated HTML file
        """
        # Create base map centered on Western US
        m = folium.Map(
            location=[39.0, -110.0],
            zoom_start=5,
            tiles='OpenStreetMap'
        )
        
        # Add different tile layers with proper attribution
        folium.TileLayer(
            tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attr='OpenTopoMap',
            name='Topographic',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='CartoDB positron',
            name='Light Map',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Create feature groups
        regions_group = folium.FeatureGroup(name='LANDFIRE Regions')
        
        # Add each region as a rectangle
        for region_name, region_data in self.REGIONS.items():
            bounds = region_data['bounds']
            center = region_data['center']
            states = ', '.join(region_data['states'])
            zone = region_data['landfire_zone']
            
            # Create popup content
            popup_html = f"""
            <div style="font-family: Arial; width: 300px;">
                <h3 style="margin-bottom: 10px; color: #d84315;">{region_name}</h3>
                <p><strong>States:</strong> {states}</p>
                <p><strong>LANDFIRE Zone:</strong> {zone}</p>
                <p><strong>Bounds:</strong><br>
                   SW: {bounds[0][0]:.2f}, {bounds[0][1]:.2f}<br>
                   NE: {bounds[1][0]:.2f}, {bounds[1][1]:.2f}
                </p>
                <hr>
                <p style="font-size: 11px; color: #666;">
                Click the region to select it for data download.<br>
                Visit <a href="https://landfire.gov/version_download.php" target="_blank">LANDFIRE</a> 
                to download data for this region.
                </p>
            </div>
            """
            
            # Add rectangle for region
            folium.Rectangle(
                bounds=bounds,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{region_name} ({states})",
                color='#d84315',
                fill=True,
                fillColor='#ff6f00',
                fillOpacity=0.2,
                weight=2
            ).add_to(regions_group)
            
            # Add marker at center
            folium.Marker(
                location=center,
                popup=popup_html,
                tooltip=region_name,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(regions_group)
        
        regions_group.add_to(m)
        
        # Add click handler for custom area selection
        draw_plugin = plugins.Draw(
            export=True,
            filename='selected_area.geojson',
            position='topleft',
            draw_options={
                'polyline': False,
                'circle': False,
                'circlemarker': False,
                'marker': False,
                'polygon': True,
                'rectangle': True,
            },
            edit_options={'edit': True}
        )
        draw_plugin.add_to(m)
        
        # Add measure control
        plugins.MeasureControl(
            position='bottomleft',
            primary_length_unit='miles',
            secondary_length_unit='kilometers',
            primary_area_unit='sqmiles',
            secondary_area_unit='acres'
        ).add_to(m)
        
        # Add fullscreen option
        plugins.Fullscreen(
            position='topright',
            title='Fullscreen',
            title_cancel='Exit Fullscreen',
            force_separate_button=True
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 300px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
            <h4 style="margin-top:0; color: #d84315;">LANDFIRE Region Selector</h4>
            <p style="margin: 5px 0;"><strong>How to use:</strong></p>
            <ol style="margin: 5px 0; padding-left: 20px;">
                <li>Click on a <span style="color: #d84315;">red region</span> to see details</li>
                <li>Use the <strong>draw tools</strong> (top-left) to select custom areas</li>
                <li>Use <strong>measure tool</strong> (bottom-left) to measure distances</li>
                <li>Toggle layers using the control (top-right)</li>
            </ol>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0; font-size: 12px;">
                <strong>Essential Products:</strong><br>
                • FBFM40 - Fuel Models<br>
                • CBH/CBD - Canopy Structure<br>
                • SLPD/ASPD - Terrain<br>
                • CC/CH - Vegetation
            </p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        output_file = self.output_dir / filename
        m.save(str(output_file))
        
        print(f"\n✓ Interactive map created: {output_file}")
        print(f"  Open in browser to select your region of interest")
        
        return str(output_file)
    
    def get_download_instructions(self, region_name: str) -> Dict:
        """
        Get download instructions for a specific region
        """
        if region_name not in self.REGIONS:
            raise ValueError(f"Unknown region: {region_name}")
        
        region = self.REGIONS[region_name]
        
        instructions = {
            'region': region_name,
            'landfire_zone': region['landfire_zone'],
            'states': region['states'],
            'bounds': region['bounds'],
            'steps': [
                {
                    'step': 1,
                    'action': 'Visit LANDFIRE website',
                    'url': 'https://landfire.gov/version_download.php',
                    'details': 'Go to the LANDFIRE data distribution page'
                },
                {
                    'step': 2,
                    'action': 'Select version',
                    'details': f'Choose LF 2020 or LF 2022 (latest available)'
                },
                {
                    'step': 3,
                    'action': 'Select geographic area',
                    'details': f'Choose one of: {", ".join(region["states"])}'
                },
                {
                    'step': 4,
                    'action': 'Select products',
                    'details': 'Choose the products you need (see product list below)'
                },
                {
                    'step': 5,
                    'action': 'Download',
                    'details': f'Save ZIP files to: {self.data_dir}'
                }
            ],
            'products': self.PRODUCTS,
            'essential_products': ['FBFM40', 'CBH', 'CBD', 'CC', 'SLPD', 'ASPD']
        }
        
        return instructions
    
    def print_download_instructions(self, region_name: str):
        """
        Print formatted download instructions
        """
        instructions = self.get_download_instructions(region_name)
        
        print("\n" + "=" * 70)
        print(f"LANDFIRE DATA DOWNLOAD INSTRUCTIONS - {instructions['region']}")
        print("=" * 70)
        print(f"\nRegion: {instructions['region']}")
        print(f"States: {', '.join(instructions['states'])}")
        print(f"LANDFIRE Zone: {instructions['landfire_zone']}")
        print(f"\nDownload Steps:")
        print("-" * 70)
        
        for step_info in instructions['steps']:
            print(f"\n{step_info['step']}. {step_info['action']}")
            if 'url' in step_info:
                print(f"   URL: {step_info['url']}")
            print(f"   {step_info['details']}")
        
        print("\n" + "-" * 70)
        print("Essential Products for Fire Analysis:")
        print("-" * 70)
        
        for prod_code in instructions['essential_products']:
            prod = self.PRODUCTS[prod_code]
            print(f"  ✓ {prod_code:10} - {prod['name']}")
            print(f"     {prod['description']}")
        
        print("\n" + "=" * 70)
        print(f"Save all downloaded files to: {self.data_dir}")
        print("=" * 70 + "\n")
    
    def save_region_config(self, region_name: str, filename: str = "region_config.json"):
        """
        Save region configuration for later use
        """
        instructions = self.get_download_instructions(region_name)
        config_file = self.data_dir / filename
        
        with open(config_file, 'w') as f:
            json.dump(instructions, f, indent=2)
        
        print(f"✓ Region configuration saved to: {config_file}")
        return str(config_file)


def main():
    """
    Main entry point - create interactive map and show instructions
    """
    print("\n" + "=" * 70)
    print("LANDFIRE INTERACTIVE REGION SELECTOR")
    print("=" * 70)
    print()
    
    selector = LANDFIRERegionSelector()
    
    # Create interactive map
    print("Creating interactive map...")
    map_file = selector.create_interactive_map()
    
    print("\n" + "=" * 70)
    print("AVAILABLE REGIONS")
    print("=" * 70)
    for i, (name, data) in enumerate(selector.REGIONS.items(), 1):
        states = ', '.join(data['states'])
        print(f"{i}. {name:25} ({states})")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print(f"\n1. Open the interactive map:")
    print(f"   {map_file}")
    print(f"\n2. Explore regions and select your area of interest")
    print(f"\n3. Get download instructions for a specific region:")
    print(f"   Example: selector.print_download_instructions('California')")
    print(f"\n4. Or try opening in your browser automatically:")
    
    # Try to open in browser
    try:
        print(f"\n   Opening map in browser...")
        import os
        # Use VS Code simple browser
        full_path = Path(map_file).absolute()
        print(f"\n   📍 Map location: {full_path}")
        print(f"\n   You can also open it manually in VS Code:")
        print(f"   - Right-click on {map_file}")
        print(f"   - Select 'Open with Live Server' or 'Preview'")
    except Exception as e:
        print(f"   Note: {e}")
    
    print("\n" + "=" * 70)
    print("EXAMPLE: California Region Download Instructions")
    print("=" * 70)
    
    # Show example for California
    selector.print_download_instructions('California')
    
    # Save config
    selector.save_region_config('California')
    
    print("\n💡 TIP: Once you have this script working, we can add:")
    print("   • Automated download using LANDFIRE web services")
    print("   • Custom area selection via polygon drawing")
    print("   • Direct data extraction and processing")
    print("   • Integration with fire behavior models")
    print()


if __name__ == "__main__":
    main()
