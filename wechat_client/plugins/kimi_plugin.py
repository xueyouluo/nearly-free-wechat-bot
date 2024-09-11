import re
from database.sql_database import delete_user_thread, get_last_user_thread, upsert_user_thread, insert_token_usage, insert_kimi_arxiv_data, get_last_user_kimi_token, upsert_user_kimi_token 
from utils.kimi import new_chat,chat
from utils.misc import get_now
from const.enums import UseCase

sumary_prompt = '''总结这篇论文，列出：1.论文的标题 2. 论文要解决什么问题 3. 论文用什么方法解决这个问题的 4. 论文做了哪些实验。如果论文是一篇综述，那么以结构化的形式列出主要内容即可。 <url id="" type="url" status="" title="" wc="">{pdf}</url>'''
url_prompt  = '''帮我阅读这个链接，以结构化的形式列出主要内容： <url id="" type="url" status="" title="" wc="">{pdf}</url>'''

kimi_summary_prompt = '''总结链接的内容：<url id="" type="url" status="" title="" wc="">http://www.followllm.online/{link}</url>           
请以一个专业主编的口吻，生成一个内容介绍综述。不要枚举每一篇文章。生成整体的概要即可。
概要包含：1. 链接的主要内容。2. 包含了哪些主要话题。3. 列举几篇你推荐的文章以及你推荐的理由。4. 总结
注意请直接输出概要内容，不要输出链接地址和你的身份内容。'''

def kimi_summary_html(link):
    kimi_id = new_chat()
    if kimi_id is None:
        return '今天的总结抽风了。'
    ans = chat(kimi_id,kimi_summary_prompt.format(link=link))
    insert_token_usage({'model':'kimi-chat'},UseCase.KIMI_CHAT,'global')
    if ans:
        insert_kimi_arxiv_data({'link':link,'content':ans})
        return ans
    else:
        return '今天的总结抽风了。'

def extract_url(text):
    url = re.search('(http(s)?:\/\/)\w+[^\s]+(\.[^\s]+){1,}',text)
    if url:
        url = url.group()
        return url
    else:
        return None

async def kimi_plugin_manager(user_id, msg, room='', send_fn=None):
    if msg[:7] == 'atoken=':
        tokens = get_last_user_kimi_token(user_id)
        if tokens:
            tokens['access_token'] = msg[7:]
        else:
            tokens = {'access_token':msg[7:],'user_id':user_id,'refresh_token':'','last_update_time': get_now()}
        upsert_user_kimi_token(**tokens)
        return 'access token已更新'
    
    if msg[:7] == 'rtoken=':
        tokens = get_last_user_kimi_token(user_id)
        if tokens:
            tokens['refresh_token'] = msg[7:]
        else:
            tokens = {'refresh_token':msg[7:],'user_id':user_id,'access_token':'','last_update_time': get_now()}
        upsert_user_kimi_token(**tokens)
        return 'refresh token已更新'
    
    user = room if room else user_id
    if msg.lower() == '退出kimi':
        delete_user_thread(user)
        return '已经退出kimi模式'
    
    thread = get_last_user_thread(user)
    if thread:
        now = get_now()
        delta = now - thread['last_update_time']
        # 5分钟认为新的thread
        if delta.seconds > 5 * 60:
            thread = None
    
    if thread is None:
        url = extract_url(msg)
        if not url:
            return None
        if 'arxiv.org' in url and '/abs/' in url:
            url = url.replace('/abs/','/pdf/') + ".pdf"
        
        if send_fn:
            await send_fn('获取到url链接，进入kimi模式，要退出请对我说“退出kimi”')
        kimi_id = new_chat(user)
        if kimi_id is None:
            return "请重新指定kimi的access token和refresh token\n请登录kimi网页版，F12在console中输入localStorage.refresh_token和localStorage.access_token，然后先输入atoken={你的access token}，在输入rtoken={你的refresh token}"
        
        if 'arxiv.org' in url:
            ans = chat(user, kimi_id,sumary_prompt.format(pdf=url),new_chat=True)
        else:
            ans = chat(user, kimi_id,url_prompt.format(pdf=url),new_chat=True)
        insert_token_usage({'model':'kimi-chat'},UseCase.KIMI_CHAT,'global')
        if not ans:
            return '抱歉，我无法总结这个链接，请尝试其他链接。'
        upsert_user_thread(user,kimi_id,get_now())
        return ans
    else:
        kimi_id = thread['thread']
        url = extract_url(msg)
        if url:
            msg = msg.replace(url, f' <url id="" type="url" status="" title="" wc="">{url}</url> ')
        ans = chat(user, kimi_id,msg)
        upsert_user_thread(user,kimi_id,get_now())
        return ans


            

