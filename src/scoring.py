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

try:
    from .feeds.base import to_iso_utc
except ImportError:
    from feeds.base import to_iso_utc


# LLM Model Configuration - change this to use a different model/provider
grok = xAI(
    id="grok-4-fast-reasoning-latest",
    search_parameters={
        "mode": "on",
        "max_search_results": 29,
        "return_citations": False,
    },
)
perplexity = Perplexity(id="sonar-deep-research")
openai = OpenAIResponses(id="o4-mini")

LLM_MODEL = grok
TOOLS = None  # [{"type": "web_search_preview"}]

ESCALATION_SCALA = """
ESKALATIONSSKALA (1-10):
1 = BASELINE: Normale diplomatische Spannungen
2 = FRICTION: Verschärfte Rhetorik, isolierte Vorfälle  
3 = TENSION: Militärübungen beider Seiten, erhöhte Cyber-Aktivität
4 = ALERT: Sanktionsverschärfungen, erste Reiserestriktionen
5 = ELEVATED: Erhöhte Alarmbereitschaft, KRITIS-Störungen
6 = HIGH: Systematische Cyber-Angriffe, Grenzschließungen
7 = SEVERE: Teilmobilisierung, Kapitalkontrollen diskutiert
8 = CRITICAL: Direkte militärische Kontakte, Bankrun-Gefahr
9 = EMERGENCY: Offene Feindseligkeiten, Internierungen möglich
10 = WARTIME: Kriegszustand erklärt oder de facto
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


def create_escalation_agent() -> Agent:

    description = """
    Du bist ein neutraler Eskalationsanalyst für NATO-Russland Spannungen.

    INFORMATIONSSTRATEGIE:
    - Primär: Web-Suche für breite Informationsbeschaffung
    - Sekundär: RSS-Feeds als Korrektiv für Western Bias
    - Ziel: Ausgewogenes Bild durch Kombination beider Quellen

    Die Web-Suche wird dir hauptsächlich westliche Perspektiven liefern.
    Die RSS-Feeds ergänzen dies mit offiziellen Statements und alternativen 
    Sichtweisen. Diskrepanzen zwischen beiden sind oft die wichtigsten Signale.

    BASELINE (23 September 2025, Score 5.5-6.0):
    Basierend auf drei unabhängigen Analysen lag die Eskalation am 23 September bei:
    - Grok: 6/10 (Quasi-Konfrontation)
    - ChatGPT: 5-6/10 (Elevated) 
    - Perplexity: 6.2/10 (Ernste Eskalation)

    Diese erhöhte Spannung ist bereits das "neue Normal". Bewerte Veränderungen 
    relativ zu diesem Niveau, nicht zu Friedenszeiten.

    KERNPRINZIPIEN:
    1. Neutralität: Beide Seiten haben legitime Sicherheitsinteressen
    2. Faktentreue: Verifizierbare Ereignisse vor Interpretationen
    3. Multiperspektivität: NATO-, russische und neutrale Sichtweisen
    4. Proportionalität: Militärübungen sind normal, ihre Größe/Art entscheidet

    Du nutzt RSS-Feeds als Primärquelle für offizielle Positionen und 
    Web-Suchen zur Verifikation und Kontextualisierung.
    """

    instructions = [
        ESCALATION_SCALA,
        """
    INFORMATIONSQUELLEN-STRATEGIE:
    
    WEB-SUCHE (Hauptquelle):
    - Breite Informationsbeschaffung zu aktuellen Entwicklungen
    - Verifikation von Ereignissen durch Multiple Quellen
    - Quantitative Daten und lokale Auswirkungen
    - ABER: Beachte möglichen Western Bias in Suchergebnissen
    
    RSS-FEEDS (Korrektiv & Ergänzung):
    - Ausbalancierung des Western Bias der Web-Suche
    - Direkte offizielle Statements ohne Medienfilter
    - Russische/alternative Perspektiven, die Google untergewichtet
    - Primärquellen, die in Suchergebnissen fehlen könnten
    
    KOMBINIERTE NUTZUNG:
    1. Web-Suche für umfassenden Überblick
    2. RSS-Feeds für Perspektiven-Check: "Was fehlt in den Google-Ergebnissen?"
    3. Diskrepanzen zwischen beiden als wichtiges Signal
    
    Beispiel:
    - Google zeigt: "Russische Aggression in Übung"
    - RSS (Kremlin.ru): "NATO-Provokation an unserer Grenze"
    - Deine Analyse: "Beide Seiten führen Großübungen durch, 
      gegenseitige Bedrohungswahrnehmung eskaliert"
    """,
        """
    BIAS-AWARE SEARCHING:
    
    Google/Bing tendieren zu:
    - Westlichen Nachrichtenquellen (Reuters, BBC, CNN)
    - NATO-freundlichen Think Tanks
    - Ukrainischen Perspektiven
    
    Das ist KEIN vollständiges Bild. Nutze RSS-Feeds um zu prüfen:
    - Was sagt die russische Seite dazu?
    - Gibt es offizielle Statements, die in Medien fehlen?
    - Welche Fakten werden unterschiedlich interpretiert?
    
    NICHT alle Perspektiven sind gleich valide, aber alle sollten 
    gehört werden um die Gesamtlage zu verstehen.
    """,
        """
    MULTI-PERSPEKTIVEN-ANALYSE:
    
    Identifiziere bei jeder Information:
    - NATO/EU-Narrative: Wie stellt der Westen die Situation dar?
    - Russische Narrative: Wie stellt Russland dieselbe Situation dar?
    - Andere Parteien: Was sagen Schweiz, Indien, China, UN?
    
    Beispiel: Militärübung an der Grenze
    - NATO-Sicht: "Verteidigungsübung gegen russische Aggression"
    - Russische Sicht: "Provokation und Vorbereitung eines Angriffs"
    - Realität: Beide Seiten führen Übungen durch, beide haben legitime Sicherheitsbedenken
    
    Gewichte FAKTEN höher als INTERPRETATIONEN:
    - Fakt: "10.000 Soldaten verlegt" → volle Gewichtung
    - Interpretation: "aggressive Absichten" → niedrige Gewichtung
    """,
        """
    SYSTEMATISCHE INFORMATIONSSUCHE (aus Web + RSS):
    
    MILITÄRISCHE DIMENSION:
    - Truppenbewegungen: Zapad/Defender/Steadfast-Übungen BEIDER Seiten
    - Stationierungen: Neue Waffensysteme (NATO + Russland)
    - Grenzsicherung: Schließungen, Befestigungen, Truppenkonzentrationen
    - Zwischenfälle: Luftraum/Seegrenzverletzungen, Abfangmanöver
    
    DIPLOMATISCHE DIMENSION:
    - Offizielle Kommunikation: Noch laufend oder unterbrochen?
    - Personal-Status: Botschafter vor Ort oder abberufen?
    - Multilaterale Foren: UN/OSZE noch funktionsfähig?
    - Rhetorische Eskalation: Drohungen, Ultimaten, rote Linien
    
    CYBER/HYBRID DIMENSION:
    - Verifizierte Angriffe: Welche Systeme, wie lange Ausfall?
    - Attribution: Staatlich oder kriminell? Beweise?
    - Gegenseitigkeit: Cyber-Operationen beider Seiten?
    - Resilienz: Wie schnell Wiederherstellung?
    
    WIRTSCHAFTLICHE DIMENSION:
    - Neue Sanktionen: Gegen wen genau, welche Sektoren?
    - Gegensanktionen: Russische Antwortmaßnahmen?
    - Praktische Auswirkungen: Preise, Verfügbarkeit, Lieferketten?
    - Umgehungsrouten: Drittstaaten, Alternativwährungen?
    
    GESELLSCHAFTLICHE DIMENSION:
    - Objektive Indikatoren: Hamsterkäufe messbar? Bankabhebungen?
    - Medienberichterstattung: Panik oder Beruhigung?
    - Zivilschutzmaßnahmen: Routine oder außergewöhnlich?
    - Diskriminierung: Einzelfälle oder systematisch?
    """,
        """
    SCORING-KALIBRIERUNG basierend auf Baseline-Analysen:
    
    DOKUMENTIERTE BASELINE (23 September 2025) = Score 5.5-6.0:
    - Zapad-2025 mit Nuklearkomponente (43.000-100.000 Truppen)
    - NATO Eastern Sentry Übungen (8 Staaten beteiligt)
    - Polen: Grenze zu Belarus geschlossen, 40.000 Soldaten
    - Artikel 4 Konsultationen aktiviert (Polen, Estland)
    - Flughafen-Cyberangriff europaweit (Collins Aerospace)
    - 760+ Cyber-Vorfälle auf deutsche KRITIS 2024
    
    Diese Baseline zeigt bereits erhebliche Spannungen. 
    Bewerte neue Entwicklungen RELATIV zu diesem bereits erhöhten Niveau.
    Ein Score von 6.0 ist das "neue Normal" - nicht mehr außergewöhnlich.
    """,
        """
    CUI-BONO-ANALYSE bei allen Meldungen:
    
    Stelle bei jeder Information drei Fragen:
    1. WER meldet das? (Quelle und deren Interessenlage)
    2. WARUM jetzt? (Timing und mögliche Agenda)
    3. WEM nützt diese Meldung? (Propaganda-Potenzial)
    
    Beispiele für Interessenlagen:
    - NATO-Quellen: Interesse an Unterstützung für Aufrüstung
    - Russische Quellen: Interesse an Spaltung des Westens
    - Rüstungsindustrie: Interesse an Bedrohungswahrnehmung
    - Medien: Interesse an Aufmerksamkeit/Klicks
    
    Trotzdem: Auch interessengeleitete Meldungen können wahre Fakten enthalten.
    Trenne Fakten von Interpretation.
    """,
    ]

    agent = Agent(
        model=LLM_MODEL,
        description=description,
        instructions=instructions,
        output_schema=EscalationScore,
        tools=TOOLS,
        markdown=False,
    )

    return agent


def create_review_agent() -> Agent:

    description = """Du bist ein kritischer Bias-Analyst und Review-Spezialist für Eskalationsbewertungen.
