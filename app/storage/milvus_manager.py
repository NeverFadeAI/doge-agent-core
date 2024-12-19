import json
from typing import Dict, List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.milvus import Milvus
from langchain_text_splitters import CharacterTextSplitter
from app.core.logger import app_logger, async_error_logger, async_app_logger
import asyncio
from app.core.config import settings
from app.storage.redis_manager import RedisManager
from concurrent.futures import ThreadPoolExecutor


class MilvusManager:
    def __init__(self, connection_args: Dict, embedding_api_key: str, redis: RedisManager, max_workers: int = 10):
        self.connection_args = connection_args
        client = settings.PROXY_HTTP_CLIENT if settings.IS_USE_PROXY else None
        self.embeddings = OpenAIEmbeddings(openai_api_key=embedding_api_key, http_client=client)
        self.redis = redis
        self.local_dict: Dict[str, Milvus] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    async def create_or_update_milvus(self, collection_name: str, texts: List[str] = None,
                                      drop_old: bool = False):
        if collection_name in self.local_dict:
            if not drop_old:
                await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool, self.local_dict[collection_name].add_texts, texts
                )
            else:
                await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool, self.local_dict[collection_name].col.drop
                )
                self.local_dict[collection_name] = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: Milvus.from_texts(
                        texts=texts,
                        embedding=self.embeddings,
                        collection_name=collection_name,
                        connection_args=self.connection_args
                    )
                )
                await self.redis.set(collection_name, "1")
        else:
            redis_exists = await self.redis.get(collection_name)
            if redis_exists is None:
                self.local_dict[collection_name] = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: Milvus.from_texts(
                        texts=texts,
                        embedding=self.embeddings,
                        collection_name=collection_name,
                        connection_args=self.connection_args
                    )
                )
                await self.redis.set(collection_name, "1")
            else:
                self.local_dict[collection_name] = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: Milvus.from_texts(
                        texts=texts,
                        embedding=self.embeddings,
                        collection_name=collection_name,
                        connection_args=self.connection_args
                    )
                )

    async def get_or_create_milvus(self, collection_name: str) -> Optional[Milvus]:
        if collection_name in self.local_dict:
            return self.local_dict[collection_name]
        else:
            redis_exists = await self.redis.get(collection_name)
            if redis_exists is not None:
                self.local_dict[collection_name] = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: Milvus.from_texts(
                        texts=["None"],
                        embedding=self.embeddings,
                        collection_name=collection_name,
                        connection_args=self.connection_args
                    )
                )
                return self.local_dict[collection_name]
            else:
                return None

    async def save_chat(self, user_id: str, character_id: str, chat_history: str, drop_old=False) -> int:
        collection_name = f"chat_history_uid_{user_id}_cid_{character_id}"

        text_splitter = CharacterTextSplitter(chunk_size=400, chunk_overlap=0)
        docs = text_splitter.split_text(chat_history)
        await self.create_or_update_milvus(collection_name, docs, drop_old)

        await async_app_logger.info(f"Collection {collection_name} saved")
        return len(docs)

    async def save_social(self, character_id: str, content: Dict, drop_old=True) -> int:
        collection_name = f"character_social_cid_{character_id}"

        docs = []
        for key, value in content.items():
            sub_content = json.dumps({key: value}, ensure_ascii=False)
            text_splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=0)
            sub_docs = text_splitter.split_text(sub_content)
            docs += sub_docs

        await self.create_or_update_milvus(collection_name, docs, drop_old)

        await async_app_logger.info(f"Collection {collection_name} saved")
        return len(docs)

    async def search_chats(self, user_id: str, character_id: str, question: str, k=3, score_threshold=0.6) -> List:
        collection_name = f"chat_history_uid_{user_id}_cid_{character_id}"

        milvus = await self.get_or_create_milvus(collection_name)
        if milvus is None:
            await async_app_logger.info(f"Collection {collection_name} not found")
            return []

        result_docs = await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            milvus.similarity_search_with_score,
            question,
            k
        )

        result_texts = [doc[0].page_content for doc in result_docs if float(doc[1]) < (1 - score_threshold)]
        print(f"搜到的角色相关long chat信息：{result_texts}")
        return result_texts

    async def search_social(self, character_id: str, question: str, k=3, score_threshold=0.6) -> List:
        collection_name = f"character_social_cid_{character_id}"

        milvus = await self.get_or_create_milvus(collection_name)
        if milvus is None:
            await async_app_logger.info(f"Collection {collection_name} not found")
            return []

        result_docs = await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            milvus.similarity_search_with_score,
            question,
            k
        )

        result_texts = [doc[0].page_content for doc in result_docs if float(doc[1]) < (1 - score_threshold)]
        print(f"搜到的角色相关social信息：{result_texts}")
        return result_texts

    # async def save_crypto_currency_map(self, collection_name: str, texts: List[str] = None,
    #                                    drop_old: bool = False):
    #     """
    #     保存加密货币数据到Milvus
    #
    #     :param collection_name: Milvus集合名称
    #     :param texts: 要保存的文本列表
    #     :param drop_old: 是否删除旧数据
    #     """
    #     await self.create_or_update_milvus(collection_name, texts, drop_old)
    #     await async_app_logger.info(f"Crypto currency map saved to collection {collection_name}")
    #
    # async def get_crypto_currency_map(self, question: str, collection_name: str, k=3, score_threshold=0.6) -> List[
    #     Dict]:
    #     """
    #     从Milvus中获取与问题最相关的加密货币数据
    #
    #     :param question: 查询问题
    #     :param collection_name: Milvus集合名称
    #     :param k: 返回结果数量
    #     :param score_threshold: 相似度阈值
    #     :return: 相关的加密货币数据列表
    #     """
    #     milvus = await self.get_or_create_milvus(collection_name)
    #     if milvus is None:
    #         await async_app_logger.info(f"Collection {collection_name} not found")
    #         return []
    #
    #     result_docs = await asyncio.get_event_loop().run_in_executor(
    #         self.thread_pool,
    #         milvus.similarity_search_with_score,
    #         question,
    #         k
    #     )
    #
    #     result_texts = [doc[0].page_content for doc in result_docs if float(doc[1]) < (1 - score_threshold)]
    #     result_dicts = [json.loads(text) for text in result_texts]
    #
    #     await async_app_logger.info(f"Found {len(result_dicts)} relevant crypto currency data")
    #     return result_dicts

    async def delete_collection(self, collection_name: str):
        await async_app_logger.info(f"Deleting collection {collection_name}")

        if collection_name in self.local_dict:
            try:
                milvus = self.local_dict[collection_name]
                await asyncio.get_event_loop().run_in_executor(self.thread_pool, milvus.col.drop)
                del self.local_dict[collection_name]
                await self.redis.delete(collection_name)
                await async_app_logger.info(f"Collection {collection_name} deleted")
            except Exception as e:
                await async_error_logger.error(f"Failed to delete collection {collection_name}: {e}")
        else:
            try:
                redis_exists = await self.redis.get(collection_name)
                if redis_exists is not None:
                    await self.redis.delete(collection_name)
                    self.local_dict[collection_name] = await asyncio.get_event_loop().run_in_executor(
                        self.thread_pool,
                        Milvus.from_texts,
                        ["None"],
                        self.embeddings,
                        collection_name,
                        self.connection_args,
                        True
                    )

                    milvus = self.local_dict[collection_name]
                    await asyncio.get_event_loop().run_in_executor(self.thread_pool, milvus.col.drop)
                    del self.local_dict[collection_name]
                    await self.redis.delete(collection_name)
                    await async_app_logger.info(f"Collection {collection_name} deleted")
            except Exception as e:
                await async_error_logger.error(f"Failed to delete collection {collection_name}: {e}")
                raise

    async def delete_chat_collection(self, user_id: str, character_id: str):
        collection_name = f"chat_history_uid_{user_id}_cid_{character_id}"
        await self.delete_collection(collection_name)

    async def delete_social_collection(self, character_id: str):
        collection_name = f"character_social_cid_{character_id}"
        await self.delete_collection(collection_name)

    async def close(self):
        self.local_dict.clear()
        self.thread_pool.shutdown(wait=True)


async def setup_milvus(embedding_api_key: str, redis: RedisManager, max_workers: int = 50, **connection_args):
    milvus_manager = MilvusManager(connection_args, embedding_api_key, redis, max_workers)
    app_logger.info("Milvus setup completed")
    return milvus_manager


async def close_milvus(app):
    if hasattr(app.state, 'milvus_manager'):
        await app.state.milvus_manager.close()
    await async_app_logger.info("Milvus connections closed")
