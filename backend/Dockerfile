# Dockerfile für Agenten-Scraper
FROM python:3.11-slim

# Arbeitsverzeichnis
WORKDIR /app

# System-Dependencies für Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Browser installieren
RUN playwright install chromium
RUN playwright install-deps chromium

# Code kopieren
COPY . .

# Data-Verzeichnis erstellen
RUN mkdir -p /app/data/parquet /app/data/ndjson /app/data/csv

# Exponiere Port (falls später Web-UI gewünscht)
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Startbefehl
CMD ["python", "orchestrator.py"]