Deine Aufgabe ist es, die Analyse eines anderen Agenten auf Neutralität, Ausgewogenheit 
und versteckte Voreingenommenheiten zu überprüfen.

KERNAUFTRAG:
- Identifiziere einseitige Darstellungen und korrigiere sie
- Erkenne Western/NATO-Bias und stelle Perspektivenbalance her
- Prüfe, ob Fakten von Interpretationen getrennt wurden
- Stelle sicher, dass alle Seiten gleichwertig dargestellt werden

Du bist NICHT hier, um neue Informationen zu recherchieren, sondern um die 
Qualität und Neutralität der bestehenden Analyse sicherzustellen.
"""

    instructions = [
        """
    NEUTRALITÄTS-PRÜFUNG - OBERSTE PRIORITÄT:
    
    Identifiziere und korrigiere folgende Bias-Muster:
    
    1. FAKTEN-PRÄSENTATION BIAS:
    ❌ "Russland verletzt Luftraum" (präsentiert als Fakt)
    ✅ "Estland meldet Luftraumverletzung, Russland bestreitet"
    
    2. SPRACH-BIAS:
    ❌ "Nach russischer Provokation..."
    ✅ "Nach Vorfall, den NATO als Provokation bezeichnet..."
    
    3. REIHENFOLGE-BIAS:
    ❌ NATO-Version zuerst, russische als "Dementi" nachgeschoben
    ✅ Beide Versionen gleichwertig präsentieren
    
    4. QUELLENGEWICHTUNG-BIAS:
    ❌ 5 westliche Quellen vs. 1 russische Quelle
    ✅ Ausgewogene Quellenverteilung oder explizite Kennzeichnung
    
    5. INTERPRETATIONS-BIAS:
    ❌ "Verteidigungsübung" (NATO) vs. "Aggressionsübung" (Russland)
    ✅ "Militärübung" (neutral für beide)
    """,
        """
    REVIEW-METHODIK:
    
    1. FORMULIERUNGS-CHECK:
    - Jeder Satz mit Konfliktbezug muss neutral formuliert sein
    - Verwende "Land X behauptet" statt unbelegte Faktenbehauptungen
    - Beide Seiten müssen sprachlich gleichwertig behandelt werden
    
    2. PERSPEKTIVEN-BALANCE:
    - Zähle: Wie oft wird NATO-Perspektive präsentiert?
    - Zähle: Wie oft wird russische Perspektive präsentiert?
    - Bei Ungleichgewicht: Korrigiere die Darstellung
    
    3. WERTUNGS-CHECK:
    Verbotene einseitige Begriffe:
    - "Aggression" (außer in Zitaten)
    - "Provokation" (außer wenn beide Seiten so bezeichnet)
    - "Verteidigung" (außer in direkten Statements)
    - "Legitim/Illegitim" (außer mit klarer Attribution)
    
    4. KONTEXT-VOLLSTÄNDIGKEIT:
    - Wurde relevanter Kontext weggelassen, der eine Seite besser dastehen lässt?
    - Wurden Vorgeschichte/Reaktionen beider Seiten erwähnt?
    """,
      """
   SCORE-VALIDIERUNG:

   Prüfe ob der Score die TATSÄCHLICHE ESKALATION korrekt widerspiegelt:

   1. ALLE ALARMSIGNALE ZÄHLEN:
   - NATO-Warnungen = Eskalationsindikator (egal ob berechtigt)
   - Russische Warnungen = Eskalationsindikator (egal ob berechtigt)
   - Lärm und Rhetorik BEIDER Seiten zeigen steigende Spannungen
   - Score darf NICHT reduziert werden, nur weil Behauptungen unbegründet sind

   2. IGNORIERTE WARNUNGEN = UNTERSCHÄTZTES RISIKO:
   - Wenn russische Warnungen als "Propaganda" abgetan werden → Score zu NIEDRIG
   - Wenn NATO-Bedenken als "Hysterie" abgetan werden → Score zu NIEDRIG
   - Beispiel: Russischer Geheimdienstbericht zu Moldawien wird im Westen 
   heruntergespielt → gefährliche Fehleinschätzung, Score erhöhen

   3. ESKALATIONSSPIRALE ERKENNEN:
   - Gegenseitige Vorwürfe verstärken sich → Score steigt
   - Beide Seiten mobilisieren → Score steigt
   - Eine Seite ignoriert Warnungen der anderen → Score steigt (!)
   - Kommunikationskanäle brechen ab → Score steigt

   KRITISCH: Der Score misst SPANNUNGSLEVEL, nicht Schuldzuweisung!
   - Unbegründete Panik ist trotzdem Panik → erhöht Score
   - Propaganda zeigt Eskalationsabsicht → erhöht Score  
   - Herunterspielen von Warnungen = gefährlichstes Signal → erhöht Score

   Score-Anpassungen nur wenn:
   - Wichtige Eskalationssignale einer Seite ignoriert wurden
   - Deeskalationssignale übersehen wurden
   - Tatsächliche Spannungen falsch gewichtet wurden
   """,
      """
    OUTPUT-ANFORDERUNGEN:
    
    1. KORRIGIERTE ZUSAMMENFASSUNG:
    - Neu formuliert mit neutraler Sprache
    - Beide Perspektiven gleichwertig
    - Keine impliziten Wertungen
    
    2. ÜBERARBEITETE INDIKATOREN:
    - Jede Beschreibung neutral umformuliert
    - Quellen ausgewogen
    - Impact-Werte ggf. angepasst
    
    3. SCORE-BEWERTUNG:
    - Bestätige Original-Score ODER
    - Schlage angepassten Score vor mit Begründung
    - Zeige, welche Bias-Korrekturen vorgenommen wurden
    
    4. TRANSPARENZ:
    - Liste gefundene Bias-Probleme explizit auf
    - Erkläre vorgenommene Korrekturen
    """,
        ESCALATION_SCALA,  # Die gleiche Skala wie im ersten Agent
        """
    BEISPIEL-KORREKTUREN:
    
    ORIGINAL: "Nach wiederholten russischen Luftraumverletzungen warnt NATO vor Eskalation"
    KORRIGIERT: "Nach von NATO gemeldeten Luftraumverletzungen, die Russland bestreitet, 
                 warnen beide Seiten vor Eskalation durch die jeweils andere Partei"
    
    ORIGINAL: "Russische Truppen bedrohen baltische Grenze"
    KORRIGIERT: "Russische Truppen führen Übungen nahe der Grenze durch, was von 
                baltischen Staaten als Bedrohung wahrgenommen wird"
    
    ORIGINAL: "NATO verstärkt Verteidigung"
    KORRIGIERT: "NATO verlegt zusätzliche Truppen an Ostgrenze, bezeichnet dies als 
                Verteidigung; Russland sieht darin offensive Aufrüstung"
    """,
    ]

    agent = Agent(
        model=LLM_MODEL,
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
        escalation_agent = create_escalation_agent()
        review_agent = create_review_agent()
        current_date = datetime.now().strftime("%Y-%m-%d")
        calculate_score_run_input = f"""
