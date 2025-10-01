# src/feeds/kommersant.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional, List
import email.utils
import json
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.xai import xAI

try:
    from .base import FeedSource, FeedItem
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem


class FilteredItemNumbers(BaseModel):
    """LLM response with item numbers only."""
    numbers: List[int] = Field(
        description="List of relevant item numbers (e.g. [1, 3, 5, 7])"
    )
    reasoning: str = Field(
        description="Brief explanation of filtering criteria applied"
    )


class KommersantFeed(FeedSource):
    """RSS feed source for Kommersant - World section."""

    def __init__(self):
        super().__init__(
            source_name="Kommersant World",
            feed_url="https://www.kommersant.ru/rss/section-world.xml"
        )

    def get_headers(self) -> Dict[str, str]:
        """Return Kommersant-specific headers."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Referer': 'https://www.kommersant.ru/',
        }

    def _create_filter_model(self) -> xAI:
        """Create fast reasoning model for filtering (search disabled)."""
        return xAI(
            id="grok-4-fast-non-reasoning-latest",
            temperature=0,
            search_parameters={
                "mode": "off"  # Explicitly disable search
            }
        )

    def _parse_kommersant_date(self, date_str: str) -> Optional[dt.datetime]:
        """Parse Kommersant date format: 'Mon, 29 Sep 2025 19:13:38 +0300'"""
        try:
            # Use email.utils.parsedate_to_datetime for RFC 2822-like format
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
        clean_text = clean_text.replace('&laquo;', '«')
        clean_text = clean_text.replace('&raquo;', '»')

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
        pub_datetime = self._parse_kommersant_date(published_str)
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
        """Filter items using time + LLM-based relevance."""
        # Step 1: Time filter (last 24 hours)
        cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)
        time_filtered = [item for item in items if item.date >= cutoff_date]
        time_filtered.sort(key=lambda x: x.date, reverse=True)

        # Step 2: If 30 or fewer items, return all
        if len(time_filtered) <= 30:
            return time_filtered

        # Step 3: LLM-based filtering for relevance
        try:
            # Prepare numbered items for LLM (full text)
            items_text = "\n\n".join([
                f"[{i+1}] {item.text}"
                for i, item in enumerate(time_filtered)
            ])

            prompt = f"""Filter these {len(time_filtered)} Kommersant news items for geopolitical escalation relevance.

**Keep items about:**
- Military conflicts, operations, tensions
- Diplomatic incidents, sanctions, expulsions
- NATO/Russia/China/US relations
- Ukraine, Middle East, Taiwan
- Arms deals, military readiness
- Political statements on war/peace

**Exclude:**
- Sports, culture, entertainment
- Pure economic/business news
- Domestic politics without geopolitical impact
- Celebrity/personal news

Return ONLY the numbers of relevant items as a JSON list.

**Example output format:**
{{
  "numbers": [1, 3, 5, 7, 9, 12, 15, 18, 21, 24],
  "reasoning": "Selected items focus on military tensions, diplomatic incidents, and geopolitical conflicts."
}}

Items:
{items_text}"""

            agent = Agent(
                model=self._create_filter_model(),
                description="Kommersant feed relevance filter",
                output_schema=FilteredItemNumbers,
                markdown=False,
                structured_outputs=True
            )

            response = agent.run(prompt)

            # Extract content from RunOutput
            filtered_result = response.content

            # Get selected items by numbers (convert 1-based to 0-based index)
            filtered = [
                time_filtered[num - 1]
                for num in filtered_result.numbers
                if 1 <= num <= len(time_filtered)
            ]

            print(f"[Kommersant LLM Filter] {len(time_filtered)} → {len(filtered)} items")
            print(f"[Kommersant LLM Filter] Selected numbers: {filtered_result.numbers[:10]}{'...' if len(filtered_result.numbers) > 10 else ''}")
            print(f"[Kommersant LLM Filter] Reasoning: {filtered_result.reasoning}")
            return filtered

        except Exception as e:
            print(f"[Kommersant LLM Filter] Error: {e}, falling back to time filtered items")
            return time_filtered


async def main():
    """Test the KommersantFeed implementation."""
    import httpx
    import time

    feed = KommersantFeed()

    # Headers optimized for Kommersant RSS feed
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Referer': 'https://www.kommersant.ru/',
    }

    print("⏱️  Starting Kommersant feed fetch...")
    start_time = time.time()

    async with httpx.AsyncClient(headers=headers) as client:
        result = await feed.fetch(client)

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"\n✅ Feed fetch completed in {execution_time:.2f} seconds")
        print(f"Source: {result['source_name']}")
        print(f"Result: {result['result']}")
        print(f"Date: {result['date']}")

        if result['result'] == 'error':
            print(f"Error: {result.get('error_message', 'Unknown error')}")
        else:
            print(f"World news items found: {len(result['items'])}")

            # Show first few items as examples
            for i, item in enumerate(result['items']):
                print(f"\n--- World News Item {i+1} ---")
                print(f"Date: {item.date.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"Text: {item.text}")
                print(f"URL: {item.url}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())