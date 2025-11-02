import requests
import os
import json
from datetime import datetime

def get_website_content():
    """获取网站内容"""
    try:
        url = 'https://d.aigclink.ai/?v=8f252a54730e49f4b8caf897b7ae49f6'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"获取网站内容失败: {e}")
        return None

def parse_news(html_content):
    """
    解析新闻内容
    注意：这部分需要根据目标网站的实际HTML结构调整
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    news_items = []
    
    # 这里需要根据实际网站结构调整选择器
    # 示例选择器，你需要根据网站实际HTML调整
    
    # 尝试多种可能的选择器
    possible_selectors = [
        'article', 
        '.news-item',
        '.post',
        '.entry',
        'h3 a',  # 标题链接
        'h2 a'
    ]
    
    for selector in possible_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"使用选择器 '{selector}' 找到 {len(elements)} 个元素")
            for element in elements[:5]:  # 只处理前5个
                try:
                    # 尝试提取标题和链接
                    if element.name == 'a':
                        title = element.get_text(strip=True)
                        link = element.get('href', '')
                    else:
                        title_element = element.find('a') or element.find('h2') or element.find('h3') or element
                        title = getattr(title_element, 'text', '').strip()
                        link_element = element.find('a') or element
                        link = link_element.get('href', '')
                    
                    # 过滤无效数据
                    if title and len(title) > 5 and link:
                        # 处理相对链接
                        if link.startswith('/'):
                            link = 'https://d.aigclink.ai' + link
                        
                        news_items.append({
                            'title': title,
                            'link': link
                        })
                        print(f"找到新闻: {title}")
                except Exception as e:
                    print(f"解析元素时出错: {e}")
            break  # 找到有效选择器后停止尝试
    
    # 如果没找到任何新闻，返回示例数据用于测试
    if not news_items:
        print("未找到新闻，返回示例数据")
        news_items = [
            {'title': '示例新闻标题1', 'link': 'https://example.com/1'},
            {'title': '示例新闻标题2', 'link': 'https://example.com/2'}
        ]
    
    return news_items

def send_to_feishu(news_items):
    """发送新闻到飞书"""
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL')
    if not webhook_url:
        print("错误: 未找到飞书Webhook URL")
        return False
    
    success_count = 0
    
    for news in news_items:
        # 构建消息卡片
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**{news['title']}**\n\n[阅读全文]({news['link']})",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"📰 来自 AIGC Link 的新闻 | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                            }
                        ]
                    }
                ],
                "header": {
                    "title": {
                        "content": "🚨 AIGC 最新动态",
                        "tag": "plain_text"
                    },
                    "template": "wathet"
                }
            }
        }
        
        try:
            response = requests.post(
                webhook_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(message),
                timeout=10
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"✓ 成功发送: {news['title']}")
            else:
                print(f"✗ 发送失败 ({response.status_code}): {news['title']}")
                print(f"响应: {response.text}")
        except Exception as e:
            print(f"✗ 请求异常: {e}")
    
    return success_count

def main():
    """主函数"""
    print("开始获取AIGC新闻...")
    
    # 获取网站内容
    html_content = get_website_content()
    if not html_content:
        print("无法获取网站内容，退出")
        return
    
    # 解析新闻
    news_items = parse_news(html_content)
    print(f"解析到 {len(news_items)} 条新闻")
    
    # 发送到飞书
    if news_items:
        success_count = send_to_feishu(news_items)
        print(f"推送完成: 成功发送 {success_count}/{len(news_items)} 条新闻")
    else:
        print("没有找到可推送的新闻")

if __name__ == "__main__":
    main()
