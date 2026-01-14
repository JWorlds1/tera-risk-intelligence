#!/usr/bin/env python3
"""
Beispiel: Integration des LangChain Agent Builder Prompts
Zeigt wie der Prompt in einen bestehenden Agent integriert wird
"""
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from pathlib import Path

# Lade den System-Prompt
def load_system_prompt() -> str:
    """Lade den System-Prompt aus der Markdown-Datei"""
    prompt_file = Path(__file__).parent.parent / "LANGCHAIN_AGENT_PROMPT.md"
    
    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extrahiere den System-Prompt (zwischen ```markdown und ```)
            start_marker = "```markdown"
            end_marker = "```"
            
            start_idx = content.find(start_marker)
            if start_idx != -1:
                start_idx += len(start_marker)
                end_idx = content.find(end_marker, start_idx)
                if end_idx != -1:
                    return content[start_idx:end_idx].strip()
    
    # Fallback: Basis-Prompt
    return """
Du bist ein intelligenter Agent für das Geospatial Intelligence System für Climate Conflict Analysis.
Hilf Benutzern dabei, Daten zu sammeln, zu analysieren und zu visualisieren.
"""


# Beispiel-Tools für den Agent
def create_geospatial_tools():
    """Erstelle Tools für Geospatial Intelligence Agent"""
    
    def check_frontend_data():
        """Prüft ob Frontend-Daten vorhanden sind"""
        frontend_dir = Path("./data/frontend")
        required_files = [
            "complete_data.json",
            "map_data.geojson",
            "early_warning.json",
            "adaptation_recommendations.json"
        ]
        
        existing = []
        missing = []
        
        for filename in required_files:
            if (frontend_dir / filename).exists():
                existing.append(filename)
            else:
                missing.append(filename)
        
        if missing:
            return f"Fehlende Dateien: {', '.join(missing)}. Führe 'generate_frontend_data.py' aus."
        else:
            return f"✅ Alle Frontend-Dateien vorhanden: {', '.join(existing)}"
    
    def get_location_info(location_name: str):
        """Holt Informationen über eine Location"""
        try:
            import json
            complete_file = Path("./data/frontend/complete_data.json")
            
            if not complete_file.exists():
                return "Frontend-Daten nicht gefunden. Führe generate_frontend_data.py aus."
            
            with open(complete_file, 'r') as f:
                data = json.load(f)
            
            # Suche Location
            for loc in data.get('locations', []):
                if location_name.lower() in loc.get('location_name', '').lower():
                    return f"""
Location: {loc['location_name']} ({loc['country_code']})
Risiko-Level: {loc['risk_level']} (Score: {loc['risk_score']:.2f})
Urgency: {loc['urgency_score']:.2f}
Warnungen: {loc['early_warning']['total_signals']}
Empfehlungen: {len(loc['adaptation_recommendations'])}
"""
            
            return f"Location '{location_name}' nicht gefunden."
        except Exception as e:
            return f"Fehler: {e}"
    
    def list_critical_regions():
        """Listet kritische Regionen auf"""
        try:
            import json
            complete_file = Path("./data/frontend/complete_data.json")
            
            if not complete_file.exists():
                return "Frontend-Daten nicht gefunden."
            
            with open(complete_file, 'r') as f:
                data = json.load(f)
            
            critical = [
                loc for loc in data.get('locations', [])
                if loc.get('risk_level') in ['CRITICAL', 'HIGH']
            ]
            
            if not critical:
                return "Keine kritischen Regionen gefunden."
            
            result = "Kritische Regionen:\n"
            for loc in sorted(critical, key=lambda x: x.get('risk_score', 0), reverse=True)[:10]:
                result += f"- {loc['location_name']} ({loc['country_code']}): {loc['risk_level']} (Score: {loc['risk_score']:.2f})\n"
            
            return result
        except Exception as e:
            return f"Fehler: {e}"
    
    return [
        Tool(
            name="check_frontend_data",
            description="Prüft ob Frontend-Daten vorhanden sind",
            func=check_frontend_data
        ),
        Tool(
            name="get_location_info",
            description="Holt detaillierte Informationen über eine Location (z.B. 'Mumbai', 'India')",
            func=get_location_info
        ),
        Tool(
            name="list_critical_regions",
            description="Listet kritische Regionen mit hohem Risiko auf",
            func=list_critical_regions
        )
    ]


class GeospatialIntelligenceAgent:
    """LangChain Agent für Geospatial Intelligence System"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        # Initialisiere LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY nicht gesetzt!")
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            openai_api_key=api_key
        )
        
        # Lade System-Prompt
        self.system_prompt = load_system_prompt()
        
        # Erstelle Tools
        self.tools = create_geospatial_tools()
        
        # Erstelle Prompt Template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Erstelle Agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def run(self, query: str):
        """Führe eine Query aus"""
        try:
            result = self.agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"Fehler: {e}"


# Beispiel-Verwendung
if __name__ == "__main__":
    print("🤖 Geospatial Intelligence Agent - Beispiel")
    print("=" * 60)
    
    # Erstelle Agent
    try:
        agent = GeospatialIntelligenceAgent()
        
        # Beispiel-Queries
        queries = [
            "Prüfe ob Frontend-Daten vorhanden sind",
            "Zeige mir kritische Regionen",
            "Gib mir Informationen über Mumbai",
            "Wie generiere ich Frontend-Daten?"
        ]
        
        for query in queries:
            print(f"\n❓ Query: {query}")
            print("-" * 60)
            response = agent.run(query)
            print(f"✅ Antwort: {response}")
            print()
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        print("\nStelle sicher dass:")
        print("1. OPENAI_API_KEY gesetzt ist")
        print("2. langchain_openai installiert ist: pip install langchain-openai")
        print("3. Frontend-Daten generiert wurden: python backend/generate_frontend_data.py")

