# -*- coding: utf-8 -*-
# 本模块用于解析文章

import re
import xmltodict
from bs4 import BeautifulSoup as bs
import logging
from utils.nlp import sent_split,REDUNDANT_PATTERN
from utils.misc import get_now,article_summary
from database.sql_database import get_artile_by_url,insert_token_usage
from config import MAX_CONTENT_SIZE
from utils.httpx_client import get_requests,proxy_selenuim
from const.enums import UseCase

def verify_url(article_url):
    """
    简单验证文章url是否是微信公众号文章

    Parameters
    ----------
    article_url: str
        文章链接
    """
    verify_lst = ["mp.weixin.qq.com"]#, "__biz", "mid", "sn", "idx"]
    for string in verify_lst:
        if string not in article_url:
            return False
    return True

def parse_publish_time(html):
    logging.warning(f'默认用现在时间')
    return get_now()

async def crawl_article(article_url):
    logging.info(f'开始爬取文章 {article_url}')
    ret = await get_requests(article_url)
    if ret.status_code in [301,302]:
        location_url = ret.headers.get('Location')
        ret = await get_requests(location_url)
    if ret.status_code != 200:
        logging.warning(f"请求文章失败，状态码：{ret.status_code}")
        html = '你的访问过于频繁，需要从微信打开验证身份，是否需要继续访问当前页面'
    else:
        html = ret.text
    if "你的访问过于频繁，需要从微信打开验证身份，是否需要继续访问当前页面" in html:
        logging.warning("访问过于频繁")
        html = await proxy_selenuim(article_url)
        if "你的访问过于频繁，需要从微信打开验证身份，是否需要继续访问当前页面" in html:
            return None
    
    soup = bs(html, "lxml")
    publish_time = parse_publish_time(html)
    try:
        body = soup.find(class_="rich_media_area_primary_inner")
        content_p = body.find(class_="rich_media_content")
        if not content_p:
            content_p = soup.find(id="js_content")
        if not content_p:
            content_p = soup.find(id='js_content_container')

        text = content_p.text.strip()
        # 只获取纯文本
        return {'content':text,"publish_time":publish_time}
        
    except:
        return  {'content': '',"publish_time":publish_time}


def get_other_info_of_article(doc):
    if 'is_clickbait' not in doc:
        doc['is_clickbait'] = False
    if 'is_marketing' not in doc:
        doc['is_marketing'] = False
    if 'category' not in doc:
        doc['category'] = ''
    if 'keywords' not in doc:
        doc['keywords'] = ''
    return doc


async def get_article_from_pub(msg, author_id, author):
    async def get_article_from_pub_inner(msg, author_id, author):
        url = msg['url']
        title = msg['title']
        # desc = msg.get('desc','')
        if not verify_url(url):
            logging.info(f"不是公众号文章, url = {url}")
            return None
        
        if 'chksm' in url:
            urls = re.findall('(.*?)&chksm=.*',url)
        else:
            urls = [url]
        if not urls:
            logging.info(f"无法获取文章链接, url = {url}")
            return None
        url = urls[0]
        doc = get_artile_by_url(url)
        if doc is not None:
            logging.info('文章已经在数据库中')
            return doc
        if url.startswith('http://'):
            redirect_url = url.replace('http://','https://')
        else:
            redirect_url = url
        doc = await crawl_article(redirect_url)
        if not doc['content']:
            logging.warning(f"无法获取文章内容, url = {url}")
            return None
        return {"url":url, 'title':title, 'author':author, 'author_id':author_id, 'content':doc['content'], 'publish_time':doc['publish_time']}

    try:
        doc = await get_article_from_pub_inner(msg, author_id, author)
    except Exception as e:
        logging.warning(f"获取文章内容失败, e = {e}")
        doc = None
    if not doc or ',轻点两下取消赞' in doc.get('content') :
        logging.warning('文章获取失败：' + '内容为空' if not doc else '公众号文章存在轻点两下取消赞内容')
        return None
    if len(doc['content']) < 50:
        logging.warning('文章字数太少')
        return None
    msg = f'文章获取成功，开始总结，字数{len(doc["content"])}'
    # 如果是新文章，则需要做summary
    if 'summary' not in doc or '调用模型失败' in doc.get('summary'):
        logging.warning('摘要为空，重新获取')
        summary, usage = article_summary(doc)
        if usage:
            insert_token_usage(
                usage=usage,
                use_case=UseCase.PUB,
                user='global')
        doc['summary'] = summary['summary']
        doc['keywords'] = summary['keywords']
        doc['is_marketing'] = summary['marketing']
        doc["is_clickbait"] = False
        doc["category"] = summary['category']
    doc = get_other_info_of_article(doc)
    return doc


async def get_article(data, raw_text = False, send_fn=None):
    logging.info('获取文章信息')
    raw_msg = data['raw_msg']
    try:    
        msg = xmltodict.parse(raw_msg)
    except:
        logging.warning(f"xml解析失败, {raw_msg}")
        return None
    msg = msg['msg']['appmsg']
    if 'url' not in msg:
        logging.info(f"不包含文章链接, msg = {msg}")
        return None
    url = msg['url']
    title = msg['title']
    # desc = msg.get('des','')
    author_id = msg['sourceusername']
    author = msg['sourcedisplayname']

    if not verify_url(url):
        logging.info(f"不是公众号文章, url = {url}")
        return None
    
    if 'chksm' in url:
        urls = re.findall('(.*?)&chksm=.*',url)
    else:
        urls = [url]
    if not urls:
        logging.info(f"无法获取文章链接, url = {url}")
        return None
    url = urls[0]
    doc = get_artile_by_url(url)
    if doc is not None:
        return doc
    if send_fn:
        await send_fn('正在获取文章内容，请稍后...')

    if url.startswith('http://'):
        redirect_url = url.replace('http://','https://')
    else:
        redirect_url = url

    doc = await crawl_article(redirect_url)
    if not doc['content']:
        logging.warning(f"无法获取文章内容, url = {url}")
        return None
    return {"url":url, 'title':title, 'author':author, 'author_id':author_id, 'content':doc['content'], 'publish_time':doc['publish_time']}


async def article_manage(data, user_id, room=''):
    try:
        doc = await get_article(data, raw_text=True, send_fn=None)
    except Exception as e:
        print(e)
        doc = None
    if not doc or ',轻点两下取消赞' in doc.get('content') :
        logging.warning('文章获取失败')
        return None
    if len(doc['content']) < 50:
        logging.warning('文章字数太少')
        return None
    msg = f'文章获取成功，开始总结，字数{len(doc["content"])}'
    logging.info(msg)
    # 如果是新文章，则需要做summary
    if 'summary' not in doc or '调用模型失败' in doc.get('summary'):
        logging.warning('摘要为空，重新获取')
        summary, usage = article_summary(doc)
        if usage:
            insert_token_usage(
                usage=usage,
                use_case=UseCase.SUMMARY,
                user=room if room else user_id)
        doc['summary'] = summary['summary']
        doc['keywords'] = summary['keywords']
        doc['is_marketing'] = summary['marketing']
        doc["is_clickbait"] = False
        doc["category"] = summary['category']
    doc = get_other_info_of_article(doc)
    return doc