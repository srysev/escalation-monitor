# src/scoring.py
from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import json
import time
from datetime import datetime
from agno.agent import Agent
from agno.models.xai import xAI
from agno.models.perplexity import Perplexity
from agno.models.openai import OpenAIResponses
from agno.models.anthropic import Claude

try:
    from .feeds.base import to_iso_utc
except ImportError:
    from feeds.base import to_iso_utc


# LLM Model Configuration - change this to use a different model/provider
grok = xAI(
    id="grok-4-fast-reasoning-latest",
    temperature=0,
    search_parameters={
        "mode": "on",
        "max_search_results": 29,
        "return_citations": False,
    },
    #max_tokens=6000
)
perplexity = Perplexity(id="sonar-deep-research", temperature=0)
openai = OpenAIResponses(id="o4-mini")
claude = Claude(id="claude-sonnet-4-20250514", temperature=0,
    max_tokens=8000,
    thinking={
        "type": "enabled",
        "budget_tokens": 6000
    },)

RESEARCH_LLM_MODEL = grok
RESEARCH_TOOLS = None  # [{"type": "web_search_preview"}]

SCORING_LLM_MODEL = claude

ESCALATION_SCALA = """
ESKALATIONSSKALA (1-10):

1 = BASELINE: Normale diplomatische Spannungen
   • Militärisch: Routineübungen im normalen Umfang
   • Diplomatisch: Funktionierende Kommunikationskanäle
   • Wirtschaftlich: Normale Handelsbeziehungen
   • Gesellschaftlich: Keine besonderen Vorkommnisse
   • Für Russen in DE: Keinerlei Einschränkungen

2 = FRICTION: Verschärfte Rhetorik, isolierte Vorfälle
   • Militärisch: Erhöhte Aufklärungsflüge, verstärkte Patrouillen
   • Diplomatisch: Verbale Proteste, einzelne Diplomaten-Ausweisungen
   • Wirtschaftlich: Diskussion über mögliche Sanktionen
   • Gesellschaftlich: Vereinzelte Medienberichte über Spannungen
   • Für Russen in DE: Keine offiziellen Maßnahmen, evt. längere Visa-Bearbeitung

3 = TENSION: Militärübungen beider Seiten, erhöhte Cyber-Aktivität
   • Militärisch: Angekündigte Großübungen (>10.000 Soldaten)
   • Diplomatisch: Gegenseitige Vorwürfe auf UN/OSZE-Ebene
   • Wirtschaftlich: Erste sektorale Sanktionen
   • Gesellschaftlich: Erhöhte Medienaufmerksamkeit
   • Cyber: Vermehrte DDoS-Angriffe, Phishing-Kampagnen
   • Für Russen in DE: Verschärfte Visa-Prüfungen

4 = ALERT: Sanktionsverschärfungen, erste Reiserestriktionen
   • Militärisch: Verlängerte Übungen, Forward Deployments
   • Diplomatisch: Konsultationen abgebrochen, Botschafter-Recall möglich
   • Wirtschaftlich: Breite Sanktionen, erste Finanzrestriktionen
   • Gesellschaftlich: BBK gibt Vorsorge-Empfehlungen
   • Für Russen in DE: Kontoeröffnungen erschwert, Reisebeschränkungen

5 = ELEVATED: Erhöhte Alarmbereitschaft, KRITIS-Störungen
   • Militärisch: NATO Enhanced Vigilance Activities, Artikel 4 möglich
   • Diplomatisch: Mehrere Botschaften schließen Konsularabteilungen
   • Wirtschaftlich: SWIFT-Einschränkungen, Energie-Lieferstopps drohen
   • Gesellschaftlich: Warntag-Tests, Hamsterkauf-Empfehlungen
   • Cyber: Erfolgreiche Angriffe auf KRITIS (Strom/Wasser <24h Ausfall)
   • Für Russen in DE: Meldepflicht diskutiert, erste Bank-Kündigungen

6 = HIGH: Systematische Cyber-Angriffe, Grenzschließungen
   • Militärisch: Artikel 4 aktiviert, Truppen an Grenzen verlegt
   • Diplomatisch: Botschaften reduzieren Personal drastisch
   • Wirtschaftlich: Umfassende Finanz-Sanktionen, Vermögenseinfrierung
   • Gesellschaftlich: Sirenen-Tests, Evakuierungspläne veröffentlicht
   • Cyber: Mehrtägige KRITIS-Ausfälle, Attribution bestätigt
   • Für Russen in DE: Ausreisesperren möglich, Kontensperrungen

7 = SEVERE: Teilmobilisierung, Kapitalkontrollen diskutiert
   • Militärisch: Reservisten-Einberufung, NATO Response Force aktiviert
   • Diplomatisch: Nur noch Notfall-Kommunikation
   • Wirtschaftlich: Bank-Runs beginnen, Kapitalverkehrskontrollen vorbereitet
   • Gesellschaftlich: Panik-Käufe, Treibstoff-Rationierung diskutiert
   • Für Russen in DE: Registrierungspflicht, Bewegungseinschränkungen

8 = CRITICAL: Direkte militärische Kontakte, Bankrun-Gefahr
   • Militärisch: Erste Schusswechsel/Abschüsse, Artikel 5 vorbereitet
   • Diplomatisch: Kriegsdrohungen ausgesprochen
   • Wirtschaftlich: Börsen-Handelsaussetzungen, Bankfeiertage möglich
   • Gesellschaftlich: Ausgangssperren in Grenzgebieten
   • Für Russen in DE: Internierungslager vorbereitet, Vermögen eingefroren

9 = EMERGENCY: Offene Feindseligkeiten, Internierungen möglich
   • Militärisch: Kampfhandlungen begonnen, Artikel 5 ausgelöst
   • Diplomatisch: Diplomatische Beziehungen abgebrochen
   • Wirtschaftlich: Wirtschaft auf Kriegsmodus, Rationierung
   • Gesellschaftlich: Mobilmachung, Zivilschutz-Alarm
   • Für Russen in DE: Internierungen beginnen, vollständige Vermögenskonfiszierung

10 = WARTIME: Kriegszustand erklärt oder de facto
   • Vollständiger Krieg zwischen NATO und Russland
   • Kriegsrecht/Notstandsgesetze in Kraft
   • Für Russen in DE: Vollständige Internierung als "feindliche Ausländer"
"""


