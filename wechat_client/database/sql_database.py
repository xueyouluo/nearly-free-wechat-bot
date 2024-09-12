import logging
import sqlite3
import json
import datetime
from database.database_config import (
    SQL_DB_NAME,SQL_WEIXIN_DOC_TABLE,SQL_WEIXIN_USER_TABLE,SQL_TOKEN_USAGE_TABLE,
    SQL_PROMPT_TABLE,SQL_PROMPT_DB_NAME,SQL_WX_FRIEND_REQUEST_TABLE,
    SQL_GITHUB_TRENDING_TABLE,SQL_KIMI_ARXIV_TABLE,SQL_THREAD_TABLE,
    SQL_ATTEND_TABLE,SQL_ATTEND_STATUS_TABLE,SQL_WEIXIN_USER_PUB_PUSH_TABLE,
    SQL_WEIXIN_USER_PUB_TABLE,SQL_WEIXIN_USER_PUB_PUSH_TABLE, SQL_ARXIV_TABLE,
    SQL_WEIXIN_USER_PUB_CONFIG_TABLE,SQL_USER_SUBSCRIPTION_TABLE, SQL_KIMI_TOKEN_TABLE,
    SQL_PUSH_INFO_TABLE,
    SQL_WEIXIN_USER_DOC_TABLE,SQL_WEIXIN_CHAT_TABLE)
from const.enums import UserStatus,AttendStatus
from config import AI_ROLE

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def try_parse_datetime(dt_str):
    dt = None
    for fmt in ['%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M:%S.%f']:
        try:
            dt = datetime.datetime.strptime(dt_str, fmt)
            break
        except ValueError:
            continue
    if dt is None: 
        try:
            dt_str = dt_str[:19]
            dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except:
            dt = datetime.datetime.now()
    return dt
        

def get_summary_by_url_and_user_id(url, user_id):
    # 连接到SQLite数据库
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"""SELECT u.title AS title,
                                u.author AS author,
                                u.url AS url,
                                d.summary AS summary
                        FROM {SQL_WEIXIN_USER_DOC_TABLE} u
                        JOIN {SQL_WEIXIN_DOC_TABLE} d ON u.url = d.url
                        WHERE u.user_id = ? AND u.url = ?;""", (user_id, url,))
        row = cursor.fetchone()

        # 如果存在数据，则打印
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            return doc
        else:
            return None   

def insert_arxiv(doc):
    if get_arxiv_by_id(doc['entry_id']):
        logging.info("Article already exist.")
        return
    table_name = SQL_ARXIV_TABLE
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    field_values = ', '.join(':' + key for key in doc.keys())

    # 构建动态SQL插入语句
    sql = f"INSERT INTO {table_name} ({field_names}) VALUES ({field_values})"
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, doc)
        conn.commit()

def get_github_trending_by_name(name):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_GITHUB_TRENDING_TABLE} WHERE name=?", (name,))
        row = cursor.fetchone()

        # 如果存在数据，则打印
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            doc['last_pushtime'] = try_parse_datetime(doc['last_pushtime'])
            
            return doc
        else:
            return None

def upsert_github_trending(doc):
    table_name = SQL_GITHUB_TRENDING_TABLE
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    placeholders = ', '.join('?' for _ in doc.keys())
    update_fields = ', '.join(f"{key} = excluded.{key}" for key in doc.keys() if key != 'name')

    # 构建动态SQL upsert语句
    sql = f"""
    INSERT INTO {table_name} ({field_names})
    VALUES ({placeholders})
    ON CONFLICT(name) DO UPDATE SET {update_fields};
    """

    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, list(doc.values()))
        conn.commit()

def get_artile_by_url(url):
    # 连接到SQLite数据库
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_DOC_TABLE} WHERE url=?", (url,))
        row = cursor.fetchone()

        # 如果存在数据，则打印
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            return doc
        else:
            return None

def get_arxiv_by_id(entry_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_ARXIV_TABLE} WHERE entry_id=?", (entry_id,))
        row = cursor.fetchone()

        # 如果存在数据，则打印
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            doc['publish_time'] = try_parse_datetime(doc['publish_time'])
            return doc
        else:
            return None
        

def insert_wx_article_to_sql(doc):
    if get_artile_by_url(doc['url']):
        logging.info("Article already exist.")
        return
    table_name = SQL_WEIXIN_DOC_TABLE
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    field_values = ', '.join(':' + key for key in doc.keys())

    # 构建动态SQL插入语句
    sql = f"INSERT INTO {table_name} ({field_names}) VALUES ({field_values})"
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, doc)
        conn.commit()


