#!/usr/bin/env python3
"""
Interactive Fire Behavior Analysis Tool
Allows users to input custom scenarios and get fire behavior predictions
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from fire_behavior_calc import FireBehaviorCalculator


def get_float_input(prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
    """Get validated float input from user"""
    while True:
        try:
            user_input = input(f"{prompt} [default: {default}]: ").strip()
            if not user_input:
                return default
            
            value = float(user_input)
            
            if min_val is not None and value < min_val:
                print(f"  ⚠️  Value must be at least {min_val}")
                continue
            
            if max_val is not None and value > max_val:
                print(f"  ⚠️  Value must be at most {max_val}")
                continue
            
            return value
        except ValueError:
            print("  ⚠️  Please enter a valid number")


def get_fuel_model_input(calc: FireBehaviorCalculator) -> str:
    """Get fuel model selection from user"""
    print("\nAvailable Fuel Models:")
    print("-" * 60)
    for i, (code, info) in enumerate(calc.FUEL_MODELS.items(), 1):
        print(f"  {i}. {code} - {info['name']}")
    print("-" * 60)
    
    while True:
        choice = input("Select fuel model (1-5) or enter code (e.g., GR2): ").strip()
        
        # Check if it's a number
        if choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(calc.FUEL_MODELS):
                return list(calc.FUEL_MODELS.keys())[choice_num - 1]
            else:
                print(f"  ⚠️  Please enter a number between 1 and {len(calc.FUEL_MODELS)}")
                continue
        
        # Check if it's a valid code
        if choice.upper() in calc.FUEL_MODELS:
            return choice.upper()
        
        print("  ⚠️  Invalid selection. Please try again.")


def print_weather_guidance():
    """Print guidance for weather inputs"""
    print("\n" + "=" * 70)
    print("WEATHER INPUT GUIDANCE")
    print("=" * 70)
    print()
    print("🌡️  Temperature:")
    print("   • Normal: 60-80°F")
    print("   • Elevated: 80-95°F")
    print("   • Extreme: 95°F+")
    print()
    print("💧 Relative Humidity:")
    print("   • Normal: 40-60%")
    print("   • Dry: 25-40%")
    print("   • Critical: <25%")
    print()
    print("💨 Wind Speed (at midflame height):")
    print("   • Calm: 0-5 mph")
    print("   • Moderate: 5-15 mph")
    print("   • Strong: 15-25 mph")
    print("   • Extreme: 25+ mph")
    print()
    print("🌿 Fuel Moisture (dead fuels):")
    print("   • Wet/Safe: >15%")
    print("   • Moderate: 8-15%")
    print("   • Dry: 5-8%")
    print("   • Critical: <5%")
    print()
    print("⛰️  Slope:")
    print("   • Flat: 0-10%")
    print("   • Moderate: 10-30%")
    print("   • Steep: 30-50%")
    print("   • Extreme: >50%")
    print("=" * 70 + "\n")


def run_interactive_mode():
    """Run interactive fire behavior analysis"""
    print("\n" + "=" * 70)
    print("INTERACTIVE FIRE BEHAVIOR CALCULATOR")
    print("=" * 70)
    print()
    print("This tool helps you predict fire behavior based on:")
    print("  • Fuel type and characteristics")
    print("  • Weather conditions (wind, temperature, humidity)")
    print("  • Topography (slope)")
    print("  • Fuel moisture content")
    print()
    
    calc = FireBehaviorCalculator()
    
    while True:
        print("\n" + "=" * 70)
        print("NEW FIRE BEHAVIOR SCENARIO")
        print("=" * 70)
        
        # Get fuel model
        fuel_model = get_fuel_model_input(calc)
        print(f"\n✓ Selected: {fuel_model} - {calc.FUEL_MODELS[fuel_model]['name']}")
        
        # Ask if user wants guidance
        show_help = input("\nShow weather input guidance? (y/n) [n]: ").strip().lower()
        if show_help == 'y':
            print_weather_guidance()
        
        # Get weather inputs
        print("\nEnter weather and terrain conditions:")
        print("-" * 60)
        
        wind_speed = get_float_input(
            "Wind speed (mph)",
            default=10,
            min_val=0,
            max_val=100
        )
        
        slope = get_float_input(
            "Slope (percent)",
            default=15,
            min_val=0,
            max_val=100
        )
        
        fuel_moisture = get_float_input(
            "Fuel moisture (percent)",
            default=8,
            min_val=1,
            max_val=50
        )
        
        temperature = get_float_input(
            "Temperature (°F)",
            default=75,
            min_val=-20,
            max_val=130
        )
        
        relative_humidity = get_float_input(
            "Relative humidity (%)",
            default=40,
            min_val=1,
            max_val=100
        )
        
        # Calculate fire behavior
        print("\nCalculating fire behavior...")
        
        results = calc.calculate_rate_of_spread(
            fuel_model=fuel_model,
            wind_speed=wind_speed,
            slope=slope,
            fuel_moisture=fuel_moisture,
            temperature=temperature,
            relative_humidity=relative_humidity
        )
        
        # Display results
        calc.print_results(results)
        
        # Provide interpretation
        print_interpretation(results)
        
        # Ask to continue
        print()
        continue_choice = input("Run another scenario? (y/n) [y]: ").strip().lower()
        if continue_choice == 'n':
            break
    
    print("\n" + "=" * 70)
    print("Thank you for using the Fire Behavior Calculator!")
    print("=" * 70)
    print()
    print("Remember: These are simplified calculations for educational use.")
    print("For operational decisions, consult professional fire behavior analysts.")
    print()


def print_interpretation(results: dict):
    """Print interpretation and recommendations"""
    print("INTERPRETATION & RECOMMENDATIONS")
    print("=" * 70)
    
    flame_length = results['flame_length_ft']
    ros = results['rate_of_spread_ft_min']
    fire_type = results['fire_type']
    
    # Suppression difficulty
    print("\n** Suppression Considerations:")
    if flame_length < 4:
        print("   • Hand crews can work directly at fire edge")
        print("   • Direct attack should be effective")
        print("   • Standard firefighting tactics applicable")
    elif flame_length < 8:
        print("   • Hand crews may work with difficulty")
        print("   • Consider using engines and hand tools")
        print("   • Direct attack possible but challenging")
    elif flame_length < 12:
        print("   • Direct attack generally not safe")
        print("   • Dozers, engines, and aircraft needed")
        print("   • Focus on indirect tactics and containment")
    else:
        print("   • ⚠️  EXTREME FIRE BEHAVIOR")
        print("   • Direct attack generally ineffective and unsafe")
        print("   • Consider evacuation and structure protection")
        print("   • Air support and heavy equipment essential")
    
    # Safety concerns
    print("\n** Safety Considerations:")
    if "extreme" in fire_type.lower() or "crown" in fire_type.lower():
        print("   • [HIGH RISK] to firefighter safety")
        print("   • Rapid fire spread possible")
        print("   • Establish wide safety zones")
        print("   • Plan escape routes in advance")
        print("   • Consider conditions for LCES (Lookouts, Communications, Escape routes, Safety zones)")
    elif flame_length > 8:
        print("   • [MODERATE RISK] - use caution")
        print("   • Monitor fire behavior closely")
        print("   • Maintain good communication")
        print("   • Have escape routes identified")
    else:
        print("   • [LOWER RISK] with standard precautions")
        print("   • Follow standard firefighting safety protocols")
        print("   • Maintain situational awareness")
    
    # Rate of spread concerns
    print("\n** Spread Characteristics:")
    if ros < 1:
        print("   • Slow-moving fire, good time for tactics")
    elif ros < 5:
        print("   • Moderate spread - standard tactics should work")
    elif ros < 15:
        print("   • Fast-moving fire - act quickly")
    else:
        print("   • ⚠️  Very fast spread - limited time for action")
        print("   • Focus on safety and protection priorities")
    
    # Weather watch
    conditions = results['conditions']
    print("\n** Weather Factors to Monitor:")
    if conditions['wind_speed_mph'] > 20:
        print("   • [HIGH] winds - major fire driver")
    if conditions['relative_humidity_percent'] < 25:
        print("   • [CRITICAL] Low humidity - critical fire weather")
    if conditions['fuel_moisture_percent'] < 6:
        print("   • [CRITICAL] Very dry fuels - extreme fire danger")
    if conditions['temperature_f'] > 90:
        print("   • [ELEVATED] High temperatures contributing to fire activity")
    
    # Red flag warning check
    if (conditions['relative_humidity_percent'] < 25 and conditions['wind_speed_mph'] > 20) or \
       (conditions['relative_humidity_percent'] < 15 and conditions['wind_speed_mph'] > 15):
        print("\n   *** RED FLAG WARNING CONDITIONS ***")
        print("   Critical fire weather - extreme caution required!")
    
    print("=" * 70)


def print_help():
    """Print help information"""
    print("\nFire Behavior Calculator - Interactive Mode")
    print()
    print("Usage:")
    print("  python fire_calc.py              # Run interactive mode")
    print("  python fire_calc.py --help       # Show this help")
    print()
    print("This tool provides fire behavior predictions based on the Rothermel")
    print("fire spread model using Scott & Burgan fuel models.")
    print()
    print("For more information, see:")
    print("  - FUEL_MODELS_GUIDE.md")
    print("  - GETTING_STARTED.md")
    print()


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        return
    
    run_interactive_mode()


if __name__ == "__main__":
    main()
