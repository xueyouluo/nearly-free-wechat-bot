import sqlite3
from database.database_config import (
    SQL_DB_NAME, SQL_WEIXIN_DOC_TABLE, 
    SQL_PROMPT_DB_NAME,SQL_PROMPT_TABLE,
    SQL_WX_FRIEND_REQUEST_TABLE,
    SQL_WEIXIN_USER_PUB_TABLE,
    SQL_WEIXIN_USER_PUB_PUSH_TABLE,
    SQL_WEIXIN_USER_PUB_CONFIG_TABLE,
    SQL_ATTEND_TABLE, SQL_ATTEND_STATUS_TABLE,
    SQL_ARXIV_TABLE, SQL_GITHUB_TRENDING_TABLE,
    SQL_THREAD_TABLE,
    SQL_PUSH_INFO_TABLE,
    SQL_KIMI_ARXIV_TABLE,
    SQL_KIMI_TOKEN_TABLE,
    SQL_USER_SUBSCRIPTION_TABLE,
    SQL_WEIXIN_USER_TABLE, SQL_WEIXIN_USER_DOC_TABLE,
    SQL_WEIXIN_CHAT_TABLE,SQL_TOKEN_USAGE_TABLE)

def drop_table(table_name):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        # 执行DELETE语句以删除表中的所有行
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        # 提交更改
        conn.commit()

def clear_table(table_name):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        # 执行DELETE语句以删除表中的所有行
        cursor.execute(f"DELETE FROM {table_name}")

        # 提交更改
        conn.commit()

def create_arxiv_article_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(f"""CREATE TABLE IF NOT EXISTS {SQL_ARXIV_TABLE}
                  (
                  entry_id TEXT PRIMARY KEY,
                  status BOOLEAN DEFAULT 1,
                  publish_time DATETIME,
                  title TEXT,
                  title_chinese TEXT,
                  summary TEXT,
                  topic TEXT,
                  matched BOOLEAN DEFAULT 1,
                  emoji TEXT,
                  simple_summary TEXT,
                  comment TEXT,
                  authors TEXT,
                  crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                  category TEXT
                  )
        """)
        conn.commit()

def create_wx_article_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_WEIXIN_DOC_TABLE}
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    author_id TEXT,
                    summary TEXT,
                    content TEXT,
                    publish_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    url TEXT,
                    is_clickbait BOOLEAN DEFAULT 1,
                    is_marketing BOOLEAN DEFAULT 1,
                    category TEXT DEFAULT '',
                    keywords TEXT DEFAULT ''
                    )"""
        )
        conn.commit()

def creat_wx_user_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_WEIXIN_USER_TABLE} 
                (
                    user_id TEXT PRIMARY KEY,
                    status TEXT,
                    need_push BOOLEAN DEFAULT 0
                )"""
        )
        conn.commit()

def create_wx_user_pub_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_WEIXIN_USER_PUB_TABLE} 
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    pub_id TEXT,
                    pub_name TEXT
                )"""
        )
        conn.commit()

def create_wx_user_pub_push_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_WEIXIN_USER_PUB_PUSH_TABLE} 
                (
                    user_id TEXT PRIMARY KEY,
                    last_push_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""
        )
        conn.commit()

def create_wx_user_pub_push_config_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_WEIXIN_USER_PUB_CONFIG_TABLE} 
                (
                    user_id TEXT PRIMARY KEY,
                    push_time TEXT,
                    keywords TEXT
                )"""
        )
        conn.commit()

def create_wx_user_article_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_WEIXIN_USER_DOC_TABLE} 
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    title TEXT,
                    author TEXT,
                    url TEXT
                )"""
        )
        conn.commit()

def create_wx_chat_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_WEIXIN_CHAT_TABLE}
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    receiver TEXT,
                    content TEXT,
                    chatroom TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""
        )
        conn.commit()

def create_token_usage_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_TOKEN_USAGE_TABLE}
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    use_case TEXT,
                    user TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""
        )
        conn.commit()

def create_prompt_table():
    with sqlite3.connect(SQL_PROMPT_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_PROMPT_TABLE}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inputs TEXT,
                outputs TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
        conn.commit()

def create_wx_friend_request_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_WX_FRIEND_REQUEST_TABLE}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encryptusername TEXT,
                fromusername TEXT,
                fromnickname TEXT,
                scene TEXT,
                ticket TEXT,
                request_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()

def create_attend_status_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_ATTEND_STATUS_TABLE}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                room TEXT,
                status TEXT
            )"""
        )
        conn.commit()

def create_attend_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_ATTEND_TABLE}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                room TEXT,
                on_time DATETIME NULL,
                off_time DATETIME NULL,
                remind INTEGER DEFAULT 1,
                last_remind_time DATETIME NULL,
                attend_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()

def create_kimi_token_tabel():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_KIMI_TOKEN_TABLE}
            (
                user_id TEXT PRIMARY KEY,
                access_token TEXT DEFAULT '',
                refresh_token TEXT DEFAULT '',
                last_update_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()

def create_kimi_arxiv_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_KIMI_ARXIV_TABLE}
            (
                link TEXT PRIMARY KEY,
                content TEXT
            )"""
        )
        conn.commit()

def create_github_trending_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_GITHUB_TRENDING_TABLE}
            (
                name TEXT PRIMARY KEY,
                about TEXT,
                about_zh TEXT,
                rank INTEGER,
                language TEXT,
                stars TEXT,
                forks TEXT,
                stars_today TEXT,
                summary TEXT,
                description TEXT,
                times_of_today INTEGER,
                last_pushtime DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                keywords TEXT
            )"""
        )
        conn.commit()

def create_thread_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_THREAD_TABLE}
            (
                user_id TEXT PRIMARY KEY,
                thread TEXT,
                last_update_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()

def create_user_subscription_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_USER_SUBSCRIPTION_TABLE}
            (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                push_time TEXT,
                keywords TEXT,
                sources TEXT
            )"""
        )
        conn.commit()

def create_push_info_table():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {SQL_PUSH_INFO_TABLE}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                html TEXT,
                source TEXT,
                summary TEXT DEFAULT ''
            )"""
        )
        conn.commit()

def init_all_tables():
    create_wx_user_pub_push_config_table()
    create_thread_table()
    creat_wx_user_table()
    create_wx_article_table()
    create_wx_user_article_table()
    create_wx_chat_table()
    create_token_usage_table()
    create_prompt_table()
    create_wx_friend_request_table()
    create_attend_table()
    create_wx_user_pub_table()
    create_attend_status_table()
    create_arxiv_article_table()
    create_github_trending_table()
    create_wx_user_pub_push_table()
    create_kimi_arxiv_table()
    create_push_info_table()
    create_user_subscription_table()
    create_kimi_token_tabel()

if __name__ == '__main__':
    init_all_tables()