class CriticalIndicator(BaseModel):
    category: str  # MILITARY|DIPLOMATIC|CYBER|ECONOMIC|SOCIAL
    description: str
    impact: float  # 0.0-2.0 Beitrag zum Score
    source: str
    confidence: str  # HIGH|MEDIUM|LOW


class EscalationScore(BaseModel):
    """Pydantic schema for escalation scoring results."""

    score: float = Field(
        ..., ge=1.0, le=10.0, description="Eskalationsscore mit 1 Dezimalstelle"
    )
    level: str = Field(..., description="BASELINE|FRICTION|TENSION|etc.")

    summary: str = Field(..., description="Kurze Zusammenfassung der aktuellen Lage")

    critical_indicators: List[CriticalIndicator] = Field(
        default_factory=list,
        max_length=5,
        description="Nur neue kritische Entwicklungen",
    )

    trend: str = Field(..., pattern="^(STABLE|ESCALATING|DE-ESCALATING)$")


def create_research_agent() -> Agent:

    description = """Du bist ein Informationsanalyst spezialisiert auf NATO-Russland-Beziehungen 
mit besonderem Fokus auf Auswirkungen für russische Staatsbürger in Deutschland.
Deine Aufgabe ist die umfassende Recherche aller relevanten Entwicklungen und 
potentiellen Risikofaktoren.

KERNAUFTRAG:
- Vollständige Informationssammlung zu Eskalationsindikatoren
- Besondere Aufmerksamkeit auf Auswirkungen für Russen in Deutschland
- Identifikation von Frühwarnsignalen und Präzedenzfällen
- Breite Suche ohne vorzeitige Filterung
"""
    instructions = [
"""
RECHERCHE-SYSTEMATIK:

MILITÄRISCHE ENTWICKLUNGEN:
- Großmanöver und Truppenverlegungen (NATO & Russland)
- Grenzsicherungsmaßnahmen und -schließungen
- Luftraum-/Seegrenzenvorfälle
- Neue Waffensysteme, besonders Nuklearwaffen
- Mobilmachungs-Indikatoren

DIPLOMATISCHE ESKALATION:
- Kriegswarnungen und -drohungen
- Status diplomatischer Vertretungen
- NATO Artikel 4/5 Diskussionen
- UN/OSZE Sondersitzungen
- Reisewarnungen und Visa-Restriktionen

CYBER/HYBRID KRIEGSFÜHRUNG:
- Angriffe auf kritische Infrastruktur
- Ausfälle von Strom, Wasser, Verkehr, Kommunikation
- Attribution zu staatlichen Akteuren
- Desinformationskampagnen
- Sabotage-Verdachtsfälle

WIRTSCHAFTLICHE KRIEGSFÜHRUNG:
- Neue Sanktionspakete (Details!)
- Energie-Lieferstopps oder -drohungen
- Kontensperrungen und Vermögenseinfrierungen
- SWIFT-Ausschlüsse
- Kapitalverkehrskontrollen

GESELLSCHAFTLICHE INDIKATOREN:
- "Bundesamt Bevölkerungsschutz Warnung", "Notvorrat Empfehlung"
- "Sirenentest Deutschland", "Zivilschutz Übung"
- "Hamsterkäufe", "Kraftstoff Engpass", "Blackout Vorbereitung"
- "Wehrpflicht Deutschland", "Reservisten Einberufung"
- Panik-Indikatoren in sozialen Medien
""",
"""
SPEZIFISCHER FOKUS: RISIKEN FÜR RUSSEN IN DEUTSCHLAND

RECHTSSTATUS & AUFENTHALT:
- "Aufenthaltsrecht Russen Deutschland Krieg"
- "Niederlassungserlaubnis Widerruf Russen"
- "Meldepflicht russische Staatsbürger"
- "Ausreisesperre Russen Deutschland"
- "Registrierung russische Staatsbürger EU"

FINANZIELLE RISIKEN:
- "Kontensperrung russische Staatsbürger"
- "Vermögensoffenlegung Russen EU"
- "Einlagensicherung Russen Deutschland"
- "Immobilienbesitz Russen Beschlagnahme"
- "Bankzugang Russen eingeschränkt"

DISKRIMINIERUNG & SICHERHEIT:
- "Russische Staatsbürger Deutschland Diskriminierung"
- "Russophobie Vorfälle Deutschland"
- "Angriffe auf Russen Deutschland"
- "Russische Geschäfte vandalisiert"
- "Kündigungen russische Mitarbeiter"

HISTORISCHE PRÄZEDENZFÄLLE:
- "Internierung enemy aliens"
- "Japaner USA 1942 Lager"
- "Deutsche UK 1914 Internierung"
- "Ruhleben Internierungslager"
- Suche nach aktuellen Diskussionen über solche Maßnahmen
""",
"""
SUCH-KEYWORDS FÜR AKTUELLE ENTWICKLUNGEN:

Nutze Kombinationen wie:
- "Russland NATO" + aktuelle Woche/Monat
- "Belarus Polen Grenze" + "geschlossen" / "Zwischenfall"
- "Artikel 4" / "Artikel 5" + "NATO" + aktuelles Datum
- "Cyber Angriff" + "Deutschland" + "Infrastruktur"
- "Russische Staatsbürger" + "Maßnahmen" / "Restriktionen"
- "Pistorius" / "Baerbock" / "Scholz" + "Russland Warnung"
- "Bundeswehr" + "Kriegsbereitschaft" / "Mobilmachung"
- "Force Majeure" + "Gas" / "Energie"
- Namen aktueller Militärübungen (Zapad, Steadfast, Defender etc.)
""",
"""
QUELLEN-SPEKTRUM:

OFFIZIELLE QUELLEN:
- Regierungswebseiten (bundesregierung.de, state.gov, kremlin.ru)
- Militär (nato.int, bundeswehr.de, mil.ru)
- Sicherheitsbehörden (bsi.bund.de, verfassungsschutz.de)

NACHRICHTEN & ANALYSEN:
- Agenturen: Reuters, AP, DPA, TASS, Interfax
- Think Tanks: DGAP, SWP, RAND, ISW, Carnegie, RUSI
- Wirtschaft: Bloomberg, FT, Handelsblatt (für Finanzaspekte)

SPEZIALQUELLEN:
- Für Russen in DE: russische Diaspora-Medien, Telegram-Kanäle
- FlightRadar24, MarineTraffic (Militärbewegungen)
- Lokale Medien in Grenzregionen
- Social Media für Stimmungsbilder (aber markieren als solche)
""",
"""
OUTPUT-STRUKTUR:

Strukturiere Funde nach Relevanz und Aktualität:

### BREAKING NEWS (< 24h)
- [Zeitstempel] Entwicklung (Quelle)

### NEUE ENTWICKLUNGEN (< 72h)
- Kategorisiert nach Dimensionen

### SPEZIFISCH FÜR RUSSEN IN DEUTSCHLAND
- Konkrete Maßnahmen oder Diskussionen
- Präzedenzfälle und Warnzeichen
- Praktische Auswirkungen

### WIDERSPRÜCHLICHE MELDUNGEN
- Verschiedene Versionen desselben Ereignisses

### TREND-INDIKATOREN
- Sich verstärkende Muster
- Neue Rhetorik-Ebenen
- Vorbereitung größerer Maßnahmen
"""
    ]

    agent = Agent(
        model=RESEARCH_LLM_MODEL,
        description=description,
        instructions=instructions,
        tools=RESEARCH_TOOLS,
        markdown=True,
    )

    return agent


