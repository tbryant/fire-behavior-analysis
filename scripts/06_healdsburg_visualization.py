#!/usr/bin/env python3
"""
Healdsburg Fire Analysis Visualization
Creates interactive maps with LANDFIRE data as colored raster overlays
"""

import rasterio
from rasterio.plot import reshape_as_image
import numpy as np
import folium
from folium import plugins, raster_layers
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap
from typing import Dict, Tuple, List
import base64
from io import BytesIO
from PIL import Image


class HealdsburgFireVisualizer:
    """
    Enhanced visualizer with actual raster data overlays
    """
    
    def __init__(self, data_dir: str = "data/landfire"):
        self.data_dir = Path(data_dir)
        self.data = {}
        self.bounds = None
        self.center = None
        
        # Healdsburg center coordinates
        self.healdsburg_lat = 38.6102
        self.healdsburg_lon = -122.8694
        
    def load_data(self) -> Dict:
        """Load all LANDFIRE GeoTIFF files"""
        print("Loading LANDFIRE data...")
        
        products = ['FBFM40', 'CBH', 'CBD', 'CC', 'SLPD', 'ASPD']
        
        for product in products:
            files = list(self.data_dir.glob(f"{product}_*.tif"))
            if files:
                filepath = files[0]
                print(f"  Loading {product} from {filepath.name}")
                
                with rasterio.open(filepath) as src:
                    self.data[product] = {
                        'array': src.read(1),
                        'transform': src.transform,
                        'crs': src.crs,
                        'bounds': src.bounds,
                        'nodata': src.nodata
                    }
                    
                    if self.bounds is None:
                        self.bounds = src.bounds
                        self.center = [
                            (src.bounds.bottom + src.bounds.top) / 2,
                            (src.bounds.left + src.bounds.right) / 2
                        ]
        
        print(f"\nLoaded {len(self.data)} products")
        return self.data
    
    def create_fuel_model_colormap(self) -> Tuple[ListedColormap, dict, list]:
        """Create colormap for FBFM40 fuel models"""
        
        # Define colors for each fuel model
        fuel_model_colors = {
            0: [255, 255, 255, 0],      # Transparent for no data
            91: [245, 222, 179, 200],   # NB1 - Urban
            92: [211, 211, 211, 200],   # NB2 - Snow/Ice
            93: [169, 169, 169, 200],   # NB3 - Agriculture
            98: [135, 206, 235, 200],   # NB8 - Water
            99: [70, 130, 180, 200],    # NB9 - Barren
            
            101: [255, 255, 153, 200],  # GR1 - Short sparse grass
            102: [255, 255, 102, 200],  # GR2 - Low load grass
            103: [255, 255, 51, 200],   # GR3 - Moderate load grass
            104: [255, 215, 0, 200],    # GR4 - High load grass
            105: [255, 165, 0, 200],    # GR5 - Dense grass
            106: [255, 140, 0, 200],    # GR6 - Moderate moisture grass
            107: [255, 99, 71, 200],    # GR7 - High load, moist grass
            108: [255, 69, 0, 200],     # GR8 - High load, very coarse
            109: [220, 20, 60, 200],    # GR9 - Dense, tall grass
            
            121: [255, 228, 181, 200],  # GS1 - Low load shrub/grass
            122: [255, 218, 185, 200],  # GS2 - Moderate load shrub/grass
            123: [255, 179, 102, 200],  # GS3 - Moderate shrub/grass
            124: [255, 153, 51, 200],   # GS4 - High load shrub/grass
            
            141: [173, 255, 47, 200],   # SH1 - Low load dry shrub
            142: [154, 205, 50, 200],   # SH2 - Moderate load dry shrub
            143: [124, 252, 0, 200],    # SH3 - High load dry shrub
            144: [50, 205, 50, 200],    # SH4 - Low load humid shrub
            145: [34, 139, 34, 200],    # SH5 - High load humid shrub
            146: [0, 100, 0, 200],      # SH6 - Low load humid shrub
            147: [139, 69, 19, 200],    # SH7 - High load humid shrub
            148: [160, 82, 45, 200],    # SH8 - High load shrub
            149: [210, 105, 30, 200],   # SH9 - Dense shrub
            
            161: [144, 238, 144, 200],  # TU1 - Light load timber
            162: [102, 205, 170, 200],  # TU2 - Moderate load timber
            163: [60, 179, 113, 200],   # TU3 - High load timber
            164: [46, 139, 87, 200],    # TU4 - Dwarf conifer
            165: [0, 100, 0, 200],      # TU5 - High load conifer
            
            181: [143, 188, 143, 200],  # TL1 - Low load compact conifer
            182: [85, 107, 47, 200],    # TL2 - Low load broadleaf
            183: [107, 142, 35, 200],   # TL3 - Moderate load conifer
            184: [128, 128, 0, 200],    # TL4 - Small downed logs
            185: [85, 107, 47, 200],    # TL5 - High load conifer
            186: [47, 79, 47, 200],     # TL6 - Moderate load broadleaf
            187: [25, 25, 112, 200],    # TL7 - Large downed logs
            188: [0, 0, 128, 200],      # TL8 - Long needle litter
            189: [0, 0, 139, 200],      # TL9 - Very high load broadleaf
            
            201: [205, 133, 63, 200],   # SB1 - Low load activity fuel
            202: [139, 69, 19, 200],    # SB2 - Moderate load activity
            203: [160, 82, 45, 200],    # SB3 - High load activity
            204: [210, 105, 30, 200],   # SB4 - Very high load activity
        }
        
        # Create legend - colors match representative models from each category
        # Comprehensive legend - showing all major color variations
        legend_items = [
            ('Urban/Developed (NB1)', '#F5DEB3'),       # NB1 Wheat
            ('Agriculture (NB3)', '#A9A9A9'),           # NB3 Gray
            ('Water (NB8)', '#87CEEB'),                 # NB8 Sky blue
            ('Barren (NB9)', '#4682B4'),                # NB9 Steel blue
            ('Grass - Short (GR1-3)', '#FFFF99'),       # GR1-3 Light yellow
            ('Grass - Tall/Dense (GR4-9)', '#FF8C00'),  # GR4-9 Orange
            ('Grass-Shrub (GS1-4)', '#FFB366'),         # GS1-4 Peach/Orange
            ('Shrub - Dry (SH1-3)', '#9ACD32'),         # SH1-3 Yellow-green
            ('Shrub - Humid (SH4-9)', '#228B22'),       # SH4-9 Forest green
            ('Timber-Understory (TU1-5)', '#66CDAA'),   # TU1-5 Aquamarine
            ('Timber Litter - Olive (TL1-7)', '#556B2F'),  # TL1-7 Dark olive
            ('Timber Litter - Navy (TL8-9)', '#000080'),   # TL8-9 Navy blue
            ('Slash-Blowdown (SB1-4)', '#8B4513'),      # SB1-4 Saddle brown
        ]
        
        return None, fuel_model_colors, legend_items
    
    def array_to_rgba(self, array: np.ndarray, colormap: dict, 
                      nodata_value: float = -9999) -> np.ndarray:
        """Convert data array to RGBA image using colormap"""
        
        # Create RGBA array
        rgba = np.zeros((array.shape[0], array.shape[1], 4), dtype=np.uint8)
        
        # Get unique values in the array
        unique_vals = np.unique(array)
        
        # Apply colors
        for val in unique_vals:
            if val == nodata_value:
                continue
            
            mask = array == val
            color = colormap.get(int(val), [200, 200, 200, 100])  # Default gray
            rgba[mask] = color
        
        return rgba
    
    def create_overlay_image(self, product: str, colormap: dict = None) -> Tuple[str, list]:
        """Create a PNG overlay for the map"""
        
        if product not in self.data:
            return None, None
        
        data = self.data[product]
        array = data['array']
        nodata = data.get('nodata', -9999)
        bounds = data['bounds']
        
        # Create RGBA image
        if colormap:
            rgba = self.array_to_rgba(array, colormap, nodata)
        else:
            # For continuous data, use a colormap
            masked = np.ma.masked_equal(array, nodata)
            norm_array = (masked - masked.min()) / (masked.max() - masked.min())
            
            cmap = plt.colormaps.get_cmap('viridis')
            rgba = (cmap(norm_array) * 255).astype(np.uint8)
            rgba[array == nodata] = [0, 0, 0, 0]  # Transparent for nodata
        
        # Convert to PIL Image
        img = Image.fromarray(rgba, 'RGBA')
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        # Encode to base64
        img_base64 = base64.b64encode(buffer.read()).decode()
        img_url = f"data:image/png;base64,{img_base64}"
        
        # Return bounds in [[lat, lon], [lat, lon]] format
        bounds_list = [
            [bounds.bottom, bounds.left],
            [bounds.top, bounds.right]
        ]
        
        return img_url, bounds_list
    
    def create_interactive_map(self) -> folium.Map:
        """Create interactive map with raster overlays"""
        print("\nCreating interactive map with raster overlays...")
        
        # Create base map
        m = folium.Map(
            location=[self.healdsburg_lat, self.healdsburg_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add tile layers
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Topographic',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Create fuel model colormap
        _, fuel_colors, fuel_legend = self.create_fuel_model_colormap()
        
        # Add FBFM40 overlay
        print("  Creating fuel model overlay...")
        fbfm_img, fbfm_bounds = self.create_overlay_image('FBFM40', fuel_colors)
        
        if fbfm_img and fbfm_bounds:
            fuel_layer = folium.raster_layers.ImageOverlay(
                image=fbfm_img,
                bounds=fbfm_bounds,
                opacity=0.7,
                interactive=True,
                cross_origin=False,
                name='Fuel Models (FBFM40)'
            )
            fuel_layer.add_to(m)
            print("    ✓ Fuel model layer added")
        
        # Add canopy cover overlay
        print("  Creating canopy cover overlay...")
        cc_img, cc_bounds = self.create_overlay_image('CC')
        
        if cc_img and cc_bounds:
            cc_layer = folium.raster_layers.ImageOverlay(
                image=cc_img,
                bounds=cc_bounds,
                opacity=0.6,
                interactive=True,
                cross_origin=False,
                name='Canopy Cover (%)',
                show=False
            )
            cc_layer.add_to(m)
            print("    ✓ Canopy cover layer added")
        
        # Add slope overlay
        print("  Creating slope overlay...")
        slope_img, slope_bounds = self.create_overlay_image('SLPD')
        
        if slope_img and slope_bounds:
            slope_layer = folium.raster_layers.ImageOverlay(
                image=slope_img,
                bounds=slope_bounds,
                opacity=0.6,
                interactive=True,
                cross_origin=False,
                name='Slope (degrees)',
                show=False
            )
            slope_layer.add_to(m)
            print("    ✓ Slope layer added")
        
        # Add Healdsburg marker
        folium.Marker(
            [self.healdsburg_lat, self.healdsburg_lon],
            popup='<b>Healdsburg, CA</b><br>Center of Analysis Area',
            tooltip='Healdsburg',
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Add data bounds rectangle
        if self.bounds:
            bounds_rect = [
                [self.bounds.bottom, self.bounds.left],
                [self.bounds.top, self.bounds.right]
            ]
            folium.Rectangle(
                bounds=bounds_rect,
                color='red',
                fill=False,
                weight=2,
                popup='LANDFIRE Data Coverage Area',
                tooltip='Data Boundary'
            ).add_to(m)
        
        # Add legend (left side, below zoom controls, hidden by default)
        # Will be shown/hidden via JavaScript when layer is toggled
        legend_html = '''
        <div id="fuel-legend" style="position: fixed; 
                    top: 150px; left: 10px; width: 260px; height: auto; 
                    background-color: white; z-index:9999; font-size:12px;
                    border:2px solid grey; border-radius: 5px; padding: 10px;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                    display: block;">
        <h4 style="margin-top:0; margin-bottom:10px; font-size:14px;">Fuel Models (FBFM40)</h4>
        '''
        
        for label, color in fuel_legend:
            legend_html += f'''
            <div style="margin-bottom: 4px;">
                <span style="background-color:{color}; width:18px; height:18px; 
                      display:inline-block; border:1px solid black; margin-right:5px;"></span>
                <span style="font-size:11px;">{label}</span>
            </div>
            '''
        
        legend_html += '''
        </div>
        <script>
        // Toggle legend visibility when Fuel Models layer is toggled
        document.addEventListener('DOMContentLoaded', function() {
            // Wait for map to be fully loaded
            setTimeout(function() {
                var legend = document.getElementById('fuel-legend');
                // Check for layer control changes
                document.addEventListener('click', function(e) {
                    setTimeout(function() {
                        // Check if fuel model layer checkbox exists and is checked
                        var layerInputs = document.querySelectorAll('.leaflet-control-layers-overlays input');
                        layerInputs.forEach(function(input) {
                            var label = input.nextSibling;
                            if (label && label.textContent.includes('Fuel Models')) {
                                legend.style.display = input.checked ? 'block' : 'none';
                            }
                        });
                    }, 100);
                });
            }, 500);
        });
        </script>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add controls
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        plugins.Fullscreen(position='topleft').add_to(m)
        plugins.MeasureControl(position='topleft').add_to(m)
        plugins.MousePosition().add_to(m)
        
        # Add scale
        plugins.MiniMap(toggle_display=True).add_to(m)
        
        print("\n✓ Map created with raster overlays")
        return m
    
    def generate_map(self, output_file: str = "outputs/healdsburg_fire_map.html"):
        """Generate the interactive map with raster overlays"""
        print("\n" + "=" * 70)
        print("HEALDSBURG FIRE VISUALIZATION")
        print("=" * 70)
        
        # Load data
        self.load_data()
        
        # Create map
        map_obj = self.create_interactive_map()
        
        # Save
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        map_obj.save(str(output_path))
        
        print("\n" + "=" * 70)
        print("VISUALIZATION COMPLETE!")
        print("=" * 70)
        print(f"\nMap saved to: {output_path.absolute()}")
        print("\nFeatures:")
        print("  ✓ Fuel model raster overlay (FBFM40)")
        print("  ✓ Canopy cover overlay (CC)")
        print("  ✓ Slope overlay (SLPD)")
        print("  ✓ Multiple base layers (OSM, Satellite, Topo)")
        print("  ✓ Interactive layer control")
        print("  ✓ Measurement tools")
        print("  ✓ Fuel model legend")
        print("=" * 70 + "\n")
        
        return str(output_path.absolute())


def main():
    """Run Healdsburg fire visualization"""
    visualizer = HealdsburgFireVisualizer()
    map_file = visualizer.generate_map()
    
    print(f"\nTo view the map, open: {map_file}")


if __name__ == "__main__":
    main()
