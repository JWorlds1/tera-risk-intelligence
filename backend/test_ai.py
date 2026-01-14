# test_ai.py - Test Script für AI-Features
import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from ai_agents import ClimateConflictAgent, FirecrawlAgent, LocalLLMManager
from rich.console import Console
from rich.panel import Panel

console = Console()


async def test_firecrawl():
    """Teste Firecrawl API"""
    console.print("\n[bold blue]Testing Firecrawl API...[/bold blue]")
    
    try:
        config = Config()
        firecrawl_agent = FirecrawlAgent(config.FIRECRAWL_API_KEY)
        
        # Teste mit einer einfachen URL
        test_url = "https://earthobservatory.nasa.gov/images"
        result = await firecrawl_agent.extract_page(test_url)
        
        if result['success']:
            console.print("✅ Firecrawl API funktioniert")
            console.print(f"📄 Inhalt extrahiert: {len(result.get('content', ''))} Zeichen")
            console.print(f"🔍 Metadaten: {result.get('metadata', {})}")
        else:
            console.print(f"❌ Firecrawl Fehler: {result.get('error')}")
            
    except Exception as e:
        console.print(f"❌ Firecrawl Test fehlgeschlagen: {e}")


async def test_local_llm():
    """Teste lokale LLMs"""
    console.print("\n[bold blue]Testing Local LLMs...[/bold blue]")
    
    try:
        config = Config()
        llm_manager = LocalLLMManager(config)
        
        available_models = llm_manager.get_available_models()
        console.print(f"🤖 Verfügbare Modelle: {available_models}")
        
        if available_models:
            model = llm_manager.get_model("llama2")
            if model:
                console.print("✅ Lokales LLM funktioniert")
                
                # Teste einfache Generierung
                test_prompt = "Was ist Klimawandel?"
                try:
                    response = await model.ainvoke(test_prompt)
                    console.print(f"🧠 LLM Antwort: {response[:100]}...")
                except Exception as e:
                    console.print(f"⚠️  LLM Generierung fehlgeschlagen: {e}")
            else:
                console.print("❌ Kein LLM verfügbar")
        else:
            console.print("❌ Keine Modelle gefunden")
            
    except Exception as e:
        console.print(f"❌ LLM Test fehlgeschlagen: {e}")


async def test_ai_agent():
    """Teste AI-Agent"""
    console.print("\n[bold blue]Testing AI Agent...[/bold blue]")
    
    try:
        config = Config()
        ai_agent = ClimateConflictAgent(config, config.FIRECRAWL_API_KEY)
        
        # Teste mit einem Beispieltext
        test_text = """
        Severe drought in East Africa has led to widespread food insecurity and displacement. 
        The United Nations reports that over 20 million people are affected across Somalia, 
        Kenya, and Ethiopia. Climate change is exacerbating the situation with rising 
        temperatures and unpredictable rainfall patterns.
        """
        
        console.print("🔍 Analysiere Testtext...")
        analysis = await ai_agent.analyze_text(test_text)
        
        if analysis:
            console.print("✅ AI-Analyse erfolgreich")
            console.print(f"🌍 Klima-Indikatoren: {analysis.climate_indicators}")
            console.print(f"⚔️  Konflikt-Indikatoren: {analysis.conflict_indicators}")
            console.print(f"📍 Betroffene Regionen: {analysis.affected_regions}")
            console.print(f"⚠️  Risikostufe: {analysis.risk_level}")
            console.print(f"📊 Dringlichkeit: {analysis.urgency_score}/10")
        else:
            console.print("❌ AI-Analyse fehlgeschlagen")
            
    except Exception as e:
        console.print(f"❌ AI-Agent Test fehlgeschlagen: {e}")


async def test_full_pipeline():
    """Teste vollständige AI-Pipeline"""
    console.print("\n[bold blue]Testing Full AI Pipeline...[/bold blue]")
    
    try:
        from ai_agents import EnhancedExtractor
        
        config = Config()
        enhanced_extractor = EnhancedExtractor(config, config.FIRECRAWL_API_KEY)
        
        # Teste mit einer echten URL
        test_url = "https://earthobservatory.nasa.gov/images"
        source_name = "NASA"
        
        console.print(f"🔍 Teste AI-Extraktion für {test_url}...")
        record = await enhanced_extractor.extract_with_ai_support(test_url, source_name)
        
        if record:
            console.print("✅ AI-Extraktion erfolgreich")
            console.print(f"📄 Titel: {record.title}")
            console.print(f"📝 Zusammenfassung: {record.summary[:100]}...")
            console.print(f"🌍 Region: {record.region}")
            console.print(f"🏷️  Themen: {record.topics}")
        else:
            console.print("❌ AI-Extraktion fehlgeschlagen")
            
    except Exception as e:
        console.print(f"❌ Pipeline Test fehlgeschlagen: {e}")


async def main():
    """Hauptfunktion für AI-Tests"""
    console.print(Panel.fit(
        "🤖 AI Features Test",
        subtitle="LangChain + Ollama + Firecrawl",
        border_style="blue"
    ))
    
    # Teste alle Komponenten
    await test_firecrawl()
    await test_local_llm()
    await test_ai_agent()
    await test_full_pipeline()
    
    console.print("\n[bold green]🎉 AI Tests abgeschlossen![/bold green]")
    console.print("\n[bold cyan]Nächste Schritte:[/bold cyan]")
    console.print("1. Starte Ollama: ollama serve")
    console.print("2. Teste Scraping: python cli.py --ai --dry-run")
    console.print("3. Vollständiges Scraping: python cli.py --ai")


if __name__ == "__main__":
    asyncio.run(main())