def get_last_user_pub_push_time(user_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_PUB_PUSH_TABLE} WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        # 如果存在数据，则打印
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                
                doc[column_name[0]] = row[i]
            for k in ['last_push_time']:
                if doc[k]:
                    doc[k] = try_parse_datetime(doc[k])
            return doc['last_push_time']
        else:
            return None

def delete_user_thread(user_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {SQL_THREAD_TABLE} WHERE user_id=?", (user_id,))
        if cursor.rowcount > 0:
            result = True
        else:
            result = False
        conn.commit()
    return result

def get_last_user_thread(user_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_THREAD_TABLE} WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        # 如果存在数据，则打印
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            for k in ['last_update_time']:
                if doc[k]:
                    doc[k] = try_parse_datetime(doc[k])
            return doc
        else:
            return None

def upsert_user_pub_push_time(user_id,last_push_time):

    table_name = SQL_WEIXIN_USER_PUB_PUSH_TABLE
    doc = {'user_id':user_id, 'last_push_time':last_push_time}
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    placeholders = ', '.join('?' for _ in doc.keys())
    update_fields = ', '.join(f"{key} = excluded.{key}" for key in doc.keys() if key != 'user_id')

    # 构建动态SQL upsert语句
    sql = f"""
    INSERT INTO {table_name} ({field_names})
    VALUES ({placeholders})
    ON CONFLICT(user_id) DO UPDATE SET {update_fields};
    """

    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, list(doc.values()))
        conn.commit()

def upsert_user_thread(user_id,thread_id,last_update_time):
    table_name = SQL_THREAD_TABLE
    doc = {'user_id':user_id, 'thread':thread_id, 'last_update_time':last_update_time}
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    placeholders = ', '.join('?' for _ in doc.keys())
    update_fields = ', '.join(f"{key} = excluded.{key}" for key in doc.keys() if key != 'user_id')
    # 构建动态SQL upsert语句
    sql = f"""
    INSERT INTO {table_name} ({field_names})
    VALUES ({placeholders})
    ON CONFLICT(user_id) DO UPDATE SET {update_fields};
    """

    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, list(doc.values()))
        conn.commit()

def get_article_by_pub_id_and_push_time(pub_id,push_time):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_DOC_TABLE} WHERE author_id=? AND publish_time>? AND is_marketing=?",
                        (pub_id,push_time.strftime('%Y-%m-%d %H:%M:%S'),False,))
        rows = cursor.fetchall()

        user_docs = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            try:
                for k in ['publish_time']:
                    if doc[k]:
                        doc[k] = try_parse_datetime(doc[k])
            except Exception as e:
                print(f'parsing error, {doc}, error: {e}')
                continue            
            user_docs.append(doc)
        return sorted(user_docs,key=lambda x:x['publish_time'],reverse=True)
    
def get_user_status(user_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_TABLE} WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            doc['status'] = UserStatus(doc['status'])
            return doc
        else:
            return None
        
def insert_user_status(user_id, status):
    sql = f"INSERT INTO {SQL_WEIXIN_USER_TABLE} (user_id, status) VALUES (?, ?)"
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, status.value))
        conn.commit()

def get_need_push_users():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_TABLE} WHERE need_push=?",(True, ))
        rows = cursor.fetchall()
        user_docs = []
        for row in rows:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            doc['status'] = UserStatus(doc['status'])
            user_docs.append(doc)
        return user_docs

def update_user_push_status(user_id, need_push):
    sql = f"UPDATE {SQL_WEIXIN_USER_TABLE} SET need_push=? WHERE user_id=?"
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (need_push, user_id))
        conn.commit()

def update_user_status(user_id, status):
    sql = f"UPDATE {SQL_WEIXIN_USER_TABLE} SET status=? WHERE user_id=?"
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (status.value, user_id))
        conn.commit()

def get_user_artile_by_url_and_user_id(user_id, url):
    # 连接到SQLite数据库
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_DOC_TABLE} WHERE url=? AND user_id=?", (url,user_id))
        row = cursor.fetchone()

        # 如果存在数据，则打印
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            return doc
        else:
            return None

def get_user_artile_by_title_author_and_user_id(user_id, title, author):
    # 连接到SQLite数据库
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_DOC_TABLE} WHERE title=? AND author=? AND user_id=?", (title,author,user_id))
        row = cursor.fetchone()

        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            return doc
        else:
            return None

