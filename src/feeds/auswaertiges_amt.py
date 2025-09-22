# src/feeds/auswaertiges_amt.py
from __future__ import annotations
import datetime as dt
import re
from typing import Any, Dict, Optional
from email.utils import parsedate_tz, mktime_tz

try:
    from .base import FeedSource, to_iso_utc
except ImportError:
    # For direct execution
    from base import FeedSource, to_iso_utc


class AuswaertigesAmtFeed(FeedSource):
    """RSS feed source for German Federal Foreign Office news."""

    def __init__(self):
        super().__init__(
            source_name="Auswärtiges Amt",
            feed_url="https://www.auswaertiges-amt.de/static/appdata/includes/rss_en/RSS_Aktuelle_Artikel.xml"
        )

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

    def _extract_text(self, description: str) -> str:
        """Extract clean text from HTML description."""
        if not description:
            return ""

        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', description)

        # Clean up whitespace and line breaks
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Remove common HTML entities
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')

        return clean_text

    def map_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Map feedparser entry to standardized format."""
        # Extract basic fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        description = entry.get("description", "")
        pubdate_str = entry.get("published", "")

        # Parse publication date
        pub_datetime = self._parse_pubdate(pubdate_str)
        date_iso = to_iso_utc(pub_datetime)

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

        return {
            "date": date_iso,
            "text": text,
            "url": link
        }


async def main():
    """Test the AuswaertigesAmtFeed implementation."""
    import asyncio
    import httpx

    feed = AuswaertigesAmtFeed()

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
                print(f"Date: {item['date']}")
                print(f"Text: {item['text'][:200]}...")
                print(f"URL: {item['url']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())