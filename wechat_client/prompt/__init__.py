import datetime

ARXIV_SYSTEM = '''你是一位阅读论文的助手，需要帮助用户筛选符合他们兴趣的论文，并总结论文的摘要。

我将为你提供论文的标题和摘要。您需要完成以下任务：
- 将标题翻译成中文
- 提取论文的主要主题词，主题词应该具体，例如，避免使用像"自然语言处理"这样宽泛的内容，而是集中在解决的具体问题上，如偏见缓解、长文本建模等。最多3个。并且不要使用用户的兴趣作为主题词。
- 判断这篇论文是否符合用户的兴趣
- 摘要论文的核心内容

你的回答必须是一个结构化的JSON，其中的内容为简体中文，如下所示：
```json
{{
    "title": "中文标题",
    "summary": "核心内容的1-2句摘要，比如通过什么技术解决了什么问题",
    "topic": "论文的中文主题词，严格根据标题和摘要进行判断，不要捏造。注意不要使用提供给你的用户兴趣作为主题，主题词使用逗号分割，不超过3个",
    "matched": "一个布尔值，表明根据这篇论文的标题、摘要和主题是否符合用户的兴趣，并且不在用户不感兴趣的内容中"
}}
```
'''

SUMMARY_PROMPT = '''请对下面这篇文章用中文写个简洁和专业的总结。

要求:
- 严格依据文章内容总结概括，不得额外推理。
- 判断文章是否为营销文：包含对会议、招生、招聘、课程、保险或其他产品和服务的推广，存在促销信息、专门的购买链接或明显的销售倾向的文章是营销文"。
- 输出文章5个以内的关键词和分类
- 输出一句话总结，再用列举不超过5个关键信息点。
- 关键信息点要尽可能覆盖文章的主要内容，包含具体细节，不能太概括。

文章内容如下：
```
标题: 
{title}

正文: 
{content}
```

输出格式为：
```
<一句话总结>
文章内容的一句话总结
</一句话总结>
<关键信息点>
1. 文章的关键信息1
2. 文章的关键信息2
...
</关键信息点>
<关键词>
能准确概括文章的主题和核心内容的3-5个关键词或短语，使用','号分割。数量不超过5个。
</关键词>
<分类>
根据文章的内容分类，如对于大模型相关的有投融资、模型发布、评测、AI产品、课程、工具等
</分类>
<营销文>
根据前面的信息判断文章是否营销文，如包含对会议、招生、招聘、课程、保险或其他产品和服务的推广，只输出是或者否
</营销文>
```

注意每个标签都必须输出结束标签。

请严格按照输出格式输出总结内容，不要解释。'''

QA_PROMPT = '''根据下面的多段已知信息，简洁和专业的来回答问题。

<已知信息>
{context}
</已知信息>

要求：
- 根据已知信息来回答问题，不要编造答案，如果不知道请说 “根据已知信息无法回答该问题”。
- 如果提供的信息不够或者不能回答问题，请说“根据已知信息无法回答该问题”。
- 用户无法看到已知信息中的内容，你必须在回答中重复重要信息。
- 你必须在回答中重复重要信息，而不是让用户去查看已知信息。
- 合理使用列表和换行符号提高回答的可读性。

开始！

问题：{query}

回答：'''

def get_default_system():
    return f'''你是一个AI助手，名字叫MIND，旨在给用户提供有用的帮助。现在的时间是{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}。你需要用中文和用户交流。'''

STANDALONE_PROMPT = '''根据以下聊天记录和后续问题，将后续问题重新表述为独立问题。要求：
- 确保避免使用任何不清楚的代词和指代（如他、它、这个、那个、产品、事件、时间、地点、人物、内容、文字等），可以保留“我”、“你”。
- 独立问题应该简洁明了，但需要保留足够的信息，以便没有先前对话知识的人也可以理解问题。
- 如果用户向AI分享了一篇文章，则应在问题中包含文章标题。
- 如果后续问题不是一个问题，输出“None”
- 如果不能转换为独立问题或后续输入不是问题，输出“None”
- 如果问题是关于AI机器人或可以通过聊天记录回答，也输出“None”，例如：你叫什么，我的上一个问题是什么，你是谁等

聊天记录：
{chat_history}
后续问题：{question}

开始，注意只输出独立问题或者“None”，不要解释。

独立问题：'''

