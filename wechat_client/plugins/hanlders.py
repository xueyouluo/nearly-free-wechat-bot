import re
import time
import traceback
import xmltodict

from config import MAX_PUBLIC_NUM
from const.notify_type import NotifyType
from plugins.handler_registry import TypeHandler
from utils.request_models import Message
from config import AT_SLEF_NAME
from utils.httpx_client import send_msg,send_super_user
from plugins.manager import manager_plugin
from plugins.kimi_plugin import kimi_plugin_manager
from plugins.pub_mail import push_manage,pub_manage
from plugins.article import article_manage,verify_url
from utils.tiangong import search_tiangong
from plugins.qa import qa_plugin_manager
from projects.project_manager import project_manager
from const.enums import UseCase
from prompt import get_default_system
from database.vector_db import insert_wx_article_chunks_to_vector_db
from utils.llm import (Messages, SystemMessage, UserMessage,
                       call_llm, convert_chat_history_to_messages)
from database.sql_database import *

@TypeHandler.register_handler(NotifyType.MT_RECV_FRIEND_MSG)
async def on_recv_friend_msg(message: Message):
    raw_msg = message.data["raw_msg"]

    try:    
        msg = xmltodict.parse(raw_msg)
    except:
        logging.warning(f"xml解析失败, {raw_msg}")
        return 
    msg = msg["msg"]
    encryptusername = msg['@encryptusername']
    fromusername = msg['@fromusername']
    fromnickname = msg['@fromnickname']
    content = msg['@content']
    scene = msg['@scene']
    ticket = msg['@ticket']
    
    await send_super_user(f'收到好友添加请求，信息如下：\nID：{fromusername}\n昵称：{fromnickname}\n正文：{content}')
    insert_friend_request(encryptusername, fromusername, fromnickname, scene, ticket)
    

@TypeHandler.register_handler(NotifyType.MT_RECV_LINK_MSG)
async def on_recv_link_msg(message: Message):
    data = message.data
    from_wxid = data["from_wxid"]
    to_wxid = data['to_wxid']
    room = data['room_wxid']

    logging.info('链接消息处理')
    # 处理公众号消息
    pubs = get_all_pub_infos()
    if from_wxid in pubs:
        try:
            info,docs = await pub_manage(data, from_wxid, pubs[from_wxid]['pub_name'])
            await send_super_user(info)
            # 定制化，该号关注内容直接推送到群聊
            push_users = get_need_push_users()
            for user in push_users:
                pub_ids = get_user_all_pub_id(user['user_id'])
                if from_wxid in pub_ids:
                    for doc in docs:
                        summary = doc['summary']
                        summary = f'🖋公众号: {pub_ids[from_wxid]["pub_name"]}\n\n📚标题: {doc["title"]}\n\n🚀摘要:\n' + summary
                        await send_msg(summary,user['user_id'],user['user_id'],"")
                        time.sleep(0.5)
            return 
        except Exception as e:
            traceback.print_exc()
            logging.warning(f'处理链接消息出错: {e}')
            await send_super_user(f'处理链接消息出错: {e}')


    if room:
        user_status = get_user_status(room)
        
    else:
        user_status = get_user_status(from_wxid)

    
    if not user_status or user_status['status'] == UserStatus.CLOSE:
        return
    
    if user_status['status'] == UserStatus.KIMI:
        # 使用KIMI模式下，解析链接的url，转发给text handler处理
        raw_msg = data['raw_msg']
        try:    
            msg = xmltodict.parse(raw_msg)
        except:
            await send_msg(f"xml解析失败, {raw_msg}",from_wxid,to_wxid,room)
            return 
        msg = msg['msg']['appmsg']
        if 'url' not in msg:
            await send_msg(f"没有获取到链接信息",from_wxid,to_wxid,room)
            return 
        url = msg['url']
        if verify_url(url):
            url = url.replace('http://','https://')
        return await on_recv_text_msg(Message.parse_obj({
            "data":{
                "from_wxid":data["from_wxid"],
                "to_wxid":data['to_wxid'],
                "room_wxid":data['room_wxid'],
                "msg": "@MIND " + url,
                "at_user_list": []
            },
            "type":NotifyType.MT_RECV_TEXT_MSG}))

    try:
        doc = await article_manage(data, from_wxid, room)
    except Exception as e:
        traceback.print_exc()
        logging.warning(f"处理链接消息出错: {e}")
        return
    if doc:
        summary = doc['summary']
        await send_msg(summary,from_wxid,to_wxid,room)
        # 微信的卡片消息限制了字数，效果不佳
        # wechat_instance.send_link_card(from_wxid,doc['title'],doc['summary'],doc['url'],'')
        insert_wx_chat_info(from_wxid,AI_ROLE,room,f"我分享了一篇《{doc['title']}》文章给你。")
        insert_wx_chat_info(AI_ROLE,from_wxid,room,doc['summary'])
        insert_wx_article_to_sql(doc)

        if room:
            user_id = room
        else:
            user_id = from_wxid
        
        if user_status:
            if user_status['status'] == UserStatus.QA:
                insert_user_article_to_sql(user_id,doc)
                insert_wx_article_chunks_to_vector_db(user_id, doc)
                ending = '提示：文章已存入知识库。'
            else:
                ending = "提示：当前您未处于知识库模式，文章不会存入知识库。输入“模式”获取和修改您的对话模式。" 
            await send_msg(ending,from_wxid,to_wxid,room)
    else:
        await send_msg('获取文章失败，暂时不支持该类型文章',from_wxid,to_wxid,room)
            
