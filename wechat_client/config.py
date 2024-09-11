# 公众号上限
MAX_PUBLIC_NUM = 100

# 超级用户, 一般为wxid_xxxxxxx
SUPER_USER = 'wxid_xxxxxxx'

# 机器人的名字
AT_SLEF_NAME= '@MIND'
# Article Config
MAX_CHARACTOR_SIZE = 30000

# LLM Config
MAX_CONTENT_SIZE = 10000
SUMMARY_SIZE = 800
HISTORY_SIZE = 1500
AI_ROLE = "AI"


# 智谱配置，你可以改成自己喜欢的其他模型服务，对应改改llm中的调用代码就好。
# 向量模型，比较便宜，百万token 0.5元
ZHIPU_EMBEDDING = 'embedding-3'
# 这个根据自己需求配吧，这里用flash的免费模型了
ZHIPU_MODEL = 'glm-4-flash'