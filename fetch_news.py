import feedparser
import json
import requests
from bs4 import BeautifulSoup
import datetime

def fetch_rss(url, source_name):
    print(f"Fetching from {source_name}...")
    feed = feedparser.parse(url)
    news_list = []
    for entry in feed.entries[:15]:
        # ပုံပါရင် ယူမယ်၊ မပါရင် အလွတ်ထားမယ်
        thumb = ""
        if 'media_content' in entry:
            thumb = entry.media_content[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if 'image' in link.get('type', ''):
                    thumb = link.get('href', '')

        news_list.append({
            "title": entry.title,
            "link": entry.link,
            "thumb": thumb,
            "date": entry.get('published', 'ခဏတာ'),
            "source": source_name
        })
    return news_list

def fetch_ykt():
    print("Fetching from YKT News...")
    url = "https://yktnews.com/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    news_list = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        # YKT ရဲ့ Article structure ကို ရှာခြင်း
        articles = soup.find_all('h3', limit=15)
        for art in articles:
            a_tag = art.find('a')
            if a_tag:
                title = a_tag.get_text().strip()
                link = a_tag['href']
                news_list.append({
                    "title": title,
                    "link": link,
                    "thumb": "", # YKT က ပုံယူရခက်လို့ လောလောဆယ် အလွတ်ထားပါမယ်
                    "date": "Today",
                    "source": "Khit Thit (YKT)"
                })
    except Exception as e:
        print(f"YKT Error: {e}")
    return news_list

# စတင်စုစည်းခြင်း
all_data = []
all_data.extend(fetch_rss("https://myanmar-now.org/mm/feed/", "Myanmar Now"))
all_data.extend(fetch_rss("https://burmese.dvb.no/feed/", "DVB News"))
all_data.extend(fetch_rss("https://www.bbc.com/burmese/index.xml", "BBC Burmese"))
all_data.extend(fetch_ykt())

# JSON ဖိုင်အဖြစ် သိမ်းဆည်းခြင်း
with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print("Done! news.json created.")
