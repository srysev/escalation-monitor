# src/scoring.py
from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import json
from agno.agent import Agent
from agno.models.xai import xAI

try:
    from .feeds.base import to_iso_utc
except ImportError:
    from feeds.base import to_iso_utc


# LLM Model Configuration - change this to use a different model/provider
grok = xAI(
    id="grok-4-fast-reasoning-latest",
    search_parameters={
        "mode": "on",
        "max_search_results": 20,
        "return_citations": False,
    },
)
DEFAULT_LLM_MODEL = grok

class CriticalIndicator(BaseModel):
    category: str  # MILITARY|DIPLOMATIC|CYBER|ECONOMIC|SOCIAL
    description: str
    impact: float  # 0.0-2.0 Beitrag zum Score
    source: str
    confidence: str  # HIGH|MEDIUM|LOW

class EscalationScore(BaseModel):
    """Pydantic schema for escalation scoring results."""
    score: float = Field(..., ge=1.0, le=10.0, description="Eskalationsscore mit 1 Dezimalstelle")
    level: str = Field(..., description="BASELINE|FRICTION|TENSION|etc.")
    
    summary: str = Field(..., max_length=300, description="2-3 Sätze Haupttreiber")
    
    critical_indicators: List[CriticalIndicator] = Field(
        default_factory=list,
        max_length=5,
        description="Nur neue kritische Entwicklungen"
    )
    
    trend: str = Field(..., pattern="^(STABLE|ESCALATING|DE-ESCALATING)$")

def create_escalation_agent_with_data(rss_markdown: str) -> Agent:
    """Create agent with RSS data inserted into instructions."""

    role_description = """Du bist der Eskalationsgrad-Scorer für die DE-RU-Lage. Du analysierst aktuelle Ereignisse und ordnest sie auf einer 1-10 Skala ein und begründest sachlich."""

    # Instructions with RSS_DATA placeholder replaced
    instructions_template = """Nutze RSS Feeds als Input und ergänze via Websuche-Tool für Verifizierung.
    Diskussionskultur: Sprich in Wahrscheinlichkeiten, trenne Fakt von Interpretation, steelmane Gegenpositionen. Halte dich an CUDOS (offen teilen, quellenagnostisch, disinteressiert, skeptisch). Keine Alarmrhetorik.
Skala 1–10:
  1 – Normalbetrieb: Reguläre diplomatische Kanäle, keine Sonderwarnungen, Sanktionsstatus unverändert.
  2 – Friktionen: Schärfere Rhetorik, begrenzte Ausweisungen von Diplomaten; vereinzelte KRITIS-Vorfälle ohne Kaskaden.
  3 – Übungsnahe Spannung: Großmanöver an Grenzen, erhöhte Luftraum-Abfänge, punktuelle Cyber-Störungen (<1 KRITIS-Sektor >24 h).
  4 – Sanktionsdrehen: Erweiterte Listen, Exportkontrollen, Visarestriktionen; spürbare, aber umgehbare Reiserestriktionen.
  5 – Alarmiert: NATO/EU Warnstufen hoch, Verdichtung der Truppen an Ostflanke; deutliche Disruptionen (2 KRITIS-Sektoren ≤24 h).
  6 – Quasi-Konfrontation: Regelmäßige Cyber-Angriffe mit Ausfällen (≥2 Sektoren >24 h), Luft-/See-Zwischenfälle; Verstärkte Polizeiverfügungen ggü. Zielgruppen.
  7 – Akute Krise (vor-Kriegsphase): Teil-Mobilisierung/Verlegeoperationen sichtbar; Ein-/Ausreiserestriktionen selektiv; Finanzaufsicht setzt verschärfte Prüf-/Sicherungsmaßnahmen.
  8 – De-facto Feindseligkeiten: Anhaltende kinetische Vorfälle (Proxy/Artikel-4); Größere Reise-/Transport-Ausfälle, Bank-/Zahlungs-Störungen, erste Sammelverfügungen ggü. Risikogruppen.
  9 – Offener Konflikt: Dauerhafte Kampfhandlungen (mit/ohne offizieller Kriegserklärung); Kapitalverkehrs-Kontrollen, breite Visasuspension, systematische Kontensperren.
  10 – Kriegszustand/Internierung: Vollmobilisierung/Artikel-5-ähnlicher Zustand; Internierungen, Konfiskationen, Grenzschließungen, Zahlungsmoratorien.
RSS Feeds:
{RSS_DATA}
  """

    # Replace placeholder with actual RSS data
    instructions = instructions_template.replace("{RSS_DATA}", rss_markdown)

    agent = Agent(
        model=DEFAULT_LLM_MODEL,
        description=role_description,
        instructions=instructions,
        output_schema=EscalationScore,
        markdown=False
    )

    return agent


