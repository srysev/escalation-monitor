# src/feeds/rbc_politics.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional, List
import email.utils

try:
    from .base import FeedSource, FeedItem
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem


class RBCPoliticsFeed(FeedSource):
    """RSS feed source for RBC News - Politics category only."""

    def __init__(self):
        super().__init__(
            source_name="RBC Politics",
            feed_url="https://rssexport.rbc.ru/rbcnews/news/30/full.rss"
        )

    def get_headers(self) -> Dict[str, str]:
        """Return RBC-specific headers."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.rbc.ru/',
        }

    def _parse_rbc_date(self, date_str: str) -> Optional[dt.datetime]:
        """Parse RBC date format: 'Tue, 23 Sep 2025 16:47:08 +0300'"""
        try:
            # Use email.utils.parsedate_to_datetime for RFC 822-like format
            parsed_date = email.utils.parsedate_to_datetime(date_str)

            # Convert to UTC
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
        clean_text = clean_text.replace('&mdash;', '—')
        clean_text = clean_text.replace('&ndash;', '–')

        # Clean up extra whitespace
        clean_text = ' '.join(clean_text.split())

        return clean_text.strip()

    def map_entry(self, entry: Dict[str, Any]) -> Optional[FeedItem]:
        """Map feedparser entry to standardized FeedItem, filtering for Politics category."""
        # Check if entry has Politics category
        category = entry.get("category", "").strip()
        if category != "Политика":
            return None  # Skip non-politics entries

        # Extract basic fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        description = entry.get("description", "").strip()
        published_str = entry.get("published", "")

        # Extract full text from custom RBC namespace (feedparser converts rbc_news:full-text to rbc_news_full-text)
        full_text = entry.get("rbc_news_full-text", "").strip()

        # Parse publication date
        pub_datetime = self._parse_rbc_date(published_str)
        if not pub_datetime:
            return None  # Skip entries without valid dates

        # Determine which text content to use (prefer full text)
        if full_text:
            # Use full article text
            content = self._clean_html_content(full_text)
        else:
            # Fallback to description
            content = self._clean_html_content(description)

        # Combine title and content for full context
        if title and content:
            text = f"{title}. {content}"
        elif title:
            text = title
        elif content:
            text = content
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
        # Filter items from the last 7 days (for news feeds, shorter timeframe)
        cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)

        filtered_items = [
            item for item in items
            if item.date >= cutoff_date
        ]

        # Sort by date (newest first)
        filtered_items.sort(key=lambda x: x.date, reverse=True)

        return filtered_items


async def main():
    """Test the RBCPoliticsFeed implementation."""
    import httpx

    feed = RBCPoliticsFeed()

    # Standard headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
    }

    async with httpx.AsyncClient(headers=headers) as client:
        result = await feed.fetch(client)

        print(f"Source: {result['source_name']}")
        print(f"Result: {result['result']}")
        print(f"Date: {result['date']}")

        if result['result'] == 'error':
            print(f"Error: {result.get('error_message', 'Unknown error')}")
        else:
            print(f"Politics items found: {len(result['items'])}")

            # Show first few items as examples
            for i, item in enumerate(result['items'][:3]):
                print(f"\n--- Politics Item {i+1} ---")
                print(f"Date: {item.date.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"Text: {item.text[:200]}...")
                print(f"URL: {item.url}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())