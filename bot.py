import os
import requests
import feedparser
from datetime import datetime

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RSS_FEEDS = [
    "https://www.autocarindia.com/RSS/rss.ashx?type=all",
    "https://www.rushlane.com/feed",
    "https://www.zigwheels.com/rss/news.xml",
    "https://www.cardekho.com/rss/news.xml",
    "https://www.drivespark.com/rss/drivespark-latest-fb.xml",
    "https://www.motorbeam.com/feed/",
    "https://insideevs.com/rss/",
]

MAX_FULL_HEADLINES = 12
MAX_MINI_HEADLINES = 5

JDM_KEYWORDS = [
    "jdm", "supra", "skyline", "gtr", "gt-r", "nissan", "toyota",
    "honda", "civic", "integra", "rx7", "rx-7", "mazda", "drift",
    "drifting", "stance", "tuners", "initial d"
]

SOUTH_INDIA_KEYWORDS = [
    "kerala", "kochi", "trivandrum", "thiruvananthapuram",
    "tamil nadu", "chennai", "coimbatore",
    "bangalore", "bengaluru", "karnataka",
    "hyderabad", "telangana", "andhra", "vizag"
]


def product_suggestion(title: str) -> str:
    t = title.lower()
    suggestions = []

    if "ev" in t or "electric" in t or "charging" in t or "battery" in t:
        suggestions.append("EV accessories (dashcam, ambient lights, mats)")
        suggestions.append("Fast-charging add-ons / chargers")

    if "thar" in t or "scorpio" in t or "fortuner" in t or "4x4" in t or "off-road" in t:
        suggestions.append("Aux lights + roof light bar")
        suggestions.append("Offroad fog lamps + relay harness")

    if "launch" in t or "unveil" in t or "facelift" in t:
        suggestions.append("DRL upgrade + projector retrofit")
        suggestions.append("Seat covers + mats combo")

    if "safety" in t or "airbag" in t or "adas" in t:
        suggestions.append("Dashcam + TPMS combo")

    if "performance" in t or "tuning" in t or "drift" in t or "turbo" in t:
        suggestions.append("Performance filter + exhaust tips")

    if "policy" in t or "ban" in t or "rule" in t or "government" in t:
        suggestions.append("Legal-compliant projector LED kits")

    if not suggestions:
        suggestions.append("LED headlight upgrade + projector fog lamps")

    return " | ".join(suggestions[:2])


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload, timeout=20)


def fetch_news():
    news_items = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()

                if title and link:
                    news_items.append({"title": title, "link": link})

        except Exception as e:
            print("Feed error:", e)

    seen = set()
    unique_news = []
    for item in news_items:
        if item["title"] not in seen:
            unique_news.append(item)
            seen.add(item["title"])

    return unique_news


def split_categories(news_list):
    jdm_news = []
    south_news = []

    for item in news_list:
        title_lower = item["title"].lower()

        if any(k in title_lower for k in JDM_KEYWORDS):
            jdm_news.append(item)

        if any(k in title_lower for k in SOUTH_INDIA_KEYWORDS):
            south_news.append(item)

    return jdm_news[:5], south_news[:5]


def is_full_digest_time():
    # GitHub Actions uses UTC time.
    # 9 AM IST = 3:30 AM UTC.
    now_utc = datetime.utcnow()
    return now_utc.hour == 3 and now_utc.minute < 10


def format_full_digest(news_list, jdm_news, south_news):
    today = datetime.now().strftime("%d %b %Y")

    msg = f"🚗 <b>Mairal AutoExtreme FULL Digest</b>\n📅 {today}\n\n"

    msg += "📰 <b>Top Auto News (India + Global)</b>\n"
    for i, item in enumerate(news_list[:MAX_FULL_HEADLINES], start=1):
        sug = product_suggestion(item["title"])
        msg += f"\n{i}) <b>{item['title']}</b>\n🔗 {item['link']}\n💡 <i>Mod Suggestion:</i> {sug}\n"

    msg += "\n\n🇯🇵 <b>JDM / Car Culture</b>\n"
    if jdm_news:
        for i, item in enumerate(jdm_news, start=1):
            msg += f"\n{i}) <b>{item['title']}</b>\n🔗 {item['link']}\n"
    else:
        msg += "\n(No strong JDM news today)\n"

    msg += "\n\n🌴 <b>South India Car Scene</b>\n"
    if south_news:
        for i, item in enumerate(south_news, start=1):
            msg += f"\n{i}) <b>{item['title']}</b>\n🔗 {item['link']}\n"
    else:
        msg += "\n(No South India mentions today)\n"

    msg += "\n\n🔥 <b>Business Tip (Nagpur)</b>\n"
    msg += "Track South India mod trends → copy DRL + projector + wrap combos into Nagpur first."

    return msg


def format_mini_update(news_list):
    now = datetime.now().strftime("%I:%M %p")

    msg = f"⚡ <b>Auto News Mini Update</b>\n🕒 {now}\n\n"
    msg += "Top Updates:\n"

    for i, item in enumerate(news_list[:MAX_MINI_HEADLINES], start=1):
        sug = product_suggestion(item["title"])
        msg += f"\n{i}) <b>{item['title']}</b>\n💡 {sug}\n🔗 {item['link']}\n"

    return msg


if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        raise Exception("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secrets")

    news = fetch_news()
    jdm_news, south_news = split_categories(news)

    if is_full_digest_time():
        message = format_full_digest(news, jdm_news, south_news)
    else:
        message = format_mini_update(news)

    send_telegram_message(message)
