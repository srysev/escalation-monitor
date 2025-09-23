import snscrape.modules.twitter as sntwitter
import feedgenerator
from datetime import datetime

# RSS-Feed vorbereiten
feed = feedgenerator.Rss201rev2Feed(
    title="RusBotschaft Twitter Feed",
    link="https://x.com/RusBotschaft",
    description="Tweets von @RusBotschaft",
    language="de",
)

# Tweets scrapen (z.B. die letzten 20)
for i, tweet in enumerate(sntwitter.TwitterUserScraper("RusBotschaft").get_items()):
    if i >= 20:
        break
    feed.add_item(
        title=f"Tweet von {tweet.date.strftime('%Y-%m-%d %H:%M')}",
        link=f"https://x.com/{tweet.user.username}/status/{tweet.id}",
        description=tweet.content,
        pubdate=tweet.date,
    )

# Feed speichern
with open("rusbotschaft.xml", "w", encoding="utf-8") as f:
    feed.write(f, "utf-8")
    
