# src/feeds/base.py
from __future__ import annotations
import datetime as dt
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
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

class FeedSource(ABC):
    """Abstract base class for RSS/Atom feed sources."""

    def __init__(self, source_name: str, feed_url: str):
        self.source_name = source_name
        self.feed_url = feed_url

    @abstractmethod
    def map_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a feedparser entry to standardized format.
        Must return: {"date": "ISO-string", "text": "...", "url": "..."}
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
                    mapped_entry = self.map_entry(entry)
                    if mapped_entry:  # Allow child classes to filter by returning None
                        items.append(mapped_entry)
                except Exception:
                    # Skip individual entry errors
                    continue

            return {
                "source_name": self.source_name,
                "date": to_iso_utc(None),
                "result": "ok",
                "items": items
            }

        except Exception as e:
            return {
                "source_name": self.source_name,
                "date": to_iso_utc(None),
                "result": "error",
                "error_message": str(e),
                "items": []
            }