# Climate Conflict Early Warning System - Usage Guide

## Overview

This system implements a multi-agent web scraping pipeline for collecting climate and conflict-related data from four key sources:

- **NASA Earth Observatory** - Environmental data and satellite imagery
- **UN Press & Meetings** - Political and security responses
- **World Food Programme (WFP)** - Humanitarian impacts
- **World Bank News** - Economic vulnerability data

## Architecture

The system uses a multi-agent architecture with the following components:

### 1. Compliance Agent (`compliance.py`)
- **Robots.txt checking** with caching and refresh logic
- **Rate limiting** with per-domain throttling
- **Domain whitelisting** for security
- **Retry logic** with exponential backoff

### 2. Multi-Agent Fetcher (`fetchers.py`)
- **Primary HTTP fetcher** using httpx (Axios-like)
- **Playwright fallback** for dynamic content
- **Concurrent processing** with throttling
- **Error handling** and retry mechanisms

### 3. Specialized Extractors (`extractors.py`)
- **NASA Extractor** - Environmental indicators, satellite data
- **UN Press Extractor** - Meeting coverage, security council
- **WFP Extractor** - Crisis types, affected populations
- **World Bank Extractor** - Countries, sectors, project IDs

### 4. Validation Agent (`validators.py`)
- **Schema validation** using Pydantic
- **Duplicate detection** with Redis/memory caching
- **Content quality checking** with scoring
- **Business rule validation**

### 5. Storage Agent (`storage.py`)
- **Multiple formats**: JSON, CSV, NDJSON, Parquet
- **Compression** and optimization
- **Analytics datasets** for ML/BI
- **Consolidated datasets** across sources

### 6. Orchestrator (`orchestrator.py`)
- **Coordinates all agents**
- **Progress tracking** with Rich UI
- **Statistics and monitoring**
- **Error handling and recovery**

## Installation

### Prerequisites
- Python 3.8+
- Docker (optional)
- Redis (optional, for duplicate detection)

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install Playwright browsers**:
```bash
playwright install chromium
```

3. **Set up environment variables** (optional):
```bash
# Create .env file
RATE_LIMIT=1.0
MAX_CONCURRENT=3
STORAGE_DIR=./data
LOG_LEVEL=INFO
```

4. **Start Redis** (optional, for duplicate detection):
```bash
docker run -d -p 6379:6379 redis:alpine
```

## Usage

### Command Line Interface

```bash
# Scrape all sources
python cli.py

# Scrape specific source
python cli.py -s nasa

# Verbose output
python cli.py -v

# Dry run (show what would be scraped)
python cli.py --dry-run

# Show help
python cli.py --help
```

### Programmatic Usage

```python
import asyncio
from config import Config
from orchestrator import ScrapingOrchestrator

async def main():
    config = Config()
    async with ScrapingOrchestrator(config) as orchestrator:
        stats = await orchestrator.run_scraping_session()
        print(f"Scraped {stats['records_stored']} records")

asyncio.run(main())
```

### Docker Usage

```bash
# Build and run
docker-compose up scraper

# Run specific source
docker-compose run scraper python cli.py -s nasa
```

## Configuration

### Rate Limiting
- **Default**: 1 request/second per domain
- **Configurable**: Set `RATE_LIMIT` environment variable
- **Per-domain**: Different limits for different sources

### Storage
- **JSON**: Human-readable format
- **CSV**: Spreadsheet compatibility
- **NDJSON**: Streaming format
- **Parquet**: Optimized for analytics

### Compliance
- **Robots.txt**: Automatically checked and cached
- **Rate limiting**: Prevents overloading servers
- **User agent**: Identifies as research bot
- **Domain whitelist**: Only approved sources

## Data Output

### Record Structure
Each scraped record contains:
- **Basic info**: URL, title, summary, date
- **Geographic**: Region, country
- **Topics**: Tags and categories
- **Source-specific**: Environmental indicators, crisis types, etc.
- **Metadata**: Fetch time, links, images

### File Organization
```
data/
├── json/           # JSON files by source
├── csv/            # CSV files by source
├── parquet/        # Parquet files by source
└── analytics/      # Consolidated datasets
```

## Monitoring and Statistics

### Real-time Progress
- **Rich UI** with progress bars
- **Source-specific** statistics
- **Performance metrics**
- **Error tracking**

### Statistics Available
- **Fetch success rate**
- **Extraction success rate**
- **Validation success rate**
- **Duplicate detection rate**
- **Storage statistics**

## Error Handling

### Retry Logic
- **HTTP errors**: Exponential backoff
- **Network timeouts**: Configurable timeouts
- **Rate limiting**: Automatic throttling
- **Validation errors**: Detailed error messages

### Fallback Strategies
- **HTTP → Playwright**: For dynamic content
- **Memory → Redis**: For duplicate detection
- **Single → Batch**: For failed individual requests

## Best Practices

### 1. Respectful Scraping
- **Rate limiting**: Never exceed 1 req/s per domain
- **Robots.txt**: Always check and respect
- **User agent**: Identify as research bot
- **Error handling**: Graceful degradation

### 2. Data Quality
- **Validation**: Schema and business rules
- **Deduplication**: Content and URL-based
- **Quality scoring**: Content completeness
- **Regular updates**: Fresh data collection

### 3. Performance
- **Concurrent processing**: Multiple sources
- **Caching**: Robots.txt and duplicates
- **Compression**: Parquet for storage
- **Monitoring**: Real-time statistics

## Troubleshooting

### Common Issues

1. **Playwright not found**:
   ```bash
   playwright install chromium
   ```

2. **Redis connection failed**:
   - System falls back to memory cache
   - No impact on functionality

3. **Rate limiting errors**:
   - Reduce `RATE_LIMIT` in config
   - Check network connectivity

4. **Validation errors**:
   - Check source website changes
   - Update extractors if needed

### Debug Mode
```bash
python cli.py -v --dry-run
```

## Contributing

### Adding New Sources
1. **Update schemas.py** with new record type
2. **Create extractor** in extractors.py
3. **Add URLs** to url_lists.py
4. **Update compliance** for new domain

### Extending Extractors
1. **Inherit from BaseExtractor**
2. **Override extract() method**
3. **Add source-specific fields**
4. **Test with sample URLs**

## License

This project is for research purposes. Please respect the terms of service of the websites being scraped and use the data responsibly.

## Support

For issues or questions:
1. Check the logs for error messages
2. Run with `-v` flag for verbose output
3. Use `--dry-run` to test configuration
4. Check the statistics for performance insights