# src/agents/research.py
import os
import logging

try:
    from .models import call_perplexity_api
except ImportError:
    from models import call_perplexity_api

logger = logging.getLogger(__name__)

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

RECHERCHE-METHODE:
Durchsuche offizielle Quellen, Agenturen und Think Tanks systematisch.
Prüfe BEIDE Seiten: NATO/EU-Perspektive UND russische Perspektive.

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

AUFTRAG:
Recherche der letzten 72h zu NATO-Russland Spannungen über 5 Dimensionen.

FOKUS-SIGNALE:
- Waffenstationierungen (nuklearfähig?)
- Kriegsrhetorik von Offiziellen
- False-Flag-Warnungen mit Details
- Grenzschließungen, militärische Vorfälle
- Maßnahmen gegen russische Staatsbürger

Dokumentiere BEIDE Seiten. Neutral formulieren. Zahlen nennen.

Output: Strukturiertes Markdown nach vorgegebenem Format.
"""

async def run_research(date: str, rss_markdown: str) -> str:
    """
    Run research agent using direct Perplexity API.

    Args:
        date: Current date string
        rss_markdown: RSS feed data in markdown format

    Returns:
        Research report in markdown format

    Raises:
        Exception: On API call failures
    """
    # Get domain filter from environment or use defaults
    domain_filter_str = os.getenv("PERPLEXITY_DOMAIN_FILTER", "")
    domain_filter = [d.strip() for d in domain_filter_str.split(",")] if domain_filter_str else [
        # Deutschland
        "tagesschau.de", "bmvg.de", "dgap.org", "swp-berlin.org",
        # NATO & International
        "europa.eu",
        # US & Think Tanks
        "rand.org", "understandingwar.org", "iiss.org",
        # Russland
        "mil.ru", "svr.gov.ru", "tass.ru",
        # Polen
        "mon.gov.pl", "wyborcza.pl",
        # Estland
        "kaitseministeerium.ee", "politsei.ee",
        # Ungarn
        "kormany.hu",
        # Baltikum & Nord
        "mod.gov.lv", "kam.lt", "regjeringen.no",
        # Agenturen
        "reuters.com"
    ]

    # Build messages
    system_content = DESCRIPTION + "\n\n" + "\n\n".join(INSTRUCTIONS)
    user_content = build_research_prompt(date, rss_markdown)

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]

    # Call Perplexity API
    model_id = os.getenv("PERPLEXITY_MODEL_ID", "sonar-pro")

    try:
        response = await call_perplexity_api(
            messages=messages,
            model=model_id,
            search_domain_filter=domain_filter,
            temperature=0.2,
            max_tokens=4000
        )

        logger.info(f"Perplexity API call successful. Usage: {response.get('usage', {})}")
        logger.debug(f"Citations: {len(response.get('citations', []))}")
        logger.debug(f"Search results: {len(response.get('search_results', []))}")

        return response["content"]

    except Exception as e:
        logger.error(f"Perplexity API call failed: {e}")
        raise

async def main():
    """Test the research agent with empty RSS data."""
    import asyncio
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