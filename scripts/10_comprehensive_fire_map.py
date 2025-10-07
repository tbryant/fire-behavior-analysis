#!/usr/bin/env python3
"""
Comprehensive Fire Analysis Map
Combines fuel layers, fire behavior predictions, and fire spread simulations
"""

import rasterio
import numpy as np
import folium
from folium import plugins
import json
from pathlib import Path
from typing import Dict, List
import base64
from io import BytesIO
from PIL import Image
import sys

# Import existing modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util

# Import fire spread simulator
spec = importlib.util.spec_from_file_location(
    "fire_spread_sim",
    Path(__file__).parent / "08_fire_spread_simulator.py"
)
sim_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim_module)
FireSpreadSimulator = sim_module.FireSpreadSimulator


class ComprehensiveFireMap:
    """
    Create a comprehensive fire analysis map with multiple layers:
    - Fuel models (FBFM40)
    - Slope and aspect
    - Fire behavior predictions
    - Fire spread simulations
    """
    
    def __init__(self, data_dir: str = "data/landfire"):
        self.data_dir = Path(data_dir)
        self.data = {}
        self.center_lat = None
        self.center_lon = None
        
    def load_data(self):
        """Load all LANDFIRE data"""
        print("\nLoading LANDFIRE data...")
        
        products = ['FBFM40', 'SLPD', 'ASPD', 'CBH', 'CBD', 'CC']
        
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
                        'nodata': src.nodata,
                        'profile': src.profile
                    }
                    
                    # Get center point
                    if self.center_lat is None:
                        bounds = src.bounds
                        self.center_lat = (bounds.bottom + bounds.top) / 2
                        self.center_lon = (bounds.left + bounds.right) / 2
        
        print(f"✓ Loaded {len(self.data)} products\n")
        return self.data
    
    def create_fuel_overlay(self, product: str, colormap: Dict) -> str:
        """Create a semi-transparent overlay for a data product"""
        if product not in self.data:
            return None
        
        data = self.data[product]['array']
        bounds = self.data[product]['bounds']
        
        # Create RGBA image
        height, width = data.shape
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        
        for value, color in colormap.items():
            mask = (data == value)
            rgba[mask] = color
        
        # Convert to PNG
        img = Image.fromarray(rgba, mode='RGBA')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    def create_comprehensive_map(self, output_file: str = "outputs/comprehensive_fire_map.html"):
        """Create comprehensive map with all layers"""
        
        print("\n" + "=" * 70)
        print("CREATING COMPREHENSIVE FIRE ANALYSIS MAP")
        print("=" * 70)
        
        # Load data
        self.load_data()
        
        # Define simulation parameters at the top so they can be used in map setup
        wind_speed = 70
        wind_direction = 45  # Northeast
        fuel_moisture = 2
        temperature = 95
        duration_hours = 48
        ignition_lat = 38.64
        ignition_lon = -122.84
        location_name = "NE Grasslands"
        
        # Create base map centered on ignition point with closer zoom
        m = folium.Map(
            location=[ignition_lat, ignition_lon],
            zoom_start=14,
            tiles='OpenStreetMap',
            control_scale=True
        )
        
        # Add satellite imagery layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite Imagery',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add topographic map layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Topographic Map',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add title with dynamic parameters
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 600px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4 style="margin:0">Comprehensive Fire Analysis - Healdsburg, CA</h4>
        <p style="margin:5px 0"><b>Extreme Fire Conditions:</b> {wind_speed} mph NE winds, {fuel_moisture}% fuel moisture, {temperature}°F</p>
        <p style="margin:5px 0">Toggle layers to view fuel types, terrain, and fire predictions</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # 1. FUEL MODEL LAYER
        print("\nCreating fuel model layer...")
        fbfm_colormap = self._get_fbfm_colormap()
        fbfm_overlay = self.create_fuel_overlay('FBFM40', fbfm_colormap)
        
        if fbfm_overlay:
            bounds = self.data['FBFM40']['bounds']
            fbfm_layer = folium.raster_layers.ImageOverlay(
                image=fbfm_overlay,
                bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
                opacity=0.6,
                name='Fuel Models (FBFM40)',
                show=True
            )
            fbfm_layer.add_to(m)
        
        # 2. SLOPE LAYER
        print("Creating slope layer...")
        slope_colormap = self._get_slope_colormap()
        slope_overlay = self.create_fuel_overlay('SLPD', slope_colormap)
        
        if slope_overlay:
            bounds = self.data['SLPD']['bounds']
            slope_layer = folium.raster_layers.ImageOverlay(
                image=slope_overlay,
                bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
                opacity=0.5,
                name='Slope',
                show=False
            )
            slope_layer.add_to(m)
        
        # 3. RUN FIRE SPREAD SIMULATION
        print("\nRunning fire spread simulation...")
        simulator = FireSpreadSimulator(str(self.data_dir))
        simulator.load_data()
        
        # Use extreme Tubbs Fire conditions (peak conditions)
        simulator.calculate_ros_map(
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            fuel_moisture=fuel_moisture,
            temperature=temperature
        )
        
        print(f"\nSimulating fire spread from ignition point...")
        print(f"  Location: {ignition_lat:.4f}, {ignition_lon:.4f} ({location_name})")
        
        # Convert lat/lon to row/col
        transform = simulator.data['FBFM40']['transform']
        col, row = ~transform * (ignition_lon, ignition_lat)
        row, col = int(row), int(col)
        
        arrival_time = simulator.simulate_spread(
            ignition_row=row,
            ignition_col=col,
            duration_hours=duration_hours
        )
        
        # Create isochrone overlay
        isochrone_url, isochrone_bounds = simulator.create_isochrone_overlay(arrival_time)
        
        if isochrone_url:
            isochrone_layer = folium.raster_layers.ImageOverlay(
                image=isochrone_url,
                bounds=isochrone_bounds,
                opacity=0.7,
                name='Fire Spread Prediction (48 hours)',
                show=True
            )
            isochrone_layer.add_to(m)
        
        # Add ignition point marker
        folium.Marker(
            location=[ignition_lat, ignition_lon],
            popup=f"Ignition Point - {location_name}<br>Extreme Fire Conditions<br>{wind_speed} mph NE winds, {fuel_moisture}% moisture, {temperature}°F",
            icon=folium.Icon(color='red', icon='fire', prefix='fa'),
            name='Ignition Point'
        ).add_to(m)
        
        # 4. SAVE SIMULATION DATA AS JSON
        print("\nSaving simulation metadata...")
        
        # Define output paths
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        json_output = output_path.parent / "comprehensive_fire_map_data.json"
        
        simulation_data = {
            "metadata": {
                "title": "Comprehensive Fire Analysis - Healdsburg, CA",
                "date_created": "2025-10-07",
                "simulation_type": "Fire Spread Prediction"
            },
            "ignition": {
                "latitude": ignition_lat,
                "longitude": ignition_lon,
                "location_description": "Northeast grasslands",
                "row": row,
                "col": col
            },
            "weather_conditions": {
                "wind_speed_mph": wind_speed,
                "wind_direction_degrees": wind_direction,
                "wind_direction_name": "Northeast",
                "fuel_moisture_percent": fuel_moisture,
                "temperature_fahrenheit": temperature,
                "relative_humidity_percent": 25,
                "conditions_description": "Extreme fire weather - similar to peak Tubbs Fire conditions"
            },
            "fire_behavior": {
                "duration_hours": duration_hours,
                "burned_area_acres": int(np.sum(arrival_time > 0) * 0.222),  # pixels to acres
                "burned_pixels": int(np.sum(arrival_time > 0)),
                "mean_ros_ft_per_min": float(np.mean(simulator.ros_map[simulator.ros_map > 0])),
                "max_ros_ft_per_min": float(np.max(simulator.ros_map)),
                "ignition_ros_ft_per_min": float(simulator.ros_map[row, col])
            },
            "isochrones": {
                "intervals_hours": [0, 1, 3, 6, 12, 24, 48, 72],
                "colors": [
                    {"range": "0-1 hr", "color": "#FF0000", "priority": "IMMEDIATE"},
                    {"range": "1-3 hrs", "color": "#FF6400", "priority": "URGENT"},
                    {"range": "3-6 hrs", "color": "#FFA500", "priority": "HIGH"},
                    {"range": "6-12 hrs", "color": "#FFD700", "priority": "MODERATE"},
                    {"range": "12-24 hrs", "color": "#ADD8E6", "priority": "PLANNING"},
                    {"range": "24-48 hrs", "color": "#9370DB", "priority": "LOW"},
                    {"range": "48-72 hrs", "color": "#4B0082", "priority": "MINIMAL"}
                ]
            },
            "data_layers": [
                {
                    "name": "Fuel Models (FBFM40)",
                    "type": "raster",
                    "description": "Scott & Burgan 40 fire behavior fuel models",
                    "visible_by_default": True
                },
                {
                    "name": "Slope",
                    "type": "raster",
                    "description": "Terrain slope in degrees",
                    "visible_by_default": False
                },
                {
                    "name": "Fire Spread Prediction",
                    "type": "raster",
                    "description": "Time-to-arrival isochrones (48 hours)",
                    "visible_by_default": True
                }
            ],
            "base_layers": [
                {
                    "name": "OpenStreetMap",
                    "type": "tile",
                    "description": "Street map with labels"
                },
                {
                    "name": "Satellite Imagery",
                    "type": "tile",
                    "description": "Aerial photography from Esri"
                },
                {
                    "name": "Topographic Map",
                    "type": "tile",
                    "description": "Topographic map with terrain contours from Esri"
                }
            ],
            "statistics": {
                "total_area_analyzed_acres": float(simulator.ros_map.size * 0.222),
                "burnable_area_acres": float(np.sum(simulator.ros_map > 0) * 0.222),
                "percent_burned": float(100 * np.sum(arrival_time > 0) / np.sum(simulator.ros_map > 0))
            }
        }
        
        json_output = output_path.parent / "comprehensive_fire_map_data.json"
        with open(json_output, 'w') as f:
            json.dump(simulation_data, f, indent=2)
        
        print(f"✓ Simulation data saved to: {json_output.absolute()}")
        
        # 5. ADD LEGEND
        legend_html = self._create_legend()
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        
        # Add fullscreen button
        plugins.Fullscreen(position='topleft').add_to(m)
        
        # Save map
        m.save(str(output_path))
        
        print(f"\n✓ Map saved to: {output_path.absolute()}")
        
        return str(output_path.absolute())
    
    def _get_fbfm_colormap(self) -> Dict:
        """Fuel model colors"""
        return {
            # Grass (101-109) - Yellows/Greens
            101: [255, 255, 150, 180],  # GR1 - Light yellow
            102: [240, 230, 100, 180],  # GR2 - Yellow
            103: [220, 200, 50, 180],   # GR3 - Dark yellow
            104: [200, 180, 30, 180],   # GR4 - Darker yellow
            
            # Shrub (121-129) - Oranges/Browns
            121: [255, 180, 100, 180],  # SH1 - Light orange
            122: [255, 150, 80, 180],   # SH2 - Orange
            123: [240, 120, 60, 180],   # SH3 - Dark orange
            124: [220, 100, 50, 180],   # SH4 - Darker orange
            125: [200, 80, 40, 180],    # SH5 - Red-brown
            
            # Timber (141-149) - Greens
            141: [150, 200, 150, 180],  # TU1 - Light green
            142: [120, 180, 120, 180],  # TU2 - Green
            143: [100, 160, 100, 180],  # TU3 - Dark green
            144: [80, 140, 80, 180],    # TU4 - Darker green
            145: [60, 120, 60, 180],    # TU5 - Deep green
            
            # Timber Litter (161-169) - Browns
            161: [180, 140, 100, 180],  # TL1 - Light brown
            162: [160, 120, 80, 180],   # TL2 - Brown
            165: [120, 90, 60, 180],    # TL5 - Dark brown
            
            # Non-burnable
            91: [200, 200, 200, 100],   # Urban
            92: [180, 180, 180, 100],   # Snow/Ice
            93: [150, 180, 220, 100],   # Agriculture
            98: [120, 140, 180, 100],   # Water
            99: [100, 100, 100, 100],   # Barren
        }
    
    def _get_slope_colormap(self) -> Dict:
        """Slope colors - blue (flat) to red (steep)"""
        colormap = {}
        for slope in range(0, 61):
            if slope < 10:
                # Flat - Blue
                r, g, b = 100, 150, 255
            elif slope < 20:
                # Gentle - Green
                r, g, b = 100, 255, 100
            elif slope < 30:
                # Moderate - Yellow
                r, g, b = 255, 255, 100
            elif slope < 40:
                # Steep - Orange
                r, g, b = 255, 150, 50
            else:
                # Very steep - Red
                r, g, b = 255, 50, 50
            
            colormap[slope] = [r, g, b, 150]
        
        return colormap
    
    def _create_legend(self) -> str:
        """Create HTML legend"""
        return '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 280px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <h4 style="margin:0 0 10px 0">Legend</h4>
        
        <div style="margin-bottom:10px">
            <b>Fire Spread (Time to Arrival):</b><br>
            <span style="color:#FF0000">■</span> 0-1 hr (IMMEDIATE)<br>
            <span style="color:#FF6600">■</span> 1-3 hrs (URGENT)<br>
            <span style="color:#FFD700">■</span> 3-6 hrs (HIGH)<br>
            <span style="color:#87CEEB">■</span> 6-12 hrs (MODERATE)<br>
            <span style="color:#9370DB">■</span> 12-24 hrs (PLANNING)<br>
            <span style="color:#4B0082">■</span> 24-48 hrs (LOW)
        </div>
        
        <div style="margin-bottom:10px">
            <b>Fuel Types:</b><br>
            <span style="color:#FFFF96">■</span> Grass<br>
            <span style="color:#FF9650">■</span> Shrub<br>
            <span style="color:#78B478">■</span> Timber/Understory<br>
            <span style="color:#B48C64">■</span> Timber Litter<br>
            <span style="color:#C8C8C8">■</span> Non-burnable
        </div>
        
        <div>
            <b>Slope:</b><br>
            <span style="color:#6496FF">■</span> 0-10° (Flat)<br>
            <span style="color:#64FF64">■</span> 10-20° (Gentle)<br>
            <span style="color:#FFFF64">■</span> 20-30° (Moderate)<br>
            <span style="color:#FF9632">■</span> 30-40° (Steep)<br>
            <span style="color:#FF3232">■</span> 40°+ (Very Steep)
        </div>
        </div>
        '''


def main():
    """Create comprehensive fire map"""
    
    print("\n" + "=" * 70)
    print("COMPREHENSIVE FIRE ANALYSIS MAP")
    print("=" * 70)
    
    mapper = ComprehensiveFireMap()
    output_file = mapper.create_comprehensive_map()
    
    print("\n" + "=" * 70)
    print("✓ COMPREHENSIVE MAP CREATED!")
    print("=" * 70)
    print(f"\nMap file: {output_file}")
    print("\nLayers included:")
    print("  • Fuel Models (FBFM40) - color-coded vegetation types")
    print("  • Slope - terrain steepness")
    print("  • Fire Spread Prediction - 48-hour isochrones")
    print("  • Satellite Imagery - toggleable base layer")
    print("\nUse layer control (top right) to toggle layers on/off")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
