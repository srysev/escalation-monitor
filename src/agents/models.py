# src/agents/models.py
"""Central model configuration factory for all agents."""

import os
from agno.models.xai import xAI
from agno.models.anthropic import Claude


def create_research_model(search_results: int = 10, sources: list[dict] | None = [{"type": "web"}, {"type": "x"}]) -> xAI:
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
        max_tokens=15000,
        thinking={
            "type": "enabled",
            "budget_tokens": 10000
        }
    )