def insert_user_article_to_sql(user_id, doc):
    if get_user_artile_by_url_and_user_id(user_id, doc['url']):
        logging.info("Article already exist.")
        return
    sql = f"INSERT INTO {SQL_WEIXIN_USER_DOC_TABLE} (user_id, title, author, url) VALUES (:user_id, :title, :author, :url)"
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, {'user_id':user_id,"title":doc['title'],'author':doc['author'],'url':doc['url']})
        conn.commit()

def get_all_user_articles(user_id):
    # 连接到SQLite数据库
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_DOC_TABLE} WHERE user_id=?", (user_id,))
        rows = cursor.fetchall()

        user_docs = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            user_docs.append(doc)
        return user_docs

def get_latest_user_article(user_id, limit=10):
    # 连接到SQLite数据库
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_DOC_TABLE} WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
        conn.commit()
        rows = cursor.fetchall()
        user_docs = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            user_docs.append(doc)
        return user_docs

def insert_wx_chat_info(sender,receiver,chatroom,message):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        sql = f"INSERT INTO {SQL_WEIXIN_CHAT_TABLE} (sender,receiver,chatroom,content) VALUES (:sender,:receiver,:chatroom,:content)"
        cursor.execute(sql, {'sender':sender,'receiver':receiver,'chatroom':chatroom,'content':message})
        conn.commit()

def get_wx_chat_history_by_timeoffset(sender,chatroom,time_offset='-5 minutes'):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        sql = f"""SELECT * FROM {SQL_WEIXIN_CHAT_TABLE}
            WHERE ((sender = :sender AND receiver = :receiver) OR (sender = :receiver AND receiver = :sender))
            AND chatroom = :chatroom
            AND timestamp >= datetime('now', :time_offset)
            ORDER BY timestamp ASC;
            """
        cursor.execute(sql, {'sender':sender,'receiver':AI_ROLE,'chatroom':chatroom,'time_offset':time_offset})
        rows = cursor.fetchall()
        chat_history = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            chat_history.append(doc)
        return chat_history
    
def get_wx_chat_history_by_count(sender,chatroom,count):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        sql = f"""SELECT * FROM {SQL_WEIXIN_CHAT_TABLE}
            WHERE ((sender = :sender AND receiver = :receiver) OR (sender = :receiver AND receiver = :sender))
            AND chatroom = :chatroom
            ORDER BY timestamp DESC
            LIMIT :count;
            """
        cursor.execute(sql, {'sender':sender,'receiver':AI_ROLE,'chatroom':chatroom,'count':count})
        rows = cursor.fetchall()
        chat_history = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            chat_history.append(doc)
        chat_history = sorted(chat_history,key=lambda x:x['timestamp'])
        return chat_history
    
def insert_token_usage_detail(model, prompt_tokens, completion_tokens, total_tokens, use_case, user):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        sql = f"""INSERT INTO {SQL_TOKEN_USAGE_TABLE} (model, prompt_tokens, completion_tokens, total_tokens, use_case, user)
            VALUES (:model, :prompt_tokens, :completion_tokens, :total_tokens, :use_case, :user) """
        cursor.execute(sql, {'model':model,'prompt_tokens':prompt_tokens,'completion_tokens':completion_tokens,'total_tokens':total_tokens,'use_case':use_case if isinstance(use_case,str) else use_case.value,'user':user})
        conn.commit()

def insert_token_usage(usage, use_case, user):
    insert_token_usage_detail(usage['model'], usage.get('prompt_tokens',0), usage.get('completion_tokens',0), usage.get('total_tokens',0), use_case, user)

def get_total_token_usage_by_time_offset(time_offset='-5 days'):
    '''获取不同模型的整体用量'''
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        sql = f"""SELECT model, SUM(prompt_tokens) AS prompt_tokens_used, SUM(completion_tokens) AS completion_tokens_used, SUM(total_tokens) AS total_tokens_used
                FROM {SQL_TOKEN_USAGE_TABLE}
                WHERE timestamp >= DATETIME('now', '{time_offset}')
                GROUP BY model;"""
        cursor.execute(sql)
        rows = cursor.fetchall()
        dict_results = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            dict_results.append(doc)
        return dict_results

