import xmltodict
import logging
import arxiv
import traceback
import concurrent.futures
from datetime import timedelta


from config import MAX_PUBLIC_NUM
from plugins.article import get_article_from_pub
from database.sql_database import (
    get_user_subscription_info,
    insert_token_usage,
    insert_wx_article_to_sql,get_user_all_pub_id,
    get_last_user_pub_push_time,get_article_by_pub_id_and_push_time,
    delete_user_pub_by_name,
    update_user_push_status,
    get_user_subscription_info,
    get_arxiv_by_id, insert_arxiv,get_github_trending_by_name,upsert_github_trending
    )

from prompt import ARXIV_SYSTEM
from utils.llm import call_llm,SystemMessage,UserMessage,Messages
from utils.misc import try_extract_json,get_now,article_summary,translate
from utils.github_trending import parse_github_trending,get_github_content
from const.enums import UseCase



def get_pub_push(user_id, max_cnt=100):
    # 获取关注的公众号
    pub_ids = get_user_all_pub_id(user_id)
    if not pub_ids:
        return []
    # 获取上次发送的时间
    last_push_time = get_last_user_pub_push_time(user_id)
    # 如果没有发送过，默认使用一周的时间
    if not last_push_time:
        last_push_time = get_now() - timedelta(days=7)
    # 获取从上次发送到现在的公众号文章
    docs = []
    for pub_id in pub_ids.values():
        docs.extend(get_article_by_pub_id_and_push_time(pub_id['pub_id'],last_push_time))
    # 聚合，抽取主题
    if not docs:
        return []
    docs = docs[:max_cnt]
    return docs

async def get_github_trending():
    # 最好的源当然是 https://github.com/trending，但是需要解析
    now = get_now()
    docs = await parse_github_trending()

    # 优先数组
    priority_docs = []
    not_priority_docs = []

    for doc in docs:
        name = doc['name']
        item = get_github_trending_by_name(name)
        if item:
            print('update',item['name'])
            # update item
            for k in doc.keys():
                item[k] = doc[k]
            last_pushtime = item['last_pushtime']
            now_date = now.date()
            last_pushtime_date = last_pushtime.date()
            difference = abs(now_date - last_pushtime_date)
            if difference >= timedelta(days=2):
                # 超过一天，优先推送
                item['times_of_today'] += 1
                item['last_pushtime'] = now
                priority_docs.append((difference.days,item))
            elif not item['summary']:
                priority_docs.append((1,item))
            else:
                not_priority_docs.append(item)
        else:
            print('new item',doc['name'])
            # update doc
            doc['about_zh'] = translate(doc['about']) if len(doc['about']) > 50 else doc['about']
            doc['summary'] = ''
            doc['description'] = ''
            doc['times_of_today'] = 1
            doc['last_pushtime'] = now
            priority_docs.append((100,doc))
        
    priority_docs = sorted(priority_docs, key=lambda x: x[0], reverse=True)
    priority_docs = [item[1] for item in priority_docs]

    # insert all docs back to sql
    print('insert github to sql')
    for doc in priority_docs:
        upsert_github_trending(doc)

    if len(priority_docs)== 0:
        return False


    # get info by crawling
    for doc in priority_docs + not_priority_docs:
        name = doc['name']
        if not doc['summary']:
            try:
                logging.info(f'爬取 {name}的内容')
                content = await get_github_content(name)
            except:
                traceback.print_exc()
                content = ''
            if not content:
                continue
            logging.info(f'爬取 {name}的内容成功, 生成摘要')
            try:
                summary, usage = article_summary({'title':name,'content':content},do_split=True)
                if usage:
                    insert_token_usage(usage,UseCase.GITHUB,'global')
                doc['summary'] = summary['summary']
                doc['keywords'] = summary['keywords']
                doc["category"] = summary['category']
                doc['description'] = content
                upsert_github_trending(doc)
            except:
                traceback.print_exc()
                continue

    return True

