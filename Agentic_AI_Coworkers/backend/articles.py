"""DailyTechUpgradeAgent: authorized RSS snippets, relevance ranking, safe source metadata."""
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from html.parser import HTMLParser
import feedparser
import requests
from .models import Article, DailyBrief, Profile
from .llm import generate

FEEDS = {
    "AWS Machine Learning Blog": "https://aws.amazon.com/blogs/machine-learning/feed/",
    "Microsoft Research": "https://www.microsoft.com/en-us/research/blog/feed/",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def clean_html(value: str) -> str:
    parser = _Text()
    parser.feed(value or "")
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()


def normalize_date(entry) -> str:
    for prop in ("published_parsed", "updated_parsed"):
        stamp = entry.get(prop)
        if stamp:
            return datetime(*stamp[:6], tzinfo=timezone.utc).date().isoformat()
    for prop in ("published", "updated"):
        try:
            return parsedate_to_datetime(entry[prop]).date().isoformat()
        except Exception:
            continue
    return "date not provided"


def _read_feed(feed_pair):
    source, url = feed_pair
    try:
        response = requests.get(url, headers={"User-Agent": "SJSU-Student-AgentDemo/1.0 (+RSS reader)"}, timeout=9)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        results = []
        for entry in parsed.entries[:18]:
            link = entry.get("link", "")
            if not link.startswith("https://"):
                continue
            excerpt = clean_html(entry.get("summary", "") or entry.get("description", ""))
            if len(excerpt) < 35:
                continue
            results.append(Article(
                title=clean_html(entry.get("title", "Untitled"))[:250],
                url=link,
                source=source,
                published_date=normalize_date(entry),
                excerpt=excerpt[:800],
            ))
        return results
    except (requests.RequestException, Exception):
        return []


def fetch_live_articles() -> list[Article]:
    # Bounded, concurrent RSS checks; no API key required.
    with ThreadPoolExecutor(max_workers=len(FEEDS)) as pool:
        grouped = list(pool.map(_read_feed, FEEDS.items()))
    return [a for batch in grouped for a in batch]


def load_sample_articles() -> list[Article]:
    path = Path(__file__).resolve().parent.parent / "data" / "sample_articles.json"
    return [Article(**a, mode="sample_data") for a in json.loads(path.read_text(encoding="utf-8"))]


def relevance_score(article: Article, profile: Profile, read_urls: set[str] | None = None) -> float:
    hay = (article.title + " " + article.excerpt).lower()
    interests = [x.strip().lower() for x in profile.interests if x.strip()]
    score = sum(7 if x in article.title.lower() else 4 for x in interests if x in hay)
    role_parts = re.findall(r"[a-z]{3,}", profile.target_role.lower())
    score += sum(1 for x in role_parts if x in hay)
    try:
        age = (datetime.now(timezone.utc).date() - datetime.fromisoformat(article.published_date).date()).days
        score += max(0, 15 - max(0, age)) / 3
    except ValueError:
        pass
    if read_urls and article.url in read_urls:
        score -= 100  # Prefer unread resources when enough options are available.
    return score


def top_three(articles: list[Article], profile: Profile, read_urls: set[str] | None = None) -> list[Article]:
    unique = {a.url.split("?")[0]: a for a in articles}
    ranked = sorted(unique.values(), key=lambda a: (relevance_score(a, profile, read_urls), a.published_date), reverse=True)
    chosen = []
    # Diverse sources when possible; fill remaining by rank.
    sources = set()
    for item in ranked:
        if item.source not in sources:
            chosen.append(item)
            sources.add(item.source)
        if len(chosen) == 3:
            return chosen
    for item in ranked:
        if item not in chosen:
            chosen.append(item)
        if len(chosen) == 3:
            break
    return chosen


def compose_brief(articles: list[Article], profile: Profile, mode: str, read_urls: set[str] | None = None) -> DailyBrief:
    chosen = top_three(articles, profile, read_urls)
    if len(chosen) < 3:
        raise ValueError("Fewer than three source articles were available. Try the offline snapshot or check your internet connection.")
    for article in chosen:
        # We have only the RSS excerpt, NOT the full article. Say so explicitly.
        article.summary = "Source excerpt summary: " + article.excerpt[:340].rstrip(" .") + "."
        ai = generate(
            f"Article title: {article.title}\nRSS excerpt: {article.excerpt}\nWrite TWO short technical takeaways. Only use the excerpt; if details are missing say so.",
            "You summarize technical RSS excerpts. Do not imply that you read the full article. No invented experiments, results or figures.",
            130,
        )
        if ai:
            article.summary = "AI summary (source excerpt only): " + ai
        matching = [x for x in profile.interests if x.lower() in (article.title + ' ' + article.excerpt).lower()]
        topic = matching[0] if matching else profile.target_role
        article.relevance_reason = (
            f"Connects to your interest in {topic}. As you prepare for {profile.target_role}, "
            "identify one concept you can explain or try in a small project."
        )
        article.reading_minutes = 6
    return DailyBrief(
        date=datetime.now().astimezone().date().isoformat(),
        generated_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        mode=mode,
        note=("LIVE RSS: sourced titles, dates and URLs; summaries use RSS excerpts, not full articles."
              if mode == "live_rss" else
              "OFFLINE SNAPSHOT: real articles published in October 2026, not refreshed today. Open the linked source for full text."),
        profile_role=profile.target_role,
        articles=chosen,
    )
