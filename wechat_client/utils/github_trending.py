from lxml import html
import time

from utils.httpx_client import proxy_requests,proxy_selenuim


async def get_github_content(name):
    url = f'https://github.com/{name}'
    # 发送请求
    retry = 5
    response = None
    while retry > 0:
        try:
            response = await proxy_requests(url)
            break
        except Exception as e:
            retry -= 1
            print(f'获取github {name}失败，重试剩余{retry}')
            time.sleep(5)
    
    if not response:
        content = await proxy_selenuim(url)
    else:
        content = response
    def parse(content):
        # 解析HTML内容
        tree = html.fromstring(content)
        # 获取所有的内容
        articles = tree.xpath("//article")
        return articles
    
    articles = parse(content)
    if not articles:
        content = await proxy_selenuim(url)
        articles = parse(content)
    if articles:
        return articles[0].text_content().strip()
    return ''



async def parse_github_trending():
    url = 'https://github.com/trending'

    # 发送请求
    retry = 5
    response = None
    while retry > 0:
        try:
            response = await proxy_requests(url)
            break
        except Exception as e:
            retry -= 1
            print(f'获取github trending失败，重试剩余{retry}')
            time.sleep(5)
    if not response:
        return []
    # 解析HTML内容
    tree = html.fromstring(response)
    # 获取所有的内容
    articles = tree.xpath("//article[@class='Box-row']")

    infos = []
    for rank, article in enumerate(articles):
        a = article.xpath(".//h2/a")[0]
        name = a.get('href')
        about = article.xpath(".//p")
        if about:
            about = about[0].text_content().strip()
        else:
            about = ''

        spans = article.xpath(".//div[2]/span")
        if len(spans) == 3:
            language = spans[0].text_content().strip()
            stars_today = spans[2].text_content().strip()
        else:
            language = ''
            stars_today = spans[1].text_content().strip()

        aa = article.xpath(".//div[2]/a")
        stars = aa[0].text_content().strip()
        forks = aa[1].text_content().strip()

        infos.append({
            'name': name[1:] if name.startswith('/') else name,
            'about': about,
            "rank": rank + 1,
            'language': language,
            'stars': stars,
            'forks': forks,
            'stars_today': stars_today,
        })
    print(f"get {len(infos)} githubs")
    return infos
