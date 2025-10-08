# src/pipeline.py
import asyncio
from typing import List, Dict, Any
import httpx

try:
    from .feeds import BundeswehrFeed, NatoFeed, AuswaertigesAmtFeed, AftershockFeed, RussianEmbassyFeed, RBCPoliticsFeed, JungeWeltFeed, FrontexFeed, KommersantFeed, RajaFeed, TagesschauAuslandFeed, TagesschauInlandFeed, TagesschauWirtschaftFeed, BundestagAktuelleThemenFeed, IRUFeed
    from .feeds.base import FeedSource, to_iso_utc
    from .scoring3 import calculate_escalation_score
    from .storage import save_escalation_report
except ImportError:
    # For direct execution
    from feeds import BundeswehrFeed, NatoFeed, AuswaertigesAmtFeed, AftershockFeed, RussianEmbassyFeed, RBCPoliticsFeed, JungeWeltFeed, FrontexFeed, KommersantFeed, RajaFeed, TagesschauAuslandFeed, TagesschauInlandFeed, TagesschauWirtschaftFeed, BundestagAktuelleThemenFeed, IRUFeed
    from feeds.base import FeedSource, to_iso_utc
    from scoring3 import calculate_escalation_score
    from storage import save_escalation_report


def format_feed_results_as_markdown(results: List[Dict[str, Any]]) -> str:
    """Format feed processing results as Markdown."""
    markdown_lines = ["# Feed Processing Results\n"]

    successful_feeds = [r for r in results if r["result"] == "ok"]
    failed_feeds = [r for r in results if r["result"] == "error"]

    # Summary
    markdown_lines.append(f"**Summary:** {len(successful_feeds)} successful, {len(failed_feeds)} failed\n")

    # Successful feeds
    if successful_feeds:
        markdown_lines.append("## Successful Feeds\n")

        for feed_result in successful_feeds:
            source_name = feed_result["source_name"]
            items = feed_result["items"]

            markdown_lines.append(f"### {source_name}")
            markdown_lines.append(f"- **Items found:** {len(items)}")
            markdown_lines.append(f"- **Last updated:** {feed_result['date']}\n")

            if items:
                markdown_lines.append("**Articles:**")
                for i, item in enumerate(items):  # Show all items
                    # Convert datetime to readable format for markdown
                    date_str = item.date.strftime("%Y-%m-%d %H:%M UTC")
                    text = item.text
                    url = item.url

                    markdown_lines.append(f"{i+1}. **{date_str}** - {text}")
                    markdown_lines.append(f"   - Link: {url}")

            markdown_lines.append("")  # Empty line between feeds

    # Failed feeds
    if failed_feeds:
        markdown_lines.append("## Failed Feeds\n")

        for feed_result in failed_feeds:
            source_name = feed_result["source_name"]
            error_message = feed_result.get("error_message", "Unknown error")

            markdown_lines.append(f"### {source_name}")
            markdown_lines.append(f"- **Status:** Error")
            markdown_lines.append(f"- **Error:** {error_message}")
            markdown_lines.append(f"- **Timestamp:** {feed_result['date']}\n")

    return "\n".join(markdown_lines)


CONCURRENCY_LIMIT = 2  # maximal gleichzeitige Feed-Requests


async def _run_feed(feed: FeedSource, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    async with semaphore:
        async with httpx.AsyncClient(headers=feed.get_headers()) as client:
            return await feed.fetch(client)


async def process_all_feeds() -> List[Dict[str, Any]]:
    """Process all available feeds in parallel."""
    feeds = [
        BundeswehrFeed(),
        NatoFeed(),
        AuswaertigesAmtFeed(),
        # AftershockFeed(),
        RussianEmbassyFeed(),
        RBCPoliticsFeed(),
        # JungeWeltFeed(),    # try to minimize Tokensamount
        FrontexFeed(),
        KommersantFeed(),
        RajaFeed(),  # Finnland border service
        TagesschauAuslandFeed(),
        TagesschauInlandFeed(),
        TagesschauWirtschaftFeed(),
        # BundestagAktuelleThemenFeed(),  # way too long texts
    ]

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    fetch_tasks = [asyncio.create_task(_run_feed(feed, semaphore)) for feed in feeds]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    processed_results: List[Dict[str, Any]] = []
    for feed, result in zip(feeds, results):
        if isinstance(result, Exception):
            cause = getattr(result, "__cause__", None)
            error_message = f"{type(result).__name__}: {result or repr(result)}"
            if cause:
                error_message += f" | cause={repr(cause)}"
            processed_results.append({
                "source_name": feed.source_name,
                "date": to_iso_utc(None),
                "result": "error",
                "error_message": error_message,
                "items": [],
            })
        else:
            processed_results.append(result)

    return processed_results


async def run_daily_pipeline():
    """Run the daily pipeline and return escalation scoring results."""
    import time

    # Process all feeds
    print("Processing RSS feeds...")
    feed_start = time.time()
    feed_results = await process_all_feeds()
    feed_duration = time.time() - feed_start
    print(f"RSS feeds processed in {feed_duration:.2f} seconds")

    # Format feed results as markdown for agent input
    print("Formatting feed data for escalation analysis...")
    markdown_data = format_feed_results_as_markdown(feed_results)
    print(f"Markdown Data:\n\n{markdown_data}")

    # Calculate escalation score using the markdown data
    print("Calculating escalation score...")
    scoring_start = time.time()
    escalation_result = await calculate_escalation_score(markdown_data)
    scoring_duration = time.time() - scoring_start
    print(f"Escalation score calculated in {scoring_duration:.2f} seconds")

    # Save escalation result to storage
    print("Saving escalation report...")
    save_success = save_escalation_report(escalation_result)
    if save_success:
        print("Escalation report saved successfully")
    else:
        print("Failed to save escalation report")

    total_duration = feed_duration + scoring_duration
    print(f"Total pipeline duration: {total_duration:.2f} seconds")

    return escalation_result


async def main():
    """Test the complete pipeline with escalation scoring."""
    import json

    print("Processing feeds and calculating escalation score...\n")

    result = await run_daily_pipeline()

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())