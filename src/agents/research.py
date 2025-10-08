# src/agents/research.py
import logging

logger = logging.getLogger(__name__)

DESCRIPTION = """
  Du bist Informationssammler für NATO-Russland-Eskalationsanalyse.

  AUFTRAG: Erstelle einen STATUS-BERICHT zum aktuellen IST-Zustand (kein Verlauf). Du nutzt ausschließlich Informationen, die innerhalb der letzten 30 Tage belegt sind. Falls keine frische Quelle
  existiert, markiere klar: „Kein aktuelles Update gefunden – letzter belegbarer Stand: <Datum> (Quelle)“.

  Jede Aussage muss Quelle + Datum + Link besitzen. Keine Annahmen, keine Rückgriffe auf ältere Berichte, keine Erfahrungswerte ohne Nachweis.

  FOKUS: Militär, Diplomatie, Wirtschaft, Gesellschaft, Russische Staatsbürger in Deutschland.
  """

INSTRUCTIONS = [
      """AKTUELLER STATUS – 5 Dimensionen (Stand ≤30 Tage)

  Vor jedem Dimensionsteil:

  PFLICHTREGELN:
  - Nur Informationen mit Quelle ≤30 Tage verwenden.
  - Fehlt eine frische Quelle: „Kein aktuelles Update gefunden – letzter belegbarer Stand: <Datum> (Quelle)“.
  - Jeder Status-Punkt muss enthalten:
    📍 THEMA
    STATUS: [präzise Beschreibung, keine Zahlen ohne Quelle]
    Quelle: [Medium, YYYY-MM-DD, URL]
    🔹 Westliche Darstellung: …
    🔹 Russische Darstellung: … (oder „Keine Stellungnahme gefunden – geprüft am YYYY-MM-DD mit Suchbegriffen <…>“)
    ⚠️ Bewertung: [Beide bestätigen / Widerspruch / Nur einseitig berichtet / Kein aktuelles Update]
    Stand: YYYY-MM-DD (Datum des Sachstands oder „kein aktuelles Update“)

  Für alle fünf Dimensionen (Militär, Diplomatie, Wirtschaft, Gesellschaft, Russen in DE) die wichtigsten Status-Punkte aufnehmen. Keine Beispiele aus früheren Berichten übernehmen.
  """,
      """ANTI-BIAS-PROTOKOLL (ZWINGEND)

  Problem: Websuche priorisiert westliche Perspektiven.

  Suchstrategie für jeden Status-Punkt:
  1. Westliche Quelle recherchieren (Zeitfilter ≤30 Tage: z. B. „<Thema> site:.de 2025“ oder „<Thema> last 7 days“).
  2. Russische Gegendarstellung aktiv suchen (deutsch/englisch/russisch, z. B. „Российская позиция <Thema> 2025“, „Russian MoD statement <topic> October 2025“).
  3. Osteuropäische Perspektive prüfen (Polen, Baltikum, Rumänien, Ukraine; Zeitfilter ≤30 Tage).
  4. Wenn nach gründlicher Suche keine Gegenseite gefunden wird, klar dokumentieren: „Keine Stellungnahme gefunden – geprüft am YYYY-MM-DD mit Suchbegriffe <…>“.

  Formulierungsregeln:
  - IMMER attributiv: „Laut [Quelle] …“.
  - Zahlen nur mit konkreter Quelle + Datum.
  - Unterschiede nicht glätten: Widersprüche benennen („⚠️ Widerspruch: NATO sagt X, Russland sagt Y“).
  - Keine Übernahme von Platzhalterbeispielen oder alten Default-Werten.
  """,
      """OUTPUT-FORMAT & SIGNALE

  Ausgabe-Struktur:

  # ESKALATIONS-STATUS <Datum>

  ## 1. MILITÄR – Aktueller Stand
  (je Status-Punkt nach obigem Schema)

  ## 2. DIPLOMATIE – Aktueller Stand
  - Enthält Pflichtpunkt „Spannungsfall (GG Art. 80a) / Verteidigungsfall (GG Art. 115a) – Status prüfen“

  ## 3. WIRTSCHAFT – Aktueller Stand
  ## 4. GESELLSCHAFT – Aktueller Stand
  ## 5. RUSSEN IN DE – Aktueller Stand

  ## KRITISCHE SIGNALE – Aktuelle Lage
  - Pflichtthemen: Nuklearfähige Waffen-Diskussionen, NATO Artikel 4/5, Grenzschließungen, militärische Vorfälle, Spannungsfall/Verteidigungsfall.
  - Für jedes Signal: gleiches Schema (STATUS, Quelle, Darstellungen, Bewertung, Stand).

  ## QUELLENABDECKUNG
  | Perspektive | Quelle | Datum | Link | Relevanz |
  Pflicht: Deutsch/West, Russisch, Osteuropa. Fehlende Perspektive => „⚠️ Nicht abgedeckt – erneute Recherche erforderlich“.

  WARNHINWEIS:
  - Keine aktuelle Quelle → explizit benennen und als Blind Spot führen.
  - Keine zusätzlichen Kommentare außerhalb der Struktur.
  """
  ]


