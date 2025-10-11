# src/feeds/__init__.py
from .base import FeedSource
from .bundeswehr import BundeswehrFeed
from .bmvg import BMVgFeed
from .nato import NatoFeed
from .auswaertiges_amt import AuswaertigesAmtFeed
from .aftershock import AftershockFeed
from .russian_embassy import RussianEmbassyFeed
from .rbc_politics import RBCPoliticsFeed
from .junge_welt import JungeWeltFeed
from .frontex import FrontexFeed
from .kommersant import KommersantFeed
from .iru import IRUFeed
from .raja import RajaFeed
from .tagesschau_ausland import TagesschauAuslandFeed
from .tagesschau_inland import TagesschauInlandFeed
from .tagesschau_wirtschaft import TagesschauWirtschaftFeed
from .bundestag_aktuelle_themen import BundestagAktuelleThemenFeed

__all__ = ["FeedSource", "BundeswehrFeed", "BMVgFeed", "NatoFeed", "AuswaertigesAmtFeed", "AftershockFeed", "RussianEmbassyFeed", "RBCPoliticsFeed", "JungeWeltFeed", "FrontexFeed", "KommersantFeed", "IRUFeed", "RajaFeed", "TagesschauAuslandFeed", "TagesschauInlandFeed", "TagesschauWirtschaftFeed", "BundestagAktuelleThemenFeed"]