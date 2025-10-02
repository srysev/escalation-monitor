# src/feeds/llm_filtering.py
"""LLM-based filtering mixin for feed sources."""
from __future__ import annotations
import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.xai import xAI

try:
    from .base import FeedItem
except ImportError:
    from base import FeedItem


class FilteredItemNumbers(BaseModel):
    """LLM response with item numbers only."""
    numbers: List[int] = Field(
        description="List of relevant item numbers (e.g. [1, 3, 5, 7])"
    )
    reasoning: str = Field(
        description="Brief explanation of filtering criteria applied"
    )


class LLMFilterMixin:
    """
    Mixin for feed sources that use LLM-based filtering.

    Child classes should define:
    - source_name: str (from FeedSource)
    - time_filter_days: int = Number of days for time-based pre-filtering
    - llm_filter_threshold: int = Min items to trigger LLM filtering
    - filter_criteria: str = Feed-specific filtering criteria (markdown)
    """

    # Type hint for attribute from FeedSource (to satisfy type checkers)
    source_name: str

    # Default values (can be overridden by child classes)
    time_filter_days: int = 1
    llm_filter_threshold: int = 30
    filter_criteria: str = """
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
"""

    def _create_filter_model(self) -> xAI:
        """Create fast reasoning model for filtering (search disabled)."""
        return xAI(
            id="grok-4-fast-non-reasoning-latest",
            temperature=0,
            search_parameters={
                "mode": "off"  # Explicitly disable search
            }
        )

    def _llm_filter(self, items: List[FeedItem]) -> List[FeedItem]:
        """
        Apply LLM-based filtering to items.

        Args:
            items: Pre-filtered items (usually time-filtered)

        Returns:
            Filtered list of relevant items
        """
        # If below threshold, return all items
        if len(items) <= self.llm_filter_threshold:
            return items

        try:
            # Prepare numbered items for LLM (full text)
            items_text = "\n\n".join([
                f"[{i+1}] {item.text}"
                for i, item in enumerate(items)
            ])

            prompt = f"""Filter these {len(items)} {self.source_name} items for geopolitical escalation relevance.

{self.filter_criteria}

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
                description=f"{self.source_name} feed relevance filter",
                output_schema=FilteredItemNumbers,
                markdown=False,
                structured_outputs=True
            )

            response = agent.run(prompt)

            # Extract content from RunOutput
            filtered_result = response.content
            if not filtered_result:
                print(f"[{self.source_name} LLM Filter] No content in response, falling back to input items")
                return items

            # Get selected items by numbers (convert 1-based to 0-based index)
            filtered = [
                items[num - 1]
                for num in filtered_result.numbers
                if 1 <= num <= len(items)
            ]

            print(f"[{self.source_name} LLM Filter] {len(items)} → {len(filtered)} items")
            print(f"[{self.source_name} LLM Filter] Selected numbers: {filtered_result.numbers[:10]}{'...' if len(filtered_result.numbers) > 10 else ''}")
            print(f"[{self.source_name} LLM Filter] Reasoning: {filtered_result.reasoning}")
            return filtered

        except Exception as e:
            print(f"[{self.source_name} LLM Filter] Error: {e}, falling back to input items")
            return items

    def filter(self, items: List[FeedItem]) -> List[FeedItem]:
        """
        Filter items using time-based + LLM-based filtering.

        Can be overridden by child classes for custom logic.
        """
        # Step 1: Time filter
        cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=self.time_filter_days)
        time_filtered = [item for item in items if item.date >= cutoff_date]
        time_filtered.sort(key=lambda x: x.date, reverse=True)

        # Step 2: LLM filter if above threshold
        return self._llm_filter(time_filtered)
