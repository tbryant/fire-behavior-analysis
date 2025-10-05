## Geospatial and Wildfire Mitigation Software Ecosystem

This guide outlines the software and data central to wildfire mitigation planning and operations, tailored to a workflow using ESRI ArcGIS and industry-standard models.

### 1. Foundational Data (Input for all Models)

* **Tool:** LANDFIRE (Landscape Fire and Resource Management Planning Tools)
* **Website:** [https://landfire.gov/](https://landfire.gov/)
* **Action:**
    * Use the website's data portal to download key geospatial layers for your Area of Interest (AOI).
    * **Primary Layers for Analysis:** Fuel Buffer Model (FBFM40), Canopy Base Height (CBH), Canopy Bulk Density (CBD).
    * **Coding Task:** Use Python libraries like `gdal` and `rasterio` to automate the downloading, clipping, and re-projecting of LANDFIRE data to match your project's coordinate system. This is a common preparatory step before loading data into ArcGIS or another model.

    ```python
    # Example pseudocode for data prep
    # import gdal
    #
    # aoi_shapefile = 'path/to/my_project_boundary.shp'
    # landfire_fuel_model_tif = 'path/to/downloaded_landfire_fuel.tif'
    # output_clipped_tif = 'path/to/project_fuel_model.tif'
    #
    # # Use gdal.Warp to clip the raster to the shapefile boundary
    # gdal.Warp(output_clipped_tif, landfire_fuel_model_tif, cutlineDSName=aoi_shapefile, cropToCutline=True)
    ```

### 2. Core Analysis and Planning Platforms (Commercial & Governmental)

These systems are typically desktop or enterprise applications and are not installed via `pip` or `git`. The coding tasks involve data preparation *for* them or analysis of their *outputs*.

* **Tool:** ESRI ArcGIS Pro
* **Role:** Central hub for data management, visualization, and custom analysis (e.g., complexity analysis).
* **Action:**
    * **Coding Task:** Automate your "complexity analysis" using `arcpy`, ESRI's Python site-package. A script could take your prepared LANDFIRE layers (fuel, slope, canopy) and access data as inputs, then run a series of geoprocessing tools (e.g., Reclassify, Weighted Overlay) to produce a final complexity map. This standardizes your bidding process.

* **Tool:** U.S. Forest Service FSIM (Large Fire Simulator)
* **Website:** [https://www.firelab.org/project/fire-simulation-fsim-system](https://www.firelab.org/project/fire-simulation-fsim-system)
* **Role:** Strategic, landscape-scale probabilistic risk assessment.
* **Action:**
    * Installation involves downloading the application and a large amount of specific data from the Forest Service.
    * **Coding Task:** FSIM inputs are highly structured text files (`.lcp`, `.fmd`, etc.) and spatial data. A key coding task is writing Python scripts to convert your standard GIS data (like LANDFIRE TIFs) into the specific formats required by FSIM. Use `gdal` and `numpy` for this.

* **Tool:** Technosylva Suite (Wildfire Analyst, FireSim)
* **Website:** [https://www.technosylva.com/](https://www.technosylva.com/)
* **Role:** Commercial, operational fire spread forecasting and risk analysis.
* **Action:**
    * This is licensed enterprise software. You cannot install it from a public repo.
    * **Coding Task:** If Technosylva provides an API, you could write Python scripts to pull simulation results or risk data into your own systems for custom analysis or dashboarding.

### 3. Open Source Simulators (For Research & Customization)

These are tools you can install and run directly. They are best for specific, targeted research questions that fall outside the scope of the major platforms.

* **Project:** ELMFIRE
* **Repository:** `https://github.com/elmfire/elmfire`
* **Primary Language:** C++
* **Installation:** Follow build instructions in the repository. Requires a C++ compilation environment.
    ```bash
    git clone [https://github.com/elmfire/elmfire.git](https://github.com/elmfire/elmfire.git)
    cd elmfire
    # Follow makefile instructions
    ```
* **Use Case:** Test specific fire spread hypotheses or compare a different model's output against your standard tools for a specific area.

* **Project:** ForeFire
* **Repository:** `https://github.com/forefireAPI/forefire`
* **Primary Language:** C++ with Python bindings
* **Installation:** Follow detailed instructions from their documentation at `https://forefire.readthedocs.io/`.
* **Use Case:** Highly scriptable. Excellent for batch processing many fire simulations under slightly different fuel or weather conditions to perform a sensitivity analysis.