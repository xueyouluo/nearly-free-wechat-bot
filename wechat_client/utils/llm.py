import os
import tiktoken
import logging
import time
from zhipuai import ZhipuAI
import numpy as np

from database.sql_database import  insert_prompt, insert_token_usage
from config import AI_ROLE,ZHIPU_MODEL,ZHIPU_EMBEDDING,HISTORY_SIZE
from const.enums import UseCase

zhipuai_client = ZhipuAI(api_key=os.getenv('ZHIPU_KEY'))
DEFAULT_ENCODING = 'cl100k_base'
encoding = tiktoken.get_encoding(DEFAULT_ENCODING)

def num_tokens_from_messages(messages):
    """Return the number of tokens used by a list of messages."""
    if isinstance(messages, Messages):
        messages = messages.to_list()
    tokens_per_message = 3
    tokens_per_name = 1
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

class Messages:
    def __init__(self, messages):
        self.messages = messages

    def __str__(self) -> str:
        text = ''
        for message in self.messages:
            if isinstance(message,SystemMessage):
                text += f'\033[31m{message}\033[0m' + '\n'
            if isinstance(message, UserMessage):
                text += f'\033[32m{message}\033[0m' + '\n'
            if isinstance(message, AssistantMessage):
                text += f'\033[33m{message}\033[0m' + '\n'
        return text

    def to_list(self):
        return [msg.to_dict() for msg in self.messages]

class SystemMessage:
    def __init__(self, system):
        self.system = system

    def __str__(self):
        return f"{self.system}"
    
    def to_dict(self):
        return {
            "role": "system",
            "content": self.system
        }

class UserMessage:
    def __init__(self, user) -> None:
        self.user  = user
    
    def __str__(self):
        return f"{self.user}"
    
    def to_dict(self):
        return {
            "role": "user",
            "content": self.user
        }

class AssistantMessage:
    def __init__(self, assistant) -> None:
        self.assistant = assistant

    def __str__(self):
        return f"{self.assistant}"
    
    def to_dict(self):
        return {
            "role": "assistant",
            "content": self.assistant
        }


def get_zhipuai_embedding(text):
    response = None
    # retry 3 times
    for i in range(3):
        try:
            response = zhipuai_client.embeddings.create(
                model=ZHIPU_EMBEDDING,
                input=text[:2000]
            )
            embeddings = response.data[0].embedding
           
            break
        except Exception as e:
            logging.error(f'error to get embedding, {e}')
            time.sleep(1)
    if response:
        v =  np.asarray(embeddings).reshape([1,-1])
        norm_v = np.linalg.norm(v)
        normalized_v = v / norm_v
        embedding = normalized_v.tolist()[0]
    else:
        embedding = []
    return embedding


def simple_call_llm(text,max_tokens = 800,temperature = 0.9):
    messages = Messages([UserMessage(text)])
    return call_llm(messages,max_tokens = max_tokens,temperature = temperature)

def call_zhipu(messages:Messages, max_tokens=200,temperature=0.):
    max_retry = 2
    if max_tokens == -1:
        max_tokens = 1000
    if temperature == 0.0:
        temperature = 0.1
    if temperature >= 1.0:
        temperature = 0.95

    while max_retry >= 0:
        try:
            response = zhipuai_client.chat.completions.create(
                model=ZHIPU_MODEL,
                messages=messages.to_list(),
                temperature=temperature,
                max_tokens=max_tokens
            )
            data = response.choices[0].message
            usage = response.usage
            insert_prompt(messages.to_list(), response.model_dump())
            return AssistantMessage(data.content.strip()), usage.model_dump()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(response.json())
            logging.warning(f'call error with {e}')
            max_retry -= 1
    raise

def call_llm(messages,max_tokens = 800,temperature = 0.9):
    try:
        logging.info('start to call zhipu')
        msg, usage= call_zhipu(messages,max_tokens = max_tokens,temperature = temperature)
        usage['model'] = 'zhipu'
        logging.info(f'call zhipu success')
    except Exception as e:
        print(e)
        logging.warning(f'调用模式失败')
        msg = AssistantMessage(f'调用模型失败，请稍后重试。')
        usage = None
    if usage:
        insert_token_usage(usage,UseCase.TOTAL,'')
    return msg, usage


def convert_chat_history_to_messages(chat_history,history_size=0):
    if not chat_history:
        return Messages([])
    # 最终结果应该为((user,ai),(user,ai))的形式
    slow = 0
    fast = 1
    while fast < len(chat_history):
        if chat_history[fast]['sender'] != chat_history[slow]['sender']:
            chat_history[slow+1] = chat_history[fast]
            slow += 1
        else:
            chat_history[slow]['content'] += chat_history[fast]['content']
        fast += 1
    chat_history = chat_history[:slow+1]

    # 找到第一个User的消息
    i = 0
    while i < len(chat_history) and chat_history[i]['sender'] == AI_ROLE:
        i += 1
    chat_history = chat_history[i:]

    if not chat_history:
        return Messages([])

    messages = []
    for item in chat_history:
        if item['sender'] == AI_ROLE:
            messages.append(AssistantMessage(item['content']))
        else:
            messages.append(UserMessage(item['content']))

    # 确保历史记录不会太长
    size = num_tokens_from_messages(Messages(messages))
    history_size = history_size if history_size > 0 else HISTORY_SIZE
    while size > history_size:
        messages.pop(0)
        size = num_tokens_from_messages(Messages(messages))
    
    # 确保开头的是user
    if isinstance(messages[0], AssistantMessage):
        messages = messages[1:]
        
    return Messages(messages)


# 测试
if __name__ == '__main__':
    messages = [{"role":"user",'content':"讲个笑话"}]
    print(call_llm(messages,max_tokens=500))