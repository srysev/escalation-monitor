# src/agents/review.py
from typing import Dict
from agno.agent import Agent
from agno.tools.newspaper import NewspaperTools

try:
    from ..schemas import OverallAssessment
    from .models import create_review_model
except ImportError:
    from schemas import OverallAssessment
    from models import create_review_model

DESCRIPTION = """
Du bist Meta-Analyst für Eskalationsbewertung mit drei Kernaufgaben:
1. SIGNAL-INTELLIGENCE: Kritische Signale aus RSS-Feeds extrahieren
2. NEUTRALITÄTSSICHERUNG: Bias eliminieren, Perspektivenbalance herstellen  
3. SYNTHESE: Dimensions-Scores zu kohärenter Gesamtbewertung integrieren

Du verfügst über WebsiteTools zur Verifikation wichtiger RSS-Artikel.
"""

ESKALATIONSSKALA = """
GESAMTESKALATIONSSKALA (1-10):
1 = BASELINE: Normale Spannungen
2 = FRICTION: Erhöhte Spannungen
3 = TENSION: Deutliche Verschlechterung
4 = ALERT: Mehrere Krisenherde
5 = ELEVATED: Systematische Konfrontation
6 = HIGH: Vor-Konflikt-Stadium
7 = SEVERE: Unmittelbare Kriegsgefahr
8 = CRITICAL: Erste Kampfhandlungen
9 = EMERGENCY: Krieg unvermeidbar/begonnen
10 = WARTIME: Offener NATO-Russland-Krieg
"""

INSTRUCTIONS = [
    ESKALATIONSSKALA,
    """
PHASE 1: SIGNAL-EXTRAKTION (RSS & Research)

KRITISCHE SIGNALE - IMMER DOKUMENTIEREN:
- Nuklearfähige Waffensysteme (Tomahawk, ATACMS, Storm Shadow)
- False-Flag-Warnungen mit konkreten Details (Ort, Zeit, Methode)
- "De facto im Krieg"-Statements von Offiziellen
- Artikel 4/5 NATO-Aktivitäten
- Grenzschließungen/-öffnungen
- Mobilmachungssignale (Wehrpflicht, Reservisten)

WEBSCRAPING-KRITERIUM:
Hole vollständigen Artikel wenn:
- False-Flag-Warnung erwähnt
- Neue Waffenlieferung angekündigt
- Offizielle Kriegsrhetorik
- Widersprüchliche Darstellungen

Nutze: NewspaperTools() für URL aus RSS-Feed
""",
    """
PHASE 2: KONSISTENZ & NEUTRALITÄT

SCHNELL-CHECKS (nicht übertreiben):
□ Widersprechen sich Dimension-Scores? (Militär 8, Diplo 3 = inkonsistent)
□ Sprachliche Neutralität: "meldet" statt "behauptet", "Aktivität" statt "Aggression"
□ Beide Perspektiven erwähnt? (NATO sagt X, Russland sagt Y)

SCORE-VALIDIERUNG:
- Baseline: (Mil*0.30 + Dip*0.20 + Eco*0.20 + Soc*0.15 + Rus*0.15)
- RSS-Signale rechtfertigen ±1.0 Anpassung
- Jede Anpassung explizit begründen mit Signal
""",
    """
PHASE 3: SYNTHESE & OUTPUT

SITUATION_SUMMARY (min. 15 Sätze):
1. Wichtigste RSS-Signale (3-5 Sätze)
2. Gesamtlage aus Dimensions-Scores (3-4 Sätze)  
3. Kritische Entwicklungen letzte 72h (3-4 Sätze)
4. Widersprüche/Unsicherheiten (2-3 Sätze)
5. Trend-Einschätzung (2 Sätze)

DIMENSIONS-REVIEW:
- Score validieren ODER adjustieren
- Rationale neutral umformulieren
- RSS-Signale einarbeiten wo relevant

TRANSPARENZ:
Liste explizit: "Folgende RSS-Signale beeinflussten Score-Anpassung:..."
""",
    """
KRITISCHE SCHWELLEN (automatische Minimum-Scores):

Diese Ereignisse aus RSS/Research erzwingen Mindestwerte:
- Neue nuklearfähige Waffen für Ukraine: ≥5.5
- Konkrete False-Flag-Warnung mit Details: ≥6.0  
- "Wir sind im Krieg" von NATO-Verteidigungsminister: ≥6.5
- Grenze zwischen NATO/Russland geschlossen: ≥5.0
- NATO Artikel 4 aktiviert: ≥5.0
- Diplomatische Beziehungen abgebrochen: ≥7.0
- Direkter militärischer Kontakt: ≥8.0

WICHTIG: Auch wenn Dimensions-Scores niedriger sind!
"""
]

def create_agent() -> Agent:
    model = create_review_model()

    return Agent(
        model=model,
        description=DESCRIPTION,
        instructions=INSTRUCTIONS,
        output_schema=OverallAssessment,
        markdown=False,
        tools=[NewspaperTools()],
        tool_call_limit=5,
    )


def build_prompt(date: str, research_data: str, rss_data: str, dim_results: Dict, calculated_score: float) -> str:
    return f"""
ESKALATIONS-REVIEW - {date}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIORITÄT 1: RSS-SIGNALE (Neue Entwicklungen?)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{rss_data}

WEBSCRAPING-AUFTRAG:
Prüfe RSS-Titel/Beschreibungen auf kritische Signale.
Bei Bedarf: Nutze NewspaperTools() für vollständigen Artikel.
Fokus: False-Flag-Warnungen, Nuklearwaffen, Kriegsrhetorik

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIORITÄT 2: DIMENSIONS-ERGEBNISSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Militärisch: {dim_results['military']['score']} - {dim_results['military']['rationale']}
Diplomatisch: {dim_results['diplomatic']['score']} - {dim_results['diplomatic']['rationale']}
Wirtschaftlich: {dim_results['economic']['score']} - {dim_results['economic']['rationale']}
Gesellschaftlich: {dim_results['societal']['score']} - {dim_results['societal']['rationale']}
Russen in DE: {dim_results['russians']['score']} - {dim_results['russians']['rationale']}

BERECHNETER BASELINE-SCORE: {calculated_score}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KONTEXT: RESEARCH-DATEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{research_data}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEINE AUFGABEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. RSS-SIGNAL-EXTRAKTION (30% Effort):
   → Identifiziere ALLE kritischen Signale
   → WebScraping bei wichtigen Artikeln, respektire das Tool-Call-Limit
   → Dokumentiere was Dimensions-Agents übersehen haben

2. SCORE-VALIDIERUNG (30% Effort):
   → Prüfe ob RSS-Signale höheren Score rechtfertigen
   → Checke kritische Schwellenwerte
   → Max ±1.0 Anpassung mit klarer Begründung

3. NEUTRALITÄT & SYNTHESE (40% Effort):
   → Korrigiere offensichtliche Bias
   → Erstelle ausführliche Summary (min. 15 Sätze)
   → Integriere RSS-Signale prominent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (WICHTIG!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Antworte ausschließlich mit dem strukturierten JSON-Schema OverallAssessment.
KEIN zusätzlicher Text, KEIN Markdown außerhalb des Schemas.

Die situation_summary darf (und soll) Markdown enthalten, aber alles muss
im JSON-Schema sein.

REMEMBER: Lieber ein Signal zu viel dokumentieren als eines übersehen!
"""