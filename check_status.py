#!/usr/bin/env python3
"""
Fire Analysis Project Status Checker
Verifies installation and provides project overview
"""

import sys
import subprocess
from pathlib import Path


def check_package(package_name: str) -> tuple[bool, str]:
    """Check if a package is installed and get version"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return True, line.split(':')[1].strip()
        return False, "Not installed"
    except Exception:
        return False, "Error checking"


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def main():
    """Check project status"""
    print("\n" + "=" * 70)
    print("FIRE ANALYSIS PROJECT - STATUS CHECK")
    print("=" * 70)
    
    # Check Python version
    print_header("PYTHON ENVIRONMENT")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Python Path: {sys.executable}")
    
    # Check packages
    print_header("REQUIRED PACKAGES")
    required_packages = [
        ('requests', True),
        ('numpy', True),
        ('pandas', True),
        ('matplotlib', True),
        ('arcgis', True),
        ('geopandas', True),
        ('shapely', True),
        ('folium', True),
        ('python-dotenv', True),
    ]
    
    optional_packages = [
        ('rasterio', False),  # Requires GDAL system libraries
    ]
    
    all_installed = True
    for package, required in required_packages:
        installed, version = check_package(package)
        status = "✅" if installed else "❌"
        print(f"  {status} {package:20} {version}")
        if not installed and required:
            all_installed = False
    
    print("\n  Optional Packages:")
    for package, _ in optional_packages:
        installed, version = check_package(package)
        status = "✅" if installed else "⚪"
        note = "" if installed else "(requires GDAL system libraries)"
        print(f"  {status} {package:20} {version} {note}")
    
    # Check project structure
    print_header("PROJECT STRUCTURE")
    project_root = Path(__file__).parent
    
    important_files = [
        'GETTING_STARTED.md',
        'FUEL_MODELS_GUIDE.md',
        'PROJECT_PLAN.md',
        'SETUP_COMPLETE.md',
        'requirements.txt',
        'fire_calc.py',
        'scripts/01_landfire_downloader.py',
        'scripts/02_fire_behavior_calc.py',
        'scripts/03_arcgis_integration.py',
        'scripts/04_demo_analysis.py',
    ]
    
    for file_path in important_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path}")
    
    # Check directories
    print_header("DATA DIRECTORIES")
    directories = {
        'data/landfire': 'LANDFIRE datasets',
        'outputs': 'Analysis outputs',
        'scripts': 'Python scripts'
    }
    
    for dir_path, description in directories.items():
        full_path = project_root / dir_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        
        if exists and full_path.is_dir():
            file_count = len(list(full_path.glob('*')))
            print(f"  {status} {dir_path:20} ({file_count} items) - {description}")
        else:
            print(f"  {status} {dir_path:20} (missing) - {description}")
    
    # Run quick script test
    print_header("FUNCTIONALITY TEST")
    print("Testing fire behavior calculator import...")
    
    try:
        scripts_path = str(project_root / 'scripts')
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)
        
        # Import with explicit path handling
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "fire_behavior_calc",
            project_root / 'scripts' / '02_fire_behavior_calc.py'
        )
        fire_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fire_module)
        
        FireBehaviorCalculator = fire_module.FireBehaviorCalculator
        calc = FireBehaviorCalculator()
        print(f"  ✅ FireBehaviorCalculator loaded successfully")
        print(f"  ✅ {len(calc.FUEL_MODELS)} fuel models available: {', '.join(calc.FUEL_MODELS.keys())}")
        
        # Quick calculation test
        result = calc.calculate_rate_of_spread(
            fuel_model='GR2',
            wind_speed=10,
            slope=15,
            fuel_moisture=8
        )
        print(f"  ✅ Test calculation successful")
        print(f"     Rate of spread: {result['rate_of_spread_ch_hr']} chains/hr")
        print(f"     Flame length: {result['flame_length_ft']} feet")
    except Exception as e:
        print(f"  ❌ Error testing calculator: {str(e)}")
    
    # Summary
    print_header("SUMMARY")
    
    if all_installed:
        print("  ✅ All required packages are installed")
    else:
        print("  ❌ Some packages are missing")
        print("     Run: pip install -r requirements.txt")
    
    print("\n  📚 Documentation:")
    print("     • GETTING_STARTED.md - Quick start guide")
    print("     • FUEL_MODELS_GUIDE.md - Fuel model reference")
    print("     • SETUP_COMPLETE.md - Installation verification")
    
    print("\n  ** Quick Commands:")
    print("     • python scripts/04_demo_analysis.py  # Run demo")
    print("     • python fire_calc.py                  # Interactive mode")
    print("     • python scripts/02_fire_behavior_calc.py  # Scenarios")
    
    print("\n  ** Next Steps:")
    print("     1. Read GETTING_STARTED.md")
    print("     2. Run the demo: python scripts/04_demo_analysis.py")
    print("     3. Try interactive mode: python fire_calc.py")
    print("     4. Download LANDFIRE data for your region")
    
    print("\n" + "=" * 70)
    
    if all_installed:
        print("\n✨ Project is ready to use! ✨\n")
        return 0
    else:
        print("\n⚠️  Please install missing packages first.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
