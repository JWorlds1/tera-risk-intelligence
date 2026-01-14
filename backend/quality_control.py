# quality_control.py - Robuste Qualitätskontrolle für garantierte Extraktion
import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
from enum import Enum
import json
import re
from collections import defaultdict, Counter

from schemas import PageRecord
from config import Config

logger = structlog.get_logger(__name__)

class QualityLevel(Enum):
    EXCELLENT = 5
    GOOD = 4
    FAIR = 3
    POOR = 2
    FAILED = 1

@dataclass
class QualityReport:
    overall_score: float
    quality_level: QualityLevel
    field_scores: Dict[str, float]
    issues: List[str]
    recommendations: List[str]
    confidence: float
    timestamp: datetime

class DataQualityController:
    """Robuste Qualitätskontrolle für garantierte Extraktion"""
    
    def __init__(self, config: Config):
        self.config = config
        self.quality_history = []
        self.field_importance = {
            'title': 0.25,
            'summary': 0.30,
            'region': 0.20,
            'topics': 0.15,
            'publish_date': 0.10
        }
        
        # Qualitätskriterien
        self.criteria = {
            'min_title_length': 10,
            'max_title_length': 200,
            'min_summary_length': 50,
            'max_summary_length': 2000,
            'min_topics_count': 1,
            'max_topics_count': 10,
            'required_region_keywords': [
                'Africa', 'Asia', 'Europe', 'America', 'Middle East',
                'Horn of Africa', 'Sahel', 'Arctic', 'Pacific', 'Caribbean'
            ],
            'climate_keywords': [
                'climate', 'weather', 'drought', 'flood', 'temperature',
                'precipitation', 'environment', 'ecosystem', 'carbon',
                'emission', 'renewable', 'sustainable', 'adaptation'
            ],
            'conflict_keywords': [
                'conflict', 'war', 'violence', 'displacement', 'refugee',
                'migration', 'crisis', 'emergency', 'humanitarian', 'aid',
                'relief', 'resilience', 'terrorism', 'insurgency'
            ]
        }
    
    async def analyze_quality(self, record: PageRecord) -> QualityReport:
        """Analysiere Datenqualität eines Records"""
        field_scores = {}
        issues = []
        recommendations = []
        
        # Analysiere jedes Feld
        for field, importance in self.field_importance.items():
            score, field_issues, field_recommendations = await self._analyze_field(
                record, field, importance
            )
            field_scores[field] = score
            issues.extend(field_issues)
            recommendations.extend(field_recommendations)
        
        # Berechne Gesamtscore
        overall_score = sum(score * importance for score, importance in 
                          zip(field_scores.values(), self.field_importance.values()))
        
        # Bestimme Qualitätslevel
        quality_level = self._determine_quality_level(overall_score)
        
        # Berechne Confidence
        confidence = self._calculate_confidence(record, field_scores)
        
        # Erstelle Report
        report = QualityReport(
            overall_score=overall_score,
            quality_level=quality_level,
            field_scores=field_scores,
            issues=issues,
            recommendations=recommendations,
            confidence=confidence,
            timestamp=datetime.now()
        )
        
        # Speichere in History
        self.quality_history.append(report)
        
        return report
    
    async def _analyze_field(self, record: PageRecord, field: str, importance: float) -> Tuple[float, List[str], List[str]]:
        """Analysiere ein spezifisches Feld"""
        score = 0.0
        issues = []
        recommendations = []
        
        if not hasattr(record, field):
            return 0.0, [f"Field {field} not found"], [f"Add {field} field to schema"]
        
        value = getattr(record, field)
        
        if field == 'title':
            score, issues, recommendations = self._analyze_title(value)
        elif field == 'summary':
            score, issues, recommendations = self._analyze_summary(value)
        elif field == 'region':
            score, issues, recommendations = self._analyze_region(value)
        elif field == 'topics':
            score, issues, recommendations = self._analyze_topics(value)
        elif field == 'publish_date':
            score, issues, recommendations = self._analyze_publish_date(value)
        else:
            # Generische Analyse
            score = 1.0 if value else 0.0
            if not value:
                issues.append(f"{field} is empty")
                recommendations.append(f"Populate {field} field")
        
        return score, issues, recommendations
    
    def _analyze_title(self, title: str) -> Tuple[float, List[str], List[str]]:
        """Analysiere Titel-Qualität"""
        score = 0.0
        issues = []
        recommendations = []
        
        if not title:
            return 0.0, ["Title is empty"], ["Extract title from content"]
        
        title_len = len(title.strip())
        
        # Längen-Check
        if title_len < self.criteria['min_title_length']:
            score += 0.3
            issues.append(f"Title too short ({title_len} chars)")
            recommendations.append("Extract longer, more descriptive title")
        elif title_len > self.criteria['max_title_length']:
            score += 0.5
            issues.append(f"Title too long ({title_len} chars)")
            recommendations.append("Truncate title to reasonable length")
        else:
            score += 0.8
        
        # Inhalt-Qualität
        if any(keyword in title.lower() for keyword in self.criteria['climate_keywords']):
            score += 0.1
        if any(keyword in title.lower() for keyword in self.criteria['conflict_keywords']):
            score += 0.1
        
        # Spezielle Zeichen
        if re.search(r'[^\w\s\-.,!?;:()]', title):
            score -= 0.1
            issues.append("Title contains special characters")
            recommendations.append("Clean title of special characters")
        
        return min(1.0, score), issues, recommendations
    
    def _analyze_summary(self, summary: str) -> Tuple[float, List[str], List[str]]:
        """Analysiere Summary-Qualität"""
        score = 0.0
        issues = []
        recommendations = []
        
        if not summary:
            return 0.0, ["Summary is empty"], ["Extract summary from content"]
        
        summary_len = len(summary.strip())
        
        # Längen-Check
        if summary_len < self.criteria['min_summary_length']:
            score += 0.2
            issues.append(f"Summary too short ({summary_len} chars)")
            recommendations.append("Extract longer, more detailed summary")
        elif summary_len > self.criteria['max_summary_length']:
            score += 0.6
            issues.append(f"Summary too long ({summary_len} chars)")
            recommendations.append("Truncate summary to reasonable length")
        else:
            score += 0.8
        
        # Inhalt-Qualität
        climate_count = sum(1 for keyword in self.criteria['climate_keywords'] 
                          if keyword in summary.lower())
        conflict_count = sum(1 for keyword in self.criteria['conflict_keywords'] 
                           if keyword in summary.lower())
        
        if climate_count > 0:
            score += 0.1
        if conflict_count > 0:
            score += 0.1
        
        # Satzstruktur
        sentences = re.split(r'[.!?]+', summary)
        if len(sentences) >= 2:
            score += 0.1
        else:
            issues.append("Summary should have multiple sentences")
            recommendations.append("Extract more detailed summary with multiple sentences")
        
        return min(1.0, score), issues, recommendations
    
    def _analyze_region(self, region: str) -> Tuple[float, List[str], List[str]]:
        """Analysiere Region-Qualität"""
        score = 0.0
        issues = []
        recommendations = []
        
        if not region:
            return 0.0, ["Region is empty"], ["Extract geographical region from content"]
        
        region_lower = region.lower()
        
        # Prüfe gegen bekannte Regionen
        region_found = any(keyword.lower() in region_lower 
                          for keyword in self.criteria['required_region_keywords'])
        
        if region_found:
            score += 0.8
        else:
            score += 0.3
            issues.append("Region not in known list")
            recommendations.append("Verify region name against geographical database")
        
        # Längen-Check
        if len(region) < 3:
            score -= 0.2
            issues.append("Region name too short")
            recommendations.append("Extract more specific region name")
        
        return min(1.0, score), issues, recommendations
    
    def _analyze_topics(self, topics: List[str]) -> Tuple[float, List[str], List[str]]:
        """Analysiere Topics-Qualität"""
        score = 0.0
        issues = []
        recommendations = []
        
        if not topics:
            return 0.0, ["Topics list is empty"], ["Extract topics/tags from content"]
        
        topics_count = len(topics)
        
        # Anzahl-Check
        if topics_count < self.criteria['min_topics_count']:
            score += 0.3
            issues.append(f"Too few topics ({topics_count})")
            recommendations.append("Extract more topics from content")
        elif topics_count > self.criteria['max_topics_count']:
            score += 0.6
            issues.append(f"Too many topics ({topics_count})")
            recommendations.append("Filter topics to most relevant ones")
        else:
            score += 0.8
        
        # Inhalt-Qualität
        climate_topics = sum(1 for topic in topics 
                           if any(keyword in topic.lower() 
                                for keyword in self.criteria['climate_keywords']))
        conflict_topics = sum(1 for topic in topics 
                            if any(keyword in topic.lower() 
                                 for keyword in self.criteria['conflict_keywords']))
        
        if climate_topics > 0:
            score += 0.1
        if conflict_topics > 0:
            score += 0.1
        
        # Duplikate
        if len(topics) != len(set(topics)):
            score -= 0.2
            issues.append("Duplicate topics found")
            recommendations.append("Remove duplicate topics")
        
        return min(1.0, score), issues, recommendations
    
    def _analyze_publish_date(self, date_str: str) -> Tuple[float, List[str], List[str]]:
        """Analysiere Publish Date-Qualität"""
        score = 0.0
        issues = []
        recommendations = []
        
        if not date_str:
            return 0.0, ["Publish date is empty"], ["Extract publication date from content"]
        
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            
            # Prüfe ob Datum sinnvoll ist
            now = datetime.now()
            if parsed_date > now:
                score += 0.3
                issues.append("Future date detected")
                recommendations.append("Verify date extraction")
            elif parsed_date < now - timedelta(days=365*5):  # Älter als 5 Jahre
                score += 0.5
                issues.append("Very old date")
                recommendations.append("Consider if old data is still relevant")
            else:
                score += 0.8
            
            # Format-Check
            if len(date_str) < 8:  # Mindestens YYYY-MM-DD
                score -= 0.2
                issues.append("Date format incomplete")
                recommendations.append("Extract full date format")
            
        except Exception as e:
            score = 0.0
            issues.append(f"Invalid date format: {str(e)}")
            recommendations.append("Fix date parsing or extraction")
        
        return min(1.0, score), issues, recommendations
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Bestimme Qualitätslevel basierend auf Score"""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.FAIR
        elif score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.FAILED
    
    def _calculate_confidence(self, record: PageRecord, field_scores: Dict[str, float]) -> float:
        """Berechne Confidence-Score"""
        # Basis-Confidence aus Feld-Scores
        base_confidence = sum(field_scores.values()) / len(field_scores)
        
        # Zusätzliche Faktoren
        bonus = 0.0
        
        # Vollständigkeit
        required_fields = ['title', 'summary', 'region', 'topics']
        completeness = sum(1 for field in required_fields 
                          if hasattr(record, field) and getattr(record, field))
        bonus += (completeness / len(required_fields)) * 0.1
        
        # Content-Länge
        if hasattr(record, 'summary') and record.summary:
            if len(record.summary) > 200:
                bonus += 0.05
        
        # Topics-Qualität
        if hasattr(record, 'topics') and record.topics:
            if len(record.topics) >= 3:
                bonus += 0.05
        
        return min(1.0, base_confidence + bonus)
    
    def get_quality_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Hole Qualitätstrends der letzten X Stunden"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_reports = [r for r in self.quality_history if r.timestamp > cutoff]
        
        if not recent_reports:
            return {"error": "No recent quality data"}
        
        scores = [r.overall_score for r in recent_reports]
        confidences = [r.confidence for r in recent_reports]
        
        return {
            'count': len(recent_reports),
            'avg_score': sum(scores) / len(scores),
            'avg_confidence': sum(confidences) / len(confidences),
            'score_trend': self._calculate_trend(scores),
            'confidence_trend': self._calculate_trend(confidences),
            'quality_distribution': self._get_quality_distribution(recent_reports),
            'common_issues': self._get_common_issues(recent_reports)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Berechne Trend (steigend, fallend, stabil)"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Einfache lineare Regression
        n = len(values)
        x = list(range(n))
        y = values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def _get_quality_distribution(self, reports: List[QualityReport]) -> Dict[str, int]:
        """Hole Verteilung der Qualitätslevel"""
        distribution = defaultdict(int)
        for report in reports:
            distribution[report.quality_level.name] += 1
        return dict(distribution)
    
    def _get_common_issues(self, reports: List[QualityReport]) -> List[Tuple[str, int]]:
        """Hole häufigste Issues"""
        all_issues = []
        for report in reports:
            all_issues.extend(report.issues)
        
        issue_counts = Counter(all_issues)
        return issue_counts.most_common(5)
    
    def get_field_performance(self) -> Dict[str, Dict[str, float]]:
        """Hole Performance-Metriken pro Feld"""
        if not self.quality_history:
            return {}
        
        field_stats = defaultdict(list)
        
        for report in self.quality_history:
            for field, score in report.field_scores.items():
                field_stats[field].append(score)
        
        performance = {}
        for field, scores in field_stats.items():
            performance[field] = {
                'avg_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'count': len(scores)
            }
        
        return performance
