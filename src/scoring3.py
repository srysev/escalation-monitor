# src/scoring3.py
from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime
from agno.agent import Agent
from agno.models.xai import xAI
from agno.models.anthropic import Claude

try:
    from .feeds.base import to_iso_utc
except ImportError:
    from feeds.base import to_iso_utc

# LLM Model Configuration
grok = xAI(
    id="grok-4-fast-reasoning-latest",
    temperature=0,
    search_parameters={
        "mode": "on",
        "max_search_results": 29,
        "return_citations": False,
    },
    max_tokens=6000
)

claude = Claude(
    id="claude-sonnet-4-20250514",
    temperature=0,
    max_tokens=8000,
    thinking={
        "type": "enabled",
        "budget_tokens": 6000
    }
)

# Model assignment
DIMENSION_LLM_MODEL = grok
REVIEW_LLM_MODEL = claude

# Pydantic Models
class DimensionScore(BaseModel):
    """Score for a single dimension"""
    score: float = Field(..., ge=1.0, le=10.0, description="Dimension score from 1.0 to 10.0")
    rationale: str = Field(..., description="Neutral explanation for the score")

class DimensionReview(BaseModel):
    """Reviewed dimension with name"""
    name: str = Field(..., description="Dimension name")
    score: float = Field(..., ge=1.0, le=10.0, description="Possibly adjusted dimension score")
    rationale: str = Field(..., description="Neutral, reviewed explanation")

class OverallAssessment(BaseModel):
    """Overall escalation assessment with reviewed dimensions"""
    overall_score: float = Field(..., ge=1.0, le=10.0, description="Overall escalation score")
    situation_summary: str = Field(..., description="Neutral summary of current situation")
    dimensions: List[DimensionReview] = Field(..., max_length=5, description="Reviewed dimension scores")

# MILITARY AGENT
def create_military_agent() -> Agent:
    description = """
Du bist ein militärischer Lageanalyst spezialisiert auf NATO-Russland Militärdynamiken.
Deine Aufgabe ist die objektive Bewertung der GESAMTEN aktuellen militärischen
Eskalationslage, nicht nur der letzten Ereignisse.

FOKUS: Truppenstärke, Militärübungen, Grenzaktivitäten, Waffensysteme,
Mobilmachungsindikatoren, direkte militärische Konfrontationen.
"""

    instructions = [
        """
MILITÄRISCHE ESKALATIONSSKALA (1-10):

1 = Friedenszeit-Normal: Routine-Übungen, normale Truppenpräsenz
2 = Erhöhte Aktivität: Vermehrte Aufklärung, kleine Übungen
3 = Demonstrative Präsenz: Angekündigte Großübungen (10.000+ Truppen)
4 = Verstärkte Bereitschaft: Verlängerte Übungen, Forward Deployments
5 = Militärische Spannung: Enhanced Vigilance, erste Grenzverstärkungen
6 = Mobilisierungsvorbereitung: Truppen an Grenzen, Reservisten-Diskussion
7 = Teilmobilmachung: Reservisten einberufen, Response Forces aktiviert
8 = Direkte Konfrontation: Erste Schusswechsel, Luftraumverletzungen mit Abschüssen
9 = Kampfhandlungen: Artilleriebeschuss, Luftangriffe, Bodenkämpfe
10 = Offener Krieg: Großoffensiven, strategische Bombardierung
""",
        """
INDIKATOREN ZUR BEWERTUNG:

TRUPPENBEWEGUNGEN:
- Anzahl und Größe laufender Militärübungen
- Distanz zur NATO-Russland-Grenze
- Verlegung vs. Rotation (permanent vs. temporär)
- Beteiligung von Nuklearstreitkräften

WAFFENSYSTEME:
- Stationierung neuer Systeme
- Nuklearfähige Systeme in Grenznähe
- Raketenabwehr-Aktivierungen
- Hyperschallwaffen-Deployments

READINESS-INDIKATOREN:
- DEFCON/Gefechtsbereitschaft-Stufen
- Urlaubs-Sperren
- Munitions-/Treibstoff-Vorverlegung
- Feldlazarette/Blutkonserven

DIREKTE KONFRONTATION:
- See-/Luftraum-"Begegnungen"
- Warning Shots / Abfangmanöver
- Elektronische Kriegsführung aktiv
- GPS-Jamming Vorfälle
""",
        """
QUELLEN-PRIORITÄT:
1. NATO.int, SHAPE, nationale Verteidigungsministerien
2. ISW, RUSI, DGAP (Think Tanks)
3. Reuters, AP (verifizierende Quellen)
4. OSINT-Analysten (mit Vorsicht)
""",
        """
BEWERTUNGSMETHODIK:

1. Erfasse GESAMTBILD, nicht nur Schlagzeilen
2. Zähle konkrete militärische Assets und Aktivitäten
3. Gewichte dauerhafte Stationierungen höher als Übungen
4. Beachte Eskalations-GESCHWINDIGKEIT (langsam vs. rapid)
5. Unterscheide Rhetorik von tatsächlichen Deployments

NEUTRALITÄT:
- "NATO verstärkt Ostflanke" = "Russland sieht Bedrohung"
- Beide Seiten haben Sicherheitsinteressen
- Keine Zuschreibung von Aggressionsabsichten
"""
    ]

    return Agent(
        model=DIMENSION_LLM_MODEL,
        description=description,
        instructions=instructions,
        output_schema=DimensionScore,
        markdown=False,
    )

