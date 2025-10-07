#!/usr/bin/env python3
"""
Interactive Fire Spread Simulator
Click anywhere on the map to set an ignition point and see fire spread
"""

import sys
from pathlib import Path
import json

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


def create_clickable_ignition_map(output_file: str = "outputs/fire_spread_interactive.html"):
    """
    Create an interactive map where clicking sets the ignition point
    """
    
    print("\n" + "=" * 70)
    print("INTERACTIVE FIRE SPREAD SIMULATOR")
    print("=" * 70)
    print("\nThis creates an interactive map where you can:")
    print("  1. Click anywhere to set an ignition point")
    print("  2. View fire spread predictions from that point")
    print("  3. See time-to-arrival isochrones (color-coded zones)")
    print("\n" + "=" * 70)
    
    # Initialize simulator
    sim = FireSpreadSimulator()
    sim.load_data()
    
    # Calculate ROS map (default moderate conditions)
    sim.calculate_ros_map(
        wind_speed=15,
        wind_direction=0,
        fuel_moisture=6,
        temperature=85,
        relative_humidity=30
    )
    
    # Create base map centered on Healdsburg
    import folium
    from folium import plugins
    
    m = folium.Map(
        location=[sim.healdsburg_lat, sim.healdsburg_lon],
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
    
    # Add Healdsburg marker
    folium.Marker(
        [sim.healdsburg_lat, sim.healdsburg_lon],
        popup='<b>Healdsburg, CA</b><br>Click anywhere on the map to simulate fire spread',
        tooltip='Healdsburg',
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)
    
    # Add instructions panel
    instructions_html = '''
    <div style="position: fixed; 
                top: 10px; left: 60px; width: 350px; 
                background-color: rgba(255, 255, 255, 0.95); z-index:9999; font-size:13px;
                border:3px solid #e74c3c; border-radius: 8px; padding: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
    <h3 style="margin-top:0; color:#e74c3c;">🔥 Interactive Fire Spread Simulator</h3>
    <p style="margin: 8px 0;"><b>How to use:</b></p>
    <ol style="margin: 5px 0; padding-left: 20px;">
        <li>Click anywhere on the map to set an ignition point</li>
        <li>Your coordinates will be displayed below</li>
        <li>Run the simulation script with those coordinates</li>
    </ol>
    
    <p style="margin: 8px 0; font-size: 12px;"><b>Current Weather Scenario:</b></p>
    <div style="font-size: 11px; margin-left: 10px;">
        • Wind: 15 mph<br>
        • Fuel Moisture: 6%<br>
        • Temperature: 85°F<br>
        • RH: 30%
    </div>
    
    <div id="coordinates" style="margin-top: 10px; padding: 8px; background-color: #f8f9fa; 
                                  border-radius: 4px; display: none;">
        <b>Selected Location:</b><br>
        <span id="coord-text" style="font-family: monospace; font-size: 11px;"></span>
    </div>
    </div>
    
    <script>
    var clickedMarker = null;
    
    // Add click handler to map
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            var maps = document.querySelectorAll('.folium-map');
            if (maps.length > 0) {
                var mapElement = maps[0];
                var leafletMap = mapElement._leaflet_map;
                
                if (leafletMap) {
                    leafletMap.on('click', function(e) {
                        var lat = e.latlng.lat.toFixed(6);
                        var lon = e.latlng.lng.toFixed(6);
                        
                        // Remove previous marker if exists
                        if (clickedMarker) {
                            leafletMap.removeLayer(clickedMarker);
                        }
                        
                        // Add new marker
                        clickedMarker = L.marker([lat, lon], {
                            icon: L.icon({
                                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                iconSize: [25, 41],
                                iconAnchor: [12, 41],
                                popupAnchor: [1, -34],
                                shadowSize: [41, 41]
                            })
                        }).addTo(leafletMap);
                        
                        clickedMarker.bindPopup('<b>Ignition Point</b><br>Lat: ' + lat + '<br>Lon: ' + lon).openPopup();
                        
                        // Update coordinates display
                        var coordDiv = document.getElementById('coordinates');
                        var coordText = document.getElementById('coord-text');
                        coordDiv.style.display = 'block';
                        coordText.innerHTML = 'Lat: ' + lat + ', Lon: ' + lon + 
                                             '<br><br>Run simulation:<br>' +
                                             '<code style="font-size: 10px;">python examples/run_fire_spread.py ' + 
                                             lat + ' ' + lon + '</code>';
                    });
                }
            }
        }, 1000);
    });
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(instructions_html))
    
    # Add layer control and tools
    folium.LayerControl(position='topright').add_to(m)
    plugins.Fullscreen(position='topleft').add_to(m)
    plugins.MeasureControl(position='topleft').add_to(m)
    plugins.MousePosition().add_to(m)
    
    # Save map
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True)
    m.save(str(output_path))
    
    print(f"\n✓ Interactive map created: {output_path.absolute()}")
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print(f"1. Open the map in your browser:")
    print(f"   {output_path.absolute()}")
    print(f"\n2. Click anywhere on the map to select an ignition point")
    print(f"\n3. Run the simulation with your selected coordinates:")
    print(f"   python examples/run_fire_spread.py <lat> <lon>")
    print("\n" + "=" * 70 + "\n")
    
    return str(output_path.absolute())


def main():
    """Create interactive ignition selector map"""
    create_clickable_ignition_map()


if __name__ == "__main__":
    main()
