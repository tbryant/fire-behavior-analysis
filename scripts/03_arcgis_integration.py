#!/usr/bin/env python3
"""
ArcGIS Integration Examples
Demonstrates arcpy usage for complexity analysis and fire modeling workflows

Note: Requires ArcGIS Pro and arcpy (included with ArcGIS Pro)
"""

import sys
from pathlib import Path

# Check if arcpy is available
try:
    import arcpy
    ARCPY_AVAILABLE = True
except ImportError:
    ARCPY_AVAILABLE = False
    print("⚠️  arcpy not available. This script requires ArcGIS Pro.")
    print("   The examples below show what you would do with arcpy.")


class FireComplexityAnalyzer:
    """
    Perform complexity analysis for fire management projects
    Used for sales bids and operational planning
    """
    
    def __init__(self, workspace: str):
        if ARCPY_AVAILABLE:
            self.workspace = workspace
            arcpy.env.workspace = workspace
            arcpy.env.overwriteOutput = True
        
    def calculate_terrain_complexity(
        self,
        dem_raster: str,
        output_complexity: str
    ) -> str:
        """
        Calculate terrain complexity from DEM
        
        Factors:
        - Slope steepness
        - Terrain ruggedness (TRI)
        - Aspect variability
        """
        if not ARCPY_AVAILABLE:
            print(f"Would calculate terrain complexity from {dem_raster}")
            return output_complexity
        
        print("Calculating terrain complexity...")
        
        # Calculate slope
        slope = arcpy.sa.Slope(dem_raster, "DEGREE")
        
        # Calculate aspect
        aspect = arcpy.sa.Aspect(dem_raster)
        
        # Terrain Ruggedness Index (simplified)
        # Focal statistics to measure elevation variability
        tri = arcpy.sa.FocalStatistics(
            dem_raster,
            arcpy.sa.NbrRectangle(3, 3, "CELL"),
            "STD"
        )
        
        # Reclassify slope to complexity classes
        slope_reclass = arcpy.sa.Reclassify(
            slope,
            "VALUE",
            arcpy.sa.RemapRange([
                [0, 10, 1],    # Low complexity
                [10, 25, 2],   # Moderate
                [25, 40, 3],   # High
                [40, 90, 4]    # Extreme
            ])
        )
        
        # Combine factors (weighted)
        complexity = (slope_reclass * 0.6) + (tri * 0.4)
        
        complexity.save(output_complexity)
        print(f"✓ Terrain complexity saved to {output_complexity}")
        
        return output_complexity
    
    def calculate_fuel_complexity(
        self,
        fuel_model_raster: str,
        canopy_cover: str,
        canopy_height: str,
        output_complexity: str
    ) -> str:
        """
        Calculate fuel complexity for fire behavior prediction
        
        Factors:
        - Fuel model diversity
        - Canopy structure complexity
        - Fuel continuity
        """
        if not ARCPY_AVAILABLE:
            print(f"Would calculate fuel complexity from fuel data")
            return output_complexity
        
        print("Calculating fuel complexity...")
        
        # Analyze fuel diversity in neighborhood
        fuel_diversity = arcpy.sa.FocalStatistics(
            fuel_model_raster,
            arcpy.sa.NbrRectangle(5, 5, "CELL"),
            "VARIETY"
        )
        
        # Canopy complexity
        cc_raster = arcpy.Raster(canopy_cover)
        ch_raster = arcpy.Raster(canopy_height)
        
        # Combined complexity metric
        complexity = (
            (fuel_diversity / 10) * 0.4 +
            (cc_raster / 100) * 0.3 +
            (ch_raster / 30) * 0.3
        )
        
        complexity.save(output_complexity)
        print(f"✓ Fuel complexity saved to {output_complexity}")
        
        return output_complexity
    
    def create_project_complexity_map(
        self,
        terrain_complexity: str,
        fuel_complexity: str,
        access_roads: str,
        output_map: str
    ) -> str:
        """
        Create overall project complexity map for bid analysis
        
        Combines:
        - Terrain complexity
        - Fuel complexity  
        - Access difficulty
        """
        if not ARCPY_AVAILABLE:
            print("Would create combined complexity map for project bidding")
            return output_map
        
        print("Creating project complexity map...")
        
        # Load rasters
        terrain = arcpy.Raster(terrain_complexity)
        fuel = arcpy.Raster(fuel_complexity)
        
        # Calculate distance from roads (access difficulty)
        access_distance = arcpy.sa.EucDistance(access_roads)
        
        # Normalize distance (0-1 scale)
        access_complexity = access_distance / 5280  # miles
        
        # Weighted combination
        # Terrain: 40%, Fuel: 40%, Access: 20%
        final_complexity = (
            terrain * 0.4 +
            fuel * 0.4 +
            access_complexity * 0.2
        )
        
        final_complexity.save(output_map)
        print(f"✓ Project complexity map saved to {output_map}")
        
        return output_map