def get_user_token_usage_by_time_offset(user, time_offset='-5 days'):
    '''获取某个用户的用量'''
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        sql = f"""SELECT model, SUM(prompt_tokens) AS prompt_tokens_used, SUM(completion_tokens) AS completion_tokens_used, SUM(total_tokens) AS total_tokens_used
            FROM {SQL_TOKEN_USAGE_TABLE}
            WHERE timestamp >= DATETIME('now', '{time_offset}') AND user = '{user}'
            GROUP BY model"""
        cursor.execute(sql)
        rows = cursor.fetchall()
        dict_results = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            dict_results.append(doc)
        return dict_results
    
def get_total_token_usage_by_user_and_time_offset(time_offset='-5 days'):
    '''按照model 和 user 分组获取token用量'''
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        sql = f"""SELECT user, model, SUM(prompt_tokens) AS prompt_tokens_used, SUM(completion_tokens) AS completion_tokens_used, SUM(total_tokens) AS total_tokens_used
            FROM {SQL_TOKEN_USAGE_TABLE}
            WHERE timestamp >= DATETIME('now', '{time_offset}')
            GROUP BY user, model
            ORDER BY total_tokens_used DESC"""
        cursor.execute(sql)
        rows = cursor.fetchall()
        dict_results = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            dict_results.append(doc)
        return dict_results
    
def get_user_token_usage_by_time_offset_and_case(user='', time_offset='-5 days'):
    '''获取某个用户的分场景的用量'''
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        if user:
            sql = f"""SELECT model, use_case, COUNT(*) as num_of_calls, SUM(prompt_tokens) AS prompt_tokens_used, SUM(completion_tokens) AS completion_tokens_used, SUM(total_tokens) AS total_tokens_used
                FROM {SQL_TOKEN_USAGE_TABLE}
                WHERE timestamp >= DATETIME('now', '{time_offset}') AND user = '{user}'
                GROUP BY model, use_case
                ORDER BY total_tokens_used DESC"""
        else:
            sql = f"""SELECT model, use_case, COUNT(*) as num_of_calls, SUM(prompt_tokens) AS prompt_tokens_used, SUM(completion_tokens) AS completion_tokens_used, SUM(total_tokens) AS total_tokens_used
                FROM {SQL_TOKEN_USAGE_TABLE}
                WHERE timestamp >= DATETIME('now', '{time_offset}')
                GROUP BY model, use_case
                ORDER BY total_tokens_used DESC"""
        cursor.execute(sql)
        rows = cursor.fetchall()
        dict_results = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            dict_results.append(doc)
        return dict_results
    
def insert_prompt(inputs, outputs):
    with sqlite3.connect(SQL_PROMPT_DB_NAME) as conn:
        cursor = conn.cursor()
        sql = f"""INSERT INTO {SQL_PROMPT_TABLE} (inputs, outputs) VALUES (?, ?)"""
        cursor.execute(sql, (json.dumps(inputs,ensure_ascii=False), json.dumps(outputs,ensure_ascii=False)))
        conn.commit()

def insert_friend_request(encryptusername, fromusername, fromnickname, scene, ticket):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""INSERT INTO {SQL_WX_FRIEND_REQUEST_TABLE} (encryptusername, fromusername, fromnickname, scene, ticket)
            VALUES (?, ?, ?, ?, ?)""",
            (
                encryptusername,
                fromusername,
                fromnickname,
                scene,
                ticket,
            ),
        )
        conn.commit()

def accept_friend_request(fromusername):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""SELECT * FROM {SQL_WX_FRIEND_REQUEST_TABLE} WHERE fromusername = ? ORDER BY request_time DESC""",
            (fromusername,),
        )
        conn.commit()
        item = c.fetchone()
        if item is None:
            return None
        doc = {column[0]: value for column, value in zip(c.description, item)}
        return doc

def get_attend_status():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""SELECT * FROM {SQL_ATTEND_STATUS_TABLE} WHERE status = ?""",
            (AttendStatus.OPEN.value,))
        conn.commit()
        rows = c.fetchall()
        docs = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(c.description, row)}
            doc['status'] = AttendStatus(doc['status'])
            docs.append(doc)
        return docs
    
def get_attend_status_by_user(user, room):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""SELECT * FROM {SQL_ATTEND_STATUS_TABLE} WHERE user = ? AND room = ?""",
            (user, room,),
        )
        conn.commit()
        rows = c.fetchone()
        if rows is None:
            return None
        doc = {column[0]: value for column, value in zip(c.description, rows)}
        doc['status'] = AttendStatus(doc['status'])
        return doc