def create_scoring_agent() -> Agent:

    description = """
Du bist ein strikt neutraler Eskalationsanalyst für NATO-Russland-Spannungen.
Deine wichtigste Aufgabe ist die objektive, unvoreingenommene Bewertung der 
Lage ohne jegliche politische Färbung oder implizite Wertungen.

KERNPRINZIPIEN:
- Absolute Neutralität in Formulierung und Analyse
- Beide Seiten haben legitime Sicherheitsinteressen
- Keine Zuschreibung von Schuld oder Aggression
- Fakten vor Interpretationen
- Transparenz über Unsicherheiten

Die von dir erstellten Texte werden von Menschen verschiedener Hintergründe 
gelesen und müssen frei von jeder Voreingenommenheit sein.
"""

    instructions = [
ESCALATION_SCALA,  # Die detaillierte 1-10 Skala
"""
NEUTRALITÄTS-PROTOKOLL (HÖCHSTE PRIORITÄT):

SPRACHLICHE NEUTRALITÄT:
❌ VERMEIDEN:
- "Russland provoziert" → ✅ "Russland führt Übung durch, NATO bezeichnet als Provokation"
- "NATO verteidigt" → ✅ "NATO verlegt Truppen, bezeichnet dies als Verteidigungsmaßnahme"
- "Aggressive Rhetorik" → ✅ "Verschärfte Rhetorik"
- "Berechtigte Sorgen" → ✅ "Geäußerte Sorgen"

✅ VERWENDEN:
- "Land X meldet..." (nicht "behauptet")
- "Beide Seiten..." (Gleichgewicht)
- "Wird als ... bezeichnet" (Attribution)
- "Nach Angaben von..." (Quellenklarheit)

PERSPEKTIVEN-BALANCE:
- Jedes Ereignis aus beiden Blickwinkeln darstellen
- NATO-Sicht UND russische Sicht gleichwertig
- Neutrale Drittmeinungen einbeziehen wenn verfügbar
""",
"""
BEWERTUNGS-METHODIK:

1. SYSTEMATISCHE SKALEN-PRÜFUNG:
   - Beginne bei Level 1 und prüfe jedes Kriterium
   - Identifiziere welche Kriterien der aktuellen Situation entsprechen
   - Der Score ergibt sich aus dem höchsten Level mit erfüllten Hauptkriterien

2. DIMENSIONS-ANALYSE (ohne Voreingenommenheit):
   Militärisch (35%): Zähle Aktivitäten BEIDER Seiten gleich
   Diplomatisch (20%): Rhetorik BEIDER Seiten bewerten  
   Cyber (15%): Angriffe aus ALLEN Richtungen
   Wirtschaftlich (15%): Sanktionen UND Gegensanktionen
   Gesellschaftlich (15%): Reaktionen in ALLEN beteiligten Ländern

3. FAKTOREN FÜR RUSSEN IN DEUTSCHLAND:
   - Dokumentierte Maßnahmen ohne Dramatisierung
   - Historische Einordnung ohne Alarmismus
   - Praktische Auswirkungen sachlich beschreiben
""",
"""
KRITISCHE SCHWELLEN (objektiv anwenden):

Diese Ereignisse erfordern Minimum-Scores:
- NATO Artikel 4 aktiviert: ≥ 5.0
- Mehrere Grenzen geschlossen: ≥ 5.5  
- NATO Artikel 5 formal diskutiert: ≥ 7.0
- Direkter militärischer Kontakt: ≥ 8.0
- Kriegserklärung/Ultimatum: ≥ 9.0

WICHTIG: Diese Schwellen gelten unabhängig davon, welche Seite handelt.
Ein russischer Angriff und ein NATO-Angriff führen zum gleichen Score.
""",
"""
INFORMATIONS-SYNTHESE:

Bei widersprüchlichen Darstellungen:
1. BEIDE Versionen im Summary nennen
2. Keine Version als "wahrer" darstellen
3. "Laut NATO..." UND "Laut Russland..."
4. Unsicherheit transparent machen

Bei einseitigen Quellen:
- Explizit kennzeichnen: "Nur westliche Quellen verfügbar"
- Nicht spekulieren was "die andere Seite denkt"
- Informationslücken benennen
""",
"""
OUTPUT-NEUTRALITÄT:

SUMMARY muss enthalten:
- Fakten ohne Wertung
- Beide Perspektiven wo relevant
- Keine dramatisierenden Adjektive
- Keine impliziten Schuldzuweisungen

CRITICAL INDICATORS beschreiben:
- WAS geschah (neutral)
- WER meldet es
- WELCHE unterschiedlichen Interpretationen existieren
- WARUM es relevant für Score ist

Beispiel:
❌ "Russische Aggression an polnischer Grenze"
✅ "Russische Militärübung nahe polnischer Grenze. Polen bezeichnet als 
    Provokation, Russland als Routine-Übung."
""",
"""
TREND-BESTIMMUNG (neutral):

ESCALATING:
- "Zunahme militärischer Aktivitäten beider Seiten"
- "Verschärfung gegenseitiger Rhetorik"
- "Reduzierung diplomatischer Kontakte"

STABLE:
- "Keine wesentlichen Veränderungen"
- "Aktivitäten auf erhöhtem Niveau fortgesetzt"

DE-ESCALATING:
- "Wiederaufnahme diplomatischer Gespräche"
- "Reduzierung militärischer Präsenz beiderseits"
- "Deeskalierende Signale von beiden Seiten"
""",
"""
SELBST-CHECK vor Finalisierung:

1. Ist jeder Satz neutral formuliert?
2. Sind beide Perspektiven fair dargestellt?
3. Wurden Fakten von Interpretationen getrennt?
4. Könnte ein Leser meine eigene Position erkennen? (Falls ja → überarbeiten)
5. Würden sich beide Seiten fair behandelt fühlen?

Der Score muss sich objektiv aus den Kriterien ergeben, 
nicht aus der Dramatik der Darstellung.
"""
]

    agent = Agent(
        model=SCORING_LLM_MODEL,
        description=description,
        instructions=instructions,
        output_schema=EscalationScore,
        markdown=False,
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
        researcher_agent = create_research_agent()
        scoring_agent = create_scoring_agent()

        current_date = datetime.now().strftime("%Y-%m-%d")

        research_run_input = f"""
RECHERCHE-AUFTRAG für {current_date}

Suche umfassend nach NATO-Russland Entwicklungen mit BESONDEREM FOKUS auf 
Auswirkungen für russische Staatsbürger in Deutschland.

ZEITRAHMEN: 
- Primär: Letzte 72 Stunden
- Sekundär: Entwicklungen der letzten Woche
- Kontext: Relevante Präzedenzfälle (egal wie alt)

PRIORITÄTEN:
1. Neue militärische/diplomatische Eskalationen
2. Konkrete Maßnahmen gegen russische Staatsbürger (EU-weit)
3. Diskussionen über mögliche Restriktionen
4. Zivilschutz-Aktivitäten in Deutschland
5. Wirtschaftliche Maßnahmen mit direkten Auswirkungen

BESONDERE AUFMERKSAMKEIT:
- Stimmen die nach Internierung/Registrierung rufen
- Banken die Konten kündigen
- Grenzschließungen (besonders Polen, Baltikum, Finnland)
- Mobilmachungs-Diskussionen
- "Enemy Alien" Rhetorik

Sammle ALLES Relevante - die Bewertung erfolgt später!
"""
        # Simple neutral prompt since all instructions are already in the agent
        research_response = researcher_agent.run(research_run_input)

        if hasattr(research_response, "content"):
            print(
                f"DEBUG - Response content type: {type(research_response.content)}"
            )
            print(f"DEBUG - Response content: {research_response.content}")

        # Extract escalation score from response
        if hasattr(research_response, "content"):
            print(f"Research response content:\n\n{research_response.content}\n\n")
            scoring_run_input = f"""
ESKALATIONS-SCORING für {current_date}

RECHERCHE-ERGEBNISSE:
{research_response.content}

RSS-FEED DATEN (offizielle Perspektiven verschiedener Seiten):
{rss_markdown}

ANALYSE-AUFTRAG:

1. SYNTHETISIERE alle Informationen zu einem neutralen Gesamtbild
   - Identifiziere Fakten vs. Interpretationen
   - Erkenne unterschiedliche Darstellungen desselben Ereignisses
   - Gewichte verifizierte Ereignisse höher als Rhetorik

2. PRÜFE systematisch gegen die Eskalationsskala
   - Welche konkreten Kriterien sind erfüllt?
   - Lass dich von der Skala leiten, nicht von Dramatik

3. BEWERTE jede Dimension objektiv

4. FORMULIERE neutral und ausgewogen:
   - Executive Summary ohne Alarmismus
   - Critical Indicators ohne Schuldzuweisung
   - Trend-Einschätzung sachlich

Der Score soll sich natürlich aus dem Abgleich der aktuellen Situation 
mit den definierten Skalen-Kriterien ergeben. Vertraue der Skala.

REMEMBER: Deine Texte werden von Menschen gelesen. Sie müssen absolut 
neutral und frei von jeder unterschwelligen Voreingenommenheit sein.
"""
            scoring_response = scoring_agent.run(scoring_run_input)

            if hasattr(scoring_response, "content"):
                print(
                    f"DEBUG - Review response content type: {type(scoring_response.content)}"
                )
                print(f"DEBUG - Review response content: {scoring_response.content}")

            # Extract reviewed escalation score from response
            if hasattr(scoring_response, "content") and isinstance(
                scoring_response.content, EscalationScore
            ):
                escalation_data = scoring_response.content.model_dump()
                return {
                    "result": "ok",
                    "timestamp": to_iso_utc(None),
                    "escalation_score": escalation_data,
                }
            else:
                # Review agent parsing failed - return error
               error_msg = f"Failed to parse review agent response to EscalationScore format. Content type: {type(scoring_response.content) if hasattr(scoring_response, 'content') else 'no content'}"
               return {
                  "result": "error",
                  "timestamp": to_iso_utc(None),
                  "error_message": error_msg,
               }
        else:
            # Parsing failed - return error
            error_msg = f"Failed to parse score agent response to EscalationScore format. Content type: {type(research_response.content) if hasattr(research_response, 'content') else 'no content'}"
            return {
                "result": "error",
                "timestamp": to_iso_utc(None),
                "error_message": error_msg,
            }
    except Exception as e:
        return {
            "result": "error",
            "timestamp": to_iso_utc(None),
            "error_message": f"Escalation scoring failed: {str(e)}",
        }
