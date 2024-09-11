import json

from config import SUPER_USER
from database.sql_database import (
    get_latest_user_article,get_user_token_usage_by_time_offset_and_case,
    get_total_token_usage_by_user_and_time_offset, get_user_status,
    accept_friend_request, get_attend_status_by_user,
    get_attend_info_of_now,update_attend_info,insert_attend_status,update_attend_status,
    get_total_token_usage_by_time_offset, get_user_token_usage_by_time_offset,
    insert_user_status, update_user_status)
from const.enums import UserStatus,AttendStatus
from utils.misc import get_now
from utils.httpx_client import send_super_user,send_text,accept_friend,search_contacts,get_room_detail

under_development = '🚧该功能正在开发中...'

def attend_manager(user_id, room, msg):
    if msg == '打卡功能':
        content = '开启打卡：启动微信通知打卡\n'
        content += '关闭打卡：关闭微信通知打卡\n'
        content += '不上班：关闭当天的打卡通知\n'
        content += '打卡：就是打卡\n'
        content += '查看打卡：查看打卡状态'
        return content
    if msg == '开启打卡':
        info = get_attend_status_by_user(user_id, room)
        if info:
            if info['status'] == AttendStatus.OPEN:
                return '已经开启了打卡功能'
            if info['status'] == AttendStatus.CLOSE:
                update_attend_status(user_id, room, AttendStatus.OPEN)
                return '已重新开启打卡功能'
        else:
            insert_attend_status(user_id, room, AttendStatus.OPEN)
            return '已开启打卡功能'
        
    if msg == '关闭打卡':
        info = get_attend_status_by_user(user_id, room)
        if info:
            if info['status'] == AttendStatus.OPEN:
                update_attend_status(user_id, room, AttendStatus.CLOSE)
                return '已关闭打卡功能'
            if info['status'] == AttendStatus.CLOSE:
                return '已经关闭了打卡功能'
        else:
            return '没有开启打卡功能'
    if msg == '不上班':
        info = get_attend_info_of_now(user_id, room)
        if not info:
            return '打开信息还没建立，稍后再试'
        info['remind'] = 0
        update_attend_info(user_id, room, info)
        return '好的，祝您休息愉快'
    if msg == '打卡':
        now = get_now()
        info = get_attend_info_of_now(user_id, room)
        if not info:
            return '打开信息还没建立，稍后再打卡'
        if info['on_time'] and info['off_time']:
            return '你已经打过卡了，无需重复打卡'
        if 9 <= now.hour <= 10:
            if info['on_time']:
                return '你今天已经打过上班卡了，无需重复打卡'
            info['on_time'] = now
            update_attend_info(user_id, room, info)
            return f'上班打卡成功，时间为{now.strftime("%Y-%m-%d %H:%M:%S")}'
        elif 18 <= now.hour <= 22:
            if info['off_time']:
                return '你今天已经打过下班卡了，无需重复打卡'
            info['off_time'] = now
            update_attend_info(user_id, room, info)
            if info['on_time']:
                diff = info['off_time'] - info['on_time']
                hours = diff.total_seconds() / 3600
                return f'下班打卡成功，时间为{now.strftime("%Y-%m-%d %H:%M:%S")}\n' + f"您已经工作了{hours:.2f}小时，早点回家休息。"
            else:
                return  f'下班打卡成功，时间为{now.strftime("%Y-%m-%d %H:%M:%S")}'
        else:
            return '打卡时间不对，上班时间9-10点，下班时间18-22点'
    if msg == '查看打卡':
        info = get_attend_status_by_user(user_id, room)
        if not info:
            return '您还没有开启打卡功能'
        if info['status'] == AttendStatus.CLOSE:
            return '打卡功能已关闭'
        info = get_attend_info_of_now(user_id, room)
        if not info:
            return '[打卡已开启]打开信息还没建立，稍后再查看'
        if info['on_time'] and info['off_time']:
            hours = (info['off_time'] - info['on_time']).total_seconds() / 3600
        else:
            hours = 0
        content = '[打卡已开启]今天打卡情况如下:\n'
        content += '[上班打卡]' + info['on_time'].strftime("%Y-%m-%d %H:%M:%S") if info['on_time'] else '' + '\n'
        content += '[下班打卡]' + info['off_time'].strftime("%Y-%m-%d %H:%M:%S") if info['off_time'] else '' + '\n'
        content += '[工作时长]' + f"{hours:.2f}小时" + '\n'
        return content.strip()

