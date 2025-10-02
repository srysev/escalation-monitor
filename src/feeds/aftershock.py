# src/feeds/aftershock.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional, List
import re
from email.utils import parsedate_tz, mktime_tz

try:
    from .base import FeedSource, FeedItem
    from .llm_filtering import LLMFilterMixin
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem
    from llm_filtering import LLMFilterMixin


class AftershockFeed(LLMFilterMixin, FeedSource):
    """RSS feed source for Aftershock.news."""

    # LLM filtering configuration
    time_filter_days = 2
    llm_filter_threshold = 5
    filter_criteria = """
**Keep items about:**
- Military conflicts, operations, special military operation (SMO)
- Diplomatic incidents, sanctions, international relations
- NATO/Russia/China/US geopolitical tensions
- Ukraine, Middle East, Taiwan, Balkans
- Arms deals, military industry, defense readiness
- Political statements on war/peace
- Russian foreign policy, international security
- Energy geopolitics (gas, oil, nuclear)

**Exclude:**
- Pure sports, entertainment, celebrity news
- Domestic Russian politics without international impact
- Local crime, accidents
- Pure cultural events
- Business news without geopolitical relevance
"""

    def __init__(self):
        super().__init__(
            source_name="Aftershock",
            feed_url="https://rss.aftershock.news/?q=rss/aftershock.xml"
        )

    def _parse_pubdate(self, pubdate_str: str) -> Optional[dt.datetime]:
        """Parse RFC-2822 format date to datetime with timezone."""
        try:
            time_tuple = parsedate_tz(pubdate_str)
            if time_tuple:
                timestamp = mktime_tz(time_tuple)
                return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        except (ValueError, TypeError):
            pass
        return None

    def _clean_html_content(self, html_content: str) -> str:
        """Remove HTML tags and clean up content."""
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
        # Clean up whitespace
        clean_text = ' '.join(clean_text.split())

        return clean_text.strip()

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

        # Clean HTML content from description
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


async def main():
    """Test the AftershockFeed implementation."""
    import asyncio
    import httpx

    feed = AftershockFeed()

    # Custom headers needed for proper RSS fetching
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