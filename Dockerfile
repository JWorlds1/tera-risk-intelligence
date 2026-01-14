# Dockerfile für Climate Conflict Pipeline
FROM python:3.11-slim

# Metadaten
LABEL maintainer="Climate Conflict Early Warning System"
LABEL description="Automated web scraping pipeline for climate conflict data"

# Arbeitsverzeichnis
WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies kopieren und installieren
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Backend-Code kopieren
COPY backend/ /app/

# Data-Verzeichnis erstellen
RUN mkdir -p /app/data/json /app/data/csv /app/data/parquet /app/data/analytics

# Exponiere Ports
EXPOSE 8000 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Standard-Command (kann überschrieben werden)
CMD ["python", "run_pipeline.py"]

