from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

from fastapi import FastAPI, Response, status
from contextlib import asynccontextmanager

from utils.request_models import Message
from plugins.handler_registry import TypeHandler
from plugins.hanlders import *
from database.sql_table_create import init_all_tables


@asynccontextmanager
async def init_app(app: FastAPI):
    # 这里放置初始化代码，例如连接数据库
    init_all_tables()
    yield
    # 这里放置清理代码，例如关闭数据库连接

app = FastAPI(lifespan=init_app)

@app.post("/wechat_callback")
async def wechat_callback(message: Message):
    await TypeHandler.process(message)
    return Response(status_code=status.HTTP_200_OK)