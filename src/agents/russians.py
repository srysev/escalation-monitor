# src/agents/russians.py
from agno.agent import Agent
from agno.tools.newspaper import NewspaperTools

try:
    from ..schemas import DimensionScore
    from .models import create_research_model
except ImportError:
    from schemas import DimensionScore
    from models import create_research_model

DESCRIPTION = """
Du bist ein Spezialist für die Situation russischer Staatsbürger in Deutschland.
Deine Aufgabe ist die Bewertung ALLER Risiken und Einschränkungen, denen
russische Staatsbürger in Deutschland aktuell ausgesetzt sind oder sein könnten.

FOKUS: Rechtsstatus, Finanzzugang, Diskriminierung, Reisefreiheit,
historische Präzedenzfälle, behördliche Maßnahmen.
"""

INSTRUCTIONS = [
    """
ESKALATIONSSKALA FÜR RUSSEN IN DEUTSCHLAND (1-10):

1 = Keine Einschränkungen: Vollständige Gleichbehandlung
2 = Bürokratische Hürden: Längere Visa-Verfahren, mehr Nachweise
3 = Finanzielle Erschwernis: Kontoeröffnung schwieriger, mehr Prüfungen
4 = Soziale Diskriminierung: Einzelne Kündigungen, Ablehnung im Alltag
5 = Systematische Nachteile: Bank-Kündigungen, Meldepflicht diskutiert
6 = Rechtliche Einschränkungen: Reisebeschränkungen, Registrierungspflicht
7 = Aktive Überwachung: Bewegungseinschränkungen, Kontensperrungen
8 = Vorbereitung Internierung: Lager identifiziert, Vermögen eingefroren
9 = Deportation/Internierung: Erste Verhaftungen, Sammellager aktiv
10 = Vollständige Entrechtung: "Enemy Alien" Status, totale Internierung
""",
    """
RECHTSSTATUS-INDIKATOREN:

AUFENTHALTSRECHT:
- Niederlassungserlaubnis: Sicher oder gefährdet?
- Neue Visa: Noch möglich? Ablehnungsquote?
- Einbürgerungen: Gestoppt oder verzögert?
- Familiennachzug: Noch erlaubt?
- Arbeitserlaubnis: Einschränkungen?

MELDEWESEN:
- Registrierungspflichten (neue Auflagen?)
- Adressänderungen (Genehmigung nötig?)
- Ausreise (Erlaubnis erforderlich?)
- Grenzkontrollen (besondere Prüfung?)

HISTORISCHE PRÄZEDENZFÄLLE:
- WK1: Ruhleben-Lager (4.273 Briten interniert)
- WK2: US-Japaner (110.000 interniert)
- Recherchiere aktuelle Diskussionen dazu
- "Enemy Alien Act" - Diskutiert in EU?
""",
    """
FINANZIELLE DIMENSION:

BANKING:
- Kontokündigungen (welche Banken?)
- Neue Konten (noch möglich wo?)
- Überweisungen nach/aus Russland
- Kreditkarten (Visa/Mastercard?)
- Vermögenseinfrierungen (ab welcher Summe?)

DISKRIMINIERUNGS-MONITORING:

DOKUMENTIERTE FÄLLE:
- Wohnungskündigungen
- Arbeitgeber-Diskriminierung
- Schulen/Kitas (Kinder betroffen?)
- Gesundheitswesen (Behandlung verweigert?)
- Polizei-Schikanen

HISTORISCHE PRÄZEDENZFÄLLE:
- WK1: Ruhleben-Lager (4.273 Briten interniert)
- WK2: US-Japaner (110.000 interniert)
- "Enemy Alien Act" - Diskutiert in EU?
- Aktuelle Diskussionen über solche Maßnahmen
"""
]

def build_prompt(date: str, research_data: str, rss_data: str) -> str:
    return f"""
LAGE RUSSISCHER STAATSBÜRGER IN DEUTSCHLAND - {date}

ZENTRALE RESEARCH-ERGEBNISSE:
{research_data}

RSS-FEEDS (Relevante Meldungen):
{rss_data}

AUFTRAG:
Bewerte die GESAMTE Situation russischer Staatsbürger mit Niederlassungserlaubnis
in Deutschland. Dies ist eine Baseline aller Risiken und Einschränkungen.

1. Recherchiere konkrete Maßnahmen gegen russische Staatsbürger
2. Erfasse Diskriminierungsfälle und gesellschaftliches Klima
3. Prüfe finanzielle und rechtliche Einschränkungen
4. Analysiere historische Parallelen und aktuelle Diskussionen

Gib einen Score und eine faktenbasierte Begründung.
WICHTIG: Sei hier besonders sensibel für frühe Warnzeichen.
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