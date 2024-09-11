import os
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import binascii
from datetime import datetime

option = webdriver.ChromeOptions()
option.add_argument("-headless")
option.add_argument("-blink-settings=imagesEnabled=false")
option.add_argument("-disable-gpu")
chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
service = Service(executable_path=chromedriver_path)
browser = webdriver.Chrome(service=service,options=option)
browser.implicitly_wait(10)


"""
dat文件和源图片文件就是用某个数按字节异或了一下，异或回来就可以了，
A ^ B = C
B ^ C = A
A ^ C = B
假设png文件头是A，dat文件是C，用A和C文件头的字节异或就可以得出B，因
为图片的格式以png，jpg，gif为主，通过这三种文件格式的头两个字节和待
转换文件的头两个字节一一异或的结果相等就找到B了，同时也知道了文件的
格式
"""
def get_top_2hex(path):
    """
    获取文件的前两个16进制数
    """
    data = open(path,'rb')
    hexstr = binascii.b2a_hex(data.read(2))
    return str(hexstr[:2], 'utf8'), str(hexstr[2:4], 'utf8')

"""
JPG文件头16进制为0xFFD8FF
PNG文件头16进制为0x89504E
GIF文件头16进制为0x474946
"""
def parse(path):
    firstV, nextV = get_top_2hex(path)
    firstV = int(firstV, 16)
    nextV = int(nextV, 16)
    coder = firstV ^ 0xFF
    kind = 'jpg'

    if firstV ^ 0xFF == nextV ^ 0xD8:
        coder = firstV ^ 0xFF
        kind = 'jpg'
    elif firstV ^ 0x89 == nextV ^ 0x50:
        coder = firstV ^ 0x89
        kind = 'png'
    elif firstV ^ 0x47 == nextV ^ 0x49:
        coder = firstV ^ 0x47
        kind = 'gif'
    
    return coder, kind

def convert_wechat_image(file_path):
    coder, kind = parse(file_path)

    dat = open(file_path, "rb")
    pic = io.BytesIO()

    for cur in dat:
        for item in cur:
            pic.write(bytes([item ^ coder]))

    dat.close()
    return pic