STANDALONE_PROMPT_ICL = f'''根据以下聊天记录和后续问题，将后续问题重新表述为独立问题。要求：
- 确保避免使用任何不清楚的代词和指代（如他、它、这个、那个、产品、事件、时间、地点、人物、内容、文字等），可以保留“我”，“你”
- 独立问题应该简洁明了，但需要保留足够的信息，以便没有看过聊天记录的人也可以理解问题。
- 如果用户向AI分享了一篇文章，则应在问题中包含文章标题。
- 如果后续问题是一个问题，但与聊天记录无关，则直接直接输出后续问题为独立问题
- 如果不能转换为独立问题、要求或后续输入不是问题，输出“None“
- 对于历史记录中包含画图的内容，需要原来提到的图片内容都包含在问题中
- 如果问题是关于AI机器人或可以通过聊天记录回答，也输出“None”，例如：你叫什么，我的上一个问题是什么，你是谁等
- 记住现在的时间是{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ''' + '''

你必须输出思考和独立问题两个字段。

举例：
聊天记录：
User: 马云是谁
AI：马云是阿里巴巴的创始人
后续问题：他创办的公司现在谁是CEO

输出：
思考：后续问题是一个问题，其中“他创办的公司”是指阿里巴巴
独立问题：阿里巴巴现在谁是CEO

聊天记录：
User: 画个可爱的猫咪
AI：好的，已完成
后续问题：加个爱心

输出：
思考：后续问题是一个要求，是对前面画的内容添加一个爱心
独立问题：画个可爱的猫咪加个爱心

开始！注意，严格按照要求，根据后续问题输出思考和最后的独立问题。

聊天记录：
{chat_history}
后续问题：{question}

输出：'''

RELEVANT_PROMPT = '''你是一个智能的搜索助手，你需要判断用户给定的查询和检索到的文章的相关性。你需要先从文章的标题和摘要中找到与查询相关的关键词证据，越多则越相关。

相关性级别说明如下：
- 高度相关：文章与查询之间存在明显且紧密的关联，满足查询需求。文章中含有与查询相关的大量关键词。
- 相关：文章包含查询所需信息，可能有轻微冗余或额外信息。文章中含有少数与查询相关的关键词。
- 不相关：文章与查询之间几乎没有关联，关联性较少，信息无关或不符。文章中几乎没有与查询相关的关键词。

你最终需要输出一个表格，表格的内容如下，其中文章按照相关性从高到低排序：
|  ID |  相关证据  | 相关性级别 |
| --- | --- | --- |
| 文章的ID | 文章与查询最相关的关键词，没有则为无 | 相关性级别 |

开始。

查询：{query}

文章列表：
|  文章ID | 文章标题 | 文章摘要 |
| --- | --- | --- |
{articles}

只要输出相关性表格，要包含全部文章，内容只包含ID，相关证据和相关性级别，不要包含其他内容，也不要解释。

相关性表格：'''

TRANSLATE_PROMPT = '''请把下面的内容翻译成中文输出，如果本身为中文，如果本身是中文，则直接输出原文本身。
要翻译的内容：
```
{text}
```
中文:'''

FORMAT_PROMPT = """Please format the result # RESULT # to a strict JSON format # STRICT JSON FORMAT #. 
Requirements:
1. Do not change the keys and values;
2. Don't tolerate any possible irregular formatting to ensure that the generated content can be converted by json.loads();
3. Do not add any additional content, you can discard incomplete content to ensure the output is in valid JSON format. 
# RESULT #:{{illegal_result}}
# STRICT JSON FORMAT #:"""


INTENT_PROMPT = '''请根据对话历史，判断用户最后一句话的意图，意图包括：
| 意图 | 解释 |
| ---  | --- |
| 闲聊 | 包含闲聊、问候、内容创作、询问对话历史中的信息、对话历史能够回答的问题，涉及AI助手的信息等。或者用户明确说了用你自己的知识回答时。 |
| 时效性问答 | 涉及到时效性的问题、新闻、事件以及搜索等，包含关键词最近、现在、近期、搜索、查一下以及时间等 |
| 知识库问答 | 涉及到专业性知识的问答，以及用户刚分享了文章给AI后的问题 |
| 画图 | 用户要求AI画图，包含关键词画图、画图、生成图片、生成图片等，也包括对生成的图片进行二次修改 |
| 其他 | 不在上述意图的或者你无法判断的情况 |

举例：
===
User: 你叫什么
===
输出：
===
思考：用户最后询问AI叫什么，是跟AI助手信息相关的，所以应该为闲聊意图
答案：闲聊
===

===
User：最近有什么好看的电影
===
输出：
===
思考：用户最后的问题包含了关键词“最近”，这是一个时效性问答
答案：时效性问答
===

===
User: 宝宝老是拉肚子怎么办
===
输出：
===
思考：对话历史中没有可以回答这个问题的内容，这可能跟知识库相关，我需要从知识库找答案
答案：知识库问答
===

===
User: 我分享了一篇文章《大模型落地应用》给你
AI: 这篇文章介绍了大模型落地的一些经验，非常不错。
User: 我分享了什么给你
===
输出：
===
思考：这个问题可以从历史对话中获取答案，因此为闲聊
答案：闲聊
===

开始！注意你必须严格按照要求输出思考和答案，格式与样例一致。

===
{chat_history}
===

输出：'''