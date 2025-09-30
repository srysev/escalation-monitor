# src/agents/military.py
from agno.agent import Agent
from agno.tools.newspaper import NewspaperTools

try:
    from ..schemas import DimensionScore
    from .models import create_research_model
except ImportError:
    from schemas import DimensionScore
    from models import create_research_model

DESCRIPTION = """
Du bist ein militärischer Lageanalyst spezialisiert auf NATO-Russland Militärdynamiken.
Deine Aufgabe ist die objektive Bewertung der GESAMTEN aktuellen militärischen
Eskalationslage, nicht nur der letzten Ereignisse.

FOKUS: Truppenstärke, Militärübungen, Grenzaktivitäten, Waffensysteme,
Mobilmachungsindikatoren, direkte militärische Konfrontationen.
"""

INSTRUCTIONS = [
    """
MILITÄRISCHE ESKALATIONSSKALA (1-10):

1 = Friedenszeit-Normal: Routine-Übungen, normale Truppenpräsenz
2 = Erhöhte Aktivität: Vermehrte Aufklärung, kleine Übungen
3 = Demonstrative Präsenz: Angekündigte Großübungen (10.000+ Truppen)
4 = Verstärkte Bereitschaft: Verlängerte Übungen, Forward Deployments
5 = Militärische Spannung: Enhanced Vigilance, erste Grenzverstärkungen
6 = Mobilisierungsvorbereitung: Truppen an Grenzen, Reservisten-Diskussion
7 = Teilmobilmachung: Reservisten einberufen, Response Forces aktiviert
8 = Direkte Konfrontation: Erste Schusswechsel, Luftraumverletzungen mit Abschüssen
9 = Kampfhandlungen: Artilleriebeschuss, Luftangriffe, Bodenkämpfe
10 = Offener Krieg: Großoffensiven, strategische Bombardierung
""",
    """
INDIKATOREN ZUR BEWERTUNG:

TRUPPENBEWEGUNGEN:
- Anzahl und Größe laufender Militärübungen
- Distanz zur NATO-Russland-Grenze
- Verlegung vs. Rotation (permanent vs. temporär)
- Beteiligung von Nuklearstreitkräften

WAFFENSYSTEME:
- Stationierung neuer Systeme
- Nuklearfähige Systeme in Grenznähe
- Raketenabwehr-Aktivierungen
- Hyperschallwaffen-Deployments

READINESS-INDIKATOREN:
- DEFCON/Gefechtsbereitschaft-Stufen
- Urlaubs-Sperren
- Munitions-/Treibstoff-Vorverlegung
- Feldlazarette/Blutkonserven

DIREKTE KONFRONTATION:
- See-/Luftraum-"Begegnungen"
- Warning Shots / Abfangmanöver
- Elektronische Kriegsführung aktiv
- GPS-Jamming Vorfälle
""",
"""
BEWERTUNGSMETHODIK:

1. Erfasse GESAMTBILD, nicht nur Schlagzeilen
2. Zähle konkrete militärische Assets und Aktivitäten
3. Gewichte dauerhafte Stationierungen höher als Übungen
4. Beachte Eskalations-GESCHWINDIGKEIT (langsam vs. rapid)
5. Unterscheide Rhetorik von tatsächlichen Deployments

NEUTRALITÄT:
- "NATO verstärkt Ostflanke" = "Russland sieht Bedrohung"
- Beide Seiten haben Sicherheitsinteressen
- Keine Zuschreibung von Aggressionsabsichten
"""
]

def build_prompt(date: str, research_data: str, rss_data: str) -> str:
    return f"""
MILITÄRISCHE LAGEBEURTEILUNG - {date}

ZENTRALE RESEARCH-ERGEBNISSE:
{research_data}

RSS-FEEDS (Offizielle Perspektiven und ergänzende Quellen):
{rss_data}

AUFTRAG:
Bewerte die GESAMTE aktuelle militärische Lage zwischen NATO und Russland.
Dies ist eine Baseline-Bewertung, nicht nur eine Analyse der letzten Tage.

1. Recherchiere den aktuellen Stand militärischer Aktivitäten beider Seiten
2. Erfasse dauerhafte Stationierungen UND temporäre Übungen
3. Identifiziere Eskalations- oder Deeskalationstrends und Waffenlieferungen
4. Bewerte gegen die Skala 1-10 basierend auf KONKRETEN militärischen Fakten

Gib einen Score und eine neutrale Begründung.
"""

def create_agent() -> Agent:
    model = create_research_model()

    return Agent(
        model=model,
        description=DESCRIPTION,
        instructions=INSTRUCTIONS,
        output_schema=DimensionScore,
        markdown=False,
        tools=[NewspaperTools()],
        tool_call_limit=5,
    )

def main():
    """Test the military agent with empty RSS data."""
    from datetime import datetime
    import time

    # Create agent
    agent = create_agent()

    # Test with empty RSS message
    current_date = datetime.now().strftime("%Y-%m-%d")
    empty_rss_message = "RSS-Feeds konnten nicht geladen werden und werden daher ignoriert."
    empty_research_message = "Research-Daten nicht verfügbar."

    # Build prompt and get response
    prompt = build_prompt(current_date, empty_research_message, empty_rss_message)

    print(f"Military Agent Test - {current_date}")
    print(f"Testing with empty RSS data...")
    print("\n" + "="*50)

    try:
        # Execute agent and measure time
        print(f"🚀 Starting agent execution...")
        start_time = time.time()
        response = agent.run(prompt)
        end_time = time.time()
        execution_time = end_time - start_time

        print(f"\n✅ Agent Response:")
        print(f"⏱️ Execution time: {execution_time:.1f} seconds")
        print(f"Response: {response}")
        print(f"isinstance(response.content, DimensionScore): {isinstance(response.content, DimensionScore)}")
        print(f"Content: {response.content}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()