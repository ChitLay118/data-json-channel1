import feedparser
import json
import requests
from bs4 import BeautifulSoup
import time

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
        elif source == "Khit Thit (YKT)":
            main_content = soup.find('div', class_='entry-content') or soup.find('div', class_='td-post-content')
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
                
                # ဗီဒီယို (YouTube/Embed) ယူခြင်း
                elif element.name == 'iframe':
                    video_url = element.get('src')
                    if video_url and 'youtube' in video_url:
                        content_html += f'<div style="position:relative; padding-bottom:56.25%; height:0; margin:15px 0;"><iframe src="{video_url}" style="position:absolute; top:0; left:0; width:100%; height:100%; border-radius:10px;" frameborder="0" allowfullscreen></iframe></div>'

        return content_html if content_html else "<p>သတင်းအကြောင်းအရာ မတွေ့ရှိပါ။</p>"
    except Exception as e:
        return f"<p>Error loading content: {str(e)}</p>"

def fetch_rss_news(rss_url, source_name):
    print(f"Fetching RSS: {source_name}")
    feed = feedparser.parse(rss_url)
    news_items = []
    for entry in feed.entries[:12]: # တစ်ခုကို ၁၂ ပုဒ်ယူမည်
        # ပုံအကြည်ယူခြင်း
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
        time.sleep(1) # Server အပိတ်မခံရစေရန် ၁ စက္ကန့်နားမည်
    return news_items

def fetch_ykt_scraping():
    print("Scraping YKT News (Khit Thit)...")
    url = "https://yktnews.com/"
    news_items = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        # ပုံစံအသစ်အရ ခေါင်းစဉ်များကို ရှာခြင်း
        articles = soup.find_all('h3', limit=10)
        for art in articles:
            a_tag = art.find('a')
            if a_tag:
                link = a_tag['href']
                title = a_tag.get_text().strip()
                news_items.append({
                    "title": title,
                    "link": link,
                    "thumb": "", 
                    "date": "ယနေ့",
                    "source": "Khit Thit",
                    "content": get_full_article(link, "Khit Thit (YKT)")
                })
    except: pass
    return news_items

# အချက်အလက်များ စုစည်းခြင်း
all_news = []
all_news.extend(fetch_rss_news("https://myanmar-now.org/mm/feed/", "Myanmar Now"))
all_news.extend(fetch_rss_news("https://burmese.dvb.no/feed/", "DVB News"))
all_news.extend(fetch_rss_news("https://www.bbc.com/burmese/index.xml", "BBC Burmese"))
all_news.extend(fetch_ykt_scraping())

# JSON ထုတ်ခြင်း
with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(all_news, f, ensure_ascii=False, indent=4)

print("Finish! news.json created successfully.")
