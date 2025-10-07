#!/usr/bin/env python3
"""
Healdsburg Fire Analysis Visualization
Creates interactive maps and visualizations of LANDFIRE data for Healdsburg, CA
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


class HealdsburgFireVisualizer:
    """
    Visualize LANDFIRE data for Healdsburg area with interactive maps
    """
    
    def __init__(self, data_dir: str = "data/landfire"):
        self.data_dir = Path(data_dir)
        self.data = {}
        self.bounds = None
        self.center = None
        
        # Healdsburg center coordinates
        self.healdsburg_lat = 38.6102
        self.healdsburg_lon = -122.8694
        
    def load_data(self) -> Dict:
        """Load all LANDFIRE GeoTIFF files"""
        print("Loading LANDFIRE data...")
        
        products = ['FBFM40', 'CBH', 'CBD', 'CC', 'SLPD', 'ASPD']
        
        for product in products:
            # Find the file (may have timestamp)
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
                        'nodata': src.nodata
                    }
                    
                    # Set overall bounds from first file
                    if self.bounds is None:
                        self.bounds = src.bounds
                        # Calculate center
                        self.center = [
                            (src.bounds.bottom + src.bounds.top) / 2,
                            (src.bounds.left + src.bounds.right) / 2
                        ]
        
        print(f"\nLoaded {len(self.data)} products")
        print(f"Bounds: {self.bounds}")
        print(f"Center: {self.center}")
        
        return self.data
    
    def create_fuel_model_colormap(self) -> Tuple[dict, list]:
        """Create colormap for FBFM40 fuel models"""
        # Scott and Burgan 40 fuel models with approximate colors
        fuel_colors = {
            0: '#FFFFFF',    # No data/Non-burnable
            91: '#F5DEB3',   # NB1 - Urban
            92: '#D3D3D3',   # NB2 - Snow/Ice
            93: '#A9A9A9',   # NB3 - Agriculture
            98: '#87CEEB',   # NB8 - Water
            99: '#4682B4',   # NB9 - Barren
            
            101: '#FFFF99',  # GR1 - Short sparse grass
            102: '#FFFF66',  # GR2 - Low load grass
            103: '#FFFF33',  # GR3 - Moderate load grass
            104: '#FFD700',  # GR4 - High load grass
            105: '#FFA500',  # GR5 - Dense grass
            106: '#FF8C00',  # GR6 - Moderate moisture grass
            107: '#FF6347',  # GR7 - High load, moist grass
            108: '#FF4500',  # GR8 - High load, very coarse grass
            109: '#DC143C',  # GR9 - Dense, tall grass
            
            121: '#FFE4B5',  # GS1 - Low load shrub/grass
            122: '#FFDAB9',  # GS2 - Moderate load shrub/grass
            123: '#FFB366',  # GS3 - Moderate shrub/grass
            124: '#FF9933',  # GS4 - High load shrub/grass
            
            141: '#ADFF2F',  # SH1 - Low load dry shrub
            142: '#9ACD32',  # SH2 - Moderate load dry shrub
            143: '#7CFC00',  # SH3 - High load dry shrub
            144: '#32CD32',  # SH4 - Low load humid shrub
            145: '#228B22',  # SH5 - High load humid shrub
            146: '#006400',  # SH6 - Low load humid shrub
            147: '#8B4513',  # SH7 - High load humid shrub
            148: '#A0522D',  # SH8 - High load shrub
            149: '#D2691E',  # SH9 - Dense shrub
            
            161: '#90EE90',  # TU1 - Light load timber-understory
            162: '#66CDAA',  # TU2 - Moderate load timber
            163: '#3CB371',  # TU3 - High load timber
            164: '#2E8B57',  # TU4 - Dwarf conifer
            165: '#006400',  # TU5 - High load conifer
            
            181: '#8FBC8F',  # TL1 - Low load compact conifer
            182: '#556B2F',  # TL2 - Low load broadleaf
            183: '#6B8E23',  # TL3 - Moderate load conifer
            184: '#808000',  # TL4 - Small downed logs
            185: '#556B2F',  # TL5 - High load conifer
            186: '#2F4F2F',  # TL6 - Moderate load broadleaf
            187: '#191970',  # TL7 - Large downed logs
            188: '#000080',  # TL8 - Long needle litter
            189: '#00008B',  # TL9 - Very high load broadleaf
            
            201: '#CD853F',  # SB1 - Low load activity fuel
            202: '#8B4513',  # SB2 - Moderate load activity fuel
            203: '#A0522D',  # SB3 - High load activity fuel
            204: '#D2691E',  # SB4 - Very high load activity fuel
        }
        
        # Create legend items
        legend_items = [
            ('Non-burnable', '#D3D3D3'),
            ('Grass (GR1-9)', '#FFD700'),
            ('Grass-Shrub (GS1-4)', '#FFB366'),
            ('Shrub (SH1-9)', '#32CD32'),
            ('Timber-Understory (TU1-5)', '#3CB371'),
            ('Timber Litter (TL1-9)', '#556B2F'),
            ('Slash-Blowdown (SB1-4)', '#A0522D'),
        ]
        
        return fuel_colors, legend_items
    
    def array_to_png(self, array: np.ndarray, colormap: dict = None, 
                     vmin: float = None, vmax: float = None) -> str:
        """Convert numpy array to PNG base64 string"""
        # Handle nodata
        masked_array = np.ma.masked_equal(array, -9999)
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        if colormap:
            # Discrete colormap for fuel models
            unique_vals = np.unique(masked_array.compressed())
            colors = [colormap.get(val, '#CCCCCC') for val in unique_vals]
            cmap = mcolors.ListedColormap(colors)
            bounds = list(unique_vals) + [unique_vals[-1] + 1]
            norm = mcolors.BoundaryNorm(bounds, cmap.N)
            im = ax.imshow(masked_array, cmap=cmap, norm=norm)
        else:
            # Continuous colormap
            if vmin is None:
                vmin = masked_array.min()
            if vmax is None:
                vmax = masked_array.max()
            im = ax.imshow(masked_array, cmap='viridis', vmin=vmin, vmax=vmax)
            plt.colorbar(im, ax=ax)
        
        ax.axis('off')
        plt.tight_layout(pad=0)
        
        # Convert to PNG
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', 
                   dpi=150, transparent=True)
        plt.close()
        
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def create_interactive_map(self) -> folium.Map:
        """Create interactive Folium map with LANDFIRE data layers"""
        print("\nCreating interactive map...")
        
        # Create base map centered on Healdsburg
        m = folium.Map(
            location=[self.healdsburg_lat, self.healdsburg_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Add additional tile layers
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Topographic',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add Healdsburg marker
        folium.Marker(
            [self.healdsburg_lat, self.healdsburg_lon],
            popup='<b>Healdsburg, CA</b><br>Center of Analysis Area',
            tooltip='Healdsburg',
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Add data bounds rectangle
        if self.bounds:
            bounds_rect = [
                [self.bounds.bottom, self.bounds.left],
                [self.bounds.top, self.bounds.right]
            ]
            folium.Rectangle(
                bounds=bounds_rect,
                color='red',
                fill=False,
                weight=2,
                popup='LANDFIRE Data Coverage Area'
            ).add_to(m)
        
        # Add feature groups for each layer
        fuel_group = folium.FeatureGroup(name='Fuel Models (FBFM40)', show=True)
        canopy_height_group = folium.FeatureGroup(name='Canopy Base Height (CBH)')
        canopy_density_group = folium.FeatureGroup(name='Canopy Bulk Density (CBD)')
        canopy_cover_group = folium.FeatureGroup(name='Canopy Cover (CC)')
        slope_group = folium.FeatureGroup(name='Slope (SLPD)')
        aspect_group = folium.FeatureGroup(name='Aspect (ASPD)')
        
        # Create fuel model colormap
        fuel_colors, fuel_legend = self.create_fuel_model_colormap()
        
        # Add raster overlays (simplified - showing data extent)
        # For full raster display, we'd need to convert to georeferenced images
        
        # Add legend for fuel models
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 250px; height: auto; 
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px; padding: 10px">
        <h4 style="margin-top:0">FBFM40 Fuel Models</h4>
        '''
        
        for label, color in fuel_legend:
            legend_html += f'''
            <div style="margin-bottom: 5px">
                <span style="background-color:{color}; width:20px; height:20px; 
                      display:inline-block; border:1px solid black;"></span>
                <span style="margin-left:5px">{label}</span>
            </div>
            '''
        
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add fullscreen button
        plugins.Fullscreen().add_to(m)
        
        # Add measure control
        plugins.MeasureControl(position='topleft').add_to(m)
        
        # Add mouse position
        plugins.MousePosition().add_to(m)
        
        return m
    
    def create_statistics_summary(self) -> Dict:
        """Calculate statistics for each LANDFIRE product"""
        print("\nCalculating statistics...")
        
        stats = {}
        
        product_info = {
            'FBFM40': {'name': 'Fuel Models', 'unit': 'model'},
            'CBH': {'name': 'Canopy Base Height', 'unit': 'm', 'scale': 0.1},
            'CBD': {'name': 'Canopy Bulk Density', 'unit': 'kg/m³', 'scale': 0.01},
            'CC': {'name': 'Canopy Cover', 'unit': '%', 'scale': 1},
            'SLPD': {'name': 'Slope', 'unit': 'degrees', 'scale': 1},
            'ASPD': {'name': 'Aspect', 'unit': 'degrees', 'scale': 1},
        }
        
        for product, data in self.data.items():
            array = data['array']
            nodata = data.get('nodata', -9999)
            
            # Mask nodata values
            masked = np.ma.masked_equal(array, nodata)
            
            info = product_info.get(product, {})
            scale = info.get('scale', 1)
            
            # Calculate statistics
            stats[product] = {
                'name': info.get('name', product),
                'unit': info.get('unit', ''),
                'min': float(masked.min() * scale) if masked.count() > 0 else None,
                'max': float(masked.max() * scale) if masked.count() > 0 else None,
                'mean': float(masked.mean() * scale) if masked.count() > 0 else None,
                'std': float(masked.std() * scale) if masked.count() > 0 else None,
                'valid_pixels': int(masked.count()),
                'total_pixels': int(array.size),
                'coverage_pct': float(masked.count() / array.size * 100)
            }
            
            print(f"\n{stats[product]['name']}:")
            print(f"  Range: {stats[product]['min']:.2f} - {stats[product]['max']:.2f} {stats[product]['unit']}")
            print(f"  Mean: {stats[product]['mean']:.2f} {stats[product]['unit']}")
            print(f"  Coverage: {stats[product]['coverage_pct']:.1f}%")
        
        return stats
    
    def create_histogram_plots(self, output_dir: str = "outputs"):
        """Create histogram plots for each variable"""
        print("\nCreating histogram plots...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('LANDFIRE Data Distribution - Healdsburg, CA', fontsize=16)
        
        products = ['FBFM40', 'CBH', 'CBD', 'CC', 'SLPD', 'ASPD']
        titles = [
            'Fuel Models (FBFM40)',
            'Canopy Base Height (m)',
            'Canopy Bulk Density (kg/m³)',
            'Canopy Cover (%)',
            'Slope (degrees)',
            'Aspect (degrees)'
        ]
        scales = [1, 0.1, 0.01, 1, 1, 1]
        
        for idx, (product, title, scale) in enumerate(zip(products, titles, scales)):
            ax = axes[idx // 3, idx % 3]
            
            if product in self.data:
                array = self.data[product]['array']
                nodata = self.data[product].get('nodata', -9999)
                masked = np.ma.masked_equal(array, nodata)
                
                if masked.count() > 0:
                    values = masked.compressed() * scale
                    ax.hist(values, bins=50, edgecolor='black', alpha=0.7)
                    ax.set_title(title)
                    ax.set_xlabel('Value')
                    ax.set_ylabel('Frequency')
                    ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', 
                       transform=ax.transAxes)
                ax.set_title(title)
        
        plt.tight_layout()
        
        output_file = output_path / 'healdsburg_data_histograms.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  Saved: {output_file}")
        plt.close()
        
        return output_file
    
    def create_fire_risk_analysis(self) -> Dict:
        """Analyze fire risk based on fuel models and topography"""
        print("\nAnalyzing fire risk...")
        
        if 'FBFM40' not in self.data or 'SLPD' not in self.data:
            print("  Missing required data for fire risk analysis")
            return {}
        
        fbfm = self.data['FBFM40']['array']
        slope = self.data['SLPD']['array']
        
        # Define high-risk fuel models
        high_risk_fuels = [
            105, 106, 107, 108, 109,  # High load grasses (GR5-9)
            123, 124,                  # High load grass-shrub (GS3-4)
            143, 145, 147, 148, 149,  # High load shrubs (SH3,5,7,8,9)
            163, 165,                  # High load timber (TU3,5)
        ]
        
        moderate_risk_fuels = [
            102, 103, 104,             # Moderate grass (GR2-4)
            122,                       # Moderate grass-shrub (GS2)
            142, 144, 146,            # Moderate shrubs (SH2,4,6)
            162, 164,                 # Moderate timber (TU2,4)
            183, 186, 189,            # Moderate timber litter (TL3,6,9)
        ]
        
        # Calculate risk zones
        high_risk_mask = np.isin(fbfm, high_risk_fuels)
        moderate_risk_mask = np.isin(fbfm, moderate_risk_fuels)
        steep_slope_mask = slope > 30  # Steep slopes
        
        # Combine factors
        extreme_risk = high_risk_mask & steep_slope_mask
        high_risk = high_risk_mask | (moderate_risk_mask & steep_slope_mask)
        
        total_pixels = fbfm.size
        valid_pixels = np.sum(fbfm != -9999)
        
        risk_summary = {
            'extreme_risk_pixels': int(np.sum(extreme_risk)),
            'high_risk_pixels': int(np.sum(high_risk)),
            'moderate_risk_pixels': int(np.sum(moderate_risk_mask)),
            'total_pixels': total_pixels,
            'valid_pixels': valid_pixels,
            'extreme_risk_pct': float(np.sum(extreme_risk) / valid_pixels * 100),
            'high_risk_pct': float(np.sum(high_risk) / valid_pixels * 100),
            'moderate_risk_pct': float(np.sum(moderate_risk_mask) / valid_pixels * 100),
        }
        
        print(f"  Extreme Risk: {risk_summary['extreme_risk_pct']:.2f}% of area")
        print(f"  High Risk: {risk_summary['high_risk_pct']:.2f}% of area")
        print(f"  Moderate Risk: {risk_summary['moderate_risk_pct']:.2f}% of area")
        
        return risk_summary
    
    def generate_full_report(self, output_dir: str = "outputs"):
        """Generate complete visualization report"""
        print("\n" + "=" * 70)
        print("HEALDSBURG FIRE ANALYSIS VISUALIZATION")
        print("=" * 70)
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Load data
        self.load_data()
        
        # Create interactive map
        map_obj = self.create_interactive_map()
        map_file = output_path / 'healdsburg_fire_map.html'
        map_obj.save(str(map_file))
        print(f"\n✓ Interactive map saved: {map_file}")
        
        # Create statistics
        stats = self.create_statistics_summary()
        
        # Create histograms
        hist_file = self.create_histogram_plots(output_dir)
        
        # Fire risk analysis
        risk_analysis = self.create_fire_risk_analysis()
        
        # Save summary report
        report = {
            'location': 'Healdsburg, CA',
            'center': {'lat': self.healdsburg_lat, 'lon': self.healdsburg_lon},
            'bounds': {
                'north': self.bounds.top,
                'south': self.bounds.bottom,
                'east': self.bounds.right,
                'west': self.bounds.left
            } if self.bounds else None,
            'statistics': stats,
            'fire_risk_analysis': risk_analysis,
            'files': {
                'map': str(map_file),
                'histograms': str(hist_file)
            }
        }
        
        report_file = output_path / 'healdsburg_analysis_report.json'
        with open(report_file, 'w') as f:
            # Convert numpy types to native Python types for JSON serialization
            def convert_types(obj):
                if isinstance(obj, dict):
                    return {k: convert_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_types(v) for v in obj]
                elif hasattr(obj, 'item'):  # numpy types
                    return obj.item()
                elif hasattr(obj, '__float__'):
                    return float(obj)
                elif hasattr(obj, '__int__'):
                    return int(obj)
                else:
                    return obj
            
            json.dump(convert_types(report), f, indent=2)
        
        print(f"\n✓ Analysis report saved: {report_file}")
        
        print("\n" + "=" * 70)
        print("VISUALIZATION COMPLETE!")
        print("=" * 70)
        print(f"\nOpen the map in your browser:")
        print(f"  {map_file.absolute()}")
        print(f"\nView histograms:")
        print(f"  {hist_file.absolute()}")
        print("=" * 70 + "\n")
        
        return report


def main():
    """Run Healdsburg visualization"""
    visualizer = HealdsburgFireVisualizer()
    report = visualizer.generate_full_report()
    
    # Open the map in browser
    map_file = Path(report['files']['map'])
    if map_file.exists():
        import webbrowser
        print(f"Opening map in browser...")
        webbrowser.open(f'file://{map_file.absolute()}')


if __name__ == "__main__":
    main()
