from enum import Enum

class UserStatus(Enum):
    """
    User status
    """
    QA = '知识库'
    NORMAL = '正常'
    CLOSE = '关闭'
    AUTO = '自动'
    KIMI = 'kimi'

class UseCase(Enum):
    """
    Use case
    """
    CHAT = '闲聊'
    INTENT = '意图判断'
    STANDALONE = '独立问题'
    KB_QA = '知识库问答'
    SEARCH_QA = '联网问答'
    FUCNTION = "函数选择"
    SUMMARY = '摘要'
    EMBEDDING = '向量'
    RELEVANCE = '相关性'
    TRANSLATE = '翻译'
    FIX_JSON = 'JSON修复'
    TOTAL = '汇总'
    KIMI_CHAT = 'kimi-chat'
    GITHUB = 'github总结-crawling'
    ARXIV = 'arxiv总结'
    PUB = "公众号推送摘要"

class UserIntent(Enum):
    """
    User intent
    '闲聊','知识库问答','时效性问答','其他',"文章查询"
    """
    CHAT = '闲聊'
    KB_QA = '知识库问答'
    SEARCH_QA = '时效性问答'
    OTHER = '其他'
    ARTICLE_SEARCH = '文章查询'
    IMAGE = '画图'

class AttendStatus(Enum):
    """
    Attend status
    """
    OPEN = '开启'
    CLOSE = '关闭'

class RelevanceEnum(Enum):
    """
    Relevance enum
    高度相关,相关,部分相关,不相关
    """
    HIGH = '高度相关'
    RELATED = '相关'
    PART_RELATED = '部分相关'
    UNRELATED = '不相关'
    