async def user_manger(msg):
    if msg[:5] == '开启服务 ':
        user_id = msg[5:].strip()
        user_status = get_user_status(user_id)
        if user_status:
            if user_status['status'] == UserStatus.CLOSE:
                update_user_status(user_id, UserStatus.QA)
                await send_text(to_wxid=user_id, content="已经重新启用了服务")
                return f'{user_id}已经重新开启了服务'
            else:
                await send_text(to_wxid=user_id, content="服务已经是启用状态")
                return f'{user_id}服务已经处于开启状态'
        else:
            insert_user_status(user_id, UserStatus.QA)
            await send_text(to_wxid=user_id, content="已经启用了服务，使用愉快")
            return f'{user_id}开启服务成功'
        
    elif msg[:5] == '关闭服务 ':
        user_id = msg[5:].strip()
        user_status = get_user_status(user_id)
        if user_status:
            if user_status['status'] != UserStatus.CLOSE:
                update_user_status(user_id, UserStatus.CLOSE)
                await send_text(to_wxid=user_id, content="服务已关闭")
                return f"{user_id}服务已经关闭"
            else:
                return f"{user_id}服务已经处于关闭状态"
        else:
            return f"{user_id}没有开启服务"
    else:
        return None
    
def usage_manager(user_id,msg):
    if msg == '用量':
        desc = """输入下面关键词获取Token使用情况
「用量 总结」获取最近5天的使用情况
「用量 场景」获取最近5天token具体用在什么地方
「用量 {数字}」获取最近1-180天的使用情况，如「用量 30」"""
        if user_id == SUPER_USER:
            desc += '\n「用量 汇总」获取最近5天所有用户用量汇总'
            desc += '\n「用量 用户」获取最近5天不同用户使用情况'
            desc += '\n「用量 场景汇总」获取最近5天所有用户token具体用在什么地方汇总'
        return desc

    if msg == '用量 总结':
        usage = get_user_token_usage_by_time_offset(user_id)
        return '最近5天的用量' + '\n' + json.dumps(usage, indent=2, ensure_ascii=False)
    
    if msg == '用量 场景':
        usage = get_user_token_usage_by_time_offset_and_case(user_id)
        return '最近5天不同场景的用量' + '\n' + json.dumps(usage, indent=2, ensure_ascii=False)
    
    if user_id == SUPER_USER:
        usage = None
        if msg == '用量 场景汇总':
            usage = get_user_token_usage_by_time_offset_and_case()
        if msg == '用量 汇总':
            usage = get_total_token_usage_by_time_offset()
        if msg == '用量 用户':    
            usage =  get_total_token_usage_by_user_and_time_offset()
        if usage:
            return '最近5天用量' + '\n' + json.dumps(usage, indent=2, ensure_ascii=False)
        
    if msg[:3] == '用量 ':
        try:
            days = int(msg[3:])
            days = min(days, 180)
            usage = get_user_token_usage_by_time_offset(user_id, f'-{days} days')
            return f'最近{days}天的用量' + '\n' + json.dumps(usage, indent=2, ensure_ascii=False)
        except:
            return '请输入要查最近多少天的，最长为180天'
    
async def friend_manager(msg):
    if msg[:5] == '接受好友 ':
        friend_id = msg[5:].strip()
        info = accept_friend_request(friend_id)
        ret = await accept_friend(info["encryptusername"], info['ticket'], int(info['scene']))
        if ret:
            return '好友添加成功'
        else:
            return '好友添加失败'


def knowledge_manager(user_id, msg):
    if msg == '知识库':
        default_msg = '''知识库功能：
输入下面的关键词进行功能选择：
「知识库 列表」获取知识库中的文章数量和最近10篇文章
「知识库 ID」获取知识库中编号为ID的文章
「知识库 关键词」根据关键词对知识库文章进行检索
'''
        return default_msg
    if msg == '知识库 列表':
        docs = get_latest_user_article(user_id)
        ret = f'知识库文章总数: {len(docs)}\n\n详细列表:\n'
        for doc in docs:
            doc.pop('url')
            doc.pop('user_id')
            ret += json.dumps(doc,ensure_ascii=False) + '\n'
        return ret
    
    if msg[:4] == '知识库 ':
        try:
            doc_id = int(msg[5:])
        except Exception as e:
            # 使用关键词进行查询
            return under_development
        return under_development

