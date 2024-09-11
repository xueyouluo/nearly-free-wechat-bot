import sqlite3
import uuid
import chromadb
from chromadb import  EmbeddingFunction, Embeddings
from database.database_config import VECTOR_DB_PATH
from utils.llm import get_zhipuai_embedding
from utils.nlp import split_doc_content_to_chunks

client = chromadb.PersistentClient(path=VECTOR_DB_PATH)


class OpenAIEmbeddingFunction(EmbeddingFunction):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.embedding_fn = get_zhipuai_embedding

    def __call__(self, input) -> Embeddings:
        # embed the documents somehow
        embeddings = []
        for text in input:
            embeddings.append(self.embedding_fn(text))
        return embeddings


def get_or_create_wx_article_vector_db(user_id):
    if user_id.endswith('@chatroom'):
        user = user_id[:-9]
    else:
        user = user_id
    collection = client.get_or_create_collection(
        name=user, 
        metadata={"hnsw:space": "ip"},
        embedding_function=OpenAIEmbeddingFunction(user_id)) # Get a collection object from an existing collection, by name. If it doesn't exist, create it.
    return collection
    
def insert_wx_article_chunks_to_vector_db(user_id, doc):
    collection = get_or_create_wx_article_vector_db('zhipu_' + user_id)
    
    # check exist
    ret = collection.get(
        where={"url":doc['url']},
        limit=1
    )
    if ret['ids']:
        return
    
    # split to chunks and save to db
    chunks = split_doc_content_to_chunks(doc)
    for chunk in chunks:
        document = ' '.join(chunk)
        # 内容太少不入库
        if len(document) < 10:
            continue
        metadata = {"url": doc['url'], "title": doc['title'], "author": doc['author']}
        _id = uuid.uuid1()
        collection.add(ids=str(_id), documents=document, metadatas=metadata)