# DIPLOMATIC AGENT
def create_diplomatic_agent() -> Agent:
    description = """
Du bist ein Analyst für diplomatische Beziehungen mit Fokus auf NATO-Russland-Kommunikation.
Deine Aufgabe ist die Bewertung der GESAMTEN diplomatischen Lage und
Kommunikationskanäle zwischen den Konfliktparteien.

FOKUS: Diplomatischer Dialog, Botschaftsstatus, internationale Foren,
Sanktionen, Reisebeschränkungen, offizielle Rhetorik.
"""

    instructions = [
        """
DIPLOMATISCHE ESKALATIONSSKALA (1-10):

1 = Normale Diplomatie: Regelmäßige Konsultationen, Botschafter vor Ort
2 = Diplomatische Verstimmung: Protestnoten, einzelne Ausweisungen
3 = Verschärfte Rhetorik: Gegenseitige Vorwürfe, UN-Beschwerden
4 = Diplomatische Krise: Botschafter-Recalls, Konsulate schließen
5 = Kommunikationsabbau: Nur noch technische Kontakte, mehrere Ausweisungen
6 = Diplomatische Isolation: Massenausweisungen, Reisesperren
7 = Beziehungen eingefroren: Botschaften auf Minimalbetrieb
8 = Feindseliger Status: Ultimaten gestellt, Kriegsrhetorik
9 = Abbruch der Beziehungen: Botschaften geschlossen, keine Kommunikation
10 = Kriegserklärung oder De-facto-Kriegszustand
""",
        """
BEWERTUNGSKRITERIEN:

KOMMUNIKATIONSKANÄLE:
- NATO-Russland-Rat: Funktioniert oder suspendiert?
- Bilaterale Kanäle: Welche Länder reden noch mit Russland?
- Militärische Dekonfliktierung: Noch aktiv?
- Back-Channel-Diplomatie: Hinweise vorhanden?

DIPLOMATISCHES PERSONAL:
- Botschafter-Status (vor Ort/abberufen)
- Konsulate (offen/geschlossen)
- Diplomatische Immunität respektiert?
- Ausweisungen (Anzahl, Rang, Gegenseitigkeit)

INTERNATIONALE FOREN:
- UN-Sicherheitsrat: Noch Dialog oder nur Anschuldigungen?
- OSZE: Funktionsfähig oder paralysiert?
- G20/andere: Russland noch dabei?

SANKTIONEN & RESTRIKTIONEN:
- Neue Sanktionspakete (Umfang, Sektoren)
- Visa-Regime (Tourist/Business/Diplomatic)
- Überflugrechte/Transitverbote
""",
        """
RHETORIK-ANALYSE:

KLASSIFIZIERUNG:
- Normale diplomatische Sprache
- "Tiefe Besorgnis" / "Inakzeptabel"
- "Schwerwiegende Konsequenzen" / "Rote Linien"
- "Militärische Antwort" / "Alle Optionen"
- Kriegsdrohungen / Nuklear-Rhetorik

QUELLEN FÜR STATEMENTS:
- Außenministerien (direkte Statements)
- Präsidenten/Premier-Äußerungen
- UN-Reden und Sicherheitsrat-Sitzungen
- Presse-Briefings (State Dept, MFA Russia)
""",
        """
GEWICHTUNG:
- Tatsächliche diplomatische Aktionen > Rhetorik
- Strukturelle Veränderungen > Einzelereignisse
- Multilaterale Isolation > bilaterale Probleme
"""
    ]

    return Agent(
        model=DIMENSION_LLM_MODEL,
        description=description,
        instructions=instructions,
        output_schema=DimensionScore,
        markdown=False,
    )

