# src/feeds/raja.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import httpx

try:
    from .base import FeedSource, FeedItem
    from .llm_filtering import LLMFilterMixin
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem
    from llm_filtering import LLMFilterMixin


class RajaFeed(LLMFilterMixin, FeedSource):
    """RSS feed source for Finnish Border Guard (Raja) news releases.

    Uses LLM filtering to focus on migration/border crisis content,
    excluding maritime operations, equipment updates, and routine organizational news.
    """

    def __init__(self):
        super().__init__(
            source_name="Raja",
            feed_url="https://raja.fi/en/news-and-press-releases/-/asset_publisher/aCK7LggrYevU/rss"
        )

        # LLM filtering configuration
        self.time_filter_days = 16000  # Wide time window (no effective time filtering)
        self.llm_filter_threshold = 10  # Activate LLM filter at 10+ items

        # Migration/border crisis-specific filtering criteria
        self.filter_criteria = """
**Keep items about:**
- Migration pressure and irregular border crossings
- Border closures, restrictions, or enhanced controls
- Hybrid threats and instrumentalized migration
- International border security cooperation (Latvia, Poland, Estonia, Lithuania)
- EU border policies (Entry/Exit System, Schengen)
- Border incidents related to Russia/Belarus
- Asylum and refugee movements

**Exclude:**
- Maritime safety and search-and-rescue operations (unless migration-related)
- Equipment procurement and technology updates
- Training exercises (unless response to specific crisis)
- Organizational announcements and personnel changes
- Routine border statistics
- Cultural events and ceremonies
"""

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
        clean_text = clean_text.replace('&laquo;', '«')
        clean_text = clean_text.replace('&raquo;', '»')

        # Clean up extra whitespace
        clean_text = ' '.join(clean_text.split())

        return clean_text.strip()

    def _parse_raja_date(self, date_str: str) -> Optional[dt.datetime]:
        """Parse Raja ISO 8601 date format."""
        try:
            # Handle ISO format with timezone (e.g., '2025-01-15T14:30:00Z' or with offset)
            if date_str.endswith('Z'):
                clean_date = date_str[:-1]  # Remove 'Z'
            else:
                clean_date = date_str

            # Parse the ISO format
            parsed_date = dt.datetime.fromisoformat(clean_date)

            # Ensure timezone is UTC
            if parsed_date.tzinfo is None:
                return parsed_date.replace(tzinfo=dt.timezone.utc)
            else:
                return parsed_date.astimezone(dt.timezone.utc)

        except (ValueError, AttributeError):
            pass
        return None

    def _extract_descriptions_from_xml(self, xml_text: str) -> Dict[str, str]:
        """
        Manually extract descriptions from raw XML because feedparser fails
        with double-encoded HTML entities in Raja.fi feed.

        Returns: dict mapping item links to their description text
        """
        import re
        from html import unescape

        descriptions = {}

        # Find all <item> blocks
        item_pattern = re.compile(r'<item>(.*?)</item>', re.DOTALL)

        for item_match in item_pattern.finditer(xml_text):
            item_xml = item_match.group(1)

            # Extract link (as unique identifier)
            link_match = re.search(r'<link>(.*?)</link>', item_xml)
            if not link_match:
                continue
            link = link_match.group(1).strip()

            # Extract description
            desc_match = re.search(r'<description>(.*?)</description>', item_xml, re.DOTALL)
            if not desc_match:
                continue

            raw_desc = desc_match.group(1)

            # First unescape: &lt;![CDATA[&lt;p&gt; → <![CDATA[<p>
            first_decode = unescape(raw_desc)

            # Remove CDATA wrapper if present
            if first_decode.startswith('<![CDATA[') and first_decode.endswith(']]>'):
                content = first_decode[9:-3]  # Remove <![CDATA[ and ]]>
            else:
                content = first_decode

            # Store the cleaned content (still has HTML tags, will be cleaned later)
            descriptions[link] = content.strip()

        return descriptions

    def map_entry(self, entry: Dict[str, Any], descriptions: Optional[Dict[str, str]] = None) -> Optional[FeedItem]:
        """Map feedparser entry to standardized FeedItem."""
        # Extract basic fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        published_str = entry.get("published", "")

        # Parse publication date (try feedparser's parsed time if ISO parsing fails)
        pub_datetime = self._parse_raja_date(published_str)
        published_parsed = entry.get("published_parsed")
        if not pub_datetime and published_parsed:
            pub_datetime = dt.datetime(*published_parsed[:6], tzinfo=dt.timezone.utc)

        if not pub_datetime:
            return None  # Skip entries without valid dates

        # Get description from manually extracted dict (contains HTML)
        description_html = ""
        if descriptions and link in descriptions:
            description_html = descriptions[link]

        # Clean HTML from description
        clean_description = self._clean_html_content(description_html)

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

    async def fetch(self, client: httpx.AsyncClient):
        """
        Override fetch to manually extract descriptions from raw XML.
        Raja.fi feed has double-encoded HTML entities that break feedparser.
        """
        import httpx
        import feedparser

        try:
            from .base import to_iso_utc
        except ImportError:
            from base import to_iso_utc

        try:
            # HTTP request
            response = await client.get(
                self.feed_url,
                timeout=20.0,
                follow_redirects=True
            )
            response.raise_for_status()

            # Manually extract descriptions from raw XML
            descriptions = self._extract_descriptions_from_xml(response.text)

            # Parse feed with feedparser (for dates, titles, links)
            parsed = feedparser.parse(response.content)

            # Process entries with manually extracted descriptions
            items = []
            for entry in parsed.entries:
                try:
                    mapped_item = self.map_entry(entry, descriptions)
                    if mapped_item:
                        items.append(mapped_item)
                except Exception:
                    # Skip individual entry errors
                    continue

            # Apply filtering (LLM filter from mixin)
            filtered_items = self.filter(items)

            return {
                "source_name": self.source_name,
                "date": to_iso_utc(None),
                "result": "ok",
                "items": filtered_items
            }

        except Exception as e:
            return {
                "source_name": self.source_name,
                "date": to_iso_utc(None),
                "result": "error",
                "error_message": str(e),
                "items": []
            }


async def main():
    """Test the RajaFeed implementation."""
    import asyncio
    import httpx

    feed = RajaFeed()

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