def build_research_prompt(date: str, rss_markdown: str) -> str:
    return f"""
  ESKALATIONS-STATUS {date}

  AUFTRAG:
  Erstelle den aktuellen STATUS-BERICHT zu NATO–Russland-Spannungen in fünf Dimensionen. Nutze nur Informationen, die mit Quellen (Datum ≤30 Tage) belegt sind. Fehlt ein Update, kennzeichne es offen.

  HINWEISE:
  - Jede Aussage benötigt Quelle + Datum + Link.
  - Kein Rückgriff auf ältere Beispielzahlen oder Vorwissen ohne frische Bestätigung.
  - Dokumentiere fehlende Gegendarstellungen oder veraltete Daten als „Kein aktuelles Update“ + Blind Spot.
  - Suche aktiv nach russischen und osteuropäischen Perspektiven.

  RSS-KONTEXT (zur Orientierung):
  {rss_markdown}
  """


async def run_research(date: str, rss_markdown: str) -> str:
    """
    Run research agent using Grok/xAI with web search.

    Args:
        date: Current date string
        rss_markdown: RSS feed data in markdown format

    Returns:
        Research report in markdown format

    Raises:
        Exception: On agent execution failures
    """
    from agno.agent import Agent
    try:
        from .models import create_research_model
    except ImportError:
        from models import create_research_model

    # Build user prompt
    user_prompt = build_research_prompt(date, rss_markdown)

    # Create Grok model with extended search
    model = create_research_model(
        search_results=20,
        sources=[
            {"type": "web"},
            {"type": "x"},
            {"type": "news"}
        ]
    )

    # Create agent with description and instructions
    agent = Agent(
        model=model,
        description=DESCRIPTION,
        instructions=INSTRUCTIONS,
        markdown=True
    )

    try:
        # Run agent with user prompt
        run_response = agent.run(user_prompt)

        logger.info(f"Research agent completed successfully")

        # Extract content from Agno response
        return run_response.content

    except Exception as e:
        logger.error(f"Research agent failed: {e}")
        raise

async def main():
    """Test the research agent with empty RSS data."""
    from datetime import datetime
    import time

    # Test with empty RSS message
    current_date = datetime.now().strftime("%Y-%m-%d")
    empty_rss_message = "RSS-Feeds konnten nicht geladen werden und werden daher ignoriert."

    print(f"Research Agent Test - {current_date}")
    print(f"Testing with empty RSS data...")
    print("\n" + "="*50)

    try:
        # Execute agent and measure time
        print(f"🚀 Starting research agent...")
        start_time = time.time()
        content = await run_research(current_date, empty_rss_message)
        end_time = time.time()
        execution_time = end_time - start_time

        print(f"\n✅ Research completed:")
        print(f"⏱️ Execution time: {execution_time:.1f} seconds")
        print(f"\nContent:\n{content}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())