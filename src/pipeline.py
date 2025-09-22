# src/pipeline.py
import asyncio
from typing import List, Dict, Any
import httpx

try:
    from .feeds import BundeswehrFeed
    from .feeds.base import to_iso_utc
except ImportError:
    # For direct execution
    from feeds import BundeswehrFeed
    from feeds.base import to_iso_utc


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
                    date = item["date"]
                    text = item["text"][:100] + "..." if len(item["text"]) > 100 else item["text"]
                    url = item["url"]

                    markdown_lines.append(f"{i+1}. **{date}** - {text}")
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


async def process_all_feeds() -> List[Dict[str, Any]]:
    """Process all available feeds in parallel."""
    # List of all available feed sources
    feeds = [
        BundeswehrFeed(),
        # Add more feeds here as they become available
    ]

    async with httpx.AsyncClient() as client:
        # Process all feeds in parallel
        tasks = [feed.fetch(client) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions that occurred during processing
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Convert exception to error result
                processed_results.append({
                    "source_name": feeds[i].source_name,
                    "date": to_iso_utc(None),
                    "result": "error",
                    "error_message": str(result),
                    "items": []
                })
            else:
                processed_results.append(result)

        return processed_results


def run_daily_pipeline():
    """Run the daily pipeline and return results."""
    # TODO: Add scoring calculation and persistence later
    results = asyncio.run(process_all_feeds())
    return {"updated": True, "feed_results": results}


async def main():
    """Test the pipeline by processing feeds and outputting Markdown."""
    print("Processing feeds...\n")

    results = await process_all_feeds()
    markdown_output = format_feed_results_as_markdown(results)

    print(markdown_output)


if __name__ == "__main__":
    asyncio.run(main())