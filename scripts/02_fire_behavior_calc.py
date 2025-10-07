#!/usr/bin/env python3
"""
Fire Behavior Calculations
Implements basic fire spread calculations using Rothermel's model
"""

import numpy as np
from typing import Dict, Tuple
import json

class FireBehaviorCalculator:
    """
    Calculate basic fire behavior characteristics using simplified Rothermel model
    
    References:
    - Rothermel, R.C. (1972). A mathematical model for predicting fire spread
    - Scott & Burgan (2005). Standard Fire Behavior Fuel Models
    """
    
    # Fuel model characteristics (simplified from FBFM40)
    FUEL_MODELS = {
        'GR1': {  # Short, sparse dry grass
            'name': 'Short, sparse dry climate grass',
            'fuel_load': 0.1,  # tons/acre
            'sav_ratio': 2200,  # surface-area-to-volume ratio (1/ft)
            'fuel_bed_depth': 0.4,  # feet
            'moisture_of_extinction': 15,  # percent
        },
        'GR2': {  # Low load, dry climate grass
            'name': 'Low load, dry climate grass',
            'fuel_load': 0.2,
            'sav_ratio': 2000,
            'fuel_bed_depth': 1.0,
            'moisture_of_extinction': 15,
        },
        'SH5': {  # High load, dry climate shrub
            'name': 'High load, dry climate shrub',
            'fuel_load': 3.5,
            'sav_ratio': 750,
            'fuel_bed_depth': 6.0,
            'moisture_of_extinction': 15,
        },
        'TU1': {  # Light load, dry climate timber-grass-shrub
            'name': 'Light load, dry climate timber-grass-shrub',
            'fuel_load': 0.6,
            'sav_ratio': 1800,
            'fuel_bed_depth': 0.6,
            'moisture_of_extinction': 20,
        },
        'TL5': {  # Moderate load conifer litter
            'name': 'Moderate load conifer litter',
            'fuel_load': 1.2,
            'sav_ratio': 1400,
            'fuel_bed_depth': 0.3,
            'moisture_of_extinction': 25,
        },
    }
    
    def __init__(self):
        self.results = {}
    
    def calculate_rate_of_spread(
        self,
        fuel_model: str,
        wind_speed: float,  # mph at midflame height
        slope: float,  # percent
        fuel_moisture: float,  # percent
        temperature: float = 70,  # Fahrenheit
        relative_humidity: float = 40,  # percent
    ) -> Dict[str, float]:
        """
        Calculate fire rate of spread
        
        Args:
            fuel_model: Fuel model code (e.g., 'GR2', 'SH5')
            wind_speed: Wind speed at midflame height (mph)
            slope: Slope steepness (percent)
            fuel_moisture: Dead fuel moisture content (percent)
            temperature: Air temperature (°F)
            relative_humidity: Relative humidity (%)
        
        Returns:
            Dictionary with fire behavior predictions
        """
        if fuel_model not in self.FUEL_MODELS:
            raise ValueError(f"Unknown fuel model: {fuel_model}")
        
        fm = self.FUEL_MODELS[fuel_model]
        
        # Simplified calculations (actual Rothermel is more complex)
        
        # Moisture damping coefficient
        moisture_damping = self._moisture_damping(
            fuel_moisture, 
            fm['moisture_of_extinction']
        )
        
        # Wind coefficient (simplified)
        wind_factor = 1 + (wind_speed / 10) ** 0.5
        
        # Slope factor (simplified)
        slope_factor = 1 + (slope / 100) * 0.3
        
        # Base rate of spread (chains per hour)
        # This is highly simplified - real model is much more complex
        base_ros = (fm['fuel_load'] * fm['sav_ratio'] / 1000) * moisture_damping
        
        # Adjusted rate of spread
        ros = base_ros * wind_factor * slope_factor
        
        # Flame length (Byram's equation, simplified)
        # FL = 0.45 * I^0.46, where I is fireline intensity
        intensity = ros * fm['fuel_load'] * 8000  # BTU/ft/s (simplified)
        flame_length = 0.45 * (intensity ** 0.46)
        
        # Fire type determination
        fire_type = self._classify_fire_type(flame_length, wind_speed)
        
        results = {
            'fuel_model': fuel_model,
            'fuel_model_name': fm['name'],
            'rate_of_spread_ch_hr': round(ros, 2),
            'rate_of_spread_ft_min': round(ros * 66 / 60, 2),  # convert chains/hr to ft/min
            'flame_length_ft': round(flame_length, 2),
            'fireline_intensity_btu_ft_s': round(intensity, 0),
            'fire_type': fire_type,
            'conditions': {
                'wind_speed_mph': wind_speed,
                'slope_percent': slope,
                'fuel_moisture_percent': fuel_moisture,
                'temperature_f': temperature,
                'relative_humidity_percent': relative_humidity,
            }
        }
        
        return results
    
    def _moisture_damping(self, moisture: float, moisture_extinction: float) -> float:
        """Calculate moisture damping coefficient"""
        if moisture >= moisture_extinction:
            return 0.0
        ratio = moisture / moisture_extinction
        return max(0, 1 - 2.59 * ratio + 5.11 * ratio**2 - 3.52 * ratio**3)
    
    def _classify_fire_type(self, flame_length: float, wind_speed: float) -> str:
        """Classify fire behavior type"""
        if flame_length < 4:
            return "Surface fire - low intensity"
        elif flame_length < 8:
            if wind_speed > 15:
                return "Surface fire - wind driven"
            else:
                return "Surface fire - moderate intensity"
        elif flame_length < 12:
            return "Transition to crown fire potential"
        else:
            return "Crown fire potential - extreme behavior"
    
    def print_results(self, results: Dict):
        """Print formatted results"""
        print("\n" + "=" * 70)
        print("FIRE BEHAVIOR PREDICTION")
        print("=" * 70)
        print(f"\nFuel Model: {results['fuel_model']} - {results['fuel_model_name']}")
        print("\nInput Conditions:")
        print(f"  Wind Speed:       {results['conditions']['wind_speed_mph']} mph")
        print(f"  Slope:            {results['conditions']['slope_percent']}%")
        print(f"  Fuel Moisture:    {results['conditions']['fuel_moisture_percent']}%")
        print(f"  Temperature:      {results['conditions']['temperature_f']}°F")
        print(f"  Rel. Humidity:    {results['conditions']['relative_humidity_percent']}%")
        
        print("\nPredicted Fire Behavior:")
        print(f"  Rate of Spread:   {results['rate_of_spread_ch_hr']} chains/hour")
        print(f"                    {results['rate_of_spread_ft_min']} feet/minute")
        print(f"  Flame Length:     {results['flame_length_ft']} feet")
        print(f"  Fireline Int.:    {results['fireline_intensity_btu_ft_s']:,.0f} BTU/ft/s")
        print(f"  Fire Type:        {results['fire_type']}")
        print("=" * 70 + "\n")