def get_arxiv_by_category(
        category=['cs.CL','cs.AI'], 
        max_results=200, 
        topics = 'Anything that related to language models, LLM, agent, GPT, llama, multi agent, multimodal, or using language models to solve problems',
        non_topics = '小语种如法语、德语、日语等非中英文方面的研究内容；命名实体识别'
        ):
    search = arxiv.Search(
        query = ' OR '.join(f"cat:{c}" for c in category),
        max_results = max_results,
        sort_by = arxiv.SortCriterion.SubmittedDate
        )
    
    tasks = []
    logging.info('查询arxiv论文')
    for result in search.results():
        if result.primary_category not in category:
            continue
        entry_id = result.entry_id
        doc = get_arxiv_by_id(entry_id)
        if doc:
            continue
        tasks.append(result)
    logging.info(f'共{len(tasks)}篇论文')

    def task_process(result):
        paper = '''## Title: \n{title}\n\n## Abstract:\n{summary}\n\n请记住我的兴趣是：{topics}.\n我不感兴趣的是：{non_topics}\n请你严格根据标题和摘要提取主题词，不要捏造，并且不要使用我提供的兴趣词。\n只输出json内容，不要任何解释和说明。'''.format(title=result.title,summary = result.summary[:3000], topics=topics,non_topics=non_topics)    
        entry_id = result.entry_id
        publish_time = result.published
        messages = Messages([SystemMessage(ARXIV_SYSTEM),
                    UserMessage(paper)])
        try:
            res,usage = call_llm(messages,max_tokens=-1,temperature=0.1)
            if usage:
                insert_token_usage(
                    usage=usage,
                    use_case=UseCase.ARXIV,
                    user="global")
            res = str(res)
            res = try_extract_json(res)
            if not res or not res.get('summary',''):
                return {
                    'category': result.primary_category,
                    'comment': result.comment,
                    'authors': ','.join(x.name for x in result.authors[:3]),
                    'status': False,
                    'entry_id':entry_id,
                    'publish_time':publish_time,
                    'title':result.title,
                    'title_chinese': '',
                    'summary':result.summary,
                    'topic':'',
                    'matched': False,
                    "emoji": "📑",
                    'simple_summary':''
                    }
            return {
                'category': result.primary_category,
                'comment': result.comment,
                'authors': ','.join(x.name for x in result.authors[:3]),
                'status': True,
                'entry_id':entry_id,
                'publish_time':publish_time,
                'title':result.title,
                'title_chinese': res['title'],
                'summary':result.summary,
                'topic':res['topic'],
                'matched': bool(res['matched']),
                "emoji": "📑",
                'simple_summary':res['summary']}
        except:
            return {   
                'category': result.primary_category,
                'comment': result.comment,
                'authors': ','.join(x.name for x in result.authors[:3]),
                'status': False,
                'entry_id':entry_id,
                'publish_time':publish_time,
                'title':result.title,
                'title_chinese': '',
                'summary':result.summary,
                'topic':'',
                'matched': False,
                "emoji": "📑",
                'simple_summary':''
                }
        

    logging.info('提取论文摘要...')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 使用 map 来并发地对每个任务调用 call_gpt 函数
        ret = executor.map(task_process, tasks)

    fails = []
    docs = []
    for doc in ret:
        doc['crawl_time'] = get_now()
        if doc['status']:
            if doc['matched']:
                docs.append(doc)
            else:
                fails.append(doc)
            insert_arxiv(doc)
        else:
            fails.append(doc)
    logging.info(f'共处理{len(docs)}篇论文，其中失败{len(fails)}，成功{len(docs)}')

    if len(docs) < 1:
        return f"今天没有更新的论文了"

    return '论文已经更新'

def push_manage(from_wxid, msg, room):
    if msg == '订阅功能':
        default_msg = f'''
「直接推荐公众号给我，我会自动帮您进行关注，关注上限为{MAX_PUBLIC_NUM}」
「取消关注 公众号名称」取消关注某个公众号
「公众号列表」获取目前关注的公众号列表
「订阅状态」获取您的订阅配置信息，如时间，邮箱
「主动推送」主动推送公众号消息
「取消主动推送」取消主动推送公众号消息
'''
        return default_msg
    
    info = get_user_subscription_info(from_wxid)
    if msg == '订阅状态':
        if not info:
            return '你还没有配置订阅信息，参考「订阅功能」进行配置'
        else:
            return f"你的订阅信息如下：\n{info}"
    
    if msg == '主动推送':
        update_user_push_status(room if room else from_wxid, True)
        return '已为您开启主动推送'
    
    if msg == '取消主动推送':
        update_user_push_status(room if room else from_wxid, False)
        return '已为您关闭主动推送'

    if msg == '公众号列表':
        pub_ids = get_user_all_pub_id(room if room else from_wxid)
        info = '\n'.join([f"{i} - {v['pub_name']}" for i,v in enumerate(pub_ids.values())])
        return "您关注的公众号列表如下:\n" + info

    if msg[:4] == '取消关注' and len(msg) > 4:
        pub_name = msg[4:].strip()
        if len(pub_name) >= 20:
            return '请检查公众号名称是否正确'
        ret = delete_user_pub_by_name(room if room else from_wxid, pub_name)
        return f"取消关注公众号{pub_name}成功" if ret else f"取消关注公众号{pub_name}失败"

async def pub_manage(data, from_wxid, pub_name=''):
    msg = data['raw_msg']
    msg = xmltodict.parse(msg)
    items = msg['msg']['appmsg']['mmreader']['category']['item']
    # 有些公众号有时候只有一条推送
    if not isinstance(items, list):
        items = [items]
    
    info = f'获取到公众号「{pub_name}」 - {len(items)}条推送'
    logging.info(info)
    if len(items) >= 10:
        info  = '推送过多，解析有问题。'
        logging.warning(info)
        return info

    docs = []
    for item in items:
        doc = await get_article_from_pub(item, from_wxid, pub_name)
        if doc:
            insert_wx_article_to_sql(doc)
            docs.append(doc)
    info += f'\n成功解析{len(docs)}条入库。'
    return info, docs
  
if __name__ == '__main__':
    get_arxiv_by_category(max_results=60)


