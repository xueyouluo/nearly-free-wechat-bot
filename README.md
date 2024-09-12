# Nearly-Free-Wechat-Bot

一个简单的微信机器人，可以接大模型实现：
- 对话
- 总结公众号文章
- 将文章入库存为知识库
- 关注公众号后自动收集公众号的推送

额外支持的能力
- 接入了天工的搜索，只需要账号密码可以自动调用，不过可能他随时升级，导致代码失效
- 接入了kimi网页版的能力，自动总结url链接的内容，也有升级后代码失效的风险

## 使用方法

### 微信配置

你需要有一台windows的云服务器，你可以买个阿里云99一年的或者腾讯云69一年的云服务器，配置低但是够用了。

你还需要有个不常用的微信号，作为机器人使用。

有了服务器后参考[微信配置](./wechat_server/readme.md)的内容设置好微信。

- 一段时间后可能会要你重新登陆，这时候也得自己去服务器扫码再登陆一下
- 微信经常会自己更新升级，这时候得我们手动去服务器把微信装回原来的版本


## 服务配置

你可以使用前面的windows服务器作为服务端，也可以再搞台linux服务器作为服务端。 

> 注意：虽然windows服务器也行，但是由于用到的向量库有点小坑，windows上安装chromadb会踩的坑是提示visual c++ 14 is required。这里参考这个[文档](https://www.partitionwizard.com/partitionmanager/microsoft-visual-c-14-is-required.html)去官网下载修复。

另外chromadb和ntchat之间有点冲突，确保先import chromadb再引用ntchat。

其他就参考[服务端配置](./wechat_server/readme.md)的内容。

启动服务后，发个消息给你的机器人试试吧。