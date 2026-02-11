"""
Step 1: News Fetcher — Google News RSS (100% free, no API key)
Fetches top headlines from Google News India via RSS feeds.
Uses feedparser + newspaper4k for full article extraction.
"""

import feedparser
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def fetch_news(
    rss_feeds: list[str] = None,
    max_articles: int = 20,
) -> list[dict]:
    """
    Fetch top news headlines from Google News RSS feeds.
    
    Returns list of dicts: [{title, summary, source, url, published}]
    """
    if rss_feeds is None:
        from config import NEWS_RSS_FEEDS
        rss_feeds = NEWS_RSS_FEEDS

    all_articles = []
    seen_titles = set()

    for feed_url in rss_feeds:
        try:
            logger.info(f"Fetching RSS: {feed_url[:80]}...")
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning(f"Feed parse warning: {feed.bozo_exception}")

            for entry in feed.entries:
                title = entry.get("title", "").strip()
                
                # Skip duplicates
                title_lower = title.lower()
                if title_lower in seen_titles:
                    continue
                seen_titles.add(title_lower)

                # Extract source from title (Google News format: "Title - Source")
                source = ""
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source = parts[1].strip() if len(parts) > 1 else ""

                # Get summary
                summary = entry.get("summary", entry.get("description", ""))
                # Clean HTML from summary
                if summary:
                    import re
                    summary = re.sub(r"<[^>]+>", "", summary).strip()

                # Get published date
                published = entry.get("published", "")
                
                article = {
                    "title": title,
                    "summary": summary[:500] if summary else "",
                    "source": source,
                    "url": entry.get("link", ""),
                    "published": published,
                }
                all_articles.append(article)

                if len(all_articles) >= max_articles:
                    break

        except Exception as e:
            logger.error(f"Error fetching feed {feed_url[:50]}: {e}")
            continue

        if len(all_articles) >= max_articles:
            break

    logger.info(f"Fetched {len(all_articles)} unique articles")
    return all_articles[:max_articles]


def fetch_full_article(url: str) -> Optional[str]:
    """
    Fetch full article text using newspaper4k.
    Falls back gracefully if article can't be fetched.
    """
    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        return article.text[:2000] if article.text else None
    except Exception as e:
        logger.debug(f"Could not fetch full article: {e}")
        return None


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    articles = fetch_news(max_articles=10)
    print(f"\n{'='*60}")
    print(f"📰 Fetched {len(articles)} articles")
    print(f"{'='*60}")
    for i, a in enumerate(articles, 1):
        print(f"\n{i}. {a['title']}")
        print(f"   Source: {a['source']}")
        print(f"   Summary: {a['summary'][:100]}...")