def insert_attend_status(user, room, status):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""INSERT INTO {SQL_ATTEND_STATUS_TABLE} (user, room, status) VALUES (?,?,?)""",
            (user, room, status.value,),
        )
        conn.commit()

def update_attend_status(user, room, status):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""UPDATE {SQL_ATTEND_STATUS_TABLE} SET status = ? WHERE user = ? AND room = ?""",
            (status.value, user, room,),
        )
        conn.commit()


def get_attend_info_of_now(user_id, room):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""SELECT * FROM {SQL_ATTEND_TABLE} WHERE user = ? AND room = ? AND DATE(attend_time) == DATE('now')""",
            (user_id,room,),
        )
        conn.commit()
        item = c.fetchone()
        if item is None:
            return None
        doc = {column[0]: value for column, value in zip(c.description, item)}
        # 将时间转换为datetime
        for k in ['on_time', 'off_time', 'last_remind_time']:
            if doc[k]:
                doc[k] = try_parse_datetime(doc[k])
        return doc

def get_push_info_of_now(source):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""SELECT * FROM {SQL_PUSH_INFO_TABLE} WHERE source = ? AND DATE(create_time) == DATE('now')""",
            (source,),
        )
        conn.commit()
        item = c.fetchone()
        if item is None:
            return None
        doc = {column[0]: value for column, value in zip(c.description, item)}
        return doc
    
def get_push_info_lastest(source):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""SELECT * FROM {SQL_PUSH_INFO_TABLE} WHERE source = ? ORDER BY create_time DESC LIMIT 1""",
            (source,),
        )
        conn.commit()
        items = c.fetchall()
        docs = [{column[0]: value for column, value in zip(c.description, item)} for item in items]
        return docs[0]
    
def insert_push_info(source, content):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""INSERT INTO {SQL_PUSH_INFO_TABLE} (html, source, create_time)
            VALUES (?, ?, datetime('now', 'localtime'))""",
            (content,source),
        )
        conn.commit()

def create_attend_info(user_id, room):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""INSERT INTO {SQL_ATTEND_TABLE} (user, room, on_time, off_time, remind, last_remind_time)
            VALUES (?, ?, NULL, NULL, 1, NULL)""",
            (user_id,room,),
        )
        conn.commit()

def update_attend_info(user_id, room, attend_info):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""UPDATE {SQL_ATTEND_TABLE} SET on_time = ?, off_time = ?, remind = ?, last_remind_time = ?
            WHERE user = ? AND room =?""",
            (attend_info['on_time'], attend_info['off_time'], attend_info['remind'], attend_info['last_remind_time'], user_id, room),
        )
        conn.commit()

def check_user_pub_exist(user_id, pub_id):
    # 连接到SQLite数据库
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()

        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_PUB_TABLE} WHERE user_id=? AND pub_id=?", (user_id, pub_id))
        row = cursor.fetchone()

        # 如果存在数据，则返回
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            return doc
        else:
            return None
        
def add_user_pub_info(user_id, pub_id, pub_name=''):
    if check_user_pub_exist(user_id, pub_id) is not None:
        return
    with sqlite3.connect(SQL_DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            f"""INSERT INTO {SQL_WEIXIN_USER_PUB_TABLE} (user_id, pub_id, pub_name)
            VALUES (?, ?, ?)""",
            (user_id, pub_id, pub_name,),
        )
        conn.commit()

def get_all_pub_infos():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT pub_id, pub_name FROM {SQL_WEIXIN_USER_PUB_TABLE}")
        rows = cursor.fetchall()
        pub_docs = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            pub_docs.append(doc)
        
        return {doc['pub_id']:doc for doc in pub_docs}

def insert_kimi_arxiv_data(doc):
    if get_kimi_arxiv_data_by_link(doc['link']):
        logging.info("link data already exist.")
        return
    table_name = SQL_KIMI_ARXIV_TABLE
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    field_values = ', '.join(':' + key for key in doc.keys())

    # 构建动态SQL插入语句
    sql = f"INSERT INTO {table_name} ({field_names}) VALUES ({field_values})"
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, doc)
        conn.commit()

def get_kimi_arxiv_data_by_link(link):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_KIMI_ARXIV_TABLE} WHERE link=?", (link,))
        row = cursor.fetchone()
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            return doc
        else:
            return None  

