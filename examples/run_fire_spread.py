#!/usr/bin/env python3
"""
Run Fire Spread Simulation
Simulates fire spread from a specified ignition point
"""

import sys
from pathlib import Path
import argparse

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


def run_simulation(
    ignition_lat: float,
    ignition_lon: float,
    wind_speed: float = 15,
    fuel_moisture: float = 6,
    temperature: float = 85,
    duration_hours: float = 24,
    output_file: str = None
):
    """
    Run fire spread simulation from specified ignition point
    """
    
    print("\n" + "=" * 70)
    print("FIRE SPREAD SIMULATION")
    print("=" * 70)
    print(f"\nIgnition Point: {ignition_lat:.6f}, {ignition_lon:.6f}")
    print(f"\nWeather Conditions:")
    print(f"  Wind Speed: {wind_speed} mph")
    print(f"  Fuel Moisture: {fuel_moisture}%")
    print(f"  Temperature: {temperature}°F")
    print(f"\nSimulation Duration: {duration_hours} hours")
    print("=" * 70)
    
    # Initialize simulator
    sim = FireSpreadSimulator()
    sim.load_data()
    
    # Calculate ROS map
    sim.calculate_ros_map(
        wind_speed=wind_speed,
        wind_direction=0,
        fuel_moisture=fuel_moisture,
        temperature=temperature,
        relative_humidity=25
    )
    
    # Convert lat/lon to pixel coordinates
    ignition_row, ignition_col = sim.latlon_to_pixel(ignition_lat, ignition_lon)
    
    # Check if within bounds
    shape = sim.ros_map.shape
    if not (0 <= ignition_row < shape[0] and 0 <= ignition_col < shape[1]):
        print(f"\n❌ ERROR: Ignition point is outside the data bounds!")
        print(f"   Row {ignition_row}, Col {ignition_col} not in shape {shape}")
        return None
    
    # Simulate spread
    arrival_time = sim.simulate_spread(
        ignition_row=ignition_row,
        ignition_col=ignition_col,
        duration_hours=duration_hours,
        time_step_minutes=30
    )
    
    # Generate output filename if not provided
    if output_file is None:
        lat_str = f"{abs(ignition_lat):.4f}{'N' if ignition_lat >= 0 else 'S'}"
        lon_str = f"{abs(ignition_lon):.4f}{'E' if ignition_lon >= 0 else 'W'}"
        output_file = f"outputs/fire_spread_{lat_str}_{lon_str}.html"
    
    # Create interactive map
    map_file = sim.create_interactive_map(
        arrival_time=arrival_time,
        ignition_lat=ignition_lat,
        ignition_lon=ignition_lon,
        scenario_name=f"{duration_hours}-Hour Fire Spread",
        output_file=output_file
    )
    
    print("\n" + "=" * 70)
    print("✓ SIMULATION COMPLETE!")
    print("=" * 70)
    print(f"\nInteractive Map: {map_file}")
    print("\nThe map shows time-to-arrival isochrones:")
    print("  🔴 Red: Fire arrives in 0-1 hours (IMMEDIATE THREAT)")
    print("  🟠 Orange: Fire arrives in 1-6 hours")
    print("  🟡 Yellow: Fire arrives in 6-12 hours")
    print("  🟢 Green: Fire arrives in 12-24+ hours")
    print("\nUse this for:")
    print("  • Evacuation timing decisions")
    print("  • Resource pre-positioning")
    print("  • Structure protection prioritization")
    print("=" * 70 + "\n")
    
    return map_file


def main():
    """Command-line interface for fire spread simulation"""
    
    parser = argparse.ArgumentParser(
        description='Run fire spread simulation from ignition point',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic simulation at Healdsburg center
  python run_fire_spread.py 38.6102 -122.8694
  
  # With custom weather
  python run_fire_spread.py 38.6102 -122.8694 --wind 25 --moisture 4 --temp 95
  
  # Longer duration
  python run_fire_spread.py 38.6102 -122.8694 --duration 48
        '''
    )
    
    parser.add_argument('latitude', type=float, help='Ignition point latitude')
    parser.add_argument('longitude', type=float, help='Ignition point longitude')
    parser.add_argument('--wind', type=float, default=15, help='Wind speed (mph, default: 15)')
    parser.add_argument('--moisture', type=float, default=6, help='Fuel moisture (%%, default: 6)')
    parser.add_argument('--temp', type=float, default=85, help='Temperature (°F, default: 85)')
    parser.add_argument('--duration', type=float, default=24, help='Simulation duration (hours, default: 24)')
    parser.add_argument('--output', type=str, default=None, help='Output HTML file path')
    
    args = parser.parse_args()
    
    run_simulation(
        ignition_lat=args.latitude,
        ignition_lon=args.longitude,
        wind_speed=args.wind,
        fuel_moisture=args.moisture,
        temperature=args.temp,
        duration_hours=args.duration,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
