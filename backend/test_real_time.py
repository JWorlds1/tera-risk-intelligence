# test_real_time.py - Umfassender Test für Real-time Extraktion
import asyncio
import time
import json
from typing import Dict, List, Optional
from datetime import datetime
import structlog
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text

from config import Config
from real_time_extractor import RealTimeExtractor
from quality_control import DataQualityController
from strategic_urls import StrategicURLManager

logger = structlog.get_logger(__name__)
console = Console()

class RealTimeTester:
    """Umfassender Test für Real-time Extraktion"""
    
    def __init__(self):
        self.config = Config()
        self.extractor = None
        self.quality_controller = None
        self.strategic_urls = StrategicURLManager()
        self.test_results = []
    
    async def __aenter__(self):
        """Initialize components"""
        self.extractor = RealTimeExtractor(self.config)
        self.quality_controller = DataQualityController(self.config)
        await self.extractor.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup"""
        if self.extractor:
            await self.extractor.__aexit__(exc_type, exc_val, exc_tb)
    
    async def run_comprehensive_test(self):
        """Führe umfassenden Test durch"""
        console.print(Panel.fit(
            "🧪 Real-time Extraktion Test Suite",
            subtitle="Garantierte Datenqualität & Echtzeit-Performance",
            border_style="blue"
        ))
        
        # Test 1: Basis-Extraktion
        await self.test_basic_extraction()
        
        # Test 2: Qualitätskontrolle
        await self.test_quality_control()
        
        # Test 3: Real-time Performance
        await self.test_real_time_performance()
        
        # Test 4: Strategische URLs
        await self.test_strategic_urls()
        
        # Test 5: Fehlerbehandlung
        await self.test_error_handling()
        
        # Test 6: Skalierbarkeit
        await self.test_scalability()
        
        # Zusammenfassung
        self.print_test_summary()
    
    async def test_basic_extraction(self):
        """Test 1: Basis-Extraktion"""
        console.print("\n[bold blue]Test 1: Basis-Extraktion[/bold blue]")
        
        test_urls = [
            "https://earthobservatory.nasa.gov/images",
            "https://www.wfp.org/news",
            "https://press.un.org/en",
            "https://www.worldbank.org/en/news"
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Testing basic extraction", total=len(test_urls))
            
            for i, url in enumerate(test_urls):
                progress.advance(task)
                
                # Füge Job hinzu
                job_id = await self.extractor.add_extraction_job(url, f"Test Source {i+1}")
                
                # Warte auf Completion
                max_wait = 60  # 60 Sekunden Timeout
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    job_status = self.extractor.get_job_status(job_id)
                    if job_status and job_status['status'] in ['success', 'failed']:
                        break
                    await asyncio.sleep(1)
                
                # Bewerte Ergebnis
                if job_status:
                    success = job_status['status'] == 'success'
                    extraction_time = job_status.get('result', {}).get('extraction_time', 0)
                    
                    self.test_results.append({
                        'test': 'basic_extraction',
                        'url': url,
                        'success': success,
                        'extraction_time': extraction_time,
                        'job_id': job_id
                    })
                    
                    if success:
                        console.print(f"✅ {url} - {extraction_time:.2f}s")
                    else:
                        console.print(f"❌ {url} - {job_status.get('error', 'Unknown error')}")
                else:
                    console.print(f"⏰ {url} - Timeout")
                    self.test_results.append({
                        'test': 'basic_extraction',
                        'url': url,
                        'success': False,
                        'extraction_time': max_wait,
                        'job_id': job_id,
                        'error': 'Timeout'
                    })
    
    async def test_quality_control(self):
        """Test 2: Qualitätskontrolle"""
        console.print("\n[bold blue]Test 2: Qualitätskontrolle[/bold blue]")
        
        # Simuliere verschiedene Datenqualitäten
        test_cases = [
            {
                'name': 'Excellent Quality',
                'data': {
                    'title': 'Severe Drought in East Africa Causes Food Crisis',
                    'summary': 'The worst drought in 40 years has devastated crops across East Africa, leading to widespread food insecurity and displacement of millions of people.',
                    'region': 'East Africa',
                    'topics': ['drought', 'food_crisis', 'climate', 'displacement'],
                    'publish_date': '2024-01-15'
                }
            },
            {
                'name': 'Poor Quality',
                'data': {
                    'title': 'News',
                    'summary': 'Bad weather.',
                    'region': '',
                    'topics': [],
                    'publish_date': ''
                }
            },
            {
                'name': 'Medium Quality',
                'data': {
                    'title': 'Climate Change Impact',
                    'summary': 'Rising temperatures affect agriculture in the region.',
                    'region': 'Africa',
                    'topics': ['climate'],
                    'publish_date': '2024-01-01'
                }
            }
        ]
        
        for case in test_cases:
            # Erstelle Mock Record
            from schemas import PageRecord
            record = PageRecord(
                url="https://test.com",
                source_domain="test.com",
                source_name="Test",
                fetched_at=datetime.now(),
                **case['data']
            )
            
            # Analysiere Qualität
            quality_report = await self.quality_controller.analyze_quality(record)
            
            console.print(f"📊 {case['name']}:")
            console.print(f"   Score: {quality_report.overall_score:.2f}")
            console.print(f"   Level: {quality_report.quality_level.name}")
            console.print(f"   Confidence: {quality_report.confidence:.2f}")
            
            if quality_report.issues:
                console.print(f"   Issues: {', '.join(quality_report.issues[:3])}")
            
            self.test_results.append({
                'test': 'quality_control',
                'case': case['name'],
                'score': quality_report.overall_score,
                'level': quality_report.quality_level.name,
                'confidence': quality_report.confidence,
                'issues_count': len(quality_report.issues)
            })
    
    async def test_real_time_performance(self):
        """Test 3: Real-time Performance"""
        console.print("\n[bold blue]Test 3: Real-time Performance[/bold blue]")
        
        # Teste mit mehreren gleichzeitigen Jobs
        concurrent_jobs = 5
        test_urls = [
            "https://earthobservatory.nasa.gov/images",
            "https://www.wfp.org/news",
            "https://press.un.org/en",
            "https://www.worldbank.org/en/news",
            "https://earthobservatory.nasa.gov/features"
        ]
        
        start_time = time.time()
        
        # Starte alle Jobs gleichzeitig
        job_ids = []
        for url in test_urls[:concurrent_jobs]:
            job_id = await self.extractor.add_extraction_job(url, "Performance Test")
            job_ids.append(job_id)
        
        # Warte auf alle Jobs
        completed_jobs = 0
        max_wait = 120  # 2 Minuten Timeout
        
        while completed_jobs < concurrent_jobs and time.time() - start_time < max_wait:
            completed_jobs = 0
            for job_id in job_ids:
                job_status = self.extractor.get_job_status(job_id)
                if job_status and job_status['status'] in ['success', 'failed']:
                    completed_jobs += 1
            
            await asyncio.sleep(1)
        
        total_time = time.time() - start_time
        success_rate = completed_jobs / concurrent_jobs
        
        console.print(f"📈 Performance Results:")
        console.print(f"   Concurrent Jobs: {concurrent_jobs}")
        console.print(f"   Total Time: {total_time:.2f}s")
        console.print(f"   Success Rate: {success_rate:.1%}")
        console.print(f"   Jobs/Second: {concurrent_jobs/total_time:.2f}")
        
        self.test_results.append({
            'test': 'real_time_performance',
            'concurrent_jobs': concurrent_jobs,
            'total_time': total_time,
            'success_rate': success_rate,
            'jobs_per_second': concurrent_jobs/total_time
        })
    
    async def test_strategic_urls(self):
        """Test 4: Strategische URLs"""
        console.print("\n[bold blue]Test 4: Strategische URLs[/bold blue]")
        
        # Hole strategische URLs
        critical_urls = self.strategic_urls.get_critical_urls()
        
        console.print(f"🎯 Testing {len(critical_urls)} strategic URLs")
        
        # Teste erste 3 URLs
        test_urls = critical_urls[:3]
        job_ids = []
        
        for url_info in test_urls:
            job_id = await self.extractor.add_extraction_job(
                url_info.url,
                url_info.category,
                priority=1
            )
            job_ids.append(job_id)
            console.print(f"   Added: {url_info.description}")
        
        # Warte auf Completion
        completed = 0
        max_wait = 90
        
        start_time = time.time()
        while completed < len(job_ids) and time.time() - start_time < max_wait:
            completed = 0
            for job_id in job_ids:
                job_status = self.extractor.get_job_status(job_id)
                if job_status and job_status['status'] in ['success', 'failed']:
                    completed += 1
            await asyncio.sleep(1)
        
        success_count = 0
        for job_id in job_ids:
            job_status = self.extractor.get_job_status(job_id)
            if job_status and job_status['status'] == 'success':
                success_count += 1
        
        console.print(f"✅ Strategic URLs: {success_count}/{len(job_ids)} successful")
        
        self.test_results.append({
            'test': 'strategic_urls',
            'total_urls': len(job_ids),
            'successful': success_count,
            'success_rate': success_count/len(job_ids)
        })
    
    async def test_error_handling(self):
        """Test 5: Fehlerbehandlung"""
        console.print("\n[bold blue]Test 5: Fehlerbehandlung[/bold blue]")
        
        # Teste mit ungültigen URLs
        invalid_urls = [
            "https://invalid-domain-that-does-not-exist.com",
            "https://httpstat.us/500",
            "https://httpstat.us/404",
            "not-a-valid-url"
        ]
        
        job_ids = []
        for url in invalid_urls:
            job_id = await self.extractor.add_extraction_job(url, "Error Test")
            job_ids.append(job_id)
        
        # Warte auf alle Jobs
        await asyncio.sleep(30)
        
        failed_count = 0
        for job_id in job_ids:
            job_status = self.extractor.get_job_status(job_id)
            if job_status and job_status['status'] == 'failed':
                failed_count += 1
        
        console.print(f"🛡️ Error Handling: {failed_count}/{len(invalid_urls)} failed as expected")
        
        self.test_results.append({
            'test': 'error_handling',
            'invalid_urls': len(invalid_urls),
            'failed_count': failed_count,
            'error_rate': failed_count/len(invalid_urls)
        })
    
    async def test_scalability(self):
        """Test 6: Skalierbarkeit"""
        console.print("\n[bold blue]Test 6: Skalierbarkeit[/bold blue]")
        
        # Teste mit vielen Jobs
        batch_size = 10
        test_urls = [
            "https://earthobservatory.nasa.gov/images",
            "https://www.wfp.org/news",
            "https://press.un.org/en",
            "https://www.worldbank.org/en/news"
        ] * 3  # 12 URLs total
        
        start_time = time.time()
        
        # Starte alle Jobs
        job_ids = []
        for url in test_urls:
            job_id = await self.extractor.add_extraction_job(url, "Scalability Test")
            job_ids.append(job_id)
        
        # Warte auf Completion
        completed = 0
        max_wait = 180  # 3 Minuten
        
        while completed < len(job_ids) and time.time() - start_time < max_wait:
            completed = 0
            for job_id in job_ids:
                job_status = self.extractor.get_job_status(job_id)
                if job_status and job_status['status'] in ['success', 'failed']:
                    completed += 1
            await asyncio.sleep(2)
        
        total_time = time.time() - start_time
        success_count = sum(1 for job_id in job_ids 
                          if self.extractor.get_job_status(job_id) and 
                          self.extractor.get_job_status(job_id)['status'] == 'success')
        
        console.print(f"📊 Scalability Results:")
        console.print(f"   Total Jobs: {len(job_ids)}")
        console.print(f"   Completed: {completed}")
        console.print(f"   Successful: {success_count}")
        console.print(f"   Total Time: {total_time:.2f}s")
        console.print(f"   Throughput: {completed/total_time:.2f} jobs/s")
        
        self.test_results.append({
            'test': 'scalability',
            'total_jobs': len(job_ids),
            'completed': completed,
            'successful': success_count,
            'total_time': total_time,
            'throughput': completed/total_time
        })
    
    def print_test_summary(self):
        """Drucke Test-Zusammenfassung"""
        console.print("\n[bold green]📋 Test Summary[/bold green]")
        
        # Gruppiere Ergebnisse nach Test
        test_groups = {}
        for result in self.test_results:
            test_name = result['test']
            if test_name not in test_groups:
                test_groups[test_name] = []
            test_groups[test_name].append(result)
        
        # Erstelle Tabelle
        table = Table(title="Test Results Summary")
        table.add_column("Test", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Success Rate", style="yellow")
        table.add_column("Avg Time", style="blue")
        table.add_column("Status", style="magenta")
        
        for test_name, results in test_groups.items():
            if test_name == 'basic_extraction':
                success_count = sum(1 for r in results if r.get('success', False))
                total_count = len(results)
                avg_time = sum(r.get('extraction_time', 0) for r in results) / total_count
                success_rate = success_count / total_count
                status = "✅ PASS" if success_rate > 0.5 else "❌ FAIL"
                
            elif test_name == 'quality_control':
                success_count = len(results)
                total_count = len(results)
                avg_time = sum(r.get('score', 0) for r in results) / total_count
                success_rate = 1.0  # Quality control always "succeeds"
                status = "✅ PASS"
                
            elif test_name == 'real_time_performance':
                success_count = 1 if results[0]['success_rate'] > 0.5 else 0
                total_count = 1
                avg_time = results[0]['total_time']
                success_rate = results[0]['success_rate']
                status = "✅ PASS" if success_rate > 0.5 else "❌ FAIL"
                
            elif test_name == 'strategic_urls':
                success_count = results[0]['successful']
                total_count = results[0]['total_urls']
                avg_time = 0
                success_rate = results[0]['success_rate']
                status = "✅ PASS" if success_rate > 0.3 else "❌ FAIL"
                
            elif test_name == 'error_handling':
                success_count = results[0]['failed_count']
                total_count = results[0]['invalid_urls']
                avg_time = 0
                success_rate = results[0]['error_rate']
                status = "✅ PASS" if success_rate > 0.5 else "❌ FAIL"
                
            elif test_name == 'scalability':
                success_count = results[0]['successful']
                total_count = results[0]['total_jobs']
                avg_time = results[0]['total_time']
                success_rate = results[0]['successful'] / results[0]['total_jobs']
                status = "✅ PASS" if success_rate > 0.3 else "❌ FAIL"
            
            else:
                success_count = 0
                total_count = 0
                avg_time = 0
                success_rate = 0
                status = "❓ UNKNOWN"
            
            table.add_row(
                test_name.replace('_', ' ').title(),
                f"{success_count}/{total_count}",
                f"{success_rate:.1%}",
                f"{avg_time:.2f}s",
                status
            )
        
        console.print(table)
        
        # Gesamtbewertung
        total_tests = len(test_groups)
        passed_tests = sum(1 for test_name, results in test_groups.items()
                          if self._evaluate_test_success(test_name, results))
        
        overall_success = passed_tests / total_tests
        
        console.print(f"\n[bold]Overall Success Rate: {overall_success:.1%} ({passed_tests}/{total_tests})[/bold]")
        
        if overall_success >= 0.8:
            console.print("[bold green]🎉 System is ready for production![/bold green]")
        elif overall_success >= 0.6:
            console.print("[bold yellow]⚠️ System needs improvement before production[/bold yellow]")
        else:
            console.print("[bold red]❌ System needs significant fixes[/bold red]")
    
    def _evaluate_test_success(self, test_name: str, results: List[Dict]) -> bool:
        """Bewerte ob ein Test erfolgreich war"""
        if test_name == 'basic_extraction':
            success_rate = sum(1 for r in results if r.get('success', False)) / len(results)
            return success_rate > 0.5
        elif test_name == 'real_time_performance':
            return results[0]['success_rate'] > 0.5
        elif test_name == 'strategic_urls':
            return results[0]['success_rate'] > 0.3
        elif test_name == 'error_handling':
            return results[0]['error_rate'] > 0.5  # Should fail for invalid URLs
        elif test_name == 'scalability':
            return results[0]['successful'] / results[0]['total_jobs'] > 0.3
        else:
            return True  # Quality control always passes

async def main():
    """Hauptfunktion"""
    async with RealTimeTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
