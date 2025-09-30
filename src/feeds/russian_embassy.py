# src/feeds/russian_embassy.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional, List
import email.utils

try:
    from .base import FeedSource, FeedItem
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem


class RussianEmbassyFeed(FeedSource):
    """RSS feed source for Russian Embassy in Germany."""

    def __init__(self):
        super().__init__(
            source_name="Russian Embassy Germany",
            feed_url="https://fetchrss.com/feed/aNKhK_-B6U4zaNKXXXURfdVl.rss"
        )

    def get_headers(self) -> Dict[str, str]:
        """Return Russian Embassy-specific headers."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,de-DE,de;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
        }

    def _parse_rfc822_date(self, date_str: str) -> Optional[dt.datetime]:
        """Parse RFC 822 date format: 'Tue, 23 Sep 2025 13:27:07 GMT'"""
        try:
            # Use email.utils.parsedate_to_datetime for RFC 822 format
            parsed_date = email.utils.parsedate_to_datetime(date_str)

            # Ensure timezone is UTC
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=dt.timezone.utc)
            else:
                parsed_date = parsed_date.astimezone(dt.timezone.utc)

            return parsed_date

        except (ValueError, AttributeError, TypeError):
            pass
        return None

    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML content from description field."""
        import re

        if not html_content:
            return ""

        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_content)

        # Replace HTML entities
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')

        # Clean up extra whitespace
        clean_text = ' '.join(clean_text.split())

        return clean_text.strip()

    def map_entry(self, entry: Dict[str, Any]) -> Optional[FeedItem]:
        """Map feedparser entry to standardized FeedItem."""
        # Extract basic fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        description = entry.get("description", "").strip()
        published_str = entry.get("published", "")

        # Parse publication date
        pub_datetime = self._parse_rfc822_date(published_str)
        if not pub_datetime:
            return None  # Skip entries without valid dates

        # Clean HTML from description
        clean_description = self._clean_html_content(description)

        # Combine title and description for full context
        if title and clean_description:
            text = f"{title}. {clean_description}"
        elif title:
            text = title
        elif clean_description:
            text = clean_description
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
        """Filter items based on relevance criteria."""
        # Filter items from the last 3 months (similar to AuswaertigesAmtFeed)
        cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)

        filtered_items = [
            item for item in items
            if item.date >= cutoff_date
        ]

        return filtered_items


async def main():
    """Test the RussianEmbassyFeed implementation."""
    import httpx

    feed = RussianEmbassyFeed()

    # Standard headers
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