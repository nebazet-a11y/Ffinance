import os
import datetime
import feedparser
import requests
import google.generativeai as genai

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def get_news():
    now_utc = datetime.datetime.utcnow()
    # UTC 16:00 (TSİ 19:00) -> Avrupa / Euro Stoxx
    # UTC 18:00 (TSİ 21:00) -> Amerika / S&P 500
    if now_utc.hour == 16:
        rss_url = "https://feeds.bloomberg.com/europe/news.rss"
        market_name = "Euro Stoxx 50 / European Markets"
    else:
        rss_url = "https://feeds.bloomberg.com/markets/news.rss"
        market_name = "S&P 500 / US Markets"

    feed = feedparser.parse(rss_url)
    if feed.entries:
        entry = feed.entries[0]
        image_url = entry.get('media_content', [{'url': 'https://via.placeholder.com/600'}])[0]['url']
        return entry.title, entry.summary, image_url, market_name
    return None, None, None, market_name

def generate_text(title, summary, market_name):
    prompt = f"""
    Market Focus: {market_name}
    News Title: {title}
    News Summary: {summary}
    
    CRITICAL RULE: The entire output MUST BE IN ENGLISH. Find the most surprising, striking news angle.
    
    Create two separate drafts based on these strict formatting rules:
    
    1. X (Twitter) Draft Rules:
    - MUST BE IN ENGLISH.
    - MAXIMUM 280 characters in total (strict limit).
    - Title/Hook: MUST BE WRITTEN IN ALL CAPS, witty/sharp, and contain EXACTLY 1 emoji.
    - Structure: [ALL CAPS TITLE WITH 1 EMOJI] + [1 blank line] + [Main body text containing 1 emoji] + [1 blank line] + [3 hashtags].
    - Total emojis across the entire X post must be exactly 2 (1 in title, 1 in body).
    
    2. LinkedIn Draft Rules:
    - MUST BE IN ENGLISH.
    - Professional, very slight subtle humor, respectful.
    - Structure: [ALL CAPS TITLE] + [1 blank line] + [Main corporate body text] + [1 blank line] + [A compelling question at the end to encourage comments/discussions].

    Output Format:
    ---X---
    [X text here]
    ---LINKEDIN---
    [LinkedIn text here]
    """
    return model.generate_content(prompt).text

def send_to_telegram(text, image_url, market_name):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    header_text = f"🔔 *Automated Report: {market_name}*"
    
    requests.post(f"{base_url}/sendPhoto", data={"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": header_text, "parse_mode": "Markdown"})
    requests.post(f"{base_url}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": text})

if __name__ == "__main__":
    title, summary, image, market_name = get_news()
    if title:
        content = generate_text(title, summary, market_name)
        send_to_telegram(content, image, market_name)
        print(f"Success for {market_name}!")
    else:
        print("News could not be fetched.")
                  
