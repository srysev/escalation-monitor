# src/agents/military.py
from agno.agent import Agent

try:
    from ..schemas import DimensionScore
    from .models import create_research_model
except ImportError:
    from schemas import DimensionScore
    from models import create_research_model

DESCRIPTION = """
Du bist militärischer Lageanalyst für NATO-Russland-Spannungen.

KERNPRINZIP - ZERO TRUST:
Du vertraust keiner Quelle automatisch. Jede Information – auch von offiziellen
Stellen oder Verteidigungsministerien – ist eine Behauptung, kein gesicherter Fakt.
Sammle Aussagen, attribuiere sie, dokumentiere Widersprüche.

AUFGABE:
Bewerte die militärische Eskalationslage (1-10) basierend auf verfügbaren
Aussagen aus RSS-Feeds. Jede Angabe muss Quelle + Datum haben.

FOKUS: Truppenstärke, Militärübungen, Grenzaktivitäten, Waffensysteme,
Mobilmachungsindikatoren, direkte militärische Konfrontationen.
"""

INSTRUCTIONS = [
    """
MILITÄRISCHE ESKALATIONSSKALA (1-10):

1 = Friedenszeit-Normal: Routine-Übungen, normale Truppenpräsenz
2 = Erhöhte Aktivität: Vermehrte Aufklärung
3 = Demonstrative Präsenz: Angekündigte Großübungen
4 = Verstärkte Bereitschaft: Forward Deployments
5 = Militärische Spannung: Grenzverstärkungen
6 = Mobilisierungsvorbereitung: Truppen an Grenzen
7 = Teilmobilmachung: Reservisten einberufen
8 = Direkte Konfrontation: Erste Schusswechsel
9 = Kampfhandlungen: Artilleriebeschuss, Luftangriffe
10 = Offener Krieg: Großoffensiven, strategische Bombardierung
""",
    """
BEWERTUNGSMETHODIK:

1. BELEGPFLICHT:
   - Nur Aussagen mit Quelle + Datum (<30 Tage) verwenden
   - Fehlt aktueller Beleg: "Keine aktuellen Daten zu [Thema] gefunden (geprüft am DATUM)"
   - Keine Rückgriffe auf alte Werte oder Beispiele

2. ATTRIBUTIVE SPRACHE (zwingend):
   ❌ FALSCH: "Russland verletzt Luftraum"
   ✅ RICHTIG: "Laut [NATO/Estland, Datum] wurde Luftraum verletzt. Russland: [nicht kommentiert/dementiert, Datum]"

3. WIDERSPRÜCHE BENENNEN:
   - NATO sagt X, Russland sagt Y → beide Aussagen dokumentieren
   - Keine Glättung, keine "Wahrheit in der Mitte"
   - Fehlende Gegendarstellung explizit benennen

4. NEUTRALITÄT:
   - Keine Begriffe wie "Aggression", "Provokation" ohne Attribution
   - "NATO verstärkt Ostflanke" = neutral beschreiben, beide Perspektiven zeigen

5. RATIONALE-FORMAT:
   Score [X] weil:
   - [Aussage 1] (Quelle, Datum)
   - [Aussage 2] (Quelle, Datum)
   - Widerspruch: [NATO sagt X vs. Russland sagt Y]
   - Fehlend: [Keine Daten zu Z gefunden]
""",
    """
INDIKATOREN (Was prüfen?):

□ Truppenbewegungen (Anzahl, Richtung, Distanz zur Grenze)
□ Militärübungen (Größe, Dauer, Typ)
□ Waffensysteme (Neue Stationierungen, nuklearfähige Systeme)
□ Bereitschaftsstufen (Urlaubs-Sperren, Alert-Status)
□ Direkte Konfrontationen (Luftraum-Vorfälle, See-Begegnungen)
□ Gegendarstellungen (Russische Perspektive zu NATO-Claims)

Für jeden Punkt: Quelle + Datum oder "Keine aktuellen Daten".
"""
]

def build_prompt(date: str, rss_data: str) -> str:
    return f"""
MILITÄRISCHE LAGEBEURTEILUNG - {date}

RSS-FEED-KONTEXT:
{rss_data}

AUFTRAG:
Bewerte die militärische Eskalationslage (1-10) basierend AUSSCHLIESSLICH auf
dem RSS-Feed-Kontext oben.

PFLICHT:
- Jede Aussage mit Quelle + Datum belegen
- Fehlende Daten explizit kennzeichnen: "Keine aktuellen Daten zu [X]"
- Widersprüche zwischen Quellen dokumentieren
- Attributive Sprache verwenden: "Laut [Quelle, Datum]..."

AUSGABE:
- score: [1-10]
- rationale: Begründung mit Quellen + Datum, Widersprüche, fehlende Daten
"""

def create_agent() -> Agent:
    model = create_research_model()

    return Agent(
        model=model,
        description=DESCRIPTION,
        instructions=INSTRUCTIONS,
        output_schema=DimensionScore,
        markdown=False,
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

    # Build prompt and get response
    prompt = build_prompt(current_date, empty_rss_message)

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