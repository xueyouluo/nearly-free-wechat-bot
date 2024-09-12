import requests
import time
import logging
import json
import os

from database.sql_database import get_last_user_kimi_token,upsert_user_kimi_token
from utils.misc import get_now

SUPER_USER = os.getenv('SUPER_USER','')

# 请求头定义
HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh-HK;q=0.9,zh;q=0.8',
    'Content-Type': 'application/json; charset=UTF-8',
    'Origin': 'https://kimi.moonshot.cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}


def refresh_access_token(tokens):
    """
    使用refresh_token刷新access_token，并更新全局tokens变量。
    """
    refresh_token = tokens['refresh_token']
    if not refresh_token:
        logging.error("[KimiChat] 缺少refresh_token，无法刷新access_token")
        return None

    headers = HEADERS.copy()
    headers['Authorization'] = refresh_token

    response = requests.get('https://kimi.moonshot.cn/api/auth/token/refresh', headers=headers)

    if response.status_code == 200:
        logging.debug("[KimiChat] access_token刷新成功！")
        response_data = response.json()
        tokens['access_token'] = response_data.get("access_token", "")
        tokens['refresh_token'] = response_data.get("refresh_token", "")
        tokens['last_update_time'] = get_now()
        upsert_user_kimi_token(**tokens)
        return tokens
    else:
        return None


def get_access_token(user_id):
    tokens = get_last_user_kimi_token(user_id)
    if not tokens:
        tokens = get_last_user_kimi_token(SUPER_USER)
        if not tokens:
            return None
    if not tokens['refresh_token'] or not tokens['access_token']:
        return None
    now = get_now()
    delta = now - tokens['last_update_time']
    # 10分钟认为需要刷新token
    if delta.seconds > 10 * 60:
        tokens = refresh_access_token(tokens)
    return tokens

def new_chat(user_id):
    tokens = get_access_token(user_id)
    if not tokens:
        return None
    # 从全局tokens变量中获取access_token
    auth_token = tokens['access_token']

    # 复制请求头并添加Authorization字段
    headers = HEADERS.copy()
    headers['Authorization'] = f'Bearer {auth_token}'
    url = "https://kimi.moonshot.cn/api/chat"
    
    data = {
        "name": "未命名会话",
        "is_example": False
    }

    response = requests.post(url, headers=headers, json=data)
    # 检查响应状态码并处理响应
    if response.status_code == 200:
        logging.info("[KimiChat] 新建会话ID操作成功！")
        return response.json().get('id')  # 返回会话ID
    else:
        logging.info(f"[KimiChat] 新建会话ID失败，状态码：{response.status_code}, {response.text}")
        return None

def chat(user_id, chat_id, query, refs_list=None, use_search=False, new_chat=False):
    """
    以流的方式发送POST请求并处理响应以获取聊天数据。
    :param chat_id: 会话ID
    :param query: 用户的查询内容。
    :param refs_list: 服务器文件对象ID列表，默认空
    :param use_search: 是否使用搜索
    :param new_chat: 用于识别是否首次对话
    :return: 返回处理后的完整响应文本。
    """
    tokens = get_access_token(user_id)
    # 从全局tokens变量中获取access_token
    auth_token = tokens['access_token']

    if refs_list is None:
        refs_list = []

    # 复制请求头并添加Authorization字段
    headers = HEADERS.copy()
    headers['Authorization'] = f'Bearer {auth_token}'

    # 拼接url
    api_url = f"https://kimi.moonshot.cn/api/chat/{chat_id}/completion/stream"

    # 定义请求的载荷
    payload = {
        "messages": [{"role": "user", "content": query}],
        "refs": refs_list,
        "use_search": use_search
    }

    full_response_text = ""
    print(f"[KimiChat] 正在请求对话")
    # 以流的方式发起POST请求
    with requests.post(api_url, json=payload, headers=headers, stream=True) as response:
        try:
            # 迭代处理每行响应数据
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    

                    # 检查行是否包含有效的数据
                    if decoded_line.startswith('data: '):
                        json_str = decoded_line.split('data: ', 1)[1]
                        try:
                            json_obj = json.loads(json_str)
                            if json_obj.get('event','') == 'rename':
                                continue
                            if 'text' in json_obj:
                                full_response_text += json_obj['text']
                        except json.JSONDecodeError:
                            print(f"[KimiChat] 解析JSON时出错: {json_str}")

                    # 检查数据流是否结束
                    if '"event":"all_done"' in decoded_line:
                        break
        except requests.exceptions.ChunkedEncodingError as e:
            print(f"[KimiChat] ChunkedEncodingError: {e}")

    if new_chat:
        first_space_index = full_response_text.find(" ")
        trimmed_text = full_response_text[first_space_index + 1:]
    else:
        trimmed_text = full_response_text
    print(f"[KimiChat] 响应内容：{trimmed_text}")
    return trimmed_text