def run_scenarios():
    """Run several fire behavior scenarios"""
    calc = FireBehaviorCalculator()
    
    scenarios = [
        {
            'name': 'Mild conditions - grassland',
            'fuel_model': 'GR1',
            'wind_speed': 5,
            'slope': 10,
            'fuel_moisture': 12,
        },
        {
            'name': 'Moderate conditions - grassland',
            'fuel_model': 'GR2',
            'wind_speed': 15,
            'slope': 20,
            'fuel_moisture': 6,
        },
        {
            'name': 'Extreme conditions - shrubland',
            'fuel_model': 'SH5',
            'wind_speed': 25,
            'slope': 30,
            'fuel_moisture': 4,
            'temperature': 95,
            'relative_humidity': 15,
        },
        {
            'name': 'Moderate conditions - timber',
            'fuel_model': 'TL5',
            'wind_speed': 10,
            'slope': 15,
            'fuel_moisture': 8,
        },
    ]
    
    print("\n" + "=" * 70)
    print("FIRE BEHAVIOR SCENARIO ANALYSIS")
    print("=" * 70)
    
    for scenario in scenarios:
        print(f"\n▶ Scenario: {scenario['name']}")
        results = calc.calculate_rate_of_spread(**{k: v for k, v in scenario.items() if k != 'name'})
        calc.print_results(results)


def main():
    """Example usage"""
    print("Fire Behavior Calculator")
    print("Based on Rothermel fire spread model")
    print()
    
    # List available fuel models
    calc = FireBehaviorCalculator()
    print("Available Fuel Models:")
    for code, info in calc.FUEL_MODELS.items():
        print(f"  {code}: {info['name']}")
    print()
    
    # Run example scenarios
    run_scenarios()
    
    print("\nNote: These are simplified calculations for demonstration.")
    print("For operational use, consult professional fire behavior tools like:")
    print("  - BehavePlus")
    print("  - FlamMap")
    print("  - FARSITE")
    print("  - Technosylva Wildfire Analyst")


if __name__ == "__main__":
    main()
