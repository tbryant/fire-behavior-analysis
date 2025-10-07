#!/usr/bin/env python3
"""
Healdsburg Fire Predictions Example
Simple example showing how to run fire predictions for the Healdsburg area
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

# Import the predictor
import importlib.util
spec = importlib.util.spec_from_file_location(
    "healdsburg_predictions",
    Path(__file__).parent.parent / "scripts" / "07_healdsburg_fire_predictions.py"
)
pred_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pred_module)

HealdsburgFirePredictor = pred_module.HealdsburgFirePredictor


def main():
    """Run fire predictions for Healdsburg area"""
    
    print("\n" + "=" * 70)
    print("HEALDSBURG FIRE BEHAVIOR PREDICTIONS")
    print("=" * 70)
    print("\nThis example calculates fire behavior predictions across the")
    print("Healdsburg area under different weather scenarios using actual")
    print("LANDFIRE fuel, terrain, and vegetation data.")
    print()
    
    # Define weather scenarios to analyze
    scenarios = [
        {
            'scenario_name': 'Typical Summer Day',
            'wind_speed': 8,
            'wind_direction': 270,  # West wind
            'fuel_moisture': 10,
            'temperature': 80,
            'relative_humidity': 35,
        },
        {
            'scenario_name': 'Red Flag Warning',
            'wind_speed': 25,
            'wind_direction': 0,  # North wind (typical for Diablo winds)
            'fuel_moisture': 5,
            'temperature': 95,
            'relative_humidity': 15,
        },
        {
            'scenario_name': 'Extreme Fire Weather (Diablo Winds)',
            'wind_speed': 40,
            'wind_direction': 0,  # North wind
            'fuel_moisture': 3,
            'temperature': 105,
            'relative_humidity': 8,
        },
    ]
    
    print("Weather scenarios to analyze:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['scenario_name']}")
        print(f"   Wind: {scenario['wind_speed']} mph from {scenario['wind_direction']}°")
        print(f"   Temp: {scenario['temperature']}°F, RH: {scenario['relative_humidity']}%")
        print(f"   Fuel moisture: {scenario['fuel_moisture']}%")
    
    print("\n" + "=" * 70)
    
    # Create predictor
    predictor = HealdsburgFirePredictor()
    
    # Load LANDFIRE data
    predictor.load_data()
    
    # Generate predictions map
    map_file = predictor.create_prediction_map(
        scenarios=scenarios,
        output_file="outputs/healdsburg_fire_predictions.html"
    )
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nInteractive map: {map_file}")
    print("\nThe map includes:")
    print("  • Fire behavior predictions for each scenario")
    print("  • Flame length overlays (color-coded)")
    print("  • Rate of spread overlays")
    print("  • Interactive layer control to compare scenarios")
    print("\nUse the layer control in the top-right to:")
    print("  • Toggle between weather scenarios")
    print("  • Switch between flame length and rate of spread")
    print("  • Compare different conditions")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
