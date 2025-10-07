#!/usr/bin/env python3
"""
Grid Fire Spread Analysis
Generate fire spread predictions for a grid of ignition points across the landscape
Display isochrones on hover for interactive risk assessment
"""

import rasterio
import numpy as np
import folium
from folium import plugins
import json
from pathlib import Path
from typing import Dict, Tuple, List
import base64
from io import BytesIO
from PIL import Image
import sys

# Import the simulator
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "fire_spread_sim",
    Path(__file__).parent.parent / "scripts" / "08_fire_spread_simulator.py"
)
sim_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim_module)

FireSpreadSimulator = sim_module.FireSpreadSimulator


class GridFireSpreadAnalysis:
    """
    Generate fire spread predictions for a grid of ignition points
    """
    
    def __init__(self, data_dir: str = "data/landfire"):
        self.sim = FireSpreadSimulator(data_dir)
        self.grid_results = []
        
    def generate_grid_points(
        self,
        bounds: Tuple[float, float, float, float],  # (lat_min, lat_max, lon_min, lon_max)
        grid_size: int = 5
    ) -> List[Tuple[float, float]]:
        """
        Generate a grid of lat/lon points
        
        Args:
            bounds: (lat_min, lat_max, lon_min, lon_max)
            grid_size: Number of points per dimension
        
        Returns:
            List of (lat, lon) tuples
        """
        lat_min, lat_max, lon_min, lon_max = bounds
        
        lats = np.linspace(lat_min, lat_max, grid_size)
        lons = np.linspace(lon_min, lon_max, grid_size)
        
        points = []
        for lat in lats:
            for lon in lons:
                points.append((lat, lon))
        
        return points
    
    def run_grid_analysis(
        self,
        grid_points: List[Tuple[float, float]],
        wind_speed: float = 20,
        wind_direction: float = 0,
        fuel_moisture: float = 5,
        temperature: float = 90,
        duration_hours: float = 12
    ) -> List[Dict]:
        """
        Run fire spread simulation for each grid point
        """
        print("\n" + "=" * 70)
        print("GRID FIRE SPREAD ANALYSIS")
        print("=" * 70)
        print(f"\nAnalyzing {len(grid_points)} ignition points...")
        print(f"Weather: {wind_speed} mph wind from {wind_direction}°, {fuel_moisture}% moisture, {temperature}°F")
        print(f"Duration: {duration_hours} hours")
        print("=" * 70)
        
        # Load data
        self.sim.load_data()
        
        # Calculate ROS map once
        self.sim.calculate_ros_map(
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            fuel_moisture=fuel_moisture,
            temperature=temperature
        )
        
        results = []
        
        for i, (lat, lon) in enumerate(grid_points, 1):
            print(f"\n[{i}/{len(grid_points)}] Point: {lat:.4f}, {lon:.4f}")
            
            # Convert to pixel coordinates
            try:
                row, col = self.sim.latlon_to_pixel(lat, lon)
            except:
                print(f"  ✗ Outside data bounds")
                continue
            
            # Check if within bounds
            shape = self.sim.ros_map.shape
            if not (0 <= row < shape[0] and 0 <= col < shape[1]):
                print(f"  ✗ Outside data bounds")
                continue
            
            # Run simulation
            try:
                arrival_time = self.sim.simulate_spread(
                    ignition_row=row,
                    ignition_col=col,
                    duration_hours=duration_hours
                )
                
                # Get actual ignition point (after burnable adjustment)
                if hasattr(self.sim, 'actual_ignition_row'):
                    actual_lat, actual_lon = self.sim.pixel_to_latlon(
                        self.sim.actual_ignition_row,
                        self.sim.actual_ignition_col
                    )
                else:
                    actual_lat, actual_lon = lat, lon
                
                # Calculate statistics
                burned_pixels = np.sum(arrival_time > 0)
                burned_acres = burned_pixels * (self.sim.pixel_size_ft ** 2) / 43560
                
                # Create isochrone overlay
                iso_img, iso_bounds = self.sim.create_isochrone_overlay(arrival_time)
                
                result = {
                    'original_lat': lat,
                    'original_lon': lon,
                    'actual_lat': actual_lat,
                    'actual_lon': actual_lon,
                    'burned_acres': burned_acres,
                    'burned_pixels': int(burned_pixels),
                    'isochrone_image': iso_img,
                    'isochrone_bounds': iso_bounds,
                    'arrival_time': arrival_time
                }
                
                results.append(result)
                print(f"  ✓ {burned_acres:.0f} acres burned")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
        
        self.grid_results = results
        
        print("\n" + "=" * 70)
        print(f"✓ Analysis complete: {len(results)} valid ignition points")
        print("=" * 70)
        
        return results
    
    def create_interactive_grid_map(
        self,
        output_file: str = "outputs/grid_fire_spread_analysis.html"
    ) -> str:
        """
        Create interactive map with grid points and hover-to-view isochrones
        """
        print("\nCreating interactive map...")
        
        if not self.grid_results:
            raise ValueError("No grid results to display. Run run_grid_analysis() first.")
        
        # Create base map
        center_lat = np.mean([r['actual_lat'] for r in self.grid_results])
        center_lon = np.mean([r['actual_lon'] for r in self.grid_results])
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Add satellite layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add all isochrone overlays directly to map (always visible)
        for i, result in enumerate(self.grid_results):
            if result['isochrone_image'] and result['isochrone_bounds']:
                folium.raster_layers.ImageOverlay(
                    image=result['isochrone_image'],
                    bounds=result['isochrone_bounds'],
                    opacity=0.7,
                    interactive=False,
                    name=f'Isochrones {i+1}'
                ).add_to(m)
        
        # Add all markers in a single always-visible layer
        marker_group = folium.FeatureGroup(name='Ignition Points', show=True)
        
        for i, result in enumerate(self.grid_results):
            # Color code by burned area
            acres = result['burned_acres']
            if acres < 50:
                color = 'green'
                risk = 'Low'
            elif acres < 200:
                color = 'orange'
                risk = 'Moderate'
            elif acres < 500:
                color = 'red'
                risk = 'High'
            else:
                color = 'darkred'
                risk = 'Extreme'
            
            popup_html = f"""
            <b>Ignition Point {i+1}</b><br>
            <b>Risk Level:</b> {risk}<br>
            <b>Burned Area:</b> {acres:.0f} acres<br>
            <b>Location:</b> {result['actual_lat']:.4f}, {result['actual_lon']:.4f}<br>
            <br>
            <i>Fire spread shown in color-coded isochrones</i>
            """
            
            marker = folium.CircleMarker(
                location=[result['actual_lat'], result['actual_lon']],
                radius=8,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"Point {i+1}: {acres:.0f} acres ({risk} risk)",
                color='black',
                fillColor=color,
                fillOpacity=0.8,
                weight=2
            )
            marker.add_to(marker_group)
        
        marker_group.add_to(m)
        
        # Add instructions
        instructions_html = '''
        <div style="position: fixed; 
                    top: 10px; left: 60px; width: 380px; 
                    background-color: rgba(255, 255, 255, 0.95); z-index:9999; font-size:12px;
                    border:3px solid #e74c3c; border-radius: 8px; padding: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <h3 style="margin-top:0; color:#e74c3c;">🔥 Grid Fire Spread Analysis</h3>
        <p style="margin: 8px 0;"><b>Extreme Fire Conditions:</b></p>
        <div style="font-size: 11px; margin-left: 10px;">
            • Wind: 35 mph (High winds)<br>
            • Fuel Moisture: 3% (Critically dry)<br>
            • Temperature: 105°F (Extreme heat)<br>
            • Duration: 48 hours (2 days)
        </div>
        
        <p style="margin: 8px 0; font-size: 11px;"><b>What you see:</b></p>
        <ul style="margin: 5px 0; padding-left: 20px; font-size: 11px;">
            <li>Color-coded isochrones showing fire spread from each ignition point</li>
            <li>Markers show potential ignition locations</li>
            <li>Hover over markers for burned area details</li>
            <li>All fire spreads visible simultaneously</li>
        </ul>
        
        <p style="margin: 8px 0; font-size: 11px;"><b>Color Legend:</b></p>
        <div style="font-size: 11px; margin-left: 10px;">
            <span style="color: green;">●</span> Green: &lt; 50 acres (Low risk)<br>
            <span style="color: orange;">●</span> Orange: 50-200 acres (Moderate)<br>
            <span style="color: red;">●</span> Red: 200-500 acres (High)<br>
            <span style="color: darkred;">●</span> Dark Red: &gt; 500 acres (Extreme)
        </div>
        
        <p style="margin: 8px 0 0 0; font-size: 11px;"><b>Isochrone Colors:</b></p>
        <div style="font-size: 10px; margin-left: 10px;">
            🔴 Red: 0-1 hr • 🟠 Orange: 1-6 hr<br>
            🟡 Gold: 6-12 hr • 🔵 Blue: 12-24 hr<br>
            � Purple: 24-48 hr • 🟪 Indigo: 48-72 hr
        </div>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(instructions_html))
        
        # Add summary legend
        total_points = len(self.grid_results)
        avg_acres = np.mean([r['burned_acres'] for r in self.grid_results])
        max_acres = np.max([r['burned_acres'] for r in self.grid_results])
        
        summary_html = f'''
        <div style="position: fixed; 
                    bottom: 30px; right: 10px; width: 220px; 
                    background-color: white; z-index:9999; font-size:11px;
                    border:2px solid grey; border-radius: 5px; padding: 10px;">
        <h4 style="margin-top:0;">Analysis Summary</h4>
        <b>Grid Points:</b> {total_points}<br>
        <b>Avg Burned:</b> {avg_acres:.0f} acres<br>
        <b>Max Burned:</b> {max_acres:.0f} acres<br>
        <br>
        <small>Toggle layers to compare<br>ignition point scenarios</small>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(summary_html))
        
        # Add controls
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        plugins.Fullscreen(position='topleft').add_to(m)
        plugins.MeasureControl(position='topleft').add_to(m)
        
        # Save map
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        m.save(str(output_path))
        
        print(f"✓ Map saved to: {output_path.absolute()}")
        
        # Save summary stats
        stats_file = output_path.parent / f"{output_path.stem}_stats.json"
        stats = {
            'total_points': total_points,
            'avg_burned_acres': float(avg_acres),
            'max_burned_acres': float(max_acres),
            'points': [
                {
                    'lat': r['actual_lat'],
                    'lon': r['actual_lon'],
                    'burned_acres': r['burned_acres']
                }
                for r in self.grid_results
            ]
        }
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✓ Statistics saved to: {stats_file.absolute()}")
        
        return str(output_path.absolute())