async def calculate_escalation_score(rss_markdown: str) -> Dict[str, Any]:
    """
    Calculate escalation score using Agno agent with RSS feed data.

    Args:
        rss_markdown: Markdown-formatted RSS feed results

    Returns:
        Dict with result, timestamp, and escalation data or error message
    """
    try:
        agent = create_escalation_agent_with_data(rss_markdown)

        # Simple neutral prompt since all instructions are already in the agent
        response = agent.run("")

        # Debug: Print raw response
        print(f"DEBUG - Raw response type: {type(response)}")
        print(f"DEBUG - Raw response: {response}")
        if hasattr(response, 'content'):
            print(f"DEBUG - Response content type: {type(response.content)}")
            print(f"DEBUG - Response content: {response.content}")

        # Extract escalation score from response
        if hasattr(response, 'content') and isinstance(response.content, EscalationScore):
            escalation_data = response.content.model_dump()
            return {
                "result": "ok",
                "timestamp": to_iso_utc(None),
                "escalation_score": escalation_data,
                "sources_analyzed": rss_markdown.count("###"),
                "items_processed": rss_markdown.count("**Articles:**") if "**Articles:**" in rss_markdown else 0
            }
        else:
            # Parsing failed - return error
            error_msg = f"Failed to parse agent response to EscalationScore format. Content type: {type(response.content) if hasattr(response, 'content') else 'no content'}"
            return {
                "result": "error",
                "timestamp": to_iso_utc(None),
                "error_message": error_msg,
                "sources_analyzed": rss_markdown.count("###"),
                "items_processed": rss_markdown.count("**Articles:**") if "**Articles:**" in rss_markdown else 0
            }

    except ImportError as e:
        return {
            "result": "error",
            "timestamp": to_iso_utc(None),
            "error_message": f"Agno library not available: {str(e)}",
            "sources_analyzed": 0,
            "items_processed": 0
        }
    except Exception as e:
        return {
            "result": "error",
            "timestamp": to_iso_utc(None),
            "error_message": f"Escalation scoring failed: {str(e)}",
            "sources_analyzed": rss_markdown.count("###") if rss_markdown else 0,
            "items_processed": rss_markdown.count("**Articles:**") if rss_markdown and "**Articles:**" in rss_markdown else 0
        }


async def main():
    """Test the escalation scoring functionality."""
    # Sample RSS markdown data for testing
    test_rss_data = """# Feed Processing Results

**Summary:** 2 successful, 0 failed

## Successful Feeds

### NATO
- **Items found:** 5
- **Last updated:** 2025-01-15T16:30:00Z

**Articles:**
1. **2025-01-15 14:30 UTC** - NATO increases readiness level for Eastern flank. Enhanced monitoring of Russian military movements near Baltic states.
   - Link: https://www.nato.int/cps/en/natohq/news_123456.htm

2. **2025-01-15 12:15 UTC** - Secretary General calls for unity in response to escalating tensions. Diplomatic channels remain open but strained.
   - Link: https://www.nato.int/cps/en/natohq/news_123457.htm

### Bundeswehr
- **Items found:** 3
- **Last updated:** 2025-01-15T16:30:00Z

**Articles:**
1. **2025-01-15 13:45 UTC** - German defense minister announces increased cyber security measures. New protocols for critical infrastructure protection.
   - Link: https://www.bundeswehr.de/news/123456
"""

    print("Testing escalation scoring...")
    result = await calculate_escalation_score(test_rss_data)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())