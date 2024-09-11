
import logging
import re

from config import AI_ROLE
from database.database_config import MAX_SIZE_PER_DOC, MIN_THRESHOLRD, TOP_N
from database.sql_database import (get_user_status, 
                                   get_wx_chat_history_by_timeoffset,
                                   insert_token_usage, insert_wx_chat_info)
from database.vector_db import get_or_create_wx_article_vector_db
from utils.tiangong import search_tiangong
from prompt import INTENT_PROMPT, QA_PROMPT, STANDALONE_PROMPT,STANDALONE_PROMPT_ICL
from utils.llm import convert_chat_history_to_messages, simple_call_llm
from const.enums import UseCase, UserStatus,UserIntent
from utils.httpx_client import send_image


async def qa_with_search(query):
    ans = await search_tiangong(query)
    if not ans:
        return '无法回答', {'model':'tiangong'}
    return ans['content'], {'model':'tiangong'}

def qa_chat(query, docs):
    context = ''
    sources = []
    for doc in docs:
        context += '----\n' + doc['document'][:MAX_SIZE_PER_DOC] + '\n'
        title,author = doc['metadata']['title'],doc['metadata']['author']
        if (title,author) not in sources:
            sources.append((title,author))
    prompt = QA_PROMPT.format(query=query, context=context)
    ans, usage = simple_call_llm(prompt,temperature=0.5)
    ans = str(ans)
    source_str = '\n\n=========\n信息来源:\n'
    for title,author in sources:
        source_str += '- 《{}》[{}]\n'.format(title,author)
    return ans + source_str, usage

        
def qa_with_knowledge(user_id, msg):
    collection = get_or_create_wx_article_vector_db('zhipu_' + user_id)
    
    results = collection.query(
        query_texts=msg,
        n_results=TOP_N
    )

    docs = []
    for i,distance in enumerate(results['distances'][0]):
        distance = 1 - distance
        if distance < MIN_THRESHOLRD:
            break
        docs.append({
            "document":results['documents'][0][i],
            "distance":distance,
            "metadata":results['metadatas'][0][i]})
    
    if not docs:
        return None, None

    # 回答问题
    return qa_chat(msg, docs)

def get_intent(chat_history, msg, user_id):
    prompt= INTENT_PROMPT.format(chat_history=chat_history + '\nUser:' + msg)
    raw_intent,usage = simple_call_llm(prompt,max_tokens=200,temperature=0.)
    if usage: insert_token_usage(usage,UseCase.INTENT,user_id)
    print(raw_intent)
    intent = re.findall('答案：(.*)',str(raw_intent))
    if not intent: intent = str(raw_intent)
    final_intent = UserIntent.OTHER
    if intent:
        intent = intent[0]
        for l in UserIntent:
            if l.value in intent:
                final_intent = l
                break
    
    return final_intent

def get_standalone(chat_history, msg, user_id, icl=False):
    if not icl:
        question = STANDALONE_PROMPT.format(chat_history=chat_history, question=msg)
    else:
        question = STANDALONE_PROMPT_ICL.format(chat_history=chat_history,question=msg)

    question,usage = simple_call_llm(question,max_tokens=200,temperature=0.)
    print(question)
    if usage: insert_token_usage(usage,UseCase.STANDALONE,user_id)
    question = str(question)
    if icl:
        if '独立问题' in question:
            question = re.findall('独立问题：(.*)',question)[0]
        else:
            question = 'None'
    return question

async def qa_plugin_manager(user_id, msg, room='', send_fn=None):
    user_status = get_user_status(room if room else user_id)
    if not user_status:
        return None
    
    raw_user_id = user_id
    user_id = room if room else user_id
    if user_status['status'] != UserStatus.QA:
        return None
    
    chat_history = get_wx_chat_history_by_timeoffset(raw_user_id,room)
    messages = convert_chat_history_to_messages(chat_history)

    def convert_to_history(messages):
        messages = messages.to_list()
        chat_history = ''
        for m in messages:
            if m['role'] == 'user':
                chat_history += 'User: ' + m['content'] + '\n'
            else:
                chat_history += 'AI: ' + m['content'] + '\n'
        return chat_history
    
    if user_status['status'] == UserStatus.QA:
        chat_history = convert_to_history(messages)
        intent = get_intent(chat_history,msg,user_id)
        logging.info(f'Intent = {intent}')
        
        # 闲聊场景直接默认大模型回复
        if intent == UserIntent.CHAT or intent == UserIntent.OTHER:
            return None
        
        question = get_standalone(chat_history,msg,user_id,icl=True)
        logging.info("standalone question: " + question)

        # 如果没有获取到问题，直接大模型回复
        if 'None' in question:
            return None
        
        async def search_answer(question, user_id):
            try:
                if send_fn: await send_fn('正在联网🔍 🔍 ，请稍后...')
                ans, usage = await qa_with_search(question)
                if usage: insert_token_usage(usage,UseCase.SEARCH_QA,user_id)
                if '无法回答' in ans:
                    if send_fn: await send_fn('🤔联网也没找到合适的内容...')
                    return None
            except:
                if send_fn: await send_fn('🤔联网搜索失败，请联系开发者...')
                return None 
            return ans
        
        async def knowledge_answer(question, user_id):
            if send_fn: await send_fn('正在知识库🔍 🔍 ，请稍后...')
            ans,usage = qa_with_knowledge(user_id,question)
            if usage: insert_token_usage(usage,UseCase.KB_QA,user_id)
            # 判断是否回复了问题
            if not ans or '无法回答' in ans:
                if send_fn: await send_fn('🤔知识库没有找到合适的内容...')
                return None
            return ans

        if intent ==  UserIntent.SEARCH_QA:
            ans = await search_answer(question, user_id)
        elif intent == UserIntent.IMAGE:
            ans = '暂不支持这个功能'
        else: # 默认使用知识库
            ans = await knowledge_answer(question, user_id)
            if not ans:
                ans = await search_answer(question, user_id)

        if ans:
            insert_wx_chat_info(raw_user_id,AI_ROLE,room,msg)
            insert_wx_chat_info(AI_ROLE,raw_user_id,room,ans)
        return ans
    else:
        return None