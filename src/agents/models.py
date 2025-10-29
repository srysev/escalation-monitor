# src/agents/models.py
"""Central model configuration factory for all agents."""

import os
from agno.models.xai import xAI
from agno.models.anthropic import Claude


def create_research_model(
    search_results: int = 15,
    sources: list[dict] | None = None,
    x_accounts: list[str] | None = None
) -> xAI:
    """
    Create xAI model for dimension agents with search capabilities.

    Args:
        search_results: Number of search results (default: 15, optimized for speed)
        sources: Search sources (default: [{"type": "web"}, {"type": "x"}])
        x_accounts: Optional list of X accounts to focus search on (e.g., ["@AuswaertigesAmt"])

    Returns:
        Configured xAI model
    """
    model_id = os.getenv("RESEARCH_MODEL_ID", "grok-4-fast-reasoning-latest")

    # Default sources if not specified
    if sources is None:
        sources = [{"type": "web"}, {"type": "x"}]

    # Add X account filtering if specified
    if x_accounts:
        # Strip '@' from handles if present (xAI API expects handles without '@')
        x_accounts = [handle.lstrip('@') for handle in x_accounts]

        # Find the X source and add included_x_handles (per xAI API spec)
        for source in sources:
            if source.get("type") == "x":
                source["included_x_handles"] = x_accounts
                break

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


def create_review_model() -> xAI:
    """
    Create a model for review agent with thinking capabilities.

    Returns:
        Configured review model
    """
    model_id = os.getenv("REVIEW_MODEL_ID", "grok-4-fast-reasoning-latest")

    return xAI(
        id=model_id,
        temperature=0,
        search_parameters={
            "mode": "off"
        },
    )
