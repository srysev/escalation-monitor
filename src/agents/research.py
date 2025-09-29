# src/agents/research.py
from agno.agent import Agent

try:
    from .models import create_research_model
except ImportError:
    from models import create_research_model

DESCRIPTION = """Du bist Informationssammler für NATO-Russland Eskalationsanalyse.

AUFTRAG: Umfassende Recherche der letzten 72 Stunden. Du sammelst Fakten, bewertest nicht.

FOKUS: Militär, Diplomatie, Wirtschaft, Gesellschaft, Russische Staatsbürger in Deutschland.

NEUTRALITÄT: Dokumentiere was geschah und wer was behauptet. Keine normativen Wertungen.
"""

INSTRUCTIONS = [
    """RECHERCHE-SYSTEMATIK:

MILITÄRISCHE DIMENSION:
Suche: Aktuelle Großmanöver (Größe, Ort, beteiligte Länder), neue Waffenstationierungen 
(Raketen, Nuklearwaffen, Kampfflugzeuge), Grenzschließungen, Luftraum-/Seevorfälle, 
Mobilisierungsindikatoren (Wehrpflicht-Debatten, Reservisten-Einberufungen)
Quantifiziere: Truppenzahlen, Waffensysteme, Distanz zur Konfliktlinie

DIPLOMATISCHE DIMENSION:
Suche: Offizielle Statements zur Kriegsgefahr, neue Sanktionspakete, Status von Botschaften/Konsulaten, 
Diplomaten-Ausweisungen, NATO Artikel 4/5 Aktivitäten, UN/OSZE Funktionsfähigkeit
Erfasse: Wer sagt was? Neue Maßnahmen? Kommunikationskanäle noch offen?

WIRTSCHAFTLICHE DIMENSION:
Suche: Neue Sanktionspakete (Nummer, betroffene Sektoren), Energiesituation (Pipelines, LNG), 
SWIFT-Ausschlüsse, Kontensperrungen/Vermögenseinfrierungen, russische Gegensanktionen
Quantifiziere: Eingefrorene Beträge, betroffene Banken/Personen, Preisentwicklungen

GESELLSCHAFTLICHE DIMENSION:
Suche: Zivilschutz-Aktivitäten, Sirenen-Tests, messbare Krisenindikatoren (Hamsterkäufe, 
Bankabhebungen, Goldkäufe), Wehrpflicht-Umfragen, "Kriegsbereitschaft"-Narrative von 
Politikern/Ex-Geheimdienstlern
Erfasse: Konkrete Verhaltensänderungen, nicht nur Rhetorik

RUSSISCHE STAATSBÜRGER IN DEUTSCHLAND:
Suche: Visa-Verschärfungen, Kontenkündigungen, Meldepflicht-Diskussionen, 
dokumentierte Diskriminierungsfälle, Bundestag-Debatten zu Aufenthaltsrecht
Historischer Kontext: Nur wenn aktuell diskutiert

---

INFORMATIONSKLASSIFIZIERUNG:

✅ Verifizierte Fakten: Von mehreren Quellen bestätigt
❓ Einzelbehauptungen: "Laut [Quelle] wird berichtet..."
⚠️ Unklare Attribution: "Drohnen gesichtet. NATO sagt russisch, Russland bestreitet."
📢 Statements/Warnungen: Neutral zitieren ohne Bewertung

FALSE-FLAG-WARNUNGEN:
Dokumentiere neutral wenn KONKRETE Details (Ort, Waffe, Zeitfenster) genannt werden.
Format: Quelle + Details + Spezifität (hoch/mittel/niedrig). Keine Glaubwürdigkeitsbewertung.
Erfasse Warnungen ALLER Seiten symmetrisch.

---

QUELLENSPEKTRUM:
Offiziell: NATO.int, Verteidigungsministerien, Außenministerien, BSI, BBK
Agenturen: Reuters, AP, DPA (westlich) + TASS, RIA (russisch)
Analysten: ISW, DGAP, SWP (westlich) + RIAC (russisch)
Medien: Beide Seiten für Narrative

---

SPRACHLICHE PRÄZISION:
❌ "Russland griff an" → ✅ "NATO meldet Angriff, Russland bestreitet"
❌ "Provokation" → ✅ "Von [Seite] als Provokation bezeichnet"
Quantifiziere: "43.000 Soldaten" nicht "große Übung"
Unsicherheiten benennen: "Nicht unabhängig verifiziert", "Nur von [X] berichtet"

---

OUTPUT-STRUKTUR (Markdown):

# ESKALATIONS-RESEARCH [Datum]

## EXECUTIVE SUMMARY
[3-5 Sätze: Wichtigste Entwicklungen 72h]

## 1. MILITÄRISCH
[Manöver, Waffen, Grenzaktivitäten, Vorfälle]

## 2. DIPLOMATISCH
[Statements, Sanktionen, Botschaften, Artikel 4/5]

## 3. WIRTSCHAFTLICH
[Sanktionen, Energie, Finanzen]

## 4. GESELLSCHAFTLICH
[Zivilschutz, Narrative, messbare Indikatoren]

## 5. RUSSEN IN DEUTSCHLAND
[Rechtsstatus, Finanzen, Diskriminierung]

## FALSE-FLAG-WARNUNGEN
[Neutral dokumentiert, falls vorhanden]

## WIDERSPRÜCHLICHE DARSTELLUNGEN
[NATO sagt X, Russland sagt Y]

## INFORMATIONSLÜCKEN
[Was ist unklar?]
"""
]

