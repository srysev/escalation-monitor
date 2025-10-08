# src/feeds/base.py
from __future__ import annotations
import datetime as dt
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
import httpx
import feedparser

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

def to_iso_utc(d: Optional[dt.datetime]) -> str:
    """Convert datetime to ISO UTC string, fallback to current time if None."""
    if not d:
        d = dt.datetime.now(dt.timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc).strftime(ISO_FORMAT)

@dataclass
class FeedItem:
    """Standardized feed item with type-safe fields."""
    date: dt.datetime  # UTC datetime object
    text: str
    url: str

class FeedSource(ABC):
    """Abstract base class for RSS/Atom feed sources."""

    def __init__(self, source_name: str, feed_url: str):
        self.source_name = source_name
        self.feed_url = feed_url

    def get_headers(self) -> Dict[str, str]:
        """
        Return HTTP headers for this feed source.
        Child classes can override for feed-specific headers.
        """
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
        }

    @abstractmethod
    def map_entry(self, entry: Dict[str, Any]) -> Optional[FeedItem]:
        """
        Map a feedparser entry to standardized FeedItem.
        Returns None to skip the entry.
        """
        pass

    @abstractmethod
    def filter(self, items: List[FeedItem]) -> List[FeedItem]:
        """
        Filter items based on relevance criteria.
        Child classes should implement their own filtering logic.
        """
        pass

    async def fetch(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """
        Fetch and parse RSS feed.
        Returns: {source_name, date, result, error_message?, items}
        """
        try:
            # HTTP request
            response = await client.get(
                self.feed_url,
                timeout=20.0,
                follow_redirects=True
            )

            response.raise_for_status()

            # Parse feed
            parsed = feedparser.parse(response.content)

            # Process entries
            items = []
            for entry in parsed.entries:
                try:
                    mapped_item = self.map_entry(entry)
                    if mapped_item:  # Allow child classes to filter by returning None
                        items.append(mapped_item)
                except Exception:
                    # Skip individual entry errors
                    continue

            # Apply filtering
            filtered_items = self.filter(items)

            return {
                "source_name": self.source_name,
                "date": to_iso_utc(None),
                "result": "ok",
                "items": filtered_items
            }

        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e) or repr(e)}"
            return {
                "source_name": self.source_name,
                "date": to_iso_utc(None),
                "result": "error",
                "error_message": error_message,
                "items": []
            }