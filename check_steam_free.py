import requests
import feedparser
import os
import json
import re
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
            
            for entry in feed.entries[:10]:  # 检查更多条目
                title = entry.title
                link = entry.link.lower()  # 链接也转为小写便于检查

                # --- 更严格的过滤条件 ---
                steam_keywords = ['steam', 'Steam']
                # 必须包含以下词条之一才推送
                must_contain_keywords = ['free', 'Free', '100%', 'giveaway']
                # 包含以下任何词条就排除（不推送）
                excluded_keywords = ['DLC', 'dlc', 'beta', 'Beta', 'demo', 'Demo', 'pack', 'Pack', 'cosmetic', 'skin', 'item', 'ingame', 'in-game', 'Epic', 'GOG', 'Amazon', 'Uplay']

                # 检查1：必须与Steam相关
                is_steam_related = any(keyword in title for keyword in steam_keywords) or 'steampowered.com' in link
                
                # 检查2：必须明确是免费活动
                is_truly_free = any(keyword in title for keyword in must_contain_keywords)
                
                # 检查3：不能是排除的内容
                is_excluded = any(exclude in title for exclude in excluded_keywords)

                # 最终判断：与Steam相关 + 是真免费 + 不是排除内容
                if is_steam_related and is_truly_free and not is_excluded:
                    # 使用链接作为唯一标识（更准确）
                    if link not in pushed_games:
                        # 清理游戏名称
                        clean_title = re.sub(r'\[.*?\]', '', title)  # 移除方括号内容
                        clean_title = re.sub(r'\(.*?\)', '', clean_title)  # 移除圆括号内容
                        clean_title = clean_title.strip()
                        
                        new_games.append({
                            'title': clean_title[:100],  # 限制长度
                            'link': link,
                            'published': entry.get('published', '最近'),
                            'source': rss_url
                        })
                        pushed_games.add(link)
        except Exception as e:
            print(f"Error: {e}")
    
    # 保存已推送的游戏列表
    with open('pushed_games.json', 'w') as f:
        json.dump(list(pushed_games), f)
    
    return new_games

def send_wechat_notification(game_info):
    sendkey = os.getenv('SERVERCHAN_KEY')
    if not sendkey:
        print("SERVERCHAN_KEY not set")
        return False
    
    # 更清晰的消息格式
    title = f"🎮 Steam喜加一: {game_info['title']}"
    desp = f"""
**🎯 游戏名称**: {game_info['title']}

**🕐 发布时间**: {game_info['published']}

**🔗 领取方式**:
1. 点击本消息进入详情页
2. 在详情页中点击「领取链接」
3. 跳转到Steam商店领取

**💡 提示**: 这是完全免费的游戏，领取后永久拥有！

---

*自动推送，尽快领取以免错过！*
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
    print("开始检查免费游戏...")
    new_games = check_steam_free_games()
    
    if new_games:
        print(f"发现 {len(new_games)} 个新免费游戏")
        for game in new_games:
            print(f"准备推送: {game['title']}")
            success = send_wechat_notification(game)
            if success:
                print(f"✅ 推送成功: {game['title']}")
            else:
                print(f"❌ 推送失败: {game['title']}")
    else:
        print("❌ 未发现新的免费游戏")
