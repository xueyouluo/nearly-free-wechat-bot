import datetime
import json
import re
import smtplib
from email.mime.text import MIMEText

from prompt import SUMMARY_PROMPT, FORMAT_PROMPT, TRANSLATE_PROMPT
from config import SUMMARY_SIZE,MAX_CONTENT_SIZE
from database.sql_database import insert_token_usage
from utils.llm import simple_call_llm,UserMessage,call_llm,Messages
from const.enums import UseCase


def translate(text):
    zh,usage = simple_call_llm(TRANSLATE_PROMPT.format(text=text),-1,0.5)
    if usage:
        insert_token_usage(usage,UseCase.TRANSLATE,'global')
    zh = str(zh)
    if '调用模型失败，请稍后重试' in zh:
        return text
    return zh

def extract_summary(text):
    def extract(pattern):
        end = pattern[0] + '/' + pattern[1:]
        x = re.findall(pattern + '(.*?)' + end,text,flags=re.DOTALL)
        if x:
            return x[0].strip()
        if pattern not in text:
            return ''
        pos = text.find(pattern) + len(pattern)
        # 找到下一个tag的开始位置
        next_pos = text.find('<',pos)
        if next_pos != -1:
            return text[pos:next_pos].strip()
        return ''
    keywords = extract('<关键词>')
    category = extract('<分类>')
    if '</营销文>' not in text:
        text += '</营销文>'
    marketing = ('是' in extract('<营销文>'))
    one_sentence = extract('<一句话总结>')
    info = extract('<关键信息点>')
    summary = f'一句话总结：\n{one_sentence}\n\n关键信息点：\n{info}'
    return {'summary':summary, 'keywords':keywords,'category':category,'marketing':marketing,'one_sentence':one_sentence,'info':info}

def article_summary(doc, do_split=False):
    if not doc:
        return '', None
    if len(doc['content']) <= 100:
        return {'summary':doc['content'], 'keywords':'','category':'','marketing':True,'one_sentence':'','info':doc['content']}, None

    if do_split and len(doc['content'].split(' ')) > 1000:
        content = ' '.join(doc['content'].split(' ')[:MAX_CONTENT_SIZE//2])
    else:
        content = doc['content'][:MAX_CONTENT_SIZE]
    pp = SUMMARY_PROMPT.format(title=doc['title'][:100], content=content)
    user = UserMessage(pp)
    ret, usage = call_llm(Messages([user]),max_tokens=SUMMARY_SIZE,temperature=0.1)
    summary = extract_summary(str(ret))
    return summary, usage

def get_now():
    return datetime.datetime.now()
    

def try_extract_json(jstr):
    # find the left most { and right most }
    _jstr = jstr[jstr.find('{'):jstr.rfind('}')+1]
    try:
        return json.loads(_jstr)
    except:
        prompt = FORMAT_PROMPT.replace("{{illegal_result}}", jstr)
        content,usage = simple_call_llm(prompt,max_tokens=-1,temperature=0.1)
        if usage:
            insert_token_usage(
                usage=usage,
                use_case=UseCase.FIX_JSON,
                user="global"
            )
        content = str(content)
        content = content.replace("\n", "")
        content = content.replace("\_", "_")
        start_pos = content.find("STRICT JSON FORMAT #:")
        if start_pos!=-1:
            content = content[start_pos+len("STRICT JSON FORMAT #:"):]
        content = content[content.find("{"):content.rfind("}")+1]
        try:
            content = json.loads(content)
            return content
        except json.JSONDecodeError as e:
            pass
    
    return None
    


