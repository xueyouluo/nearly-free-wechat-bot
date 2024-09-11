# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()  # 打上猴子补丁

import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

import time
from PIL import Image
import ntchat
import requests
from flask import Flask, jsonify, request
from utils import browser

wechat = ntchat.WeChat()

WECHAT_CALLBACK = os.getenv('WECHAT_CALLBACK')
SUPER_USER = os.getenv('SUPER_USER')

def convert_to_jpg(input_image_path, output_image_path, quality=85):
    """
    将图片转换为JPG格式。

    :param input_image_path: 原始图片的路径。
    :param output_image_path: 转换后的JPG图片的保存路径。
    :param quality: JPG图片的质量，范围是1（最差）到95（最好），100为不压缩。
    """
    # 打开原始图片
    with Image.open(input_image_path) as img:
        # 转换图片格式为'RGB'，因为某些图片格式可能不支持转换
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # 保存为JPG格式
        img.save(output_image_path, 'JPEG', quality=quality)
        print(f"图片已转换并保存到：{output_image_path}")
    return output_image_path


def download_image(url, folder='temp'):
    # 确保临时文件夹存在
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 为图片创建一个文件名
    filename = os.path.join(folder, url.split('/')[-1])

    # 发送HTTP GET请求
    response = requests.get(url, stream=True)

    # 检查请求是否成功
    if response.status_code == 200:
        # 打开文件进行写入
        with open(filename, 'wb') as f:
            # 将图片数据写入文件
            for chunk in response.iter_content(1024):
                f.write(chunk)
        absolute_path = os.path.abspath(filename)
        print(f"图片的绝对路径是：{absolute_path}")
        absolute_path2 = convert_to_jpg(absolute_path,absolute_path + '.jpg')
        os.remove(absolute_path)
        return absolute_path2
    else:
        print(f"图片下载失败，状态码：{response.status_code}")
        return ''
   

# 进行登录
def login():
    if wechat.login_status == False:
        wechat.open(smart=True)
        wechat.on(ntchat.MT_ALL, on_recv)
        time.sleep(5)

def set_login_with_qrcode():
    if wechat.login_status == False:
        wechat.open(smart=True, show_login_qrcode=True)
        wechat.on(ntchat.MT_ALL, on_recv)

def login_status():
    login()
    return {'status':wechat.login_status}

# 事件调用
def on_recv(wechat_instance: ntchat.WeChat, message):
    print("Recv: ", message)
    response = requests.post(WECHAT_CALLBACK, json=message)
    if response.status_code != 200:
        print("Error: ", response.status_code, response.text)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return 'It works!'

@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify(login_status())

@app.route('/login_with_qrcode', methods=['GET'])
def login_with_qrcde():
    set_login_with_qrcode()
    return jsonify(text='请注意二维码')

@app.route('/get_login_info', methods=['GET'])
def get_login_info():
    login()
    return jsonify(wechat.get_login_info())

@app.route('/get_self_info', methods=['GET'])
def get_self_info():
    login()
    return jsonify(wechat.get_self_info())

@app.route('/get_contacts', methods=['GET'])
def get_contacts():
    login()
    return jsonify(wechat.get_contacts())

@app.route('/get_publics', methods=['GET'])
def get_publics():
    # 获取关注公众号列表
    login()
    return jsonify(wechat.get_publics())

@app.route('/get_contact_detail', methods=['GET'])
def get_contact_detail():
    login()
    wxid = request.args.get('wxid')
    return jsonify(wechat.get_contact_detail(wxid))

@app.route('/get_rooms', methods=['GET'])
def get_rooms():
    login()
    return jsonify(wechat.get_rooms())

@app.route('/get_room_detail', methods=['GET'])
def get_room_detail():
    login()
    room_wxid = request.args.get('room_wxid')
    return jsonify(wechat.get_room_detail(room_wxid))

@app.route('/get_room_members', methods=['GET'])
def get_room_members():
    login()
    room_wxid = request.args.get('room_wxid')
    return jsonify(wechat.get_room_members(room_wxid))

@app.route('/get_room_notice', methods=['GET'])
def get_room_notice():
    login()
    room_wxid = request.args.get('room_wxid')
    res = wechat.get_room_notice(room_wxid)
    return jsonify(res)