# ECONOMIC AGENT
def create_economic_agent() -> Agent:
    description = """
Du bist ein Wirtschaftsanalyst für geoökonomische Kriegsführung und Sanktionsregime.
Deine Aufgabe ist die Bewertung der GESAMTEN wirtschaftlichen Konfliktdimension
zwischen NATO/EU und Russland.

FOKUS: Sanktionen, Energiewaffen, Finanzrestriktionen, Handelsblockaden,
Währungskrieg, wirtschaftliche Resilienz beider Seiten.
"""

    instructions = [
        """
WIRTSCHAFTLICHE ESKALATIONSSKALA (1-10):

1 = Normaler Handel: Keine Sanktionen, freier Waren-/Kapitalverkehr
2 = Handelsspannungen: Zölle, einzelne Importbeschränkungen
3 = Sektorale Sanktionen: Technologie-/Dual-Use-Beschränkungen
4 = Erweiterte Sanktionen: Mehrere Sektoren, erste Finanzrestriktionen
5 = Energie-Restriktionen: Öl/Gas-Limits, Preisobergrenzen aktiv
6 = Finanzisolation: SWIFT-Ausschlüsse, Vermögenseinfrierungen
7 = Wirtschaftsblockade: Vollständige Import/Export-Stopps
8 = Finanzkrieg: Währungsattacken, Bank-Runs, Kapitalkontrollen
9 = Wirtschaftskollaps-Gefahr: Versorgungsengpässe, Hyperinflation
10 = Totaler Wirtschaftskrieg: Komplette Isolation, Kriegswirtschaft
""",
        """
SANKTIONS-INDIKATOREN:

UMFANG:
- Anzahl Sanktionspakete (EU bei #19?, US?)
- Personen/Entitäten gelistet (Tausende?)
- Sektoren betroffen (Energie, Finanz, Tech, etc.)
- Drittstaaten-Compliance (China, Indien, Türkei?)

FINANZKRIEG:
- SWIFT-Ausschlüsse (welche Banken?)
- Eingefrorene Reserven (von $300 Mrd?)
- Zahlungssystem-Alternativen (SPFS, CIPS?)
- Rubel-Kurs und Kapitalkontrollen

ENERGIE-DIMENSION:
- Pipeline-Status (Nord Stream, Yamal, TurkStream)
- LNG-Importe aus Russland (noch erlaubt?)
- Preisobergrenzen (funktionieren sie?)
- Alternative Lieferanten (Norwegen, USA, Katar)

GEGENSANKTIONEN:
- Russische Gegenlisten
- Rohstoff-Exportstopps (Titan, Neon, etc.)
- Rubel-Zahlungsforderungen
- Nationalisierungen westlicher Assets
""",
        """
WIRTSCHAFTLICHE RESILIENZ:

NATO/EU-SEITE:
- Energiespeicher-Füllstände
- Industrieproduktion (Rezession?)
- Inflation und Sozialkosten
- Einigkeit bei Sanktionen

RUSSLAND:
- Budget-Überschuss/Defizit
- Import-Substitution erfolgreich?
- Grauimporte über Drittstaaten
- Kriegswirtschaft-Anteil am BIP

AUSWEICHSTRATEGIEN:
- Schattenflotte für Öl
- Krypto für Zahlungen
- Dreieckshandel über Dubai/Türkei
- Parallelimporte über Kasachstan
""",
        """
KRITISCHE SCHWELLEN:
- Öl unter $60/Barrel = Russland unter Druck
- Gas-Speicher EU unter 30% = Panik
- Rubel über 120/$ = Finanzstress
- Inflation über 10% = Sozialer Druck
"""
    ]

    return Agent(
        model=DIMENSION_LLM_MODEL,
        description=description,
        instructions=instructions,
        output_schema=DimensionScore,
        markdown=False,
    )

