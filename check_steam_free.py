import requests
import feedparser
import os
import json
from datetime import datetime

def check_steam_free_games():
    rss_sources = [
        "https://www.reddit.com/r/FreeGameFindings/new/.rss",
        "https://gg.deals/free-games/feed/",
    ]
    
    try:
        with open('pushed_games.json', 'r') as f:
            pushed_games = set(json.load(f))
    except:
        pushed_games = set()
    
    new_games = []
    
    for rss_url in rss_sources:
        try:
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:5]:
                title = entry.title.lower()
                link = entry.link
                
                if 'steam' in title or 'free' in title:
                    if title not in pushed_games:
                        new_games.append({
                            'title': entry.title,
                            'link': link,
                            'published': entry.get('published', 'Unknown')
                        })
                        pushed_games.add(title)
        except Exception as e:
            print(f"Error: {e}")
    
    with open('pushed_games.json', 'w') as f:
        json.dump(list(pushed_games), f)
    
    return new_games

def send_wechat_notification(game_info):
    sendkey = os.getenv('SERVERCHAN_KEY')
    if not sendkey:
        print("SERVERCHAN_KEY not set")
        return False
    
    title = f"🎮 Steam喜加一: {game_info['title']}"
    desp = f"""
**游戏名称**: {game_info['title']}

**发布时间**: {game_info['published']}

**领取链接**: [点击前往Steam商店]({game_info['link']})

---

*自动推送，尽快领取！*
    """
    
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = {
        "title": title,
        "desp": desp
    }
    
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Send error: {e}")
        return False

if __name__ == "__main__":
    new_games = check_steam_free_games()
    
    if new_games:
        print(f"Found {len(new_games)} new games")
        for game in new_games:
            success = send_wechat_notification(game)
            if success:
                print(f"Sent: {game['title']}")
            else:
                print(f"Failed: {game['title']}")
    else:
        print("No new games")
