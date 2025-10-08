# src/feeds/tagesschau_wirtschaft.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional, List
from email.utils import parsedate_tz, mktime_tz

try:
    from .base import FeedSource, FeedItem
    from .llm_filtering import LLMFilterMixin
except ImportError:
    # For direct execution
    from base import FeedSource, FeedItem
    from llm_filtering import LLMFilterMixin


class TagesschauWirtschaftFeed(LLMFilterMixin, FeedSource):
    """RSS feed source for Tagesschau economic news (Wirtschaft) with geopolitical relevance filtering.

    Uses LLM filtering to focus on war economy, sanctions, trade conflicts, and strategic dependencies,
    excluding pure financial markets, domestic economic policy, and consumer topics.
    """

    def __init__(self):
        super().__init__(
            source_name="Tagesschau Wirtschaft",
            feed_url="https://www.tagesschau.de/wirtschaft/index~rss2.xml"
        )

        # LLM filtering configuration
        self.time_filter_days = 7  # Last week
        self.llm_filter_threshold = 15  # Activate LLM filter at 15+ items

        # Economic relevance filtering criteria
        self.filter_criteria = """
**BEHALTEN - Kriegs- & Sanktionswirtschaft:**
- Russland-Sanktionen (Öl, Gas, Kohle, Handel, Finanzen)
- Ukraine-Kriegsfinanzierung, Wiederaufbau
- China-Handelskrieg (Zölle, Technologie-Embargo, Chip-Sanktionen)
- Iran-Sanktionen, Nordkorea-Wirtschaftsblockade
- Energiesicherheit mit Konfliktbezug (LNG-Terminals, Pipeline-Politik, russisches Gas)
- Rüstungsindustrie, Wehrinvestitionen, Verteidigungshaushalt
- Krisenmetalle bei Lieferkettenrisiken (Gold als Krisenwährung, Seltene Erden aus China)

**BEHALTEN - Wirtschaftskrieg & strategische Abhängigkeiten:**
- EU/US-Handelskonflikte mit strategischer Dimension (Stahl, Aluminium, Technologie)
- Lieferketten-Krisen mit Verteidigungsbezug (Halbleiter, kritische Rohstoffe)
- Wirtschaftsblockaden, strategische Industrien (Häfen, Telekommunikation, 5G-Huawei)
- Cyber-Angriffe auf Wirtschaft/kritische Infrastruktur mit Staatenbezug
- Wirtschaftsspionage China/Russland
- Energieabhängigkeiten als Druckmittel (Gazprom, chinesische Rohstoffkontrolle)

**BEHALTEN - Geopolitisch relevante Wirtschaftspolitik:**
- EU-Handelspolitik mit Sicherheitsbezug (Chip Act, Critical Raw Materials Act)
- Blockbildung in Wirtschaft (G7 vs. BRICS, dedollarization)
- Währungskriege, Swift-Ausschluss, alternative Zahlungssysteme
- Staatsunternehmen mit geopolitischer Rolle (chinesische Staatskonzerne in EU)

**AUSSCHLIESSEN:**
- Börsen/DAX/Aktienkurse ohne direkten Kriegsbezug (Marktberichte, Tesla, Tech-Aktien)
- Innerdeutsche Wirtschaftspolitik ohne internationale Dimension (Bürgergeld, Rente, Mindestlohn)
- Konjunkturdaten ohne Kriegsursache (BIP-Wachstum, Industrieproduktion, Arbeitslosigkeit)
- Inflation/Zinsen/EZB-Politik (außer kriegsbedingte Energiepreise)
- Unternehmens-News ohne geopolitischen Kontext (Fusionen, Quartalszahlen, Managerwechsel)
- Verbraucherthemen (Lebensmittelpreise, Verbraucherrechte, Produktrückrufe)
- Verkehr/Infrastruktur (Bahn-Tickets, Autoindustrie-Förderung, Straßenbau)
- Immobilien/Wohnen (Mieten, Baupreise, Wohnungsnot)
- Arbeitswelt ohne Kriegsbezug (Tarifverhandlungen, Streiks, Homeoffice)
- Landwirtschaft (außer kriegsbedingte Ernährungssicherheit)
- Tourismus, Sport-Wirtschaft, Unterhaltungsindustrie
"""

    def _parse_pubdate(self, pubdate_str: str) -> Optional[dt.datetime]:
        """Parse RFC-2822 format date to datetime with timezone."""
        try:
            # Parse RFC-2822 format (standard RSS format)
            time_tuple = parsedate_tz(pubdate_str)
            if time_tuple:
                timestamp = mktime_tz(time_tuple)
                return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        except (ValueError, TypeError):
            pass
        return None

    def get_headers(self) -> Dict[str, str]:
        """Return HTTP headers for this feed source."""
        return {"User-Agent": "python-httpx/0.27"}

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

        # Combine title and description for full context
        if title and description:
            text = f"{title}. {description}"
        elif title:
            text = title
        elif description:
            text = description
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
    """Test the TagesschauWirtschaftFeed implementation."""
    import asyncio
    import httpx

    feed = TagesschauWirtschaftFeed()

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