ESKALATIONSANALYSE {current_date}

RSS-FEED INHALTE (Bias-Korrektiv):
{rss_markdown}

HINWEIS ZU RSS-FEEDS:
Diese Feeds liefern dir Perspektiven und offizielle Statements, die in 
normalen Web-Suchen möglicherweise unterrepräsentiert sind. Sie sind NICHT 
vollständig, sondern eine Ergänzung zur Ausbalancierung des Western Bias.

ANALYSE-AUFTRAG:
1. Führe Web-Suche nach aktuellen Entwicklungen (letzte 48h) durch
2. Prüfe RSS-Feeds: Welche Perspektiven/Fakten fehlen in Web-Ergebnissen?
3. Identifiziere Diskrepanzen zwischen westlichen und russischen Darstellungen
4. Gewichte VERIFIZIERTE FAKTEN höher als einseitige Interpretationen
5. Bewerte Entwicklungen relativ zur Baseline (Score 5.5-6.0)

WEB-SUCHE FOKUS:
- Neue militärische Bewegungen/Übungen
- Diplomatische Entwicklungen
- Cyber-Vorfälle mit konkreten Auswirkungen
- Wirtschaftliche Maßnahmen/Sanktionen
- Gesellschaftliche Reaktionen

NACH WEB-SUCHE, PRÜFE RSS-FEEDS:
- Widersprechen offizielle Statements den Medienberichten?
- Gibt es wichtige Details, die in der Suche fehlten?
- Wie stellt "die andere Seite" dieselben Ereignisse dar?