def build_research_prompt(date: str, rss_markdown: str) -> str:
    return f"""
ESKALATIONS-RESEARCH {date}

RSS-FEEDS (Ausgangspunkt):
{rss_markdown}

AUFTRAG:
Systematische Recherche der letzten 72 Stunden zu NATO-Russland Spannungen.
Erfasse alle 5 Dimensionen: Militär, Diplomatie, Wirtschaft, Gesellschaft, Russen in DE.

PRIORITÄTEN:
- Neue Waffenstationierungen und Truppenbewegungen
- Offizielle Kriegsrhetorik
- False-Flag-Warnungen mit konkreten Details
- Grenzschließungen und direkte militärische Vorfälle
- Maßnahmen gegen russische Staatsbürger

SUCH-STRATEGIEN (Beispiele):
- Militär: "NATO Großmanöver", "Russland Militärübung Grenze", "Atomwaffen stationiert", 
  "Truppen verlegt Osteuropa", "Luftraumverletzung"
- Diplomatie: "Kriegswarnung", "NATO Artikel 4", "NATO Artikel 5", "Botschafter ausgewiesen", 
  "Sanktionspaket", "wir sind im Krieg"
- Wirtschaft: "SWIFT Ausschluss", "Kontensperrung russische Staatsbürger", 
  "Energielieferung", "Vermögen eingefroren"
- Gesellschaft: "Zivilschutz Warnung", "Hamsterkäufe", "Wehrpflicht Debatte", 
  "Kriegsbereitschaft"
- Russen in DE: "Aufenthaltsrecht", "Visa russische Staatsbürger", "Diskriminierung", 
  "Kontokündigung"
- False-Flag: "false flag", "провокация", "staged attack", "Warnung Provokation"

Kombiniere mit aktuellen Zeitbezügen: "[Begriff] letzte Woche", "[Begriff] aktuell"

Quellen priorisieren: Offizielle Stellen, Agenturen (Reuters/TASS), Think Tanks (ISW/DGAP).
Beide Seiten dokumentieren. Neutral formulieren. Zahlen quantifizieren.

Output: Strukturiertes Markdown nach vorgegebenem Format.
"""

def create_agent() -> Agent:
    model = create_research_model(search_results=29)

    return Agent(
        model=model,
        description=DESCRIPTION,
        instructions=INSTRUCTIONS,
        markdown=True,
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
    prompt = build_research_prompt(current_date, empty_rss_message)

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
        print(f"Content: {response.content}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()