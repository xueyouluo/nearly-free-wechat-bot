# 微信服务配置

准备一个不常用的微信号，用于接收消息。别用自己的主要微信号了。 可以申请个每个月8块钱的联通卡，注册个微信号用。

## 基础配置
1. 购买一台windows系统的云服务器
2. Mac的话安装microsoft remote desktop for mac。使用IP地址、用户名和密码登录。
    - 不要使用云服务商提供的网页版登录，太难用了。
    - 是remote desktop的另外一个好处是方便传输文件。
3. 在服务器上安装python 3.10
4. 安装[微信客户端3.6.0.18版本](https://github.com/tom-snow/wechat-windows-versions/releases/download/v3.6.0.18/WeChatSetup-3.6.0.18.exe)
5. 打开一个命令行，安装ntchat和其他依赖
```
pip install -r requirments.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 这里特别注意，因为ntchat有个文件会引发云服务的杀毒，如果遇到这个情况，要么从杀毒里面把ntchat的被杀或者隔离的文件放出来；如果直接被删了，重新安装一下ntchat

## 配置环境变量
新建一个.env文件（最好用notepad++或者vscode建，不然会保存会有问题）
```
WECHAT_CALLBACK=这里写你的微信回调地址，比如http://127.0.0.1:8080/callback
SUPER_USER=这里写一个管理员账号，可以为空，如果不知道，可以起了服务后给机器人的微信发个消息看看日志显示是什么账号
CHROMEDRIVER_PATH=参考下文的selenium，这里写你的chromedriver路径，比如D:\chromedriver.exe，如果不需要selenium，可以不填
```

注意：
- 其中WECHAT_CALLBACK是最重要的参数，这个决定了微信收到消息后发送到哪个服务进行处理。
- SUPER_USER主要可以用来控制服务的开启关闭，以及接受一些信息。设置成你自己常用的微信号。

## 开启服务
在windows上登录你的微信，然后运行下面的命令：
```
python app_for_win.py
```

注意在云服务器安全这块打开对应端口。

## 安全设置

配置IP白名单，只能让你的client服务器访问。

## 其他

### selenium
方便你爬一些网页内容。当然你也可以用playwright，看自己喜欢。

安装selenium:
```
pip install selenium
```

如果你要使用selenium，你还需要安装chrome浏览器，由于我的系统是windows server 2012太老，还得找对应的chrome版本安装。

Chrome 109支持server 2012，下载地址：https://webcdn.m.qq.com/spcmgr/download/109.0.5414.120_chrome_installer-win64.exe

下载好后直接安装。

再在这里找到109的chromedriver: https://sites.google.com/chromium.org/driver/downloads。找到对应chromedriver_win32.zip，解压后把chromedriver.exe路径配置到env文件中。

使用
```python
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
option = webdriver.ChromeOptions()
option.add_argument("-headless")
option.add_argument("-blink-settings=imagesEnabled=false")
option.add_argument("-disable-gpu")
#
chromedriver_path = 'C:\\Users\\Administrator\\Downloads\\chromedriver_win32\\chromedriver.exe'
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service,options=option)
driver.implicitly_wait(10) 
driver.get('https://www.baidu.com')
driver.title
```

其他资料：
- 参考selenium的安装文档：https://selenium-python.readthedocs.io/installation.html
- 正常可以在这里： https://googlechromelabs.github.io/chrome-for-testing/
