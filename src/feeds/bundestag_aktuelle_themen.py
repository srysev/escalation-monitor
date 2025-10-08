# src/feeds/bundestag_aktuelle_themen.py
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


class BundestagAktuelleThemenFeed(LLMFilterMixin, FeedSource):
    """RSS feed source for Bundestag "Aktuelle Themen" with geopolitical relevance filtering.

    Filters parliamentary news for security policy, defense, migration, sanctions,
    and escalation-relevant topics. Excludes domestic policy without international impact.
    """

    def __init__(self):
        super().__init__(
            source_name="Bundestag Aktuelle Themen",
            feed_url="https://www.bundestag.de/static/appdata/includes/rss/aktuellethemen.rss"
        )

        # LLM filtering configuration (aggressive due to very long texts)
        self.time_filter_days = 7  # Last week
        self.llm_filter_threshold = 1  # Allways activate LLM filter

        # Relevance filtering criteria for parliamentary news
        self.filter_criteria = """
**BEHALTEN - Verteidigung & Sicherheit:**
- Verteidigungspolitik (Wehrdienst, Wehrpflicht, Bundeswehr-Personal, NATO)
- Verteidigungshaushalt, Rüstung, Waffenlieferungen
- Sicherheitsvorfälle
- Verfassungsschutz-Themen mit Auslandsbezug
- Spannungsfall/Verteidigungsfall-relevante Gesetzgebung

**BEHALTEN - Migration & Grenzpolitik:**
- Einbürgerung, Abschiebungen, Grenzkontrollen

**BEHALTEN - Außen- & Geopolitik:**
- Sanktionen (insbesondere Russland, Belarus)
- Außenpolitik-Statements zu Ukraine, Nahost, Taiwan
- EU-Sicherheitspolitik, NATO-Beziehungen
- Energiesicherheit mit Kriegs-/Sanktionsbezug (Gas, Öl)
- Russland/China/USA-Beziehungen

**AUSSCHLIESSEN - Innenpolitik ohne Sicherheitsbezug:**
- Sozialpolitik
- Gesundheitspolitik
- Bildungspolitik
- Verkehrspolitik
- Umweltpolitik ohne geopolitischen Kontext
- Wirtschaftspolitik ohne Kriegsbezug
- Justiz/Prozesse ohne Sicherheitsbezug
- Kultur, Sport, Medien
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
    """Test the BundestagAktuelleThemenFeed implementation."""
    import asyncio
    import httpx

    feed = BundestagAktuelleThemenFeed()

    async with httpx.AsyncClient() as client:
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
                print(f"Text: {item.text[:300]}...")
                print(f"URL: {item.url}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