def mode_manager(user_id, msg):
    default_msg = '''
=======
输入下面的关键词进行模式切换：
「模式 知识库」使用知识库/联网进行回答，分享的文章会存入知识库，适合时效性和专业性的问题。
「模式 聊天」使用GPT进行对话，适用于广泛的场景。
「模式 kimi」将使用Kimi对所有链接进行总结'''
    if msg == '模式':
        user_status = get_user_status(user_id)
        return '当前模式为：{}\n'.format(user_status['status'].value) + default_msg
    
    if msg == '模式 知识库':
        update_user_status(user_id, UserStatus.QA)
        return '当前模式已切换为知识库\n' + default_msg
    
    if msg == '模式 聊天':
        update_user_status(user_id, UserStatus.NORMAL)
        return '当前模式已切换为聊天\n' + default_msg

    if msg == '模式 kimi':
        update_user_status(user_id, UserStatus.KIMI)
        kimi = "\n默认使用全局账号，如果您想要自己的账号，请登录kimi网页版，F12在console中输入localStorage.refresh_token和localStorage.access_token，然后先输入atoken={你的access token}，在输入rtoken={你的refresh token}\n"
        return '当前模式已切换为kimi，任何链接消息都默认走kimi总结\n' + kimi + default_msg
    return ''

async def info_manager(msg):
    if msg[:3] == '查询 ':
        user_id = msg[3:].strip()
        if 'chatroom' in user_id:
            info = await get_room_detail(user_id)
            return json.dumps(info, indent=2, ensure_ascii=False)
        else:
            info = await search_contacts(wxid=user_id)
            if not info:
                return '没有获取到联系人的信息'
            return json.dumps(info, indent=2, ensure_ascii=False)

async def manager_plugin(user_id, room, msg):
    room_or_user = room if room else user_id
    # 获取用户状态
    user_status = get_user_status(room_or_user)

    # 超级用户必须加入到数据库中
    if user_id == SUPER_USER and not user_status and not room:
        insert_user_status(user_id, UserStatus.NORMAL)
        user_status = get_user_status(user_id)

    # 管理好友请求
    if user_id == SUPER_USER:
        ret = await friend_manager(msg)
        if ret: return ret

    # 收到开通申请，要发送给SUPER USER
    if msg == '申请开通权限':
        if user_status and user_status['status'] != UserStatus.CLOSE:
            return '您已经开通了权限，输入“模式”进行切换'
        else:
            await send_super_user(f'用户 {user_id}, 群聊 {room} 申请开通权限')
            if room:
                info = await info_manager(f"查询 {room}")
            else:
                info = await info_manager(f"查询 {user_id}")
            await send_super_user(f"用户信息：{info}")
            return '已通知管理员，请等待审核。'

    # SUPER USER管理知识库的开关
    if user_id == SUPER_USER:
        ret = await user_manger(msg)
        if ret: return ret

    if not user_status or user_status['status'] == UserStatus.CLOSE:
        return '❌您没有权限❌，👷‍♂️请直接发送消息“申请开通权限”给我，等待管理员开通权限🆗后使用。'

    # 用户管理自己的知识库模式
    ret = mode_manager(room_or_user, msg)
    if ret: return ret
    ret = knowledge_manager(room_or_user, msg)
    if ret: return ret

    # 打卡管理
    ret = attend_manager(user_id, room, msg)
    if ret: return ret

    # super user管理联系人
    if user_id == SUPER_USER:
        ret = await info_manager(msg)
        if ret: return ret

    ret = usage_manager(room_or_user, msg)
    if ret: return ret

    if msg == '功能':
        functions = '''🛠️🛠️@MIND并输入以下关键词获取功能说明：
🚀「模式」提供模式切换
🚀「知识库」提供知识库管理
🚀「打卡功能」提供打卡管理
🚀「订阅功能」提供订阅相关服务
🚀「搜索 关键词」根据关键词联网查询
'''
        if user_id == SUPER_USER:
            functions +='''🚀「查询+ID」获取联系人或者群聊的信息
🚀「开启服务+ID」开启用户知识库
🚀「关闭服务+ID」关闭用户知识库
🚀「接受好友+ID」通过好友申请
🚀「用量」获取账号使用情况
'''
        return functions

    return ''


    