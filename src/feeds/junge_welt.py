# src/feeds/junge_welt.py
from __future__ import annotations
import datetime as dt
import re
from typing import Any, Dict, Optional, List
from email.utils import parsedate_tz, mktime_tz

try:
    from .base import FeedSource, FeedItem, to_iso_utc
    from .llm_filtering import LLMFilterMixin
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem, to_iso_utc
    from llm_filtering import LLMFilterMixin


class JungeWeltFeed(LLMFilterMixin, FeedSource):
    """RSS feed source for Junge Welt newsticker."""

    # LLM filtering configuration
    time_filter_days = 2
    llm_filter_threshold = 30
    filter_criteria = """
**Keep items about:**
- Military conflicts, NATO operations, arms deliveries to Ukraine
- Peace movement, anti-war protests, civil disobedience
- Diplomatic tensions, sanctions policy
- US/NATO military presence in Europe
- Ukraine war, Middle East conflicts, Taiwan tensions
- Nuclear weapons, military infrastructure, defense policy
- German foreign/defense policy with geopolitical impact
- International solidarity movements related to war/peace
- Energy geopolitics affecting military conflicts

**Exclude:**
- Pure labor/union news without war/peace context
- Domestic German politics without international relevance
- Culture, sports, entertainment
- Local German news (crime, accidents, regional politics)
- Historical articles without current geopolitical relevance
- Pure economic news without military/sanctions context
"""

    def __init__(self):
        super().__init__(
            source_name="Junge Welt",
            feed_url="https://www.jungewelt.de/feeds/newsticker.rss"
        )

    def _parse_pubdate(self, pubdate_str: str) -> Optional[dt.datetime]:
        """Parse RFC-2822 format date to datetime with timezone."""
        try:
            # Parse RFC-2822 format (e.g., "Thu, 18 Sep 2025 15:30:00 +0200")
            time_tuple = parsedate_tz(pubdate_str)
            if time_tuple:
                timestamp = mktime_tz(time_tuple)
                return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        except (ValueError, TypeError):
            pass
        return None

    def _extract_text(self, description: str) -> str:
        """Extract clean text from HTML description."""
        if not description:
            return ""

        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', description)

        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        return clean_text

    def map_entry(self, entry: Dict[str, Any]) -> Optional[FeedItem]:
        """Map feedparser entry to standardized FeedItem."""
        # Extract basic fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        description = entry.get("description", "")
        pubdate_str = entry.get("published", "")

        # Parse publication date
        pub_datetime = self._parse_pubdate(pubdate_str)
        if not pub_datetime:
            return None  # Skip entries without valid dates

        # Extract and combine text
        description_text = self._extract_text(description)

        # Combine title and description for full context
        if title and description_text:
            text = f"{title}. {description_text}"
        elif title:
            text = title
        elif description_text:
            text = description_text
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
    """Test the JungeWeltFeed implementation."""
    import httpx

    feed = JungeWeltFeed()

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
            for i, item in enumerate(result['items'][:3]):
                print(f"\n--- Item {i+1} ---")
                print(f"Date: {item.date.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"Text: {item.text[:200]}...")
                print(f"URL: {item.url}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())