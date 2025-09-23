# src/feeds/__init__.py
from .base import FeedSource
from .bundeswehr import BundeswehrFeed
from .nato import NatoFeed
from .auswaertiges_amt import AuswaertigesAmtFeed
from .aftershock import AftershockFeed
from .russian_embassy import RussianEmbassyFeed
from .rbc_politics import RBCPoliticsFeed

__all__ = ["FeedSource", "BundeswehrFeed", "NatoFeed", "AuswaertigesAmtFeed", "AftershockFeed", "RussianEmbassyFeed", "RBCPoliticsFeed"]