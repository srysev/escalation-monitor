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
    """RECHERCHE-SCHWERPUNKTE (letzte 72h):

1. MILITÄR: Manöver, Waffenstationierungen (nuklearfähig?), Grenzaktivitäten, Mobilisierung
2. DIPLOMATIE: Kriegsrhetorik, Sanktionen, Artikel 4/5, Botschaftsstatus, Diplomaten-Ausweisungen
3. WIRTSCHAFT: Sanktionspakete, SWIFT, Kontensperrungen, Energielieferungen
4. GESELLSCHAFT: Zivilschutz, Hamsterkäufe, Wehrpflicht-Debatten
5. RUSSEN IN DE: Visa, Kontokündigungen, Diskriminierung, Bundestag-Debatten

KRITISCHE SIGNALE (immer dokumentieren):
- False-Flag-Warnungen mit konkreten Details (Ort, Zeit, Methode)
- Nuklearfähige Waffen (Tomahawk, ATACMS, Hyperschall)
- NATO Artikel 4/5 Aktivitäten
- Grenzschließungen
- Direkte militärische Vorfälle

QUELLENPRIORITÄT:
Offizielle Stellen (NATO.int, Ministerien) > Agenturen (Reuters, TASS) > Think Tanks (ISW, DGAP)

SPRACHLICHE PRÄZISION:
- Neutral formulieren: "NATO meldet X, Russland bestreitet" statt "X geschah"
- Quantifizieren: "43.000 Soldaten" statt "große Übung"
- Attribution: "Laut [Quelle]..." bei Einzelmeldungen

OUTPUT-STRUKTUR:

# ESKALATIONS-RESEARCH [Datum]

## 1. MILITÄR
[Manöver, Waffen, Vorfälle mit Zahlen]

## 2. DIPLOMATIE
[Statements, Sanktionen, Botschaften]

## 3. WIRTSCHAFT
[Sanktionen, Energie, Finanzen]

## 4. GESELLSCHAFT
[Zivilschutz, Narrative]

## 5. RUSSEN IN DE
[Rechtsstatus, Diskriminierung]

## KRITISCHE SIGNALE
[False-Flags, Widersprüche, Unsicherheiten]
"""
]

def build_research_prompt(date: str, rss_markdown: str) -> str:
    return f"""
ESKALATIONS-RESEARCH {date}

RSS-FEEDS (Ausgangspunkt):
{rss_markdown}

AUFTRAG:
Recherche der letzten 72h zu NATO-Russland Spannungen über 5 Dimensionen.

FOKUS-SIGNALE:
- Waffenstationierungen (nuklearfähig?)
- Kriegsrhetorik von Offiziellen
- False-Flag-Warnungen mit Details
- Grenzschließungen, militärische Vorfälle
- Maßnahmen gegen russische Staatsbürger

Quellen: Offizielle Stellen > Agenturen (Reuters/TASS) > Think Tanks (ISW/DGAP)
Beide Seiten dokumentieren. Neutral formulieren. Zahlen nennen.

Output: Strukturiertes Markdown nach vorgegebenem Format.
"""

def create_agent() -> Agent:
    model = create_research_model(search_results=10)
    from agno.models.perplexity import Perplexity

    return Agent(
        model=Perplexity(id="sonar-pro", max_tokens=4000, temperature=0),
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