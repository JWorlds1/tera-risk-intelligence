# storage.py - Storage Agent with multiple output formats (JSON, CSV, Parquet)
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from dataclasses import asdict
import structlog
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiofiles

from schemas import PageRecord
from config import Config

logger = structlog.get_logger(__name__)


class StorageAgent:
    """Storage agent for multiple output formats with compression and optimization"""
    
    def __init__(self, config: Config):
        self.config = config
        self.storage_dir = Path(config.STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different formats
        self.json_dir = self.storage_dir / "json"
        self.csv_dir = self.storage_dir / "csv"
        self.parquet_dir = self.storage_dir / "parquet"
        self.analytics_dir = self.storage_dir / "analytics"
        
        for dir_path in [self.json_dir, self.csv_dir, self.parquet_dir, self.analytics_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'records_stored': 0,
            'json_files_created': 0,
            'csv_files_created': 0,
            'parquet_files_created': 0,
            'total_size_bytes': 0
        }
    
    def _get_timestamp_prefix(self) -> str:
        """Get timestamp prefix for files"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _get_source_prefix(self, source_name: str) -> str:
        """Get source prefix for files"""
        return source_name.lower().replace(' ', '_')
    
    def _record_to_dict(self, record: PageRecord) -> Dict[str, Any]:
        """Convert record to dictionary for storage"""
        data = asdict(record)
        
        # Convert datetime objects to ISO strings
        if data.get('fetched_at'):
            data['fetched_at'] = data['fetched_at'].isoformat()
        
        return data
    
    async def store_json(self, records: List[PageRecord], source_name: str, batch_id: str = None) -> str:
        """Store records in JSON format"""
        if not records:
            return None
        
        timestamp = self._get_timestamp_prefix()
        source_prefix = self._get_source_prefix(source_name)
        batch_suffix = f"_{batch_id}" if batch_id else ""
        filename = f"{source_prefix}_{timestamp}{batch_suffix}.json"
        filepath = self.json_dir / filename
        
        # Convert records to dictionaries
        data = [self._record_to_dict(record) for record in records]
        
        # Write JSON file
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        
        file_size = filepath.stat().st_size
        self.stats['records_stored'] += len(records)
        self.stats['json_files_created'] += 1
        self.stats['total_size_bytes'] += file_size
        
        logger.info(f"Stored {len(records)} records in JSON: {filepath}")
        return str(filepath)
    
    async def store_csv(self, records: List[PageRecord], source_name: str, batch_id: str = None) -> str:
        """Store records in CSV format"""
        if not records:
            return None
        
        timestamp = self._get_timestamp_prefix()
        source_prefix = self._get_source_prefix(source_name)
        batch_suffix = f"_{batch_id}" if batch_id else ""
        filename = f"{source_prefix}_{timestamp}{batch_suffix}.csv"
        filepath = self.csv_dir / filename
        
        # Convert records to dictionaries
        data = [self._record_to_dict(record) for record in records]
        
        # Write CSV file
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8')
        
        file_size = filepath.stat().st_size
        self.stats['records_stored'] += len(records)
        self.stats['csv_files_created'] += 1
        self.stats['total_size_bytes'] += file_size
        
        logger.info(f"Stored {len(records)} records in CSV: {filepath}")
        return str(filepath)
    
    async def store_parquet(self, records: List[PageRecord], source_name: str, batch_id: str = None) -> str:
        """Store records in Parquet format for analytics"""
        if not records:
            return None
        
        timestamp = self._get_timestamp_prefix()
        source_prefix = self._get_source_prefix(source_name)
        batch_suffix = f"_{batch_id}" if batch_id else ""
        filename = f"{source_prefix}_{timestamp}{batch_suffix}.parquet"
        filepath = self.parquet_dir / filename
        
        # Convert records to dictionaries
        data = [self._record_to_dict(record) for record in records]
        
        # Write Parquet file
        if data:
            df = pd.DataFrame(data)
            df.to_parquet(filepath, compression='snappy', index=False)
        
        file_size = filepath.stat().st_size
        self.stats['records_stored'] += len(records)
        self.stats['parquet_files_created'] += 1
        self.stats['total_size_bytes'] += file_size
        
        logger.info(f"Stored {len(records)} records in Parquet: {filepath}")
        return str(filepath)
    
    async def store_ndjson(self, records: List[PageRecord], source_name: str, batch_id: str = None) -> str:
        """Store records in NDJSON (Newline Delimited JSON) format"""
        if not records:
            return None
        
        timestamp = self._get_timestamp_prefix()
        source_prefix = self._get_source_prefix(source_name)
        batch_suffix = f"_{batch_id}" if batch_id else ""
        filename = f"{source_prefix}_{timestamp}{batch_suffix}.ndjson"
        filepath = self.json_dir / filename
        
        # Write NDJSON file
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            for record in records:
                data = self._record_to_dict(record)
                await f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        file_size = filepath.stat().st_size
        self.stats['records_stored'] += len(records)
        self.stats['json_files_created'] += 1
        self.stats['total_size_bytes'] += file_size
        
        logger.info(f"Stored {len(records)} records in NDJSON: {filepath}")
        return str(filepath)
    
    async def store_all_formats(self, records: List[PageRecord], source_name: str, batch_id: str = None) -> Dict[str, str]:
        """Store records in all formats"""
        if not records:
            return {}
        
        # Store in all formats concurrently
        tasks = [
            self.store_json(records, source_name, batch_id),
            self.store_csv(records, source_name, batch_id),
            self.store_parquet(records, source_name, batch_id),
            self.store_ndjson(records, source_name, batch_id)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            'json': results[0],
            'csv': results[1],
            'parquet': results[2],
            'ndjson': results[3]
        }
    
    def create_analytics_dataset(self, records: List[PageRecord], source_name: str) -> str:
        """Create optimized analytics dataset"""
        if not records:
            return None
        
        timestamp = self._get_timestamp_prefix()
        source_prefix = self._get_source_prefix(source_name)
        filename = f"{source_prefix}_analytics_{timestamp}.parquet"
        filepath = self.analytics_dir / filename
        
        # Convert to DataFrame
        data = [self._record_to_dict(record) for record in records]
        df = pd.DataFrame(data)
        
        # Optimize for analytics
        df['fetched_at'] = pd.to_datetime(df['fetched_at'])
        if 'publish_date' in df.columns:
            df['publish_date'] = pd.to_datetime(df['publish_date'], errors='coerce')
        
        # Create additional analytics columns
        df['content_length'] = df['summary'].str.len().fillna(0)
        df['topic_count'] = df['topics'].str.len().fillna(0)
        df['has_region'] = df['region'].notna()
        df['has_date'] = df['publish_date'].notna()
        
        # Store optimized dataset
        df.to_parquet(filepath, compression='snappy', index=False)
        
        logger.info(f"Created analytics dataset: {filepath}")
        return str(filepath)
    
    def create_consolidated_dataset(self, all_records: Dict[str, List[PageRecord]]) -> str:
        """Create consolidated dataset from all sources"""
        timestamp = self._get_timestamp_prefix()
        filename = f"consolidated_dataset_{timestamp}.parquet"
        filepath = self.analytics_dir / filename
        
        # Combine all records
        all_data = []
        for source_name, records in all_records.items():
            for record in records:
                data = self._record_to_dict(record)
                data['source_name'] = source_name
                all_data.append(data)
        
        if not all_data:
            return None
        
        # Create consolidated DataFrame
        df = pd.DataFrame(all_data)
        
        # Optimize for analytics
        df['fetched_at'] = pd.to_datetime(df['fetched_at'])
        if 'publish_date' in df.columns:
            df['publish_date'] = pd.to_datetime(df['publish_date'], errors='coerce')
        
        # Create analytics columns
        df['content_length'] = df['summary'].str.len().fillna(0)
        df['topic_count'] = df['topics'].str.len().fillna(0)
        df['has_region'] = df['region'].notna()
        df['has_date'] = df['publish_date'].notna()
        
        # Store consolidated dataset
        df.to_parquet(filepath, compression='snappy', index=False)
        
        logger.info(f"Created consolidated dataset: {filepath}")
        return str(filepath)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_files = (
            len(list(self.json_dir.glob('*.json'))) +
            len(list(self.csv_dir.glob('*.csv'))) +
            len(list(self.parquet_dir.glob('*.parquet')))
        )
        
        return {
            **self.stats,
            'total_files': total_files,
            'storage_dir': str(self.storage_dir),
            'json_dir': str(self.json_dir),
            'csv_dir': str(self.csv_dir),
            'parquet_dir': str(self.parquet_dir),
            'analytics_dir': str(self.analytics_dir)
        }
    
    def cleanup_old_files(self, days_to_keep: int = 30):
        """Clean up old files to save space"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_files = 0
        
        for dir_path in [self.json_dir, self.csv_dir, self.parquet_dir]:
            for file_path in dir_path.glob('*'):
                if file_path.is_file() and datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:
                    file_path.unlink()
                    cleaned_files += 1
        
        logger.info(f"Cleaned up {cleaned_files} old files")
        return cleaned_files


class DataExporter:
    """Export data in various formats for analysis"""
    
    def __init__(self, storage_agent: StorageAgent):
        self.storage_agent = storage_agent
    
    def export_to_excel(self, records: List[PageRecord], source_name: str, filename: str = None) -> str:
        """Export records to Excel format"""
        if not records:
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_prefix = source_name.lower().replace(' ', '_')
            filename = f"{source_prefix}_{timestamp}.xlsx"
        
        filepath = self.storage_agent.analytics_dir / filename
        
        # Convert to DataFrame
        data = [self.storage_agent._record_to_dict(record) for record in records]
        df = pd.DataFrame(data)
        
        # Export to Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        logger.info(f"Exported {len(records)} records to Excel: {filepath}")
        return str(filepath)
    
    def export_summary_report(self, all_records: Dict[str, List[PageRecord]]) -> str:
        """Export summary report of all data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_report_{timestamp}.txt"
        filepath = self.storage_agent.analytics_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Climate Conflict Early Warning System - Data Summary Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            total_records = sum(len(records) for records in all_records.values())
            f.write(f"Total Records: {total_records}\n\n")
            
            for source_name, records in all_records.items():
                f.write(f"{source_name}:\n")
                f.write(f"  - Records: {len(records)}\n")
                
                if records:
                    # Get date range
                    dates = [r.publish_date for r in records if r.publish_date]
                    if dates:
                        min_date = min(dates)
                        max_date = max(dates)
                        f.write(f"  - Date Range: {min_date} to {max_date}\n")
                    
                    # Get regions
                    regions = set(r.region for r in records if r.region)
                    f.write(f"  - Regions: {', '.join(sorted(regions))}\n")
                    
                    # Get topics
                    all_topics = []
                    for record in records:
                        all_topics.extend(record.topics)
                    topic_counts = pd.Series(all_topics).value_counts()
                    f.write(f"  - Top Topics: {', '.join(topic_counts.head(5).index.tolist())}\n")
                
                f.write("\n")
        
        logger.info(f"Exported summary report: {filepath}")
        return str(filepath)