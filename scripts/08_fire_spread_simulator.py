#!/usr/bin/env python3
"""
Fire Spread Simulator with Time-to-Arrival Isochrones
Simulates fire spread from an ignition point and generates isochrones
"""

import rasterio
import numpy as np
import folium
from folium import plugins
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Dict, Tuple, List, Optional
import base64
from io import BytesIO
from PIL import Image
from collections import deque
import importlib.util


# Import fire behavior calculator
script_dir = Path(__file__).parent
spec = importlib.util.spec_from_file_location(
    "fire_behavior_calc",
    script_dir / "02_fire_behavior_calc.py"
)
fire_calc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fire_calc_module)
FireBehaviorCalculator = fire_calc_module.FireBehaviorCalculator


class FireSpreadSimulator:
    """
    Simulate fire spread using Huygens' principle with cellular propagation
    """
    
    # Map FBFM40 codes to simplified fuel models
    FBFM_TO_MODEL = {
        # Grass models (101-109)
        101: 'GR1', 102: 'GR1', 103: 'GR2', 104: 'GR2',
        105: 'GR2', 106: 'GR2', 107: 'GR2', 108: 'GR2', 109: 'GR2',
        
        # Grass-shrub models (121-124)
        121: 'GR2', 122: 'GR2', 123: 'GR2', 124: 'GR2',
        
        # Shrub models (141-149)
        141: 'SH5', 142: 'SH5', 143: 'SH5', 144: 'SH5', 145: 'SH5',
        146: 'SH5', 147: 'SH5', 148: 'SH5', 149: 'SH5',
        
        # Timber understory (161-165)
        161: 'TU1', 162: 'TU1', 163: 'TU1', 164: 'TU1', 165: 'TU1',
        
        # Timber litter (181-189)
        181: 'TL5', 182: 'TL5', 183: 'TL5', 184: 'TL5', 185: 'TL5',
        186: 'TL5', 187: 'TL5', 188: 'TL5', 189: 'TL5',
        
        # Slash-blowdown (201-204)
        201: 'TL5', 202: 'TL5', 203: 'TL5', 204: 'TL5',
        
        # Non-burnable (91-99)
        91: None, 92: None, 93: None, 98: None, 99: None,
    }
    
    def __init__(self, data_dir: str = "data/landfire"):
        self.data_dir = Path(data_dir)
        self.data = {}
        self.calculator = FireBehaviorCalculator()
        self.ros_map = None  # Rate of spread for each pixel (ft/min)
        self.pixel_size_ft = 98.4  # 30m = ~98.4 feet
        
        # Healdsburg center
        self.healdsburg_lat = 38.6102
        self.healdsburg_lon = -122.8694
        
    def load_data(self) -> Dict:
        """Load LANDFIRE GeoTIFF files"""
        print("Loading LANDFIRE data...")
        
        products = ['FBFM40', 'SLPD', 'ASPD']
        
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
        
        print(f"✓ Loaded {len(self.data)} products\n")
        return self.data
    
    def calculate_ros_map(
        self,
        wind_speed: float = 15,
        wind_direction: float = 0,
        fuel_moisture: float = 6,
        temperature: float = 85,
        relative_humidity: float = 25
    ) -> np.ndarray:
        """
        Pre-calculate rate of spread for each pixel
        
        Returns:
            Array of ROS in feet per minute for each pixel
        """
        print(f"\nCalculating rate of spread map...")
        print(f"  Wind: {wind_speed} mph from {wind_direction}°")
        print(f"  Fuel moisture: {fuel_moisture}%")
        print(f"  Temperature: {temperature}°F, RH: {relative_humidity}%")
        
        if 'FBFM40' not in self.data or 'SLPD' not in self.data:
            raise ValueError("Required data (FBFM40, SLPD) not loaded")
        
        fbfm = self.data['FBFM40']['array']
        slope = self.data['SLPD']['array']
        
        # Initialize ROS array
        shape = fbfm.shape
        ros_array = np.zeros(shape, dtype=np.float32)
        
        # Get unique fuel models
        unique_fbfm = np.unique(fbfm)
        unique_fbfm = unique_fbfm[unique_fbfm > 0]
        
        print(f"  Processing {len(unique_fbfm)} unique fuel models...")
        
        # Calculate for each fuel model
        for fbfm_code in unique_fbfm:
            fuel_model = self.FBFM_TO_MODEL.get(int(fbfm_code))
            
            if fuel_model is None:
                continue  # Non-burnable
            
            # Find pixels with this fuel model
            mask = (fbfm == fbfm_code)
            
            # Get average slope for this fuel type
            avg_slope = np.mean(slope[mask])
            
            # Calculate fire behavior
            try:
                result = self.calculator.calculate_rate_of_spread(
                    fuel_model=fuel_model,
                    wind_speed=wind_speed,
                    slope=avg_slope,
                    fuel_moisture=fuel_moisture,
                    temperature=temperature,
                    relative_humidity=relative_humidity
                )
                
                # Store ROS in ft/min
                ros_array[mask] = result['rate_of_spread_ft_min']
                
            except Exception as e:
                print(f"    Warning: Could not calculate for {fuel_model}: {e}")
                continue
        
        self.ros_map = ros_array
        
        # Statistics
        burnable_mask = ros_array > 0
        print(f"\n✓ ROS map calculated")
        print(f"  Mean ROS: {np.mean(ros_array[burnable_mask]):.1f} ft/min")
        print(f"  Max ROS: {np.max(ros_array[burnable_mask]):.1f} ft/min")
        
        return ros_array
    
    def simulate_spread(
        self,
        ignition_row: int,
        ignition_col: int,
        duration_hours: float = 24,
        time_step_minutes: float = 30
    ) -> np.ndarray:
        """
        Simulate fire spread from ignition point using wave propagation
        
        Args:
            ignition_row: Row index of ignition point
            ignition_col: Column index of ignition point
            duration_hours: How long to simulate (hours)
            time_step_minutes: Time step for simulation (minutes)
        
        Returns:
            Array with arrival time in hours for each pixel (0 = unburned)
        """
        print(f"\nSimulating fire spread...")
        print(f"  Ignition: row={ignition_row}, col={ignition_col}")
        print(f"  Duration: {duration_hours} hours")
        print(f"  Time step: {time_step_minutes} minutes")
        
        if self.ros_map is None:
            raise ValueError("Must call calculate_ros_map() first")
        
        shape = self.ros_map.shape
        
        # Check if ignition point is burnable
        ignition_ros = self.ros_map[ignition_row, ignition_col]
        print(f"  Ignition point ROS: {ignition_ros:.2f} ft/min")
        
        if ignition_ros <= 0:
            print(f"  WARNING: Ignition point is non-burnable! Searching for nearest burnable pixel...")
            
            # Find nearest burnable pixel
            search_radius = 100
            best_row, best_col = ignition_row, ignition_col
            best_distance = float('inf')
            
            for dr in range(-search_radius, search_radius + 1):
                for dc in range(-search_radius, search_radius + 1):
                    r = ignition_row + dr
                    c = ignition_col + dc
                    if 0 <= r < shape[0] and 0 <= c < shape[1]:
                        if self.ros_map[r, c] > 0:
                            dist = (dr**2 + dc**2)**0.5
                            if dist < best_distance:
                                best_distance = dist
                                best_row, best_col = r, c
            
            if best_distance < float('inf'):
                print(f"  Found burnable pixel at row={best_row}, col={best_col}")
                print(f"  Distance: {best_distance:.1f} pixels ({best_distance * self.pixel_size_ft:.0f} ft)")
                print(f"  ROS at new location: {self.ros_map[best_row, best_col]:.2f} ft/min")
                ignition_row, ignition_col = best_row, best_col
            else:
                print(f"  ERROR: No burnable pixels found within {search_radius} pixels!")
                return np.zeros(self.ros_map.shape, dtype=np.float32)
        
        arrival_time = np.zeros(shape, dtype=np.float32)  # Hours
        burning = np.zeros(shape, dtype=bool)
        
        # Priority queue: (arrival_time, row, col)
        # Using simple approach: track cells to process
        active = deque()
        active.append((0.0, ignition_row, ignition_col))
        arrival_time[ignition_row, ignition_col] = 0.0
        burning[ignition_row, ignition_col] = True
        
        # 8-neighbor offsets
        neighbors = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        # Distance for each neighbor (pixels)
        neighbor_dist = [
            1.414, 1.0, 1.414,  # Diagonal, straight, diagonal
            1.0,        1.0,     # Straight, straight
            1.414, 1.0, 1.414   # Diagonal, straight, diagonal
        ]
        
        processed = 0
        max_steps = int(duration_hours * 60 / time_step_minutes)
        
        while active and processed < max_steps * 1000:  # Safety limit
            current_time, row, col = active.popleft()
            
            if current_time > duration_hours:
                continue
            
            processed += 1
            
            # Process neighbors
            for (dr, dc), dist in zip(neighbors, neighbor_dist):
                new_row = row + dr
                new_col = col + dc
                
                # Check bounds
                if not (0 <= new_row < shape[0] and 0 <= new_col < shape[1]):
                    continue
                
                # Skip if already burned
                if burning[new_row, new_col]:
                    continue
                
                # Skip non-burnable
                ros = self.ros_map[new_row, new_col]
                if ros <= 0:
                    continue
                
                # Calculate travel time to this cell
                distance_ft = dist * self.pixel_size_ft
                travel_time_hours = (distance_ft / ros) / 60.0  # Convert min to hours
                new_arrival_time = current_time + travel_time_hours
                
                # Only update if this is first time reaching or faster route
                if new_arrival_time <= duration_hours:
                    arrival_time[new_row, new_col] = new_arrival_time
                    burning[new_row, new_col] = True
                    active.append((new_arrival_time, new_row, new_col))
        
        burned_pixels = np.sum(burning)
        burned_acres = burned_pixels * (self.pixel_size_ft ** 2) / 43560
        
        print(f"\n✓ Simulation complete")
        print(f"  Processed {processed} cell transitions")
        print(f"  Burned area: {burned_acres:,.0f} acres")
        print(f"  Burned pixels: {burned_pixels:,}")
        
        # Store actual ignition point used (for accurate marker placement)
        self.actual_ignition_row = ignition_row
        self.actual_ignition_col = ignition_col
        
        return arrival_time
    
    def latlon_to_pixel(self, lat: float, lon: float) -> Tuple[int, int]:
        """Convert lat/lon to pixel coordinates"""
        transform = self.data['FBFM40']['transform']
        # rasterio transform: (lon, lat) -> (col, row)
        # We need (x, y) = (lon, lat) then inverse transform gives (col, row)
        col, row = ~transform * (lon, lat)
        return int(round(row)), int(round(col))
    
    def pixel_to_latlon(self, row: int, col: int) -> Tuple[float, float]:
        """Convert pixel coordinates to lat/lon"""
        transform = self.data['FBFM40']['transform']
        lon, lat = transform * (col, row)
        return lat, lon
    
    def create_isochrone_overlay(
        self,
        arrival_time: np.ndarray,
        max_hours: float = 24
    ) -> Tuple[str, list]:
        """
        Create colored overlay showing time-to-arrival isochrones
        
        Args:
            arrival_time: Array with arrival time in hours
            max_hours: Maximum time to display
        """
        bounds = self.data['FBFM40']['bounds']
        
        # Define isochrone intervals (hours) - extended timeline
        intervals = [0, 1, 3, 6, 12, 24, 48, 72]
        # Better color scheme: Red -> Orange -> Yellow -> Light Blue -> Purple
        # (Hot colors = imminent threat, cool colors = distant threat)
        colors_rgb = [
            [255, 0, 0, 230],      # 0-1 hr: Bright red (IMMEDIATE)
            [255, 100, 0, 210],    # 1-3 hr: Orange-red (URGENT)
            [255, 165, 0, 200],    # 3-6 hr: Orange (HIGH PRIORITY)
            [255, 215, 0, 190],    # 6-12 hr: Gold (MODERATE)
            [173, 216, 230, 170],  # 12-24 hr: Light blue (PLANNING)
            [147, 112, 219, 150],  # 24-48 hr: Purple (LOW PRIORITY)
            [75, 0, 130, 130],     # 48-72 hr: Indigo (MINIMAL THREAT)
        ]
        
        # Create RGBA image
        rgba = np.zeros((*arrival_time.shape, 4), dtype=np.uint8)
        
        # Apply colors based on arrival time
        for i in range(len(intervals) - 1):
            t_min = intervals[i]
            t_max = intervals[i + 1]
            mask = (arrival_time > t_min) & (arrival_time <= t_max)
            rgba[mask] = colors_rgb[i]
        
        # Unburned areas stay transparent
        rgba[arrival_time == 0] = [0, 0, 0, 0]
        
        # Convert to PIL Image
        img = Image.fromarray(rgba, 'RGBA')
        
        # Save to BytesIO and encode
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        img_url = f"data:image/png;base64,{img_base64}"
        
        # Bounds
        bounds_list = [
            [bounds.bottom, bounds.left],
            [bounds.top, bounds.right]
        ]
        
        return img_url, bounds_list
    
    def create_interactive_map(
        self,
        arrival_time: np.ndarray,
        ignition_lat: float,
        ignition_lon: float,
        scenario_name: str = "Fire Spread Simulation",
        output_file: str = "outputs/fire_spread_simulation.html"
    ) -> str:
        """
        Create interactive map with isochrones and click-to-ignite feature
        """
        print(f"\nCreating interactive map...")
        
        # Use actual ignition point if available (after adjustment for burnable fuel)
        if hasattr(self, 'actual_ignition_row') and hasattr(self, 'actual_ignition_col'):
            actual_lat, actual_lon = self.pixel_to_latlon(
                self.actual_ignition_row, 
                self.actual_ignition_col
            )
            print(f"  Using adjusted ignition point: {actual_lat:.6f}, {actual_lon:.6f}")
        else:
            actual_lat, actual_lon = ignition_lat, ignition_lon
        
        # Create base map
        m = folium.Map(
            location=[self.healdsburg_lat, self.healdsburg_lon],
            zoom_start=12,
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
        
        # Add isochrone overlay
        iso_img, iso_bounds = self.create_isochrone_overlay(arrival_time)
        if iso_img and iso_bounds:
            folium.raster_layers.ImageOverlay(
                image=iso_img,
                bounds=iso_bounds,
                opacity=0.7,
                name='Fire Spread (Time-to-Arrival)',
                interactive=True
            ).add_to(m)
        
        # Add ignition point marker
        folium.Marker(
            [actual_lat, actual_lon],
            popup=f'<b>Ignition Point</b><br>{scenario_name}<br>Lat: {actual_lat:.6f}<br>Lon: {actual_lon:.6f}',
            tooltip='Ignition Point',
            icon=folium.Icon(color='red', icon='fire', prefix='fa')
        ).add_to(m)
        
        # Add Healdsburg marker
        folium.Marker(
            [self.healdsburg_lat, self.healdsburg_lon],
            popup='<b>Healdsburg, CA</b>',
            tooltip='Healdsburg',
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        
        # Calculate perimeters for key time intervals
        burned_1hr = np.sum((arrival_time > 0) & (arrival_time <= 1))
        burned_6hr = np.sum((arrival_time > 0) & (arrival_time <= 6))
        burned_24hr = np.sum((arrival_time > 0) & (arrival_time <= 24))
        
        acres_1hr = burned_1hr * (self.pixel_size_ft ** 2) / 43560
        acres_6hr = burned_6hr * (self.pixel_size_ft ** 2) / 43560
        acres_24hr = burned_24hr * (self.pixel_size_ft ** 2) / 43560
        
        # Add legend with statistics
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; right: 10px; width: 260px; 
                    background-color: white; z-index:9999; font-size:12px;
                    border:2px solid grey; border-radius: 5px; padding: 10px;">
        <h4 style="margin-top:0;">{scenario_name}</h4>
        
        <p style="margin: 5px 0;"><b>Time-to-Arrival Isochrones:</b></p>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ff0000; width:20px; height:15px; display:inline-block;"></span>
            0-1 hour (IMMEDIATE)
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ff6400; width:20px; height:15px; display:inline-block;"></span>
            1-3 hours (URGENT)
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ffa500; width:20px; height:15px; display:inline-block;"></span>
            3-6 hours (HIGH)
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ffd700; width:20px; height:15px; display:inline-block;"></span>
            6-12 hours (MODERATE)
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#add8e6; width:20px; height:15px; display:inline-block;"></span>
            12-24 hours (PLANNING)
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#9370db; width:20px; height:15px; display:inline-block;"></span>
            24-48 hours (LOW)
        </div>
        <div style="margin-bottom: 10px;">
            <span style="background-color:#4b0082; width:20px; height:15px; display:inline-block;"></span>
            48-72 hours (MINIMAL)
        </div>
        
        <p style="margin: 5px 0;"><b>Burned Area:</b></p>
        <div style="font-size: 11px;">
            • 1 hour: {acres_1hr:,.0f} acres<br>
            • 6 hours: {acres_6hr:,.0f} acres<br>
            • 24 hours: {acres_24hr:,.0f} acres
        </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add controls
        folium.LayerControl(position='topright').add_to(m)
        plugins.Fullscreen(position='topleft').add_to(m)
        plugins.MeasureControl(position='topleft').add_to(m)
        plugins.MousePosition().add_to(m)
        
        # Save map
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        m.save(str(output_path))
        
        print(f"✓ Map saved to: {output_path.absolute()}")
        
        return str(output_path.absolute())


def main():
    """Run fire spread simulation"""
    
    print("\n" + "=" * 70)
    print("FIRE SPREAD SIMULATOR - TIME-TO-ARRIVAL ISOCHRONES")
    print("=" * 70)
    
    # Initialize simulator
    sim = FireSpreadSimulator()
    sim.load_data()
    
    # Calculate ROS map for weather conditions
    sim.calculate_ros_map(
        wind_speed=20,
        wind_direction=0,
        fuel_moisture=5,
        temperature=95,
        relative_humidity=20
    )
    
    # Set ignition point (Healdsburg center for demo)
    ignition_lat = 38.6102
    ignition_lon = -122.8694
    ignition_row, ignition_col = sim.latlon_to_pixel(ignition_lat, ignition_lon)
    
    print(f"\nIgnition point: {ignition_lat}, {ignition_lon}")
    print(f"Pixel coordinates: row={ignition_row}, col={ignition_col}")
    
    # Simulate spread
    arrival_time = sim.simulate_spread(
        ignition_row=ignition_row,
        ignition_col=ignition_col,
        duration_hours=24,
        time_step_minutes=30
    )
    
    # Create interactive map
    map_file = sim.create_interactive_map(
        arrival_time=arrival_time,
        ignition_lat=ignition_lat,
        ignition_lon=ignition_lon,
        scenario_name="24-Hour Fire Spread",
        output_file="outputs/fire_spread_simulation.html"
    )
    
    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE!")
    print("=" * 70)
    print(f"\nMap: {map_file}")
    print("\nThe map shows time-to-arrival isochrones:")
    print("  • Red zones: Fire arrives in 0-1 hours")
    print("  • Orange zones: Fire arrives in 1-6 hours")
    print("  • Yellow zones: Fire arrives in 6-12 hours")
    print("  • Green zones: Fire arrives in 12-24+ hours")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
