# src/agents/models.py
"""Central model configuration factory for all agents."""

import os
import httpx
from typing import TypedDict, Any
from agno.models.xai import xAI
from agno.models.anthropic import Claude
from agno.models.perplexity import Perplexity


class PerplexityResponse(TypedDict, total=False):
    """Perplexity API response structure."""
    content: str
    citations: list[str]
    search_results: list[dict[str, Any]]
    usage: dict[str, Any]


def create_research_model(search_results: int = 5, sources: list[dict] | None = [{"type": "x"}]) -> xAI:
    """
    Create xAI model for dimension agents with search capabilities.

    Args:
        search_results: Number of search results (default: 5, optimized for speed)

    Returns:
        Configured xAI model
    """
    model_id = os.getenv("RESEARCH_MODEL_ID", "grok-4-fast-reasoning-latest")

    return xAI(
        id=model_id,
        temperature=0,
        search_parameters={
            "mode": "on",
            "max_search_results": search_results,
            "return_citations": False,
            "sources": sources
        },
    )


def create_perplexity_model() -> Perplexity:
    """
    Create Perplexity model for research.py agent.

    Returns:
        Configured Perplexity model
    """
    model_id = os.getenv("PERPLEXITY_MODEL_ID", "sonar-pro")

    return Perplexity(
        id=model_id,
        max_tokens=4000,
        temperature=0,
        request_params = {
            "search_domain_filter" :[
                # Deutschland
                "tagesschau.de", "bmvg.de", "dgap.org", "swp-berlin.org",
                # NATO & International
                "europa.eu",
                # US & Think Tanks
                "rand.org", "understandingwar.org", "iiss.org",
                # Russland
                "mil.ru", "svr.gov.ru", "tass.ru",
                # Polen
                "mon.gov.pl", "wyborcza.pl",
                # Estland
                "kaitseministeerium.ee", "politsei.ee",
                # Ungarn
                "kormany.hu",
                # Baltikum & Nord
                "mod.gov.lv", "kam.lt", "regjeringen.no",
                # Agenturen
                "reuters.com"
            ]
        }
    )


def create_review_model() -> Claude:
    """
    Create Claude model for review agent with thinking capabilities.

    Returns:
        Configured Claude model
    """
    model_id = os.getenv("REVIEW_MODEL_ID", "claude-sonnet-4-5")

    return Claude(
        id=model_id,
        temperature=0,
        max_tokens=10000,
        thinking={
            "type": "enabled",
            "budget_tokens": 6000
        }
    )


async def call_perplexity_api(
    messages: list[dict[str, str]],
    model: str = "sonar-pro",
    search_domain_filter: list[str] | None = None,
    search_recency_filter: str | None = None,
    search_after_date_filter: str | None = None,
    search_before_date_filter: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4000,
    **kwargs
) -> PerplexityResponse:
    """
    Call Perplexity API directly with full control over parameters.

    Args:
        messages: List of message dicts with "role" and "content"
        model: Perplexity model ID (sonar, sonar-pro, sonar-deep-research, etc.)
        search_domain_filter: List of domains to include/exclude (prefix with - for deny)
        search_recency_filter: Time filter (e.g., "week", "day")
        search_after_date_filter: Only content after this date (%m/%d/%Y)
        search_before_date_filter: Only content before this date (%m/%d/%Y)
        temperature: Randomness (0-2, default 0.2)
        max_tokens: Maximum response tokens
        **kwargs: Additional Perplexity API parameters

    Returns:
        PerplexityResponse with content, citations, search_results, usage

    Raises:
        httpx.HTTPError: On API request failures
        KeyError: On unexpected response structure
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY environment variable not set")

    # Build request payload
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        **kwargs
    }

    # Add optional filters
    if search_domain_filter:
        payload["search_domain_filter"] = search_domain_filter
    if search_recency_filter:
        payload["search_recency_filter"] = search_recency_filter
    if search_after_date_filter:
        payload["search_after_date_filter"] = search_after_date_filter
    if search_before_date_filter:
        payload["search_before_date_filter"] = search_before_date_filter

    # Make API request
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()

    # Parse response
    return PerplexityResponse(
        content=data["choices"][0]["message"]["content"],
        citations=data.get("citations", []),
        search_results=data.get("search_results", []),
        usage=data.get("usage", {})
    )
