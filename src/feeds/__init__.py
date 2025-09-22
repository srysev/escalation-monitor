# src/feeds/__init__.py
from .base import FeedSource
from .bundeswehr import BundeswehrFeed

__all__ = ["FeedSource", "BundeswehrFeed"]