# src/feeds/frontex.py
from __future__ import annotations
import datetime as dt
from datetime import timedelta
from typing import Any, Dict, Optional, List

try:
    from .base import FeedSource, FeedItem
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem


class FrontexFeed(FeedSource):
    """RSS feed source for Frontex News Releases."""

    def __init__(self):
        super().__init__(
            source_name="Frontex",
            feed_url="https://www.frontex.europa.eu/media-centre/news/news-release/feed"
        )

    def _parse_frontex_date(self, date_str: str) -> Optional[dt.datetime]:
        """Parse Frontex ISO 8601 date format: '2025-09-18T10:35:21Z'"""
        try:
            # Frontex uses standard ISO 8601 format with Z (UTC) timezone
            # Remove the Z and parse as naive datetime, then set UTC timezone
            if date_str.endswith('Z'):
                clean_date = date_str[:-1]  # Remove 'Z'
            else:
                clean_date = date_str

            # Parse the ISO format
            parsed_date = dt.datetime.fromisoformat(clean_date)

            # Set timezone to UTC
            return parsed_date.replace(tzinfo=dt.timezone.utc)

        except (ValueError, AttributeError):
            pass
        return None

    def map_entry(self, entry: Dict[str, Any]) -> Optional[FeedItem]:
        """Map feedparser entry to standardized FeedItem."""
        # Extract basic fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        content = entry.get("content", [])
        summary = entry.get("summary", "").strip()
        published_str = entry.get("published", "")

        # Parse publication date
        pub_datetime = self._parse_frontex_date(published_str)
        if not pub_datetime:
            return None  # Skip entries without valid dates

        # Extract content text (Atom feeds can have content in different formats)
        content_text = ""
        if content and isinstance(content, list) and len(content) > 0:
            content_text = content[0].get("value", "").strip()
        elif summary:
            content_text = summary

        # Combine title and content for full context
        if title and content_text:
            text = f"{title}. {content_text}"
        elif title:
            text = title
        elif content_text:
            text = content_text
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
        """Filter items to only include those from the last X days"""
        cutoff_date = dt.datetime.now(dt.timezone.utc) - timedelta(days=7)

        # Filter items by date
        filtered_items = [
            item for item in items
            if item.date >= cutoff_date
        ]

        return filtered_items


async def main():
    """Test the FrontexFeed implementation."""
    import asyncio
    import httpx

    feed = FrontexFeed()

    # Standard headers for HTTP requests
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