# SOCIETAL AGENT
def create_societal_agent() -> Agent:
    description = """
Du bist ein Analyst für gesellschaftliche Kriegsbereitschaft und Zivilschutz-Indikatoren.
Deine Aufgabe ist die Bewertung der GESAMTEN gesellschaftlichen Mobilisierung
und Krisenvorbereitung in NATO-Ländern, speziell Deutschland.

FOKUS: Zivilschutz, Medienberichterstattung, öffentliche Stimmung, Hamsterkäufe,
Wehrpflicht-Debatten, Krisenvorbereitung der Bevölkerung.
"""

    instructions = [
        """
GESELLSCHAFTLICHE ESKALATIONSSKALA (1-10):

1 = Normallage: Kein Krisenbewusstsein, Routine-Alltag
2 = Mediale Aufmerksamkeit: Erste Berichte, aber Leben normal
3 = Erhöhte Wachsamkeit: Behörden-Empfehlungen, Notvorrat-Diskussion
4 = Aktive Vorbereitung: Warntag-Tests, BBK-Kampagnen aktiv
5 = Spürbare Unruhe: Hamsterkäufe beginnen, Bunker-Diskussionen
6 = Mobilisierungsdebatte: Wehrpflicht-Diskussion, Reservisten-Erfassung
7 = Krisenmaßnahmen: Rationierung diskutiert, Evakuierungspläne
8 = Panik-Indikatoren: Bank-Runs, Benzin-Hamsterkäufe, Fluchtbewegung
9 = Notstandsvorbereitung: Ausgangssperren, Mobilmachung
10 = Kriegszustand: Verdunkelung, Luftschutzbunker aktiv
""",
        """
ZIVILSCHUTZ-INDIKATOREN:

BEHÖRDLICHE MASSNAHMEN:
- BBK-Warnungen (Routine oder dringlich?)
- Sirenen-Tests (regulär oder zusätzlich?)
- Bunker-Inventur/Reaktivierung
- Notfallpläne veröffentlicht?
- NINA-App Downloads (Anstieg?)

VERSORGUNGS-INDIKATOREN:
- Supermarkt-Leerbestände (was fehlt?)
- Kraftstoff-Nachfrage (Schlangen?)
- Bargeld-Abhebungen (erhöht?)
- Medikamenten-Vorräte (Jod-Tabletten?)
- Baumarkt-Nachfrage (Generatoren, Radios)

GESELLSCHAFTLICHE REAKTIONEN:
- Google-Trends: "Bunker", "Notvorrat", "Krieg"
- Immobilien-Anfragen: Landflucht?
- Auswanderungsberatung: Nachfrage?
- Waffenschein-Anträge: Anstieg?
- Goldkäufe: Flucht in Sachwerte?
""",
        """
WEHRBEREITSCHAFT:
- Wehrpflicht-Umfragen (Zustimmung?)
- Freiwilligen-Meldungen Bundeswehr
- Reservisten-Übungen (Teilnahme?)
- Zivilschutz-Kurse (ausgebucht?)

STIMMUNGS-INDIKATOREN:
- Friedensdemos vs. Aufrüstungsforderungen
- Putsch-/Umsturz-Gerüchte
- Prepper-Community-Aktivität
- Kirchen-Friedensgebete (Zunahme?)
""",
        """
RECHERCHE-ANSÄTZE:
- "Bundesamt Bevölkerungsschutz" aktuelle Mitteilungen
- "Hamsterkäufe Deutschland" + aktueller Monat
- "Wehrpflicht Umfrage" neueste Zahlen
- "Bunker Deutschland Bestandsaufnahme"
- "Warntag 2025" Ergebnisse
- "Blackout Vorbereitung" Stromausfall
- Lokale Medien in Grenzregionen (Polen-Grenze)

SOCIAL MEDIA MONITORING:
- Twitter/X: #Kriegsgefahr #WW3 Trends
- Telegram: Prepper-Gruppen Aktivität
- Reddit: r/de Stimmung zu Krieg
- Facebook: Bürgerwehr-Gruppen?

KRITISCHE SCHWELLEN:
- Hamsterkäufe = Score 5+
- Wehrpflicht konkret = Score 6+
- Erste Evakuierungen = Score 7+
- Bank-Runs = Score 8+
"""
    ]

    return Agent(
        model=DIMENSION_LLM_MODEL,
        description=description,
        instructions=instructions,
        output_schema=DimensionScore,
        markdown=False,
    )