@app.route('/accept_friend', methods=['POST'])
def accept_friend():
    login()
    info = request.get_json()
    ret = wechat.accept_friend_request(info["encryptusername"], info['ticket'], int(info['scene']))
    if ret:
        wechat.send_text(to_wxid=ret["userName"], content="您好！我们开始新的旅程吧！")
        return jsonify(ret)
    else:
        return jsonify(ret)
    
@app.route('/search_contacts', methods=['POST'])
def search_contacts():
    login()
    info = request.get_json()
    info = wechat.search_contacts(wxid=info['wxid'])
    if not info:
        return jsonify({'code': 1, 'msg': '未找到该用户'})
    return jsonify(info)

@app.route('/send_super_user', methods=['POST'])
def send_super_user():
    login()
    data = request.get_json()
    # 发送给super user
    wechat.send_text(to_wxid=SUPER_USER,content=data['content'])
    return jsonify(ok=True)

@app.route('/send_text', methods=['POST'])
def send_text():
    login()
    data = request.get_json()
    wechat.send_text(to_wxid=data['to_wxid'], content=data['content'])
    return jsonify(ok=True)

@app.route('/send_room_at_msg', methods=['POST'])
def send_room_at_msg():
    login()
    data = request.get_json()
    wechat.send_room_at_msg(to_wxid=data['to_wxid'], content='{$@}' +  data['content'], at_list=data['at_list'])
    return jsonify(ok=True)

@app.route('/send_card', methods=['POST'])
def send_card():
    login()
    data = request.get_json()
    wechat.send_card(to_wxid=data['to_wxid'], card_wxid=data['card_wxid'])
    return jsonify(ok=True)

@app.route('/send_link_card', methods=['POST'])
def send_link_card():
    login()
    data = request.get_json()
    wechat.send_link_card(to_wxid=data['to_wxid'], title=data['title'], desc=data['desc'], url=data['url'], image_url=data['image_url'])
    return jsonify(ok=True)

@app.route('/send_image', methods=['POST'])
def send_image():
    login()
    data = request.get_json()
    # 图片下载到本地临时文件
    image_url = data['image_url']
    image_path = download_image(image_url)
    if image_path:
        wechat.send_image(to_wxid=data['to_wxid'], file_path=image_path)
        # TODO：删除临时文件,直接删除会发送不成功
        # os.remove(image_path)
    else:
        return jsonify(ok=False, msg='图片下载失败')

    return jsonify(ok=True)

@app.route('/send_file', methods=['POST'])
def send_file():
    login()
    data = request.get_json()
    wechat.send_file(to_wxid=data['to_wxid'], file_path=data['file_path'])
    return jsonify(ok=True)

@app.route('/send_video', methods=['POST'])
def send_video():
    login()
    data = request.get_json()
    wechat.send_video(to_wxid=data['to_wxid'], file_path=data['file_path'])
    return jsonify(ok=True)

@app.route('/send_gif', methods=['POST'])
def send_gif():
    login()
    data = request.get_json()
    wechat.send_gif(to_wxid=data['to_wxid'], file_path=data['file_path'])
    return jsonify(ok=True)

@app.route('/send_xml', methods=['POST'])
def send_xml():
    login()
    data = request.get_json()
    wechat.send_xml(to_wxid=data['to_wxid'], xml=data['xml'], app_type=data['app_type'])
    return jsonify(ok=True)

@app.route('/send_pat', methods=['POST'])
def send_pat():
    login()
    data = request.get_json()
    wechat.send_pat(room_wxid=data['room_wxid'], patted_wxid=data['patted_wxid'])
    return jsonify(ok=True)

@app.route('/modify_friend_remark', methods=['POST'])
def modify_friend_remark():
    login()
    data = request.get_json()
    wechat.modify_friend_remark(wxid=data['wxid'], remark=data['remark'])
    return jsonify(ok=True)

@app.route('/requests', methods=['POST'])
def proxy_requests():
    data = request.get_json()
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"}
    timeout = data.get('timeout',25)
    response = requests.get(data['url'],headers=headers,timeout=timeout)
    return jsonify(text=response.text)


@app.route('/selenium', methods=['POST'])
def selenium():
    data = request.get_json()
    browser.get(data['url'])
    page_source = browser.page_source
    return jsonify(text=page_source)

if __name__ == '__main__': 
    login()
    try:
        from gevent import pywsgi
        server = pywsgi.WSGIServer( ('0.0.0.0', 8000 ), app )
        server.serve_forever()
    except KeyboardInterrupt:
        ntchat.exit_()
        exit(0)
