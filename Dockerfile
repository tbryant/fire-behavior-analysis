FROM nstrumenta/developer:3.1.47

# Install GDAL system dependencies required for rasterio
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt
