#!/usr/bin/env python3
"""
Demo Fire Analysis
Runs a complete demonstration of fire behavior analysis without requiring external data
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime


class DemoFireAnalysis:
    """
    Demonstration fire analysis using synthetic data
    Shows the workflow for a real fire analysis project
    """
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_synthetic_landscape(self, size: int = 100) -> dict:
        """
        Create a synthetic landscape for demonstration
        
        Returns a dictionary with terrain and fuel characteristics
        """
        print("Creating synthetic landscape...")
        
        # Create terrain
        x = np.linspace(0, 10, size)
        y = np.linspace(0, 10, size)
        X, Y = np.meshgrid(x, y)
        
        # Elevation - create hills and valleys
        elevation = (
            100 * np.sin(X * 0.5) * np.cos(Y * 0.5) +
            50 * np.sin(X * 1.2) * np.sin(Y * 0.8) +
            500
        )
        
        # Calculate slope (simplified)
        grad_y, grad_x = np.gradient(elevation)
        slope = np.sqrt(grad_x**2 + grad_y**2) * 5  # percent
        
        # Calculate aspect
        aspect = np.arctan2(grad_y, grad_x) * 180 / np.pi
        aspect = (aspect + 360) % 360  # convert to 0-360
        
        # Fuel models - create zones
        fuel_zones = np.zeros((size, size), dtype=int)
        fuel_zones[elevation < 480] = 1  # Grassland in valleys
        fuel_zones[(elevation >= 480) & (elevation < 520)] = 2  # Shrubland
        fuel_zones[elevation >= 520] = 3  # Timber on ridges
        
        # Canopy cover (higher in timber areas)
        canopy_cover = np.zeros((size, size))
        canopy_cover[fuel_zones == 1] = np.random.uniform(5, 20, (fuel_zones == 1).sum())
        canopy_cover[fuel_zones == 2] = np.random.uniform(20, 50, (fuel_zones == 2).sum())
        canopy_cover[fuel_zones == 3] = np.random.uniform(50, 85, (fuel_zones == 3).sum())
        
        landscape = {
            'size': size,
            'elevation': elevation,
            'slope': slope,
            'aspect': aspect,
            'fuel_zones': fuel_zones,
            'canopy_cover': canopy_cover,
        }
        
        print(f"✓ Created {size}x{size} landscape")
        print(f"  Elevation range: {elevation.min():.0f} - {elevation.max():.0f} m")
        print(f"  Slope range: {slope.min():.1f} - {slope.max():.1f} %")
        print(f"  Fuel zones: {np.unique(fuel_zones).size}")
        
        return landscape
    
    def analyze_fire_risk(self, landscape: dict, weather: dict) -> dict:
        """
        Analyze fire risk across the landscape
        
        Args:
            landscape: Landscape characteristics
            weather: Weather conditions
        """
        print("\nAnalyzing fire risk...")
        
        size = landscape['size']
        slope = landscape['slope']
        fuel_zones = landscape['fuel_zones']
        
        # Base fire risk by fuel type
        fuel_risk = np.zeros((size, size))
        fuel_risk[fuel_zones == 1] = 0.6  # Grass - moderate
        fuel_risk[fuel_zones == 2] = 0.8  # Shrub - high
        fuel_risk[fuel_zones == 3] = 0.5  # Timber - moderate (unless crown fire)
        
        # Adjust for slope
        slope_factor = 1 + (slope / 100) * 0.5
        
        # Adjust for weather
        wind_factor = 1 + (weather['wind_speed'] / 20)
        moisture_factor = max(0.3, 1 - (weather['fuel_moisture'] / 20))
        
        # Combined risk
        fire_risk = fuel_risk * slope_factor * wind_factor * moisture_factor
        fire_risk = np.clip(fire_risk, 0, 1)
        
        # Classify risk levels
        risk_categories = np.zeros((size, size), dtype=int)
        risk_categories[fire_risk < 0.3] = 1  # Low
        risk_categories[(fire_risk >= 0.3) & (fire_risk < 0.6)] = 2  # Moderate
        risk_categories[(fire_risk >= 0.6) & (fire_risk < 0.8)] = 3  # High
        risk_categories[fire_risk >= 0.8] = 4  # Extreme
        
        # Calculate statistics
        total_pixels = size * size
        risk_stats = {
            'low': (risk_categories == 1).sum() / total_pixels * 100,
            'moderate': (risk_categories == 2).sum() / total_pixels * 100,
            'high': (risk_categories == 3).sum() / total_pixels * 100,
            'extreme': (risk_categories == 4).sum() / total_pixels * 100,
        }
        
        print(f"✓ Fire risk analysis complete")
        print(f"  Risk distribution:")
        print(f"    Low:      {risk_stats['low']:.1f}%")
        print(f"    Moderate: {risk_stats['moderate']:.1f}%")
        print(f"    High:     {risk_stats['high']:.1f}%")
        print(f"    Extreme:  {risk_stats['extreme']:.1f}%")
        
        return {
            'fire_risk': fire_risk,
            'risk_categories': risk_categories,
            'risk_stats': risk_stats,
        }
    
    def simulate_fire_spread(self, landscape: dict, ignition_point: tuple, hours: int = 6) -> dict:
        """
        Simple fire spread simulation
        
        Args:
            landscape: Landscape characteristics
            ignition_point: (x, y) coordinates of fire start
            hours: Hours to simulate
        """
        print(f"\nSimulating fire spread for {hours} hours...")
        
        size = landscape['size']
        slope = landscape['slope']
        fuel_zones = landscape['fuel_zones']
        
        # Initialize burned area
        burned = np.zeros((size, size), dtype=bool)
        burned[ignition_point] = True
        
        # Spread rates by fuel type (relative)
        spread_rates = {1: 1.2, 2: 1.5, 3: 0.8}  # grass, shrub, timber
        
        # Simulate spread over time
        for hour in range(hours):
            new_burned = burned.copy()
            
            # Find fire perimeter
            for i in range(1, size - 1):
                for j in range(1, size - 1):
                    if burned[i, j]:
                        # Check neighbors
                        neighbors = [
                            (i-1, j), (i+1, j), (i, j-1), (i, j+1)
                        ]
                        
                        for ni, nj in neighbors:
                            if not burned[ni, nj]:
                                # Probability of spread
                                fuel_type = fuel_zones[ni, nj]
                                base_prob = spread_rates.get(fuel_type, 1.0) * 0.15
                                slope_boost = slope[ni, nj] / 100 * 0.1
                                
                                prob = min(base_prob + slope_boost, 0.9)
                                
                                if np.random.random() < prob:
                                    new_burned[ni, nj] = True
            
            burned = new_burned
            acres_burned = burned.sum() * 0.25  # Assume ~0.25 acres per pixel
            print(f"  Hour {hour + 1}: {acres_burned:.0f} acres burned")
        
        final_acres = burned.sum() * 0.25
        
        print(f"✓ Simulation complete")
        print(f"  Total area burned: {final_acres:.0f} acres")
        
        return {
            'burned_area': burned,
            'total_acres': final_acres,
            'hours': hours,
        }
    
    def generate_report(self, analysis_results: dict) -> str:
        """Generate analysis report"""
        report_file = self.output_dir / f"fire_analysis_report_{self.analysis_id}.json"
        
        with open(report_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"\n✓ Report saved to {report_file}")
        return str(report_file)


def main():
    """Run demonstration analysis"""
    print("\n" + "=" * 70)
    print("FIRE ANALYSIS DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Initialize
    demo = DemoFireAnalysis()
    
    # Create synthetic landscape
    landscape = demo.create_synthetic_landscape(size=100)
    
    # Define weather conditions
    weather = {
        'wind_speed': 15,  # mph
        'wind_direction': 270,  # degrees (west wind)
        'temperature': 85,  # F
        'relative_humidity': 25,  # percent
        'fuel_moisture': 6,  # percent
    }
    
    print(f"\nWeather Conditions:")
    print(f"  Wind: {weather['wind_speed']} mph from {weather['wind_direction']}°")
    print(f"  Temperature: {weather['temperature']}°F")
    print(f"  RH: {weather['relative_humidity']}%")
    print(f"  Fuel Moisture: {weather['fuel_moisture']}%")
    
    # Analyze fire risk
    risk_analysis = demo.analyze_fire_risk(landscape, weather)
    
    # Simulate fire spread
    ignition = (50, 50)  # Center of landscape
    spread_sim = demo.simulate_fire_spread(landscape, ignition, hours=6)
    
    # Generate report
    results = {
        'analysis_id': demo.analysis_id,
        'landscape': {
            'size': landscape['size'],
            'elevation_range': [float(landscape['elevation'].min()), 
                               float(landscape['elevation'].max())],
            'slope_range': [float(landscape['slope'].min()), 
                           float(landscape['slope'].max())],
        },
        'weather': weather,
        'risk_stats': risk_analysis['risk_stats'],
        'fire_simulation': {
            'ignition_point': ignition,
            'hours_simulated': spread_sim['hours'],
            'total_acres_burned': float(spread_sim['total_acres']),
        },
    }
    
    report_file = demo.generate_report(results)
    
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"\nUnder these conditions:")
    print(f"  • {risk_analysis['risk_stats']['high'] + risk_analysis['risk_stats']['extreme']:.1f}% of area at HIGH or EXTREME risk")
    print(f"  • Simulated fire burned {spread_sim['total_acres']:.0f} acres in {spread_sim['hours']} hours")
    print(f"  • Average spread rate: {spread_sim['total_acres'] / spread_sim['hours']:.0f} acres/hour")
    print(f"\nThis demonstrates the workflow you would use with real LANDFIRE data")
    print(f"and actual fire behavior models (FSIM, Technosylva, etc.)")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
