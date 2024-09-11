
import os
import asyncio
from typing import Dict, Callable
from utils.request_models import Message
from utils.httpx_client import get_login_info,send_msg

def get_self_wxid():
    res = get_login_info()
    self_wxid = res['wxid']
    return self_wxid

class TypeHandlerRegistry:
    def __init__(self):
        self.handlers: Dict[int, Callable] = {}

    def register(self, type_key: int, handler_func: Callable):
        self.handlers[type_key] = handler_func

    def get_handler(self, type_key: int) -> Callable:
        return self.handlers.get(type_key)

class TypeHandler:
    registry = TypeHandlerRegistry()
    self_wxid = get_self_wxid()
    locks = {}

    @classmethod
    async def acquire_lock(cls, from_wxid):
        if from_wxid not in cls.locks:
            cls.locks[from_wxid] = asyncio.Lock()
        lock = cls.locks[from_wxid]
        if lock.locked():
            return None
        await lock.acquire()
        return lock

    @classmethod
    async def release_lock(cls, lock, from_wxid):
        if lock is None or from_wxid is None:
            return  # 如果lock或from_wxid为空，则不执行任何操作

        lock.release()
        if not lock.locked():
            cls.locks.pop(from_wxid, None)

    @staticmethod
    def register_handler(type_key: int):
        def decorator(handler_func: Callable):
            TypeHandler.registry.register(type_key, handler_func)
            return handler_func
        return decorator
    
    @classmethod
    async def process(cls, request: Message):
        from_wxid = request.data.get('from_wxid')
        # 不处理自己发的消息
        if from_wxid == TypeHandler.self_wxid:
            return
        
        lock = None
        if from_wxid is not None:
            lock = await cls.acquire_lock(from_wxid)
            if lock is None:
                try:
                    data = request.data
                    from_wxid = data["from_wxid"]
                    to_wxid = data['to_wxid']
                    room = data['room_wxid']
                    await send_msg("您问的太快了，请等我回复后再提问。",from_wxid,to_wxid,room)
                except Exception as e:
                    print(e)
                return

        print(request.data)
        print(request.type)
        try:
            handler = cls.registry.get_handler(request.type)
            if handler:
                await handler(request)
        finally:
            if lock is not None:
                await cls.release_lock(lock, from_wxid)

