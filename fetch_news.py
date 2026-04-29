import feedparser
import json
import requests
from bs4 import BeautifulSoup
import time
import re

# Browser ကဲ့သို့ လှည့်စားရန် Header သတ်မှတ်ခြင်း
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

def get_full_article(url, source):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_html = ""
        
        # သတင်းဌာနအလိုက် Content ရှိသော Class/Tag များကို ရှာခြင်း
        if source == "Myanmar Now":
            main_content = soup.find('div', class_='entry-content')
        elif source == "DVB News":
            main_content = soup.find('div', class_='entry-content')
        elif source == "BBC Burmese":
            main_content = soup.find('main', role='main')
        else:
            main_content = soup.find('article')

        if main_content:
            # လိုအပ်သော Tag များကိုသာ ယူမည် (စာသား၊ ပုံ၊ ဗီဒီယို)
            for element in main_content.find_all(['p', 'img', 'iframe', 'h2', 'h3']):
                # စာသားယူခြင်း
                if element.name in ['p', 'h2', 'h3']:
                    text = element.get_text().strip()
                    if len(text) > 2:
                        content_html += f"<{element.name}>{text}</{element.name}>"
                
                # ပုံယူခြင်း
                elif element.name == 'img':
                    img_url = element.get('src') or element.get('data-src')
                    if img_url and img_url.startswith('http'):
                        content_html += f'<img src="{img_url}" style="width:100%; border-radius:10px; margin:15px 0;">'
                
                # ဗီဒီယို (YouTube Embed Fix) - Error 153 မတက်စေရန် ပြင်ဆင်ခြင်း
                elif element.name == 'iframe':
                    video_url = element.get('src')
                    if video_url and 'youtube' in video_url:
                        # Video ID ကို Regex ဖြင့် ထုတ်ယူခြင်း
                        video_id_match = re.search(r"(?:v=|\/embed\/|\/watch\?v=|\/v\/|\.be\/)([a-zA-Z0-9_-]{11})", video_url)
                        if video_id_match:
                            video_id = video_id_match.group(1)
                            # enablejsapi=1 ကို ဖြုတ်ပြီး playsinline=1 ထည့်သွင်းထားပါသည်
                            clean_embed_url = f"https://www.youtube.com/embed/{video_id}?rel=0&playsinline=1&modestbranding=1"
                            
                            content_html += f'<div style="position:relative; padding-bottom:56.25%; height:0; margin:15px 0;">'
                            content_html += f'<iframe src="{clean_embed_url}" style="position:absolute; top:0; left:0; width:100%; height:100%; border-radius:10px;" '
                            content_html += f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>'

        return content_html if content_html else "<p>သတင်းအကြောင်းအရာ မတွေ့ရှိပါ။</p>"
    except Exception as e:
        return f"<p>Error loading content: {str(e)}</p>"

def fetch_rss_news(rss_url, source_name):
    print(f"Fetching RSS: {source_name}")
    feed = feedparser.parse(rss_url)
    news_items = []
    for entry in feed.entries[:12]: # တစ်ခုကို ၁၂ ပုဒ်ယူမည်
        thumb = ""
        if 'media_content' in entry:
            thumb = entry.media_content[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if 'image' in link.get('type', ''): thumb = link.get('href', '')
        
        print(f"Processing: {entry.title}")
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "thumb": thumb,
            "date": entry.get('published', 'ယနေ့'),
            "source": source_name,
            "content": get_full_article(entry.link, source_name)
        })
        time.sleep(1) # Server Block မဖြစ်စေရန်
    return news_items

# အချက်အလက်များ စုစည်းခြင်း (YKT News ကို ဖယ်ရှားလိုက်ပါပြီ)
all_news = []
all_news.extend(fetch_rss_news("https://myanmar-now.org/mm/feed/", "Myanmar Now"))
all_news.extend(fetch_rss_news("https://burmese.dvb.no/feed/", "DVB News"))
all_news.extend(fetch_rss_news("https://www.bbc.com/burmese/index.xml", "BBC Burmese"))

# JSON ထုတ်ခြင်း
with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(all_news, f, ensure_ascii=False, indent=4)

print(f"Finish! news.json created with {len(all_news)} articles.")
