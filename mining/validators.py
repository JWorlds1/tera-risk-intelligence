# validators.py - Validation Agent with schema checking and duplicate detection
import hashlib
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
from pydantic import ValidationError
import redis
import json

from schemas import PageRecord, SCHEMA_MAP
from config import Config

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of validation process"""
    is_valid: bool
    record: Optional[PageRecord] = None
    errors: List[str] = None
    warnings: List[str] = None
    is_duplicate: bool = False
    duplicate_url: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class DuplicateDetector:
    """Detects and manages duplicate records"""
    
    def __init__(self, config: Config):
        self.config = config
        self.redis_client = None
        self.memory_cache: Set[str] = set()
        self.url_hashes: Dict[str, str] = {}  # hash -> url mapping
        
        # Try to connect to Redis, fallback to memory
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis for duplicate detection")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache: {e}")
    
    def _generate_content_hash(self, record: PageRecord) -> str:
        """Generate hash for content-based duplicate detection"""
        # Create hash from key content fields
        content_fields = [
            record.title or '',
            record.summary or '',
            record.publish_date or '',
            record.region or ''
        ]
        content_string = '|'.join(content_fields)
        return hashlib.md5(content_string.encode()).hexdigest()
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate hash for URL-based duplicate detection"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def is_duplicate(self, record: PageRecord) -> Tuple[bool, Optional[str]]:
        """Check if record is a duplicate"""
        url_hash = self._generate_url_hash(record.url)
        content_hash = self._generate_content_hash(record)
        
        # Check URL-based duplicates
        if self._is_url_duplicate(url_hash):
            return True, f"URL duplicate: {record.url}"
        
        # Check content-based duplicates
        if self._is_content_duplicate(content_hash):
            return True, f"Content duplicate: {record.title}"
        
        # Store hashes
        self._store_hashes(url_hash, content_hash, record.url)
        
        return False, None
    
    def _is_url_duplicate(self, url_hash: str) -> bool:
        """Check if URL hash exists"""
        if self.redis_client:
            return self.redis_client.exists(f"url_hash:{url_hash}")
        else:
            return url_hash in self.memory_cache
    
    def _is_content_duplicate(self, content_hash: str) -> bool:
        """Check if content hash exists"""
        if self.redis_client:
            return self.redis_client.exists(f"content_hash:{content_hash}")
        else:
            return content_hash in self.memory_cache
    
    def _store_hashes(self, url_hash: str, content_hash: str, url: str):
        """Store hashes for future duplicate detection"""
        if self.redis_client:
            # Store with 7-day expiration
            self.redis_client.setex(f"url_hash:{url_hash}", 604800, url)
            self.redis_client.setex(f"content_hash:{content_hash}", 604800, url)
        else:
            self.memory_cache.add(url_hash)
            self.memory_cache.add(content_hash)
            self.url_hashes[url_hash] = url
    
    def get_stats(self) -> Dict[str, Any]:
        """Get duplicate detection statistics"""
        if self.redis_client:
            url_count = self.redis_client.dbsize() // 2  # Each record has 2 hashes
            return {"total_hashes": url_count, "backend": "redis"}
        else:
            return {"total_hashes": len(self.memory_cache), "backend": "memory"}


class SchemaValidator:
    """Validates records against their schemas"""
    
    def __init__(self):
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_record(self, record: PageRecord) -> Tuple[bool, List[str], List[str]]:
        """Validate record against its schema"""
        errors = []
        warnings = []
        
        try:
            # Get the appropriate schema class
            schema_class = SCHEMA_MAP.get(record.source_domain, PageRecord)
            
            # Validate the record
            validated_record = schema_class(**record.dict())
            
            # Additional business logic validation
            self._validate_business_rules(validated_record, warnings)
            
            return True, errors, warnings
            
        except ValidationError as e:
            for error in e.errors():
                errors.append(f"{error['loc']}: {error['msg']}")
            return False, errors, warnings
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors, warnings
    
    def _validate_business_rules(self, record: PageRecord, warnings: List[str]):
        """Validate business rules specific to the project"""
        
        # Check for required fields
        if not record.title or len(record.title.strip()) < 10:
            warnings.append("Title is too short or missing")
        
        if not record.summary or len(record.summary.strip()) < 20:
            warnings.append("Summary is too short or missing")
        
        # Check for recent content (within last 2 years)
        if record.publish_date:
            try:
                pub_date = datetime.strptime(record.publish_date, '%Y-%m-%d')
                if pub_date < datetime.now() - timedelta(days=730):
                    warnings.append("Content is older than 2 years")
            except ValueError:
                warnings.append("Invalid date format")
        
        # Check for climate-related content
        climate_keywords = [
            'climate', 'weather', 'drought', 'flood', 'temperature', 'precipitation',
            'environment', 'ecosystem', 'biodiversity', 'carbon', 'emission',
            'renewable', 'sustainable', 'adaptation', 'mitigation'
        ]
        
        content_text = f"{record.title or ''} {record.summary or ''}".lower()
        has_climate_content = any(keyword in content_text for keyword in climate_keywords)
        
        if not has_climate_content:
            warnings.append("Content may not be climate-related")
        
        # Check for conflict-related content
        conflict_keywords = [
            'conflict', 'war', 'violence', 'displacement', 'refugee', 'migration',
            'crisis', 'emergency', 'humanitarian', 'aid', 'relief', 'resilience'
        ]
        
        has_conflict_content = any(keyword in content_text for keyword in conflict_keywords)
        
        if not has_conflict_content:
            warnings.append("Content may not be conflict-related")


class ContentQualityChecker:
    """Checks content quality and completeness"""
    
    def __init__(self):
        self.quality_thresholds = {
            'min_title_length': 10,
            'min_summary_length': 20,
            'max_title_length': 200,
            'max_summary_length': 1000,
            'min_topics': 1,
            'max_topics': 10
        }
    
    def check_quality(self, record: PageRecord) -> Tuple[float, List[str]]:
        """Check content quality and return score (0-1) and issues"""
        score = 1.0
        issues = []
        
        # Title quality
        if not record.title:
            score -= 0.3
            issues.append("Missing title")
        elif len(record.title) < self.quality_thresholds['min_title_length']:
            score -= 0.2
            issues.append("Title too short")
        elif len(record.title) > self.quality_thresholds['max_title_length']:
            score -= 0.1
            issues.append("Title too long")
        
        # Summary quality
        if not record.summary:
            score -= 0.3
            issues.append("Missing summary")
        elif len(record.summary) < self.quality_thresholds['min_summary_length']:
            score -= 0.2
            issues.append("Summary too short")
        elif len(record.summary) > self.quality_thresholds['max_summary_length']:
            score -= 0.1
            issues.append("Summary too long")
        
        # Topics quality
        if not record.topics:
            score -= 0.1
            issues.append("No topics/tags")
        elif len(record.topics) > self.quality_thresholds['max_topics']:
            score -= 0.1
            issues.append("Too many topics")
        
        # Date quality
        if not record.publish_date:
            score -= 0.1
            issues.append("Missing publish date")
        
        # Region quality
        if not record.region:
            score -= 0.1
            issues.append("Missing region information")
        
        # Links quality
        if not record.links:
            score -= 0.05
            issues.append("No external links")
        
        return max(0.0, score), issues


class ValidationAgent:
    """Main validation agent that coordinates all validation processes"""
    
    def __init__(self, config: Config):
        self.config = config
        self.duplicate_detector = DuplicateDetector(config)
        self.schema_validator = SchemaValidator()
        self.quality_checker = ContentQualityChecker()
        self.stats = {
            'total_validated': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'duplicates_found': 0,
            'quality_issues': 0
        }
    
    def validate(self, record: PageRecord) -> ValidationResult:
        """Validate a single record"""
        self.stats['total_validated'] += 1
        
        # Check for duplicates
        is_duplicate, duplicate_reason = self.duplicate_detector.is_duplicate(record)
        if is_duplicate:
            self.stats['duplicates_found'] += 1
            return ValidationResult(
                is_valid=False,
                is_duplicate=True,
                duplicate_url=duplicate_reason
            )
        
        # Schema validation
        is_schema_valid, schema_errors, schema_warnings = self.schema_validator.validate_record(record)
        
        # Quality check
        quality_score, quality_issues = self.quality_checker.check_quality(record)
        
        # Combine results
        all_errors = schema_errors.copy()
        all_warnings = schema_warnings + quality_issues
        
        if quality_score < 0.5:
            all_warnings.append(f"Low quality score: {quality_score:.2f}")
            self.stats['quality_issues'] += 1
        
        is_valid = is_schema_valid and not is_duplicate
        
        if is_valid:
            self.stats['valid_records'] += 1
        else:
            self.stats['invalid_records'] += 1
        
        return ValidationResult(
            is_valid=is_valid,
            record=record,
            errors=all_errors,
            warnings=all_warnings,
            is_duplicate=is_duplicate
        )
    
    def validate_batch(self, records: List[PageRecord]) -> List[ValidationResult]:
        """Validate multiple records"""
        results = []
        for record in records:
            result = self.validate(record)
            results.append(result)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total = self.stats['total_validated']
        return {
            **self.stats,
            'validation_rate': self.stats['valid_records'] / max(total, 1),
            'duplicate_rate': self.stats['duplicates_found'] / max(total, 1),
            'quality_issue_rate': self.stats['quality_issues'] / max(total, 1),
            'duplicate_detector_stats': self.duplicate_detector.get_stats()
        }
    
    def reset_stats(self):
        """Reset validation statistics"""
        self.stats = {
            'total_validated': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'duplicates_found': 0,
            'quality_issues': 0
        }
