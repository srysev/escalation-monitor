# src/scoring3.py
from __future__ import annotations
from typing import Dict, Any
import asyncio
from datetime import datetime

try:
    from .feeds.base import to_iso_utc
    from .agents import AGENTS
    from .agents.review import create_agent as create_review_agent, build_prompt
    from .agents.research import create_agent as create_research_agent
    from .agents.research import build_research_prompt
    from .schemas import DimensionScore, OverallAssessment
except ImportError:
    from feeds.base import to_iso_utc
    from agents import AGENTS
    from agents.review import create_agent as create_review_agent, build_prompt
    from agents.research import create_agent as create_research_agent
    from agents.research import build_research_prompt
    from schemas import DimensionScore, OverallAssessment

async def calculate_escalation_score(rss_markdown: str) -> Dict[str, Any]:
    """
    Calculate escalation score using 6-agent architecture:
    - 5 parallel dimension agents (Grok)
    - 1 review agent for synthesis (Claude)

    Args:
        rss_markdown: Markdown-formatted RSS feed results

    Returns:
        Dict with result, timestamp, and escalation data or error message
    """
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Phase 0: Research over the last news
        research_agent = create_research_agent()
        research_run_input = build_research_prompt(date=current_date, rss_markdown=rss_markdown)
        research_response = research_agent.run(research_run_input)

        # Extract research data content, fallback if failed
        if hasattr(research_response, 'content') and research_response.content:
            research_data = research_response.content
        else:
            research_data = "Research-Daten nicht verfügbar"

        # Phase 1: Create all dimension agents and run in parallel
        dimension_tasks = {}
        for name, agent_module in AGENTS.items():
            agent = agent_module.create_agent()
            run_input = agent_module.build_prompt(current_date, research_data, rss_markdown)
            dimension_tasks[name] = asyncio.create_task(run_agent_async(agent, run_input))

        # Wait for all dimension agents to complete
        dimension_results = {}
        for name, task in dimension_tasks.items():
            try:
                response = await task
                if hasattr(response, 'content') and isinstance(response.content, DimensionScore):
                    dimension_results[name] = response.content.model_dump()
                else:
                    print(f"Warning: {name} agent did not return proper DimensionScore")
                    dimension_results[name] = {"score": 2.0, "rationale": f"{name} agent failed to respond properly"}
            except Exception as e:
                print(f"Error in {name} agent: {str(e)}")
                dimension_results[name] = {"score": 2.0, "rationale": f"{name} agent failed: {str(e)}"}

        # Phase 2: Calculate weighted score
        weights = {
            'military': 0.30,
            'diplomatic': 0.20,
            'economic': 0.20,
            'societal': 0.15,
            'russians': 0.15
        }

        calculated_score = 0.0
        for name, result in dimension_results.items():
            calculated_score += result['score'] * weights[name]
        calculated_score = round(calculated_score, 1)

        # Phase 3: Review agent synthesis
        review_agent = create_review_agent()
        review_input = build_prompt(current_date, research_data, rss_markdown, dimension_results, calculated_score)
        final_response = await review_agent.arun(review_input)

        if hasattr(final_response, 'content') and isinstance(final_response.content, OverallAssessment):
            assessment_data = final_response.content.model_dump()

            return {
                "result": "ok",
                "timestamp": to_iso_utc(None),
                "escalation_score": {
                    "score": assessment_data["overall_score"],
                    "level": get_escalation_level(assessment_data["overall_score"]),
                    "summary": assessment_data["situation_summary"],
                    "dimensions": assessment_data["dimensions"],
                    "methodology": {
                        "dimension_scores": dimension_results,
                        "weights": weights,
                        "calculated_score": calculated_score,
                        "final_score": assessment_data["overall_score"],
                        "adjustment": assessment_data["overall_score"] - calculated_score
                    }
                }
            }
        else:
            return {
                "result": "error",
                "timestamp": to_iso_utc(None),
                "error_message": f"Review agent failed to return proper OverallAssessment. Content type: {type(final_response.content) if hasattr(final_response, 'content') else 'no content'}"
            }

    except Exception as e:
        return {
            "result": "error",
            "timestamp": to_iso_utc(None),
            "error_message": f"Escalation scoring failed: {str(e)}"
        }

async def run_agent_async(agent, input_text: str):
    """Run agent asynchronously"""
    return await agent.arun(input_text)

def get_escalation_level(score: float) -> str:
    """Convert numerical score to level name"""
    if score < 1.5:
        return "BASELINE"
    elif score < 2.5:
        return "FRICTION"
    elif score < 3.5:
        return "TENSION"
    elif score < 4.5:
        return "ALERT"
    elif score < 5.5:
        return "ELEVATED"
    elif score < 6.5:
        return "HIGH"
    elif score < 7.5:
        return "SEVERE"
    elif score < 8.5:
        return "CRITICAL"
    elif score < 9.5:
        return "EMERGENCY"
    else:
        return "WARTIME"