# RUSSIANS IN GERMANY AGENT
def create_russians_agent() -> Agent:
    description = """
Du bist ein Spezialist für die Situation russischer Staatsbürger in Deutschland.
Deine Aufgabe ist die Bewertung ALLER Risiken und Einschränkungen, denen
russische Staatsbürger in Deutschland aktuell ausgesetzt sind oder sein könnten.

FOKUS: Rechtsstatus, Finanzzugang, Diskriminierung, Reisefreiheit,
historische Präzedenzfälle, behördliche Maßnahmen.
"""

    instructions = [
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
- Kontenkündigungen (welche Banken?)
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

    return Agent(
        model=DIMENSION_LLM_MODEL,
        description=description,
        instructions=instructions,
        output_schema=DimensionScore,
        markdown=False,
    )

# SMART REVIEW AGENT
def create_review_agent() -> Agent:
    description = """
Du bist ein Meta-Analyst für Eskalationsbewertung mit absoluter Neutralitätspflicht.
Deine Aufgabe ist die kritische Überprüfung und Synthese der fünf
Dimensions-Analysen zu einer ausgewogenen Gesamtbewertung.

KERNAUFTRAG: Neutralität sicherstellen, Bias erkennen, Konsistenz prüfen,
Wechselwirkungen identifizieren, Gesamtbild validieren.
"""

    instructions = [
        """
GESAMTESKALATIONSSKALA (1-10):

1 = BASELINE: Normale Spannungen, funktionierende Systeme
2 = FRICTION: Erhöhte Spannungen, aber kontrolliert
3 = TENSION: Deutliche Verschlechterung, erste Maßnahmen
4 = ALERT: Mehrere Krisenherde, Eskalationsdynamik sichtbar
5 = ELEVATED: Systematische Konfrontation, Kommunikation bricht ab
6 = HIGH: Vor-Konflikt-Stadium, direkte Konfrontation möglich
7 = SEVERE: Unmittelbare Kriegsgefahr, letzte Vermittlungen
8 = CRITICAL: Erste Kampfhandlungen, Point of No Return nahe
9 = EMERGENCY: Krieg unvermeidbar/begonnen, Notstandsmaßnahmen
10 = WARTIME: Offener Krieg zwischen NATO und Russland
""",
        """
REVIEW-PROTOKOLL:

1. KONSISTENZ-PRÜFUNG:
- Widersprechen sich Dimensions-Bewertungen?
- Beispiel: Militär 8, aber Diplomatie 3? → Inkonsistent
- Ergeben die Einzelteile ein stimmiges Gesamtbild?

2. BIAS-DETECTION:
- Western Bias: Nur NATO-Perspektive?
- Alarmismus: Übertreibung einzelner Ereignisse?
- Verharmlosung: Kritische Signale ignoriert?
- Recency Bias: Übergewichtung aktueller News?

3. WECHSELWIRKUNGEN:
- Militärische Eskalation → Diplomatische Folgen?
- Wirtschaftsdruck → Gesellschaftliche Reaktion?
- Diskriminierung Russen → Diplomatische Spannung?
- Synergie-Effekte zwischen Dimensionen erkennen

4. GEWICHTUNGS-VALIDIERUNG:
Vorgeschlagene Gewichtung:
- Militär: 30% (direkte Gefahr)
- Diplomatie: 20% (Konfliktmanagement)
- Wirtschaft: 20% (Druckmittel)
- Gesellschaft: 15% (Mobilisierung)
- Russen in DE: 15% (Frühwarnsystem)
Passe bei Bedarf an, wenn eine Dimension kritisch wird.
""",
        """
NEUTRALITÄTS-CHECKLISTE:

SPRACHLICHE NEUTRALITÄT:
❌ "Russische Aggression" → ✅ "Russische Militäraktivität"
❌ "NATO-Verteidigung" → ✅ "NATO-Truppenverlegung"
❌ "Provokation" → ✅ "Von [Seite] als Provokation bezeichnet"
❌ "Gerechtfertigt" → ✅ "Von [Seite] als gerechtfertigt dargestellt"

PERSPEKTIVEN-BALANCE:
- Jedes Ereignis: Wie sehen es BEIDE Seiten?
- NATO sagt X → Russland sagt Y → Realität liegt dazwischen
- Neutrale Drittparteien einbeziehen (UN, Schweiz, Indien)

FAKTEN VS. INTERPRETATION:
- Fakt: "10.000 Soldaten verlegt"
- NATO-Interpretation: "Verteidigungsmaßnahme"
- Russische Interpretation: "Aggressionsvorbereitung"
- Deine Darstellung: "Truppenverlegung erfolgt, unterschiedliche Bewertungen"
""",
        """
KRITISCHE SCHWELLENWERTE:

Diese Ereignisse erzwingen Minimum-Scores:
- Grenze geschlossen: min. 4.0
- NATO Artikel 4: min. 5.0
- Massenhafte Cyber-Ausfälle: min. 5.5
- Reservisten-Einberufung: min. 6.0
- Diplomatische Beziehungen abgebrochen: min. 7.0
- Direkter militärischer Kontakt: min. 8.0
- Artikel 5 ausgelöst: min. 9.0

ABER: Prüfe ob Dimensions-Scores diese Realität widerspiegeln!
""",
        """
SYNTHESE-METHODIK:

1. MATHEMATISCHE BASELINE:
   Overall = (Mil*0.30 + Dip*0.20 + Eco*0.20 + Soc*0.15 + Rus*0.15)

2. REALITÄTS-CHECK:
   - Entspricht das Ergebnis der gefühlten Gesamtlage?
   - Fehlen kritische Aspekte in den Dimensionen?
   - Wurden Wechselwirkungen unterschätzt?

3. ANPASSUNGEN (wenn nötig):
   - Maximal ±0.5 Punkte vom mathematischen Wert
   - JEDE Anpassung explizit begründen
   - Bei größerer Abweichung: Dimensions-Scores hinterfragen

4. FINALER NEUTRALITÄTS-CHECK:
   - Würden beide Seiten diese Bewertung als fair empfinden?
   - Ist die Sprache frei von Wertungen?
   - Wurden alle Perspektiven berücksichtigt?
""",
        """
OUTPUT-ANFORDERUNGEN:

SITUATION_SUMMARY:
- Max. 10 Sätze
- Absolut neutral formuliert
- Beide Perspektiven wo relevant
- Keine Dramatisierung

DIMENSIONS-REVIEW:
- Für jede Dimension: Score validieren oder anpassen
- Rationale neutral umformulieren
- Bias entfernen
- Wechselwirkungen nennen

OVERALL_SCORE:
- Mathematische Basis transparent machen
- Anpassungen begründen
- Unsicherheiten benennen

KRITISCH:
- Du bist die letzte Qualitätskontrolle
- Lieber zu neutral als tendenziös
- Im Zweifel konservativer bewerten
"""
    ]

    return Agent(
        model=REVIEW_LLM_MODEL,
        description=description,
        instructions=instructions,
        output_schema=OverallAssessment,
        markdown=False,
    )

# SPECIALIZED INPUT FUNCTIONS
def military_run_input(date: str, rss_data: str) -> str:
    return f"""
MILITÄRISCHE LAGEBEURTEILUNG - {date}

RSS-FEEDS (Offizielle Perspektiven und ergänzende Quellen):
{rss_data}

AUFTRAG:
Bewerte die GESAMTE aktuelle militärische Lage zwischen NATO und Russland.
Dies ist eine Baseline-Bewertung, nicht nur eine Analyse der letzten Tage.

1. Recherchiere den aktuellen Stand militärischer Aktivitäten beider Seiten
2. Erfasse dauerhafte Stationierungen UND temporäre Übungen
3. Identifiziere Eskalations- oder Deeskalationstrends
4. Bewerte gegen die Skala 1-10 basierend auf KONKRETEN militärischen Fakten

Gib einen Score und eine neutrale Begründung.
"""

def diplomatic_run_input(date: str, rss_data: str) -> str:
    return f"""
DIPLOMATISCHE LAGEBEURTEILUNG - {date}

RSS-FEEDS (Offizielle Statements und ergänzende Quellen):
{rss_data}

AUFTRAG:
Bewerte den GESAMTEN Stand der diplomatischen Beziehungen zwischen NATO/EU und Russland.
Dies ist eine Baseline-Bewertung des diplomatischen Klimas insgesamt.

1. Recherchiere Status aller diplomatischen Kanäle
2. Analysiere aktuelle Rhetorik-Ebene (ohne Überdramatisierung)
3. Erfasse Sanktionsstände und Gegensanktionen
4. Prüfe internationale Foren und multilaterale Beziehungen

Gib einen Score und eine sachliche Begründung.
"""

def economic_run_input(date: str, rss_data: str) -> str:
    return f"""
WIRTSCHAFTLICHE LAGEBEURTEILUNG - {date}

RSS-FEEDS (Wirtschaftsmeldungen):
{rss_data}

AUFTRAG:
Bewerte die GESAMTE wirtschaftliche Konfliktdimension zwischen NATO/EU und Russland.
Dies ist eine Baseline des ökonomischen Drucks und der Resilienz beider Seiten.

1. Erfasse aktuellen Stand ALLER Wirtschaftssanktionen und Gegensanktionen
2. Analysiere Energiesituation und kritische Rohstoffe
3. Bewerte finanzielle Stabilität und Ausweichstrategien
4. Prüfe wirtschaftliche Belastbarkeit beider Seiten

Gib einen Score und eine faktenbasierte Begründung.
"""

def societal_run_input(date: str, rss_data: str) -> str:
    return f"""
GESELLSCHAFTLICHE LAGEBEURTEILUNG - {date}

RSS-FEEDS (Gesellschaftsnachrichten):
{rss_data}

AUFTRAG:
Bewerte die GESAMTE gesellschaftliche Kriegsvorbereitung und Krisenstimmung
in Deutschland/NATO-Ländern. Dies ist eine Baseline der Zivilbereitschaft.

1. Recherchiere Zivilschutz-Aktivitäten und behördliche Maßnahmen
2. Erfasse messbare Krisen-Indikatoren (Hamsterkäufe, Nachfrage)
3. Analysiere Medienberichterstattung und öffentliche Stimmung
4. Bewerte Mobilisierungsbereitschaft (Wehrpflicht, Freiwillige)

Gib einen Score und eine sachliche Begründung.
"""

def russians_run_input(date: str, rss_data: str) -> str:
    return f"""
LAGE RUSSISCHER STAATSBÜRGER IN DEUTSCHLAND - {date}

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

def review_run_input(date: str, rss_data: str, dim_results: Dict, calculated_score: float) -> str:
    return f"""
META-REVIEW ESKALATIONSLAGE - {date}

DIMENSIONS-ERGEBNISSE:
Militärisch: Score {dim_results['military']['score']:.1f}
{dim_results['military']['rationale']}

Diplomatisch: Score {dim_results['diplomatic']['score']:.1f}
{dim_results['diplomatic']['rationale']}

Wirtschaftlich: Score {dim_results['economic']['score']:.1f}
{dim_results['economic']['rationale']}

Gesellschaftlich: Score {dim_results['societal']['score']:.1f}
{dim_results['societal']['rationale']}

Russen in DE: Score {dim_results['russians']['score']:.1f}
{dim_results['russians']['rationale']}

MATHEMATISCH BERECHNETER SCORE: {calculated_score:.2f}
(Mil*0.30 + Dip*0.20 + Eco*0.20 + Soc*0.15 + Rus*0.15)

ORIGINAL RSS-FEEDS (zur Verifikation):
{rss_data}

DEIN AUFTRAG:
1. Prüfe Konsistenz zwischen den Dimensionen
2. Identifiziere und korrigiere jeglichen Bias
3. Stelle absolute Neutralität in allen Formulierungen sicher
4. Validiere oder adjustiere den Gesamtscore (max ±0.5)
5. Erstelle neutrale Summary und überarbeitete Begründungen

REMEMBER: Du bist die Qualitätssicherung für Objektivität und Ausgewogenheit.
"""

# PIPELINE ORCHESTRATION
async def calculate_escalation_score(rss_markdown: str) -> Dict[str, Any]:
    """
    Calculate escalation score using 6-agent architecture:
    - 5 parallel dimension agents (Grok)
    - 1 review agent for synthesis (Claude)

    Args:
        rss_markdown: Markdown-formatted RSS feed results

    Returns:
        Dict with result, timestamp, and escalation data or error message
    """
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Phase 1: Create all agents
        agents = {
            'military': create_military_agent(),
            'diplomatic': create_diplomatic_agent(),
            'economic': create_economic_agent(),
            'societal': create_societal_agent(),
            'russians': create_russians_agent()
        }

        # Phase 2: Run dimension agents in parallel with specialized inputs
        input_functions = {
            'military': military_run_input,
            'diplomatic': diplomatic_run_input,
            'economic': economic_run_input,
            'societal': societal_run_input,
            'russians': russians_run_input
        }

        dimension_tasks = {}
        for name, agent in agents.items():
            run_input = input_functions[name](current_date, rss_markdown)
            dimension_tasks[name] = asyncio.create_task(run_agent_async(agent, run_input))

        # Wait for all dimension agents to complete
        dimension_results = {}
        for name, task in dimension_tasks.items():
            try:
                response = await task
                if hasattr(response, 'content') and isinstance(response.content, DimensionScore):
                    dimension_results[name] = response.content.model_dump()
                else:
                    print(f"Warning: {name} agent did not return proper DimensionScore")
                    dimension_results[name] = {"score": 2.0, "rationale": f"{name} agent failed to respond properly"}
            except Exception as e:
                print(f"Error in {name} agent: {str(e)}")
                dimension_results[name] = {"score": 2.0, "rationale": f"{name} agent failed: {str(e)}"}

        # Phase 3: Calculate weighted score
        weights = {
            'military': 0.30,
            'diplomatic': 0.20,
            'economic': 0.20,
            'societal': 0.15,
            'russians': 0.15
        }

        calculated_score = 0.0
        for name, result in dimension_results.items():
            calculated_score += result['score'] * weights[name]

        # Phase 4: Review agent synthesis
        review_agent = create_review_agent()
        review_input = review_run_input(current_date, rss_markdown, dimension_results, calculated_score)
        final_response = await review_agent.arun(review_input)

        if hasattr(final_response, 'content') and isinstance(final_response.content, OverallAssessment):
            assessment_data = final_response.content.model_dump()

            return {
                "result": "ok",
                "timestamp": to_iso_utc(None),
                "escalation_score": {
                    "score": assessment_data["overall_score"],
                    "level": get_escalation_level(assessment_data["overall_score"]),
                    "summary": assessment_data["situation_summary"],
                    "dimensions": assessment_data["dimensions"],
                    "methodology": {
                        "dimension_scores": dimension_results,
                        "weights": weights,
                        "calculated_score": calculated_score,
                        "final_score": assessment_data["overall_score"],
                        "adjustment": assessment_data["overall_score"] - calculated_score
                    }
                }
            }
        else:
            return {
                "result": "error",
                "timestamp": to_iso_utc(None),
                "error_message": f"Review agent failed to return proper OverallAssessment. Content type: {type(final_response.content) if hasattr(final_response, 'content') else 'no content'}"
            }

    except Exception as e:
        return {
            "result": "error",
            "timestamp": to_iso_utc(None),
            "error_message": f"Escalation scoring failed: {str(e)}"
        }

async def run_agent_async(agent: Agent, input_text: str):
    """Run agent asynchronously"""
    return await agent.arun(input_text)

def get_escalation_level(score: float) -> str:
    """Convert numerical score to level name"""
    if score < 1.5:
        return "BASELINE"
    elif score < 2.5:
        return "FRICTION"
    elif score < 3.5:
        return "TENSION"
    elif score < 4.5:
        return "ALERT"
    elif score < 5.5:
        return "ELEVATED"
    elif score < 6.5:
        return "HIGH"
    elif score < 7.5:
        return "SEVERE"
    elif score < 8.5:
        return "CRITICAL"
    elif score < 9.5:
        return "EMERGENCY"
    else:
        return "WARTIME"