def example_workflow():
    """
    Example workflow for complexity analysis
    """
    print("\n" + "=" * 70)
    print("ARCGIS FIRE COMPLEXITY ANALYSIS WORKFLOW")
    print("=" * 70)
    print()
    
    if not ARCPY_AVAILABLE:
        print("This is a demonstration of what the workflow would look like.")
        print("To run this for real, you need ArcGIS Pro installed.\n")
    
    # Example paths
    workspace = "C:/FireProjects/MyProject.gdb"
    
    print("Example Workflow Steps:")
    print("-" * 70)
    print("1. Set workspace and load LANDFIRE data")
    print(f"   Workspace: {workspace}")
    print()
    
    print("2. Calculate terrain complexity")
    print("   Input: DEM from LANDFIRE")
    print("   Factors: Slope, aspect, ruggedness")
    print()
    
    print("3. Calculate fuel complexity")
    print("   Inputs: Fuel models, canopy cover, canopy height")
    print("   Factors: Fuel diversity, canopy structure")
    print()
    
    print("4. Calculate access complexity")
    print("   Input: Road network")
    print("   Factor: Distance from roads")
    print()
    
    print("5. Create weighted complexity map")
    print("   Output: Project complexity raster for bid analysis")
    print()
    
    # Demonstrate the code structure
    analyzer = FireComplexityAnalyzer(workspace)
    
    print("Sample Code:")
    print("-" * 70)
    print("""
# Initialize analyzer
analyzer = FireComplexityAnalyzer("C:/FireProjects/MyProject.gdb")

# Calculate terrain complexity
terrain_complex = analyzer.calculate_terrain_complexity(
    dem_raster="LANDFIRE_DEM",
    output_complexity="terrain_complexity"
)

# Calculate fuel complexity  
fuel_complex = analyzer.calculate_fuel_complexity(
    fuel_model_raster="LANDFIRE_FBFM40",
    canopy_cover="LANDFIRE_CC",
    canopy_height="LANDFIRE_CH",
    output_complexity="fuel_complexity"
)

# Create final project complexity map
project_map = analyzer.create_project_complexity_map(
    terrain_complexity=terrain_complex,
    fuel_complexity=fuel_complex,
    access_roads="roads_network",
    output_map="project_complexity_final"
)
    """)
    print("-" * 70)
    print()
    
    print("Integration with Field Maps:")
    print("-" * 70)
    print("• Export complexity maps to ArcGIS Online")
    print("• Share with field crews via ArcGIS Field Maps")
    print("• Collect operational data in the field")
    print("• Sync back to ArcGIS Pro for analysis")
    print()


def main():
    """Main entry point"""
    example_workflow()
    
    print("\nResources:")
    print("-" * 70)
    print("• arcpy documentation: https://pro.arcgis.com/en/pro-app/arcpy/")
    print("• ArcGIS Pro Spatial Analyst: https://pro.arcgis.com/en/pro-app/tool-reference/spatial-analyst/")
    print("• Field Maps: https://www.esri.com/en-us/arcgis/products/arcgis-field-maps")
    print()


if __name__ == "__main__":
    main()