def main():
    """Run grid fire spread analysis"""
    
    print("\n" + "=" * 70)
    print("GRID FIRE SPREAD ANALYSIS")
    print("=" * 70)
    
    # Define analysis area around Healdsburg
    # Using a 5x5 grid covering the region
    analysis_bounds = (
        38.58,   # lat_min (south)
        38.68,   # lat_max (north)
        -122.92, # lon_min (west)
        -122.84  # lon_max (east)
    )
    
    print(f"\nAnalysis area:")
    print(f"  Latitude: {analysis_bounds[0]:.2f} to {analysis_bounds[1]:.2f}")
    print(f"  Longitude: {analysis_bounds[2]:.2f} to {analysis_bounds[3]:.2f}")
    
    # Create analyzer
    analyzer = GridFireSpreadAnalysis()
    
    # Generate grid (5x5 = 25 points)
    grid_points = analyzer.generate_grid_points(
        bounds=analysis_bounds,
        grid_size=5
    )
    
    print(f"\nGenerated {len(grid_points)} grid points")
    
    # Run analysis with Tubbs Fire conditions (October 8-9, 2017)
    # The Tubbs Fire was driven by extreme northeast "Diablo" winds
    # Peak winds reached 60+ mph with very low humidity and fuel moisture
    print("\n" + "=" * 70)
    print("TUBBS FIRE CONDITIONS (October 8-9, 2017)")
    print("=" * 70)
    print("\nWeather Parameters:")
    print("  • Wind Speed: 60 mph (peak Diablo winds)")
    print("  • Wind Direction: 45° (Northeast)")
    print("  • Fuel Moisture: 3% (extremely dry)")
    print("  • Temperature: 85°F (evening Diablo conditions)")
    print("  • Relative Humidity: ~10% (very dry air)")
    print("\nHistoric Fire Behavior:")
    print("  • Ignited: 9:43 PM, October 8, 2017 near Calistoga")
    print("  • Traveled 12+ miles in first 3 hours")
    print("  • Reached Santa Rosa by 1:00 AM")
    print("  • Peak winds: 60+ mph at 4:30 AM")
    print("  • Total burned: 36,807 acres")
    print("  • Structures destroyed: 5,643")
    print("=" * 70)
    
    results = analyzer.run_grid_analysis(
        grid_points=grid_points,
        wind_speed=60,  # Peak Tubbs Fire winds
        wind_direction=45,  # Northeast (Diablo winds)
        fuel_moisture=3,  # Diablo wind conditions - very dry
        temperature=85,  # Evening temps during Diablo winds
        duration_hours=48  # Extended timeline - 2 days
    )
    
    # Create interactive map
    map_file = analyzer.create_interactive_grid_map(
        output_file="outputs/grid_fire_spread_analysis.html"
    )
    
    print("\n" + "=" * 70)
    print("✓ GRID ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nInteractive map: {map_file}")
    print("\nFeatures:")
    print("  • Toggleable fire spread for each ignition point")
    print("  • Color-coded risk levels")
    print("  • Time-to-arrival isochrones")
    print("  • Hover tooltips with burned area")
    print("\nUse the layer control to toggle individual scenarios on/off")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
