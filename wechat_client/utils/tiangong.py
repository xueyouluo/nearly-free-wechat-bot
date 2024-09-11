import os
import websockets
import json
import requests
import re
import logging
import random

TG_USER_PWD = os.getenv('TG_USER_PWD')
try:
    TG_USER_PWD = [x.split(':') for x in TG_USER_PWD.split(',')]
except:
    TG_USER_PWD = []

try:
    SSO_TOKEN = open('token.txt').read().strip()
except:
    SSO_TOKEN = ''

def get_new_sso_token():
    url = "https://api.tiangong.cn/usercenter/v1/passport/login"
    if not TG_USER_PWD:
        return False, 'No user/pwd provided'
    user,pwd = random.choice(TG_USER_PWD)
    payload = json.dumps({
        "password": pwd,
        "phone": user
    })
    headers = {
    'Content-Type': 'application/json',
    'Origin': 'https://sso.tiangong.cn',
    'Referer': 'https://sso.tiangong.cn/',
    'K-Client-Id': '200004'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return True, response.json()['data']['token']

async def query_tiangong_global(msg, sso_token):
    wss_url = "wss://work.tiangong.cn/dialogue-aggregation/dialogue/aggregation/v2/agent?device=Web&device_id=f87a3ebb15b6a8d9a94220fccbce974e&device_hash=f87a3ebb15b6a8d9a94220fccbce974e"
    
    headers = {
        "Origin": "https://search.tiangong.cn",
        "Host": "api-search.tiangong.cn",
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Cookie": f'k_sso_token={sso_token};',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }
    ret = {}
    async with websockets.connect(wss_url, extra_headers=headers) as websocket:
        print("Connected to server")

        message = {
            "agent_id":"001",
            "agent_type":"universal",
            "prompt":{
                "ask_from":"user",
                "ask_id":None,
                "content":msg,
                "prompt_content":None,"template_id":None,"action":None,"file":None,"template":None,"copilot":True,"bubble_text":None,"publish_agent":None,"copilot_option":None}}
        
        await websocket.send(json.dumps(message))
        response = ''
        async for message in websocket:
            data = json.loads(message)
            if data.get('target') == 'end':
                break

            if data.get('card_type','') == 'ban':
                ret['ban'] = ''
                break

            if data.get('card_type','') == 'options':
                ret['options'] = ''
                break

            if data.get('card_type','') == 'markdown':
                if data.get('target') == 'update':
                    response += data['arguments'][0]['messages'][0]['text']

                if data.get('target') == 'finish':
                    break
        ret['markdown'] = response
    print("Disconnected from server")
    return ret

async def query_tiangong(msg, sso_token):
    wss_url = "wss://work.tiangong.cn/dialogue-aggregation/dialogue/aggregation/v2/agent?device=Web&device_id=f87a3ebb15b6a8d9a94220fccbce974e&device_hash=f87a3ebb15b6a8d9a94220fccbce974e"
    
    headers = {
        "Origin": "https://search.tiangong.cn",
        "Host": "api-search.tiangong.cn",
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Cookie": f'k_sso_token={sso_token};',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }

    ret = {}
    async with websockets.connect(wss_url, extra_headers=headers) as websocket:
        print("Connected to server")
        message = {"agent_id":"016","agent_type":"universal","conversation_id":"cc080d0b-eda6-4d7d-b8d8-a834f6c1e426","prompt":{"ask_from":"user","ask_id":None,"content":None,"prompt_content":None,"template_id":None,"action":"clear","file":None,"template":None,"copilot":True,"bubble_text":None,"publish_agent":None,"copilot_option":None}}
        await websocket.send(json.dumps(message))
        async for message in websocket:
            data = json.loads(message)
            if data.get('target') == 'end':
                break

        message ={"agent_id":"016","agent_type":"universal","conversation_id":"cc080d0b-eda6-4d7d-b8d8-a834f6c1e426","prompt":{"ask_from":"user","ask_id":None,"content":msg,"prompt_content":None,"template_id":None,"action":None,"file":None,"template":None,"copilot":True,"bubble_text":None,"publish_agent":None,"copilot_option":None}}
        await websocket.send(json.dumps(message))
        response = ''
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get('card_type','') == 'ban':
                    ret['ban'] = ''
                    break
                if data.get('target') == 'end':
                    break
                if data.get('card_type','') == 'options':
                    ret['options'] = ''
                    break
                
                if data.get('card_type','') == 'markdown':
                    if data.get('target') == 'update':
                        response += data['arguments'][0]['messages'][0]['text']

                    if data.get('target') == 'finish':
                        break
                
            except json.JSONDecodeError:
                pass

        print("Disconnected from server")
        ret['markdown'] = response
    return ret


async def process_query_tiangong(msg, sso_token):
    data = await query_tiangong_global(msg, sso_token)
    if 'ban' in data:
        return {'content': "抱歉，我无法回答这个问题。"}
    if 'options' in data:
        logging.info('需要做选择，走另外的agent')
        data = await query_tiangong(msg, sso_token)
    content = data.get('markdown','对不起，没有获取到有用的信息，请换个问题重试。')
    # replce reference
    content = re.sub('\[\d+\]','',content).strip()
    # 使用正则表达式去除链接
    pattern = re.compile(r'\[\]\([^)]+\)')
    content = re.sub(pattern, '', content)
    content = re.sub('\n+','\n',content)
    pattern = r'<tiangong.*?\/>|<audio.*?<\/audio>'
    content = re.sub(pattern,'',content)
    return {'content': content}


async def query_tiangong_with_retry(msg):
    global SSO_TOKEN
    if not SSO_TOKEN:
        success, info = get_new_sso_token()
        if not success:
            return None
        SSO_TOKEN = info

    try:
        data = await process_query_tiangong(msg, SSO_TOKEN)
        return data
    except Exception as e:
        logging.warning(e)
    logging.info('尝试换一个token')
    success, token = get_new_sso_token()
    if not success:
        return None
    try:
        data = await process_query_tiangong(msg, token)
    except Exception as e:
        logging.warning(e)
        logging.warning('换一个token也失败')
        return None
    SSO_TOKEN = token
    with open('token.txt','w') as f:
        f.write(SSO_TOKEN)
    return data

async def search_tiangong(msg):
    try:
        data = await query_tiangong_with_retry(msg)
    except Exception as e:
        print(e)
        logging.warning(f'# 联网搜索失败 「e」')
        return {'content': "联网搜索失败。"}
    return data

if __name__ == "__main__":
    print(get_new_sso_token())