def delete_user_pub_by_name(user_id, pub_name):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {SQL_WEIXIN_USER_PUB_TABLE} WHERE user_id=? AND pub_name=?", (user_id, pub_name))
        if cursor.rowcount > 0:
            result = True
        else:
            result = False
        conn.commit()
    return result

def get_user_by_pub_id(pub_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT user_id FROM {SQL_WEIXIN_USER_PUB_TABLE} WHERE pub_id=?", (pub_id,))
        rows = cursor.fetchall()
        user_docs = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            user_docs.append(doc)
        return {doc['user_id'] for doc in user_docs}

def get_user_all_pub_id(user_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_PUB_TABLE} WHERE user_id=?", (user_id,))
        rows = cursor.fetchall()
        user_docs = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            user_docs.append(doc)
        return {doc['pub_id']:doc for doc in user_docs}

def get_pub_config(user_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_PUB_CONFIG_TABLE} WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            return doc
        else:
            return None

def get_user_subscription_info(user_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_USER_SUBSCRIPTION_TABLE} WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            return doc
        else:
            return None

def get_all_user_subscription_info():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_USER_SUBSCRIPTION_TABLE}")
        rows = cursor.fetchall()
        user_docs = []
        for row in rows:
            doc = {column[0]: value for column, value in zip(cursor.description, row)}
            user_docs.append(doc)
        return user_docs

def upsert_user_subscription_config(user_id, email, keywords, push_time, sources):
    table_name = SQL_USER_SUBSCRIPTION_TABLE
    doc = {'user_id':user_id, 'keywords':keywords, 'push_time':push_time, "email":email, "sources":sources}
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    placeholders = ', '.join('?' for _ in doc.keys())
    update_fields = ', '.join(f"{key} = excluded.{key}" for key in doc.keys() if key != 'user_id')
    # 构建动态SQL upsert语句
    sql = f"""
    INSERT INTO {table_name} ({field_names})
    VALUES ({placeholders})
    ON CONFLICT(user_id) DO UPDATE SET {update_fields};
    """

    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, list(doc.values()))
        conn.commit()

def get_all_pub_config():
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL_WEIXIN_USER_PUB_CONFIG_TABLE}")
        rows = cursor.fetchall()
        user_docs = []
        for row in rows:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            user_docs.append(doc)
        return user_docs

def upsert_pub_config(user_id, keywords, push_time):
    table_name = SQL_WEIXIN_USER_PUB_CONFIG_TABLE
    doc = {'user_id':user_id, 'keywords':keywords, 'push_time':push_time}
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    placeholders = ', '.join('?' for _ in doc.keys())
    update_fields = ', '.join(f"{key} = excluded.{key}" for key in doc.keys() if key != 'user_id')
    # 构建动态SQL upsert语句
    sql = f"""
    INSERT INTO {table_name} ({field_names})
    VALUES ({placeholders})
    ON CONFLICT(user_id) DO UPDATE SET {update_fields};
    """

    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, list(doc.values()))
        conn.commit()

def get_last_user_kimi_token(user_id):
    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        # 执行SELECT语句以检查表中是否存在具有特定URL的数据
        cursor.execute(f"SELECT * FROM {SQL_KIMI_TOKEN_TABLE} WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        # 如果存在数据，则打印
        if row is not None:
            doc = {}
            for i, column_name in enumerate(cursor.description):
                doc[column_name[0]] = row[i]
            for k in ['last_update_time']:
                if doc[k]:
                    doc[k] = try_parse_datetime(doc[k])
            return doc
        else:
            return None

def upsert_user_kimi_token(user_id,access_token, refresh_token,last_update_time):
    table_name = SQL_KIMI_TOKEN_TABLE
    doc = {'user_id':user_id, 'access_token':access_token, 'refresh_token':refresh_token, 'last_update_time':last_update_time}
    # 提取 doc 字典中的字段名和对应的值
    field_names = ', '.join(doc.keys())
    placeholders = ', '.join('?' for _ in doc.keys())
    update_fields = ', '.join(f"{key} = excluded.{key}" for key in doc.keys() if key != 'user_id')
    # 构建动态SQL upsert语句
    sql = f"""
    INSERT INTO {table_name} ({field_names})
    VALUES ({placeholders})
    ON CONFLICT(user_id) DO UPDATE SET {update_fields};
    """

    with sqlite3.connect(SQL_DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, list(doc.values()))
        conn.commit()

if __name__ == '__main__':
    a = get_need_push_users()
    print(a)
