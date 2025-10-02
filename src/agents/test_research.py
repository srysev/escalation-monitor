import asyncio
import sys
import time
sys.path.insert(0, 'src/agents')
import research
from models import create_research_model
from agno.agent import Agent

async def test():
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    empty_rss = 'RSS-Feeds konnten nicht geladen werden.'

    print(f'Testing with Grok (20 search_results, web/x/news/rss) - {current_date}')
    print('='*80)

    # Build prompt
    user_prompt = research.build_research_prompt(current_date, empty_rss)

    # Create Grok model with extended search
    model = create_research_model(
        search_results=20,
        sources=[
            {"type": "web"},
            {"type": "x"},
            {"type": "news"}
        ]
    )

    # Create agent with description and instructions
    agent = Agent(
        model=model,
        description=research.DESCRIPTION,
        instructions=research.INSTRUCTIONS,
        markdown=True
    )

    # Start timer
    start_time = time.perf_counter()

    # Run agent with user prompt
    run_response = agent.run(user_prompt)

    duration = time.perf_counter() - start_time

    print(f'\n⏱️  Time: {duration:.2f}s ({duration/60:.2f} min)')
    print('='*80)

    # Extract content from Agno response
    content = run_response.content

    # Analyze content for structure and source mentions
    has_emoji = '📍' in content and '🔹' in content and '⚠️' in content

    # Count Russian vs Western domain mentions in content
    ru_domains = ['mil.ru', 'mid.ru', 'tass.ru', 'kremlin.ru', 'svr.gov.ru']
    west_domains = ['tagesschau.de', 'bmvg.de', 'reuters.com', 'nato.int', 'zdfheute.de']

    ru_mentions = sum(content.lower().count(d.lower()) for d in ru_domains)
    west_mentions = sum(content.lower().count(d.lower()) for d in west_domains)

    print(f'\n📝 CONTENT ANALYSIS:')
    print(f'   Length: {len(content)} chars')
    print(f'   Uses emoji structure (📍/🔹/⚠️): {has_emoji}')
    print(f'   Mentions Russian domains: {ru_mentions} times')
    print(f'   Mentions Western domains: {west_mentions} times')
    print(f'   Balance: {"⚠️ WESTERN BIAS" if west_mentions > ru_mentions * 2 else "✓ Balanced"}')

    print(f'\n📄 FULL CONTENT:')
    print('='*80)
    print(content)

    print(f'\n\n✅ Test completed in {duration:.2f}s')
    print(f'📊 Domain Mentions: West {west_mentions} vs RU {ru_mentions}')

asyncio.run(test())