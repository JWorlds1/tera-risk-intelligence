# TERA Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies for GeoPandas/PostGIS
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Expose port
EXPOSE 8080

# Run
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

