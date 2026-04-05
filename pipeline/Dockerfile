FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for GDAL, rasterio, and building native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables often needed for compilation/runtime
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root --without dev

COPY pipeline/ ./pipeline/
COPY regions/ ./regions/

RUN pip install --no-cache-dir --no-deps .
