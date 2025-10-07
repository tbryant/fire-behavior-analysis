# Examples

Example scripts demonstrating fire analysis workflows.

## Scripts

### `download_healdsburg.py`
Download LANDFIRE data for Healdsburg, CA region.
```bash
python examples/download_healdsburg.py
```

### `download_landfire.py`
General LANDFIRE data downloader example.
```bash
python examples/download_landfire.py
```

### `fire_calc.py`
Interactive CLI calculator for fire behavior calculations.
```bash
python examples/fire_calc.py
```

### `check_status.py`
Check download status and data availability.
```bash
python examples/check_status.py
```

### `healdsburg_fire_predictions.py` ⭐ **NEW**
Generate landscape-scale fire behavior predictions for Healdsburg area under multiple weather scenarios.
```bash
python examples/healdsburg_fire_predictions.py
```

Creates an interactive map with:
- Fire behavior predictions (flame length, rate of spread)
- Multiple weather scenarios (typical, red flag warning, extreme)
- Color-coded overlays showing fire intensity across the landscape
- Layer control to compare different conditions

**Output:**
- `outputs/healdsburg_fire_predictions.html` - Interactive map
- `outputs/healdsburg_fire_predictions_statistics.json` - Detailed statistics

### `compare_predictions.py` ⭐ **NEW**
Create comparison charts from fire prediction results.
```bash
python examples/compare_predictions.py
```

Generates visualizations comparing:
- Mean and maximum fire behavior across scenarios
- Weather conditions
- Fire intensity distributions

**Output:**
- `outputs/healdsburg_predictions_comparison.png` - Comparison charts

## Complete Healdsburg Workflow

Here's the complete workflow for fire prediction analysis:

```bash
# 1. Download LANDFIRE data
python examples/download_healdsburg.py

# 2. Run fire predictions for multiple scenarios
python examples/healdsburg_fire_predictions.py

# 3. Create comparison charts
python examples/compare_predictions.py

# 4. View results
# Open outputs/healdsburg_fire_predictions.html in your browser
# View outputs/healdsburg_predictions_comparison.png
```

## See Also

For production workflows, see the main `scripts/` directory.
