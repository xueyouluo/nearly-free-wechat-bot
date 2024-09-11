import httpx
import atexit
import os
import asyncio

WECHAT_SERVER = os.getenv('WECHAT_SERVER', 'http://localhost:8080')

# 创建一个全局的异步客户端实例
async_httpx_client = httpx.AsyncClient(timeout=30)
httpx_client = httpx.Client(timeout=30)

# 定义一个异步函数来关闭客户端
async def close_async_client():
    await async_httpx_client.aclose()

def close_client_sync():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(close_async_client())

# 注册关闭客户端的函数
atexit.register(close_client_sync)
atexit.register(httpx_client.close)

async def health_check():
    respone = await async_httpx_client.get(WECHAT_SERVER + '/healthz')
    return respone.json()

FLLM_ENDING = ''''''

async def send_image(to_wxid, image_url):
    respone = await async_httpx_client.post(WECHAT_SERVER + '/send_image', json={
        "to_wxid": to_wxid,
        "image_url": image_url
    })
    return respone.json()

async def send_text(to_wxid, content):
    respone = await async_httpx_client.post(WECHAT_SERVER + '/send_text', json={
        "to_wxid": to_wxid,
        "content": content + FLLM_ENDING
    })
    return respone.json()

async def send_room_at_msg(to_wxid, content, at_list):
    if not isinstance(at_list, list):
        at_list = [at_list]
    respone = await async_httpx_client.post(WECHAT_SERVER + '/send_room_at_msg', json={
        "to_wxid": to_wxid,
        "content": content + FLLM_ENDING,
        "at_list": at_list
    })
    return respone.json()

async def accept_friend(encryptusername,ticket,scene):
    respone = await async_httpx_client.post(WECHAT_SERVER + '/accept_friend', json={
        "encryptusername": encryptusername,
        "ticket": ticket,
        "scene": scene
    })
    return respone.json()

async def get_room_detail(room_wxid):
    respone = await async_httpx_client.get(WECHAT_SERVER + '/get_room_detail', params={
        "room_wxid": room_wxid
    })
    return respone.json()

async def search_contacts(wxid):
    response = await async_httpx_client.post(WECHAT_SERVER + '/search_contacts', json={
        "wxid": wxid
    })
    return response.json()

async def send_msg(content, from_wxid, to_wxid, room):
    if room:
        return await send_room_at_msg(to_wxid=to_wxid,
                            content='{$@}' + content,
                            at_list=[from_wxid])
    else:
        return await send_text(to_wxid=from_wxid, content=content)

async def send_super_user(content):
    respone = await async_httpx_client.post(WECHAT_SERVER + '/send_super_user', json={
        "content": content
    })
    return respone.json()

async def get_requests(url):
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
    respone = await async_httpx_client.get(url, headers=headers)
    return respone

async def proxy_requests(url):
    respone = await async_httpx_client.post(WECHAT_SERVER + '/requests', json={
        "url": url
    })
    return respone.json()['text']

async def proxy_selenuim(url):
    respone = await async_httpx_client.post(WECHAT_SERVER + '/selenium', json={
        "url": url
    })
    return respone.json()['text']

def get_login_info():
    respone = httpx_client.get(WECHAT_SERVER + '/get_login_info')
    return respone.json()