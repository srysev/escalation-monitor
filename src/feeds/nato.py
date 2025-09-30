# src/feeds/nato.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional, List

try:
    from .base import FeedSource, FeedItem
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem


class NatoFeed(FeedSource):
    """RSS feed source for NATO Latest News."""

    def __init__(self):
        super().__init__(
            source_name="NATO",
            feed_url="https://www.nato.int/cps/rss/en/natohq/rssFeed.xsl/rssFeed.xml"
        )

    def get_headers(self) -> Dict[str, str]:
        """Return NATO-specific headers."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nato.int/',
        }

    def _parse_nato_date(self, date_str: str) -> Optional[dt.datetime]:
        """Parse NATO date format: '19 Sep. 2025 12:00:00 GMT'"""
        try:
            # NATO uses format like "19 Sep. 2025 12:00:00 GMT"
            # Remove the period after month abbreviation
            clean_date = date_str.replace(" GMT", "").replace(".", "")

            # Parse the cleaned date
            parsed_date = dt.datetime.strptime(clean_date, "%d %b %Y %H:%M:%S")

            # Set timezone to UTC (GMT = UTC)
            return parsed_date.replace(tzinfo=dt.timezone.utc)

        except (ValueError, AttributeError):
            pass
        return None

    def map_entry(self, entry: Dict[str, Any]) -> Optional[FeedItem]:
        """Map feedparser entry to standardized FeedItem."""
        # Extract basic fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        summary = entry.get("summary", "").strip()
        published_str = entry.get("published", "")

        # Parse publication date
        pub_datetime = self._parse_nato_date(published_str)
        if not pub_datetime:
            return None  # Skip entries without valid dates

        # Combine title and summary for full context
        if title and summary:
            text = f"{title}. {summary}"
        elif title:
            text = title
        elif summary:
            text = summary
        else:
            text = ""

        if not text.strip():
            return None  # Skip entries without content

        return FeedItem(
            date=pub_datetime,
            text=text,
            url=link
        )

    def filter(self, items: List[FeedItem]) -> List[FeedItem]:
        """Filter items based on relevance criteria. Default: no filtering."""
        # Default implementation: return all items
        # Child classes can override for specific filtering logic
        return items


async def main():
    """Test the NatoFeed implementation."""
    import asyncio
    import httpx

    feed = NatoFeed()

    # Custom headers needed for NATO site
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    async with httpx.AsyncClient(headers=headers) as client:
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