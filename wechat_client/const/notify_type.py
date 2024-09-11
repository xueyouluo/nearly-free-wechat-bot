class NotifyType:
    # 用于接收所有的通知消息
    MT_ALL = 11000

    # 微信进程退出通知
    MT_RECV_WECHAT_QUIT_MSG = 11001

    # 第个通知消息，此时已经托管上微信
    MT_READY_MSG = 11024

    # 登录二维码通知
    MT_RECV_LOGIN_QRCODE_MSG = 11087

    # 用户登录成功的通知
    MT_USER_LOGIN_MSG = 11025

    # 用户注销或退出微信的通知
    MT_USER_LOGOUT_MSG = 11026

    # 文本消息通知
    MT_RECV_TEXT_MSG = 11046

    # 语音转文本的消息
    MT_RECV_VOICE_TEXT_MSG = 11112

    # 图片消息通知
    MT_RECV_IMAGE_MSG = 11047
    MT_RECV_PICTURE_MSG = 11047

    # 语音消息通知
    MT_RECV_VOICE_MSG = 11048

    # 新好友请求通知
    MT_RECV_FRIEND_MSG = 11049

    # 好友分享名片通知
    MT_RECV_CARD_MSG = 11050

    # 视频消息通知
    MT_RECV_VIDEO_MSG = 11051

    # 表情消息通知
    MT_RECV_EMOJI_MSG = 11052

    # 位置消息通知
    MT_RECV_LOCATION_MSG = 11053

    # 链接卡片消息通知
    MT_RECV_LINK_MSG = 11054

    # 文件消息通知
    MT_RECV_FILE_MSG = 11055

    # 小程序消息通知
    MT_RECV_MINIAPP_MSG = 11056

    # 二维码支付通知
    MT_RECV_WCPAY_MSG = 11057

    # 系统消息通知
    MT_RECV_SYSTEM_MSG = 11058

    # 撤回消息通知
    MT_RECV_REVOKE_MSG = 11059

    # 未知消息通知
    MT_RECV_OTHER_MSG = 11060

    # 未知应用消息通知
    MT_RECV_OTHER_APP_MSG = 11061

    # 群成员新增通知
    MT_ROOM_ADD_MEMBER_NOTIFY_MSG = 11098

    # 群成员删除通知
    MT_ROOM_DEL_MEMBER_NOTIFY_MSG = 11099

    # 通过接口创建群聊的通知
    MT_ROOM_CREATE_NOTIFY_MSG = 11100

    #  退群或被踢通知
    MT_ROOM_DEL_NOTIFY_MSG = 11101

    # 联系人新增通知
    MT_CONTACT_ADD_NOITFY_MSG = 11102

    # 联系人删除通知
    MT_CONTACT_DEL_NOTIFY_MSG = 11103

