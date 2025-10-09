#!/usr/bin/env python3
"""
Test xAI Search functionality with included_x_handles parameter.

Purpose: Verify if xAI's included_x_handles parameter works correctly.
"""

import asyncio
import os
from agno.agent import Agent
from agno.models.xai import xAI


async def test_x_search_with_accounts():
    """Test X-only search with included_x_handles."""
    print("=" * 80)
    print("TEST: X-only Search with included_x_handles")
    print("=" * 80)

    model = xAI(
        id="grok-4-fast-reasoning-latest",
        temperature=0,
        search_parameters={
            "mode": "on",
            "max_search_results": 10,
            "return_citations": True,
            "sources": [
                {
                    "type": "x",
                    "included_x_handles": [
                        "AuswaertigesAmt",
                        "bmi_bund",
                        "bamf_dialog"
                    ]
                }
            ]
        }
    )

    agent = Agent(model=model, markdown=False)

    query = "Visa Russland Deutschland Einbürgerung Migration"
    print(f"\nQuery: {query}")
    print(f"Expected: Only tweets from @AuswaertigesAmt, @bmi_bund, @bamf_dialog\n")

    try:
        response = await agent.arun(query)
        print(f"Response Type: {type(response)}")
        print(f"Response Content: {response.content}\n")

        if hasattr(response, 'citations'):
            print(f"Citations: {response.citations}")

            # Check if citations are actually from specified accounts
            if response.citations and hasattr(response.citations, 'urls'):
                print("\n--- Citation Analysis ---")
                for citation in response.citations.urls:
                    url = citation.url if hasattr(citation, 'url') else str(citation)
                    print(f"  - {url}")

                    # Check if it's an X/Twitter URL
                    if 'twitter.com' in url or 'x.com' in url:
                        # Extract handle from URL
                        parts = url.split('/')
                        if len(parts) > 3:
                            handle = parts[3]
                            expected_handles = ["AuswaertigesAmt", "BMI_Bund", "bamf_dialog"]
                            if handle in expected_handles:
                                print(f"    ✅ Match: @{handle}")
                            else:
                                print(f"    ❌ Unexpected handle: @{handle}")
        else:
            print("No citations attribute found")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    print("\n")


async def main():
    """Run test for included_x_handles parameter."""
    print("\n" + "=" * 80)
    print("xAI included_x_handles Parameter Test")
    print("=" * 80 + "\n")

    # Check for API key
    if not os.getenv("XAI_API_KEY"):
        print("⚠️  Warning: XAI_API_KEY not set in environment")
        print("Set it with: export XAI_API_KEY=your_key_here\n")
        return

    await test_x_search_with_accounts()

    print("=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
