#!/usr/bin/env python3
import asyncio
import httpx
import feedparser

async def test_nato_feed():
    """Test NATO RSS feed with custom headers."""
    url = "https://www.nato.int/cps/rss/en/natohq/rssFeed.xsl/rssFeed.xml"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"Testing URL: {url}")
            response = await client.get(
                url,
                headers=headers,
                timeout=20.0,
                follow_redirects=True
            )

            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Content Length: {len(response.content)} bytes")

            if response.status_code == 200:
                # Parse feed
                parsed = feedparser.parse(response.content)
                print(f"\nFeed Title: {parsed.feed.get('title', 'Unknown')}")
                print(f"Feed Description: {parsed.feed.get('description', 'Unknown')}")
                print(f"Entries found: {len(parsed.entries)}")

                if parsed.entries:
                    print("\nFirst entry structure:")
                    entry = parsed.entries[0]
                    print(f"  title: {entry.get('title', 'N/A')}")
                    print(f"  published: {entry.get('published', 'N/A')}")
                    print(f"  link: {entry.get('link', 'N/A')}")
                    print(f"  summary: {entry.get('summary', 'N/A')[:100]}...")
                    print(f"  Available keys: {list(entry.keys())}")

            else:
                print(f"Error: HTTP {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")

        except Exception as e:
            print(f"Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_nato_feed())