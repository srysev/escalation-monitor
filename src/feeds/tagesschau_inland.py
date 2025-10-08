# src/feeds/tagesschau_inland.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional, List
from email.utils import parsedate_tz, mktime_tz

try:
    from .base import FeedSource, FeedItem
    from .llm_filtering import LLMFilterMixin
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem
    from llm_filtering import LLMFilterMixin


class TagesschauInlandFeed(LLMFilterMixin, FeedSource):
    """RSS feed source for Tagesschau domestic news (Inland) with geopolitical relevance filtering.

    Uses LLM filtering to focus on domestic news with international/security implications,
    excluding pure domestic politics, social issues, and crime without geopolitical context.
    """

    def __init__(self):
        super().__init__(
            source_name="Tagesschau Inland",
            feed_url="https://www.tagesschau.de/inland/index~rss2.xml"
        )

        # LLM filtering configuration
        self.time_filter_days = 7  # Last week
        self.llm_filter_threshold = 15  # Activate LLM filter at 15+ items

        # Relevance filtering criteria for domestic news
        self.filter_criteria = """
**BEHALTEN - Sicherheitspolitik & internationale Bezüge:**
- Migration/Asyl mit EU-/Außenpolitikbezug (EU-Asylreform, Grenzkontrollen)
- Wehrdienst, Wehrpflicht, Bundeswehr-Personalfragen
- Sicherheitsvorfälle mit Auslandsbezug (Drohnen, Spionage, Cyberangriffe)
- Terrorismus, extremistische Netzwerke mit Auslandskontakten
- EU-Sicherheitspolitik (Chatkontrolle, Überwachung, Datenschutz mit EU-Bezug)
- NATO/Russland/China-Bezüge in deutscher Politik
- Verfassungsschutz-relevante Themen mit Auslandsbezug

**BEHALTEN - Geopolitische Innenpolitik:**
- Deutsche Außenpolitik-Statements (Kanzler, Außenminister zu Konflikten)
- Regierungskrisen mit außenpolitischen Auswirkungen
- Sanktionen, Waffenlieferungen, Verteidigungshaushalt
- Energiesicherheit mit Russland/Ukraine-Bezug

**AUSSCHLIESSEN:**
- Reine Innenpolitik ohne internationale Auswirkung (Koalitionsstreit, Wahlkampf)
- Wirtschaftspolitik ohne Kriegs-/Sanktionsbezug (Bürgergeld, Rente, Steuern)
- Gesundheitspolitik (Arztgebühren, Krankenversicherung, Corona ohne internationale Dimension)
- Bildung, Wohnen, Verkehr (Studentenwohnungen, Autoindustrie-Förderung, Verkehrskontrollen)
- Kriminalität ohne geopolitischen Kontext (Zwangsprostitution, Reichsbürger-Prozesse, Neonazi-Anschläge ohne ausländischen Einfluss)
- Justiz/Prozesse ohne Sicherheitsbezug (Verfassungsrichter-Ernennung, Freisprüche)
- Soziale Themen (Arbeitsbedingungen, Integration ohne Asyl-/Migrationsbezug)
- Sport, Kultur, Unterhaltung
"""

    def _parse_pubdate(self, pubdate_str: str) -> Optional[dt.datetime]:
        """Parse RFC-2822 format date to datetime with timezone."""
        try:
            # Parse RFC-2822 format (standard RSS format)
            time_tuple = parsedate_tz(pubdate_str)
            if time_tuple:
                timestamp = mktime_tz(time_tuple)
                return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        except (ValueError, TypeError):
            pass
        return None

    def get_headers(self) -> Dict[str, str]:
        """Return HTTP headers for this feed source."""
        return {"User-Agent": "python-httpx/0.27"}

    def map_entry(self, entry: Dict[str, Any]) -> Optional[FeedItem]:
        """Map feedparser entry to standardized FeedItem."""
        # Extract basic fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        description = entry.get("description", "").strip()
        pubdate_str = entry.get("published", "")

        # Parse publication date
        pub_datetime = self._parse_pubdate(pubdate_str)
        if not pub_datetime:
            return None  # Skip entries without valid dates

        # Combine title and description for full context
        if title and description:
            text = f"{title}. {description}"
        elif title:
            text = title
        elif description:
            text = description
        else:
            text = ""

        if not text.strip():
            return None  # Skip entries without content

        return FeedItem(
            date=pub_datetime,
            text=text,
            url=link
        )


async def main():
    """Test the TagesschauInlandFeed implementation."""
    import asyncio
    import httpx

    feed = TagesschauInlandFeed()

    async with httpx.AsyncClient(headers=feed.get_headers()) as client:
        result = await feed.fetch(client)

        print(f"Source: {result['source_name']}")
        print(f"Result: {result['result']}")
        print(f"Date: {result['date']}")

        if result['result'] == 'error':
            print(f"Error: {result.get('error_message', 'Unknown error')}")
        else:
            print(f"Items found: {len(result['items'])}")

            # Show first few items as examples
            for i, item in enumerate(result['items'][:5]):
                print(f"\n--- Item {i+1} ---")
                print(f"Date: {item.date.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"Text: {item.text}")
                print(f"URL: {item.url}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