@TypeHandler.register_handler(NotifyType.MT_RECV_CARD_MSG)
async def on_recv_card_msg(message: Message):
    logging.info("收到名片消息")
    data = message.data
    from_wxid = data["from_wxid"]
    to_wxid = data['to_wxid']
    room = data['room_wxid']
    
    async def send_fn(x):
        await send_msg(x,from_wxid,to_wxid,room)

    
    info = xmltodict.parse(data['raw_msg'])
    info = info['msg']

    print(info)

    # 判断是否为微信公众号
    # 是否有@certinfo，@brandSubscriptConfigUrl
    def check_is_public_account(info):
        if info.get('@certinfo') or info.get('@brandSubscriptConfigUrl'):
            return True
        return False
    
    if not check_is_public_account(info):
        logging.info('非公众号消息')
        return

    username = info['@username']
    nickname = info['@nickname']
    certinfo = info['@certinfo']

    if room:
        user_id = room
    else:
        user_id = from_wxid
    pub_ids = get_user_all_pub_id(user_id)
    if len(pub_ids) >= MAX_PUBLIC_NUM:
        await send_fn(f'公众号自动关注上限为{MAX_PUBLIC_NUM}，请先使用订阅功能取消关注部分公众号')
        return
    if username in pub_ids:
        await send_fn(f'{nickname} 已经关注了')
        return

    msg = f'''收到公众号推荐。
    来源：
    ROOM: {room}
    User: {user_id}
    公众号信息：
    UserName: {username}
    NickName: {nickname}
    CertInfo: {certinfo}'''
    # 这里还需要通知开发者手动操作关注公众号
    await send_super_user(msg)

    # 注册公众号关注信息
    from database.sql_database import add_user_pub_info
    add_user_pub_info(user_id, username, nickname)
    print(f'已为用户{user_id} 关注公众号 - {username} - {nickname}')
    await send_fn(f'已收到公众号推荐 - {nickname}, 我会持续为您关注公众号的更新。')


@TypeHandler.register_handler(NotifyType.MT_RECV_TEXT_MSG)
@TypeHandler.register_handler(NotifyType.MT_RECV_VOICE_TEXT_MSG) # 如果要处理语音消息，需要在微信上设置语音自动转文本
async def on_recv_text_msg(message: Message):
    data = message.data
    if message.type != NotifyType.MT_RECV_TEXT_MSG:
        at_user_list = []
    else:
        at_user_list = data['at_user_list']
    from_wxid = data["from_wxid"]
    to_wxid = data['to_wxid']
    room = data['room_wxid']

    # 不回复公众号的消息
    pubs = get_all_pub_infos()
    if from_wxid in pubs:
        return
    
    msg = data['msg'] if message.type == NotifyType.MT_RECV_TEXT_MSG else data['text']

    if message.type == NotifyType.MT_RECV_TEXT_MSG:
        # 判断群消息是否为@自己的
        if room and TypeHandler.self_wxid not in at_user_list and AT_SLEF_NAME not in msg:
            return
    elif room:
        # 判断群里面是否找自己
        voice_trigger = ['助手','机器人','mind',"小微"]
        trigger = False
        
        for v in voice_trigger:
            if v in msg:
                trigger = True
                break
        if not trigger:
            return
       

    # 去除消息中@人的内容
    msg = re.sub('@[^@]*?\u2005','',msg).strip()
    msg = re.sub('@[^@]*? ','',msg).strip()
    async def send_fn(x):
        await send_msg(x,from_wxid,to_wxid,room)

    if not msg:
        await send_fn('请在@我的同时并把问题告诉我哦')
        return 
    
    if msg == 'ECHO':
        info = json.dumps(data,ensure_ascii=False,indent=2)
        await send_fn(info)
        return 

    # 权限管理
    # 在其他判断之前
    ret = await manager_plugin(from_wxid,room,msg)
    if ret:
        await send_fn(ret)
        return


    # 其他定制化需求，先走project判断
    ret = project_manager(from_wxid,msg,room,message)
    if ret:
        await send_fn(ret)
        return

    if msg[:3] == '搜索 ':
        await send_fn('🔍 🔍')
        ret = await search_tiangong(msg[3:])
        await send_fn(ret['content'])
        return 
    
    if not ret:
        ret = await kimi_plugin_manager(from_wxid, msg, room, send_fn)

    if not ret:
        ret = push_manage(from_wxid,msg,room)
    
    
    # 使用QA组件判断
    if not ret:
        ret = await qa_plugin_manager(from_wxid, msg, room, send_fn)

    # 默认使用chatgpt回复
    if not ret:
        chat_history = get_wx_chat_history_by_timeoffset(from_wxid,room)
        messages = convert_chat_history_to_messages(chat_history,history_size=2500)
        ret, usage = call_llm(Messages([SystemMessage(get_default_system())] + messages.messages + [UserMessage(msg)]))
        ret = str(ret)
        if usage:
            insert_token_usage(
                usage=usage,
                use_case=UseCase.CHAT,
                user=room if room else from_wxid)
        insert_wx_chat_info(from_wxid,AI_ROLE,room,msg)
        insert_wx_chat_info(AI_ROLE,from_wxid,room,ret)

    await send_fn(ret)
    