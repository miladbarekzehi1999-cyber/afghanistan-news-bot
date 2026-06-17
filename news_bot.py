import requests
from bs4 import BeautifulSoup
import os
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS").split(",")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# -----------------------------
# Breaking news detection
# -----------------------------
def is_breaking(title):

    keywords = [
        "فوری",
        "انفجار",
        "حمله",
        "کشته",
        "بازداشت",
        "زلزله",
        "درگیری"
    ]

    for k in keywords:
        if k in title:
            return True

    return False


# -----------------------------
# Normalize title
# -----------------------------
def normalize(text):

    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


# -----------------------------
# Extract article image
# -----------------------------
def get_image(article_url):

    try:
        r = requests.get(article_url, headers=HEADERS, timeout=20)

        soup = BeautifulSoup(r.text, "lxml")

        meta = soup.find("meta", property="og:image")

        if meta:
            return meta["content"]

        img = soup.find("img")

        if img and img.get("src"):
            return img["src"]

    except:
        pass

    return None


# -----------------------------
# Khaama Press
# -----------------------------
def khaama_news():

    url = "https://www.khaama.com/persian/"

    r = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(r.text, "lxml")

    news = []

    for a in soup.select("h2 a")[:6]:

        title = a.get_text(strip=True)

        link = a["href"]

        news.append(("خامه پرس", title, link))

    return news


# -----------------------------
# TOLOnews
# -----------------------------
def tolo_news():

    url = "https://tolonews.com/fa/afghanistan"

    r = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(r.text, "lxml")

    news = []

    for a in soup.select("h3 a")[:6]:

        title = a.get_text(strip=True)

        href = a.get("href")

        if href.startswith("/"):
            link = "https://tolonews.com" + href
        else:
            link = href

        news.append(("طلوع نیوز", title, link))

    return news


# -----------------------------
# AVA Press
# -----------------------------
def ava_news():

    url = "https://www.avapress.com/fa"

    r = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(r.text, "lxml")

    news = []

    for a in soup.select("h3 a")[:6]:

        title = a.get_text(strip=True)

        link = a["href"]

        news.append(("خبرگزاری آوا", title, link))

    return news


# -----------------------------
# Load sent links
# -----------------------------
def load_links():

    if not os.path.exists("last_news.txt"):
        return set()

    with open("last_news.txt", "r") as f:
        return set(f.read().splitlines())


# -----------------------------
# Save new links
# -----------------------------
def save_links(links):

    with open("last_news.txt", "a") as f:

        for link in links:
            f.write(link + "\n")


# -----------------------------
# Send text
# -----------------------------
def send_message(message):

    for chat_id in CHAT_IDS:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            requests.post(url, data=data, timeout=20)
        except:
            pass


# -----------------------------
# Send photo
# -----------------------------
def send_photo(caption, image):

    for chat_id in CHAT_IDS:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        data = {
            "chat_id": chat_id,
            "photo": image,
            "caption": caption,
            "parse_mode": "HTML"
        }

        try:
            requests.post(url, data=data, timeout=20)
        except:
            pass


# -----------------------------
# Mix sources (balanced feed)
# -----------------------------
def collect_news():

    khaama = khaama_news()
    tolo = tolo_news()
    ava = ava_news()

    mixed = []

    max_len = max(len(khaama), len(tolo), len(ava))

    for i in range(max_len):

        if i < len(khaama):
            mixed.append(khaama[i])

        if i < len(tolo):
            mixed.append(tolo[i])

        if i < len(ava):
            mixed.append(ava[i])

    return mixed


# -----------------------------
# Main
# -----------------------------
def main():

    old_links = load_links()

    all_news = collect_news()

    seen_titles = set()

    new_links = []

    sent = 0

    for source, title, link in all_news:

        if link in old_links:
            continue

        norm = normalize(title)

        if norm in seen_titles:
            continue

        seen_titles.add(norm)

        if is_breaking(title):
            prefix = "🚨 <b>خبر فوری</b>\n\n"
        else:
            prefix = ""

        caption = f"""{prefix}📰 <b>{source}</b>

<a href="{link}">{title}</a>

🔗 ادامه خبر:
{link}
"""

        image = get_image(link)

        if image:
            send_photo(caption, image)
        else:
            send_message(caption)

        new_links.append(link)

        sent += 1

        if sent >= 5:
            break

    save_links(new_links)


if __name__ == "__main__":
    main()
