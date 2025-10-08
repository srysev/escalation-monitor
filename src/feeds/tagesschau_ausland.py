# src/feeds/tagesschau.py
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


class TagesschauAuslandFeed(LLMFilterMixin, FeedSource):
    """RSS feed source for Tagesschau international news (Ausland).

    Uses LLM filtering to focus on geopolitically relevant regions and escalation-related topics,
    excluding irrelevant geographic areas and domestic politics without international impact.
    """

    def __init__(self):
        super().__init__(
            source_name="Tagesschau Ausland",
            feed_url="https://www.tagesschau.de/ausland/index~rss2.xml"
        )

        # LLM filtering configuration
        self.time_filter_days = 7  # Last week
        self.llm_filter_threshold = 15  # Activate LLM filter at 15+ items

        # Geographic and thematic filtering criteria
        self.filter_criteria = """
**BEHALTEN - Geografische Hotspots:**
- Russland, Ukraine, Belarus, Baltikum, Polen, Moldau, Georgien
- Naher Osten (Israel, Palästina, Syrien, Iran, Irak, Libanon, Türkei)
- China, Taiwan, Südchinesisches Meer
- Balkan (Serbien, Kosovo, Bosnien)
- Nordafrika (Libyen, Ägypten) und Sahelzone (bei Wagner/Russland-Bezug)

**BEHALTEN - Themen mit Eskalationsbezug:**
- Kriege, Militäroperationen, Waffenlieferungen
- NATO/EU/Russland/China Beziehungen
- Sanktionen, diplomatische Krisen
- Migration/Flüchtlinge aus Konfliktgebieten
- EU-Sicherheitspolitik (Überwachung, Chatkontrolle, Verteidigung)
- Organisierte Kriminalität mit Bezug zu Russland/Konfliktparteien
- Regierungskrisen in strategischen EU-Ländern (Frankreich, Italien, Deutschland)

**AUSSCHLIESSEN:**
- Lateinamerika (außer direkter Russland/China-Einfluss)
- Subsahara-Afrika (außer Wagner/Russland-Aktivitäten)
- Südostasien ohne China-Bezug
- Reine Innenpolitik ohne internationale Auswirkung
- Kriminalität ohne geopolitischen Kontext (italienische/albanische Mafia)
- Sport, Unterhaltung, reine Kulturthemen
- Wirtschaftsnachrichten ohne Sanktions-/Kriegsbezug
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
            return {"User-Agent": "python-httpx/0.27"}  # oder {}
    
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
    """Test the TagesschauFeed implementation."""
    import asyncio
    import httpx

    feed = TagesschauAuslandFeed()

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
