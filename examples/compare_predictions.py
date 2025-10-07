#!/usr/bin/env python3
"""
Create comparison charts for Healdsburg fire predictions
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def create_comparison_charts(stats_file: str = "outputs/healdsburg_fire_predictions_statistics.json"):
    """Create comparison charts from prediction statistics"""
    
    # Load statistics
    stats_path = Path(stats_file)
    if not stats_path.exists():
        print(f"Error: Statistics file not found: {stats_file}")
        print("Run 'python examples/healdsburg_fire_predictions.py' first")
        return
    
    with open(stats_path) as f:
        stats_list = json.load(f)
    
    # Extract data
    scenarios = [s['scenario'] for s in stats_list]
    mean_ros = [s['statistics']['rate_of_spread']['mean'] for s in stats_list]
    max_ros = [s['statistics']['rate_of_spread']['max'] for s in stats_list]
    mean_fl = [s['statistics']['flame_length']['mean'] for s in stats_list]
    max_fl = [s['statistics']['flame_length']['max'] for s in stats_list]
    
    wind_speeds = [s['conditions']['wind_speed'] for s in stats_list]
    fuel_moistures = [s['conditions']['fuel_moisture'] for s in stats_list]
    temps = [s['conditions']['temperature'] for s in stats_list]
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Healdsburg Fire Behavior Predictions - Scenario Comparison', 
                 fontsize=16, fontweight='bold')
    
    # Color scheme
    colors = ['#2ecc71', '#f39c12', '#e74c3c']  # Green, Orange, Red
    
    # Plot 1: Mean Fire Behavior by Scenario
    ax1 = axes[0, 0]
    x = np.arange(len(scenarios))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, mean_ros, width, label='Rate of Spread', color=colors)
    ax1_twin = ax1.twinx()
    bars2 = ax1_twin.bar(x + width/2, mean_fl, width, label='Flame Length', color='orange', alpha=0.7)
    
    ax1.set_xlabel('Scenario', fontweight='bold')
    ax1.set_ylabel('Mean Rate of Spread (chains/hr)', color='steelblue', fontweight='bold')
    ax1_twin.set_ylabel('Mean Flame Length (ft)', color='orange', fontweight='bold')
    ax1.set_title('Mean Fire Behavior by Scenario')
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios, rotation=15, ha='right')
    ax1.tick_params(axis='y', labelcolor='steelblue')
    ax1_twin.tick_params(axis='y', labelcolor='orange')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        height = bar.get_height()
        ax1_twin.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}', ha='center', va='bottom', fontsize=9)
    
    # Plot 2: Maximum Fire Behavior
    ax2 = axes[0, 1]
    x_pos = np.arange(len(scenarios))
    
    bars = ax2.bar(x_pos, max_fl, color=colors, alpha=0.8, edgecolor='black')
    ax2.set_xlabel('Scenario', fontweight='bold')
    ax2.set_ylabel('Maximum Flame Length (ft)', fontweight='bold')
    ax2.set_title('Maximum Flame Length by Scenario')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(scenarios, rotation=15, ha='right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f} ft', ha='center', va='bottom', fontsize=9)
    
    # Add danger threshold lines
    ax2.axhline(y=4, color='yellow', linestyle='--', alpha=0.5, label='Low intensity threshold')
    ax2.axhline(y=8, color='orange', linestyle='--', alpha=0.5, label='Moderate intensity threshold')
    ax2.axhline(y=12, color='red', linestyle='--', alpha=0.5, label='Crown fire potential')
    ax2.legend(fontsize=8, loc='upper left')
    
    # Plot 3: Weather Conditions
    ax3 = axes[1, 0]
    x_pos = np.arange(len(scenarios))
    width = 0.25
    
    bars1 = ax3.bar(x_pos - width, wind_speeds, width, label='Wind Speed (mph)', color='skyblue')
    bars2 = ax3.bar(x_pos, fuel_moistures, width, label='Fuel Moisture (%)', color='brown')
    bars3 = ax3.bar(x_pos + width, [t/10 for t in temps], width, label='Temp (°F ÷10)', color='red', alpha=0.7)
    
    ax3.set_xlabel('Scenario', fontweight='bold')
    ax3.set_ylabel('Value', fontweight='bold')
    ax3.set_title('Weather Conditions by Scenario')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(scenarios, rotation=15, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Fire Intensity Categories
    ax4 = axes[1, 1]
    
    # Calculate percentage of area in each intensity category based on flame length
    categories = ['Low\n(< 4 ft)', 'Moderate\n(4-8 ft)', 'High\n(8-12 ft)', 'Very High\n(12-20 ft)', 'Extreme\n(> 20 ft)']
    
    # For simplicity, create approximate distributions based on mean and max
    scenario_data = []
    for i, s in enumerate(stats_list):
        mean = s['statistics']['flame_length']['mean']
        # Simplified distribution
        if mean < 4:
            dist = [70, 20, 7, 2, 1]
        elif mean < 8:
            dist = [20, 40, 25, 10, 5]
        elif mean < 12:
            dist = [10, 25, 35, 20, 10]
        elif mean < 20:
            dist = [5, 15, 25, 35, 20]
        else:
            dist = [2, 8, 15, 30, 45]
        scenario_data.append(dist)
    
    # Create stacked bar chart
    scenario_data = np.array(scenario_data).T
    category_colors = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c', '#8b0000']
    
    bottom = np.zeros(len(scenarios))
    for i, (category, color) in enumerate(zip(categories, category_colors)):
        ax4.bar(scenarios, scenario_data[i], bottom=bottom, label=category, 
                color=color, edgecolor='white', linewidth=0.5)
        bottom += scenario_data[i]
    
    ax4.set_xlabel('Scenario', fontweight='bold')
    ax4.set_ylabel('Approximate Area Distribution (%)', fontweight='bold')
    ax4.set_title('Fire Intensity Distribution (Estimated)')
    ax4.legend(title='Flame Length', loc='upper left', fontsize=8)
    ax4.set_xticklabels(scenarios, rotation=15, ha='right')
    
    plt.tight_layout()
    
    # Save figure
    output_path = Path("outputs/healdsburg_predictions_comparison.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Comparison charts saved to: {output_path}")
    
    # Also display summary
    print("\n" + "=" * 70)
    print("FIRE PREDICTION SUMMARY")
    print("=" * 70)
    
    for i, s in enumerate(stats_list):
        print(f"\n{i+1}. {s['scenario']}")
        print(f"   Conditions:")
        print(f"     Wind: {s['conditions']['wind_speed']} mph")
        print(f"     Temperature: {s['conditions']['temperature']}°F")
        print(f"     Fuel Moisture: {s['conditions']['fuel_moisture']}%")
        print(f"   Predicted Fire Behavior:")
        print(f"     Mean ROS: {s['statistics']['rate_of_spread']['mean']:.1f} ch/hr")
        print(f"     Max ROS: {s['statistics']['rate_of_spread']['max']:.1f} ch/hr")
        print(f"     Mean Flame Length: {s['statistics']['flame_length']['mean']:.1f} ft")
        print(f"     Max Flame Length: {s['statistics']['flame_length']['max']:.1f} ft")
    
    print("\n" + "=" * 70)
    print(f"Chart saved to: {output_path.absolute()}")
    print("=" * 70 + "\n")
    
    return str(output_path.absolute())


def main():
    """Create comparison charts"""
    create_comparison_charts()


if __name__ == "__main__":
    main()
