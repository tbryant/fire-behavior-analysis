#!/usr/bin/env python3
"""
Healdsburg Fire Behavior Predictions
Combines LANDFIRE data with fire behavior calculations to predict fire behavior
across the Healdsburg area under different weather scenarios.
"""

import rasterio
import numpy as np
import folium
from folium import plugins
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Dict, Tuple, List
import base64
from io import BytesIO
from PIL import Image
import sys

# Import fire behavior calculator
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Import from the fire behavior calc script
import importlib.util
spec = importlib.util.spec_from_file_location(
    "fire_behavior_calc",
    script_dir / "02_fire_behavior_calc.py"
)
fire_calc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fire_calc_module)
FireBehaviorCalculator = fire_calc_module.FireBehaviorCalculator


class HealdsburgFirePredictor:
    """
    Predict fire behavior across Healdsburg area using LANDFIRE data
    """
    
    # Map FBFM40 codes to simplified fuel model categories
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
        self.predictions = {}
        self.calculator = FireBehaviorCalculator()
        
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
    
    def calculate_fire_predictions(
        self,
        scenario_name: str,
        wind_speed: float,
        wind_direction: float = 0,  # degrees (0=North, 90=East, etc.)
        fuel_moisture: float = 8,
        temperature: float = 85,
        relative_humidity: float = 25
    ) -> Dict:
        """
        Calculate fire behavior predictions for each pixel
        
        Args:
            scenario_name: Name of the scenario
            wind_speed: Wind speed in mph
            wind_direction: Wind direction in degrees (0=North)
            fuel_moisture: Fuel moisture percent
            temperature: Temperature in °F
            relative_humidity: Relative humidity percent
        
        Returns:
            Dictionary with prediction arrays
        """
        print(f"\nCalculating fire predictions for scenario: {scenario_name}")
        print(f"  Wind: {wind_speed} mph from {wind_direction}°")
        print(f"  Fuel moisture: {fuel_moisture}%")
        print(f"  Temperature: {temperature}°F")
        print(f"  Relative humidity: {relative_humidity}%")
        
        if 'FBFM40' not in self.data or 'SLPD' not in self.data:
            raise ValueError("Required data (FBFM40, SLPD) not loaded")
        
        fbfm = self.data['FBFM40']['array']
        slope = self.data['SLPD']['array']
        
        # Initialize output arrays
        shape = fbfm.shape
        ros_array = np.zeros(shape, dtype=np.float32)
        flame_length_array = np.zeros(shape, dtype=np.float32)
        intensity_array = np.zeros(shape, dtype=np.float32)
        
        # Get unique fuel models
        unique_fbfm = np.unique(fbfm)
        unique_fbfm = unique_fbfm[unique_fbfm > 0]  # Remove nodata
        
        print(f"  Processing {len(unique_fbfm)} unique fuel models...")
        
        # Calculate for each fuel model
        for fbfm_code in unique_fbfm:
            # Map to simplified fuel model
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
                
                # Fill arrays
                ros_array[mask] = result['rate_of_spread_ch_hr']
                flame_length_array[mask] = result['flame_length_ft']
                intensity_array[mask] = result['fireline_intensity_btu_ft_s']
                
            except Exception as e:
                print(f"    Warning: Could not calculate for {fuel_model}: {e}")
                continue
        
        # Store predictions
        self.predictions[scenario_name] = {
            'rate_of_spread': ros_array,
            'flame_length': flame_length_array,
            'intensity': intensity_array,
            'conditions': {
                'wind_speed': wind_speed,
                'wind_direction': wind_direction,
                'fuel_moisture': fuel_moisture,
                'temperature': temperature,
                'relative_humidity': relative_humidity,
            }
        }
        
        # Calculate statistics
        burnable_mask = ros_array > 0
        stats = {
            'scenario': scenario_name,
            'conditions': self.predictions[scenario_name]['conditions'],
            'statistics': {
                'rate_of_spread': {
                    'mean': float(np.mean(ros_array[burnable_mask])),
                    'max': float(np.max(ros_array[burnable_mask])),
                    'min': float(np.min(ros_array[burnable_mask])),
                    'std': float(np.std(ros_array[burnable_mask])),
                },
                'flame_length': {
                    'mean': float(np.mean(flame_length_array[burnable_mask])),
                    'max': float(np.max(flame_length_array[burnable_mask])),
                    'min': float(np.min(flame_length_array[burnable_mask])),
                    'std': float(np.std(flame_length_array[burnable_mask])),
                },
                'area_acres': float(np.sum(burnable_mask) * 900 / 4047),  # 30m pixels to acres
            }
        }
        
        print(f"✓ Predictions complete")
        print(f"  Mean ROS: {stats['statistics']['rate_of_spread']['mean']:.1f} ch/hr")
        print(f"  Mean flame length: {stats['statistics']['flame_length']['mean']:.1f} ft")
        print(f"  Burnable area: {stats['statistics']['area_acres']:.0f} acres")
        
        return stats
    
    def create_prediction_overlay(
        self,
        scenario_name: str,
        variable: str = 'flame_length'
    ) -> Tuple[str, list]:
        """
        Create colored overlay for predictions
        
        Args:
            scenario_name: Name of scenario
            variable: 'rate_of_spread', 'flame_length', or 'intensity'
        """
        if scenario_name not in self.predictions:
            return None, None
        
        array = self.predictions[scenario_name][variable]
        bounds = self.data['FBFM40']['bounds']
        
        # Define color schemes for each variable
        if variable == 'flame_length':
            # Green -> Yellow -> Orange -> Red
            colors = ['#00ff00', '#ffff00', '#ff8800', '#ff0000', '#880000']
            boundaries = [0, 4, 8, 12, 20, 50]
            label = 'Flame Length (ft)'
        elif variable == 'rate_of_spread':
            # Blue -> Cyan -> Yellow -> Red
            colors = ['#0000ff', '#00ffff', '#ffff00', '#ff8800', '#ff0000']
            boundaries = [0, 5, 10, 20, 40, 100]
            label = 'Rate of Spread (ch/hr)'
        else:  # intensity
            colors = ['#00ff00', '#ffff00', '#ff8800', '#ff0000', '#880000']
            boundaries = [0, 100, 500, 1000, 2000, 10000]
            label = 'Fireline Intensity (BTU/ft/s)'
        
        # Create colormap
        cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(boundaries, cmap.N)
        
        # Mask non-burnable areas
        masked_array = np.ma.masked_where(array == 0, array)
        
        # Apply colormap
        rgba = cmap(norm(masked_array))
        rgba = (rgba * 255).astype(np.uint8)
        
        # Set transparency for non-burnable
        rgba[array == 0] = [0, 0, 0, 0]
        
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
    
    def create_prediction_map(
        self,
        scenarios: List[Dict],
        output_file: str = "outputs/healdsburg_fire_predictions.html"
    ) -> str:
        """
        Create interactive map with fire predictions
        
        Args:
            scenarios: List of scenario dictionaries
            output_file: Output HTML file path
        """
        print("\n" + "=" * 70)
        print("CREATING FIRE PREDICTION MAP")
        print("=" * 70)
        
        # Calculate predictions for each scenario
        stats_list = []
        for scenario in scenarios:
            stats = self.calculate_fire_predictions(**scenario)
            stats_list.append(stats)
        
        # Create base map
        print("\nCreating interactive map...")
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
        
        # Add prediction overlays for each scenario
        for i, scenario in enumerate(scenarios):
            scenario_name = scenario['scenario_name']
            
            # Flame length overlay
            fl_img, fl_bounds = self.create_prediction_overlay(scenario_name, 'flame_length')
            if fl_img and fl_bounds:
                folium.raster_layers.ImageOverlay(
                    image=fl_img,
                    bounds=fl_bounds,
                    opacity=0.7,
                    name=f'{scenario_name} - Flame Length',
                    show=(i == 0)  # Show first scenario by default
                ).add_to(m)
            
            # Rate of spread overlay
            ros_img, ros_bounds = self.create_prediction_overlay(scenario_name, 'rate_of_spread')
            if ros_img and ros_bounds:
                folium.raster_layers.ImageOverlay(
                    image=ros_img,
                    bounds=ros_bounds,
                    opacity=0.7,
                    name=f'{scenario_name} - Rate of Spread',
                    show=False
                ).add_to(m)
        
        # Add Healdsburg marker
        folium.Marker(
            [self.healdsburg_lat, self.healdsburg_lon],
            popup='<b>Healdsburg, CA</b>',
            icon=folium.Icon(color='red', icon='fire', prefix='fa')
        ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 10px; width: 220px; 
                    background-color: white; z-index:9999; font-size:12px;
                    border:2px solid grey; border-radius: 5px; padding: 10px;">
        <h4 style="margin-top:0;">Fire Prediction Legend</h4>
        
        <p style="margin: 5px 0;"><b>Flame Length:</b></p>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#00ff00; width:20px; height:15px; display:inline-block;"></span>
            &lt; 4 ft (Low)
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ffff00; width:20px; height:15px; display:inline-block;"></span>
            4-8 ft (Moderate)
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ff8800; width:20px; height:15px; display:inline-block;"></span>
            8-12 ft (High)
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ff0000; width:20px; height:15px; display:inline-block;"></span>
            12-20 ft (Very High)
        </div>
        <div style="margin-bottom: 10px;">
            <span style="background-color:#880000; width:20px; height:15px; display:inline-block;"></span>
            &gt; 20 ft (Extreme)
        </div>
        
        <p style="margin: 5px 0;"><b>Rate of Spread:</b></p>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#0000ff; width:20px; height:15px; display:inline-block;"></span>
            &lt; 5 ch/hr
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#00ffff; width:20px; height:15px; display:inline-block;"></span>
            5-10 ch/hr
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ffff00; width:20px; height:15px; display:inline-block;"></span>
            10-20 ch/hr
        </div>
        <div style="margin-bottom: 2px;">
            <span style="background-color:#ff8800; width:20px; height:15px; display:inline-block;"></span>
            20-40 ch/hr
        </div>
        <div>
            <span style="background-color:#ff0000; width:20px; height:15px; display:inline-block;"></span>
            &gt; 40 ch/hr
        </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add controls
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        plugins.Fullscreen(position='topleft').add_to(m)
        plugins.MeasureControl(position='topleft').add_to(m)
        
        # Save map
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        m.save(str(output_path))
        
        # Save statistics
        stats_file = output_path.parent / f"{output_path.stem}_statistics.json"
        with open(stats_file, 'w') as f:
            json.dump(stats_list, f, indent=2)
        
        print("\n" + "=" * 70)
        print("FIRE PREDICTION MAP COMPLETE!")
        print("=" * 70)
        print(f"\nMap saved to: {output_path.absolute()}")
        print(f"Statistics saved to: {stats_file.absolute()}")
        print("\nScenarios analyzed:")
        for stats in stats_list:
            print(f"\n  {stats['scenario']}:")
            print(f"    Mean flame length: {stats['statistics']['flame_length']['mean']:.1f} ft")
            print(f"    Max flame length: {stats['statistics']['flame_length']['max']:.1f} ft")
            print(f"    Mean ROS: {stats['statistics']['rate_of_spread']['mean']:.1f} ch/hr")
        print("=" * 70 + "\n")
        
        return str(output_path.absolute())


def main():
    """Run Healdsburg fire predictions"""
    
    # Define weather scenarios
    scenarios = [
        {
            'scenario_name': 'Moderate Conditions',
            'wind_speed': 10,
            'wind_direction': 0,
            'fuel_moisture': 8,
            'temperature': 75,
            'relative_humidity': 40,
        },
        {
            'scenario_name': 'Red Flag Warning',
            'wind_speed': 25,
            'wind_direction': 0,
            'fuel_moisture': 5,
            'temperature': 95,
            'relative_humidity': 15,
        },
        {
            'scenario_name': 'Extreme Fire Weather',
            'wind_speed': 40,
            'wind_direction': 0,
            'fuel_moisture': 3,
            'temperature': 105,
            'relative_humidity': 10,
        },
    ]
    
    # Create predictor and generate map
    predictor = HealdsburgFirePredictor()
    predictor.load_data()
    map_file = predictor.create_prediction_map(scenarios)
    
    print(f"\nTo view the predictions, open: {map_file}")
    print("\nUse the layer control to toggle between scenarios and variables.")


if __name__ == "__main__":
    main()