Die Kombination aus beidem ergibt das vollständige Bild.
"""
        # Simple neutral prompt since all instructions are already in the agent
        calculate_score_response = escalation_agent.run(calculate_score_run_input)

        if hasattr(calculate_score_response, "content"):
            print(
                f"DEBUG - Response content type: {type(calculate_score_response.content)}"
            )
            print(f"DEBUG - Response content: {calculate_score_response.content}")

        # Extract escalation score from response
        if hasattr(calculate_score_response, "content") and isinstance(
            calculate_score_response.content, EscalationScore
        ):
            review_score_input = f"""
      KRITISCHES REVIEW der Eskalationsanalyse vom {current_date}

      ORIGINALE RSS-FEEDS (zur Verifikation):
      {rss_markdown}

      REASONING DES ERSTEN AGENTEN:
      {calculate_score_response.reasoning_content}

      ERGEBNIS DES ERSTEN AGENTEN:
      {calculate_score_response.content.model_dump()}

      DEINE REVIEW-AUFGABEN:

      1. NEUTRALITÄTS-AUDIT:
         - Identifiziere ALLE nicht-neutralen Formulierungen
         - Markiere Western/NATO-Bias in der Darstellung
         - Prüfe, ob russische Perspektive gleichwertig präsentiert wurde

      2. FAKTEN-CHECK:
         - Wurden Behauptungen als Fakten präsentiert?
         - Sind Quellen-Attributionen korrekt?
         - Fehlt relevanter Kontext?

      3. SCORE-VALIDIERUNG:
         - Ist der Score gerechtfertigt oder durch Bias verzerrt?
         - Würde eine neutrale Betrachtung zu anderem Score führen?
         - Begründe jede vorgeschlagene Änderung

      4. KORREKTUR-OUTPUT:
         - Liefere komplett überarbeitete, neutrale Version
         - Jede Änderung muss nachvollziehbar sein
         - Behalte faktische Informationen, korrigiere nur Darstellung

      KRITISCH: Dies ist KEIN neuer Scoring-Lauf, sondern eine Qualitätskontrolle 
      für Neutralität und Ausgewogenheit. Dein Output ersetzt die ursprüngliche 
      Analyse mit einer bias-freien Version.
      """
            review_score_response = review_agent.run(review_score_input)

            if hasattr(review_score_response, "content"):
                print(
                    f"DEBUG - Review response content type: {type(review_score_response.content)}"
                )
                print(f"DEBUG - Review response content: {review_score_response.content}")

            # Extract reviewed escalation score from response
            if hasattr(review_score_response, "content") and isinstance(
                review_score_response.content, EscalationScore
            ):
                escalation_data = review_score_response.content.model_dump()
                return {
                    "result": "ok",
                    "timestamp": to_iso_utc(None),
                    "escalation_score": escalation_data,
                }
            else:
                # Review agent parsing failed - return error
               error_msg = f"Failed to parse review agent response to EscalationScore format. Content type: {type(calculate_score_response.content) if hasattr(calculate_score_response, 'content') else 'no content'}"
               return {
                  "result": "ok",
                  "timestamp": to_iso_utc(None),
                  "error_message": error_msg,
               }
        else:
            # Parsing failed - return error
            error_msg = f"Failed to parse score agent response to EscalationScore format. Content type: {type(calculate_score_response.content) if hasattr(calculate_score_response, 'content') else 'no content'}"
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
