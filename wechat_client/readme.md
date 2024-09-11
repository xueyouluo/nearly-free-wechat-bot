# Wechat Client

这里主要接受微信消息，并进行处理。

## 1. 安装依赖

你可以考虑直接用部署微信服务的那台服务器，也可以再申请一台服务器。但是windows上面开发起来太麻烦了，建议另外搞台linux服务器。

```
pip install -r requirements.txt
```

## 2. 配置环境变量
.env:

```
ZHIPU_KEY=你的智谱申请的key
WECHAT_SERVER=你的微信服务器地址
SUPER_USER=你可以接受系统消息的微信号，不是部署成机器人的微信号
TG_USER_PWD=天工搜索的账号和密码，支持联网搜索获取答案，如果有多个请用,分割，账号密码使用:号分割，如user1:pwd1,user2:pwd2
```

额外的配置信息在config.py：
- 还有其他一些自己看了，酌情配置

## 3. 运行
```
uvicorn service:app --host 0.0.0.0 --port=8080
```

## 4. 安全
考虑在服务器上运行，所以需要配置安全组，开放8080端口，并且设置IP为wechat_server的服务器地址