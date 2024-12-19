# app/chat_history/chat_history_manager.py
import time
import json
import asyncio
import aiohttp
from app.storage.redis_manager import RedisManager
from abc import ABC, abstractmethod
from app.storage.milvus_manager import MilvusManager
from app.prompts.prompts import create_memory_update_prompt
from app.utils.helpers import async_retry
from aiohttp_socks import ProxyConnector
from app.core.config import settings
from app.core.logger import async_app_logger, async_error_logger


class ChatHistoryStorageBase(ABC):
    @abstractmethod
    async def get_recent_chat(self, user_id, character_id):
        pass

    @abstractmethod
    async def put_recent_chat(self, user_id, character_id, data, max_records):
        pass

    @abstractmethod
    async def get_long_memory_chat(self, user_id, character_id, question, k, score_threshold):
        pass

    @abstractmethod
    async def rm_long_memory_chat(self, user_id, character_id):
        pass

    @abstractmethod
    async def rm_recent_chat(self, user_id, character_id):
        pass

    @abstractmethod
    async def update_important_memories(self, user_id, character_id, character_name, base_prompt, recent_chat_history,
                                        social_network, long_chat_history, question, response_text):
        pass

    @abstractmethod
    async def get_important_memories(self, user_id, character_id):
        pass

    @abstractmethod
    async def rm_importance_memories(self, user_id, character_id):
        pass


class RemoteDBChatHistoryStorage(ChatHistoryStorageBase):
    def __init__(self, redis_manager: RedisManager, milvus_manager: MilvusManager, max_records: int = 14):
        self.max_records = max_records
        self.redis_manager = redis_manager
        self.milvus_manager = milvus_manager

    async def get_recent_chat(self, user_id, character_id):
        key = f"tw_recent_data_{user_id}_{character_id}"
        data = await self.redis_manager.get(key)

        if data:
            data = json.loads(data)
            chat_history = data["chat_history"]
            recent_messages = chat_history[-self.max_records:]
            recent_chat = []
            for msg in recent_messages:
                recent_chat.append(
                    (msg['timestamp'], msg['role'], msg['content']))
            data["chat_history"] = recent_chat
            return data
        else:
            return None

    async def put_recent_chat(self, user_id, character_id, data,max_records=14):
        self.max_records = max_records
        chat_history = data["chat_history"]
        key = f"tw_recent_data_{user_id}_{character_id}"
        old_data = await self.redis_manager.get(key)
        if old_data:
            old_data = json.loads(old_data)
            messages = old_data["chat_history"]
            new_messages = [{'timestamp': t, 'role': r, 'content': c} for
                            t, r, c in chat_history]
            messages.extend(new_messages)
            if len(messages) > self.max_records:
                messages = messages[-self.max_records:]
        else:
            messages = [{'timestamp': t, 'role': r, 'content': c} for
                        t, r, c in chat_history]

        data["chat_history"] = messages
        await self.redis_manager.set(key, json.dumps(data))

        texts = f"\n".join(
            f"chat_time:{t}, role:{r}, content:{c}" for t, r, c in
            chat_history)
        # 插入永久记忆
        await self.milvus_manager.save_chat(user_id, character_id, texts)

    async def get_long_memory_chat(self, user_id, character_id, question, k=3, score_threshold=0.6):
        return await self.milvus_manager.search_chats(user_id, character_id, question, k=k,
                                                      score_threshold=score_threshold)

    async def rm_recent_chat(self, user_id, character_id):
        key = f"tw_recent_data_{user_id}_{character_id}"
        await self.redis_manager.delete(key)

    async def rm_long_memory_chat(self, user_id, character_id):
        await self.milvus_manager.delete_chat_collection(user_id, character_id)

    async def update_important_memories(self, user_id, character_id, character_name, base_prompt, recent_chat_history,
                                        social_network, long_chat_history, question, response_text):

        key = f"tw_important_memories_{user_id}_{character_id}"

        existing_memories = await self.redis_manager.get(key)
        if existing_memories:
            sys_prompt, user_prompt = create_memory_update_prompt(existing_memories, character_name, base_prompt,
                                                                  recent_chat_history,
                                                                  social_network, long_chat_history, question,
                                                                  response_text)
        else:
            sys_prompt, user_prompt = create_memory_update_prompt("None", character_name, base_prompt,
                                                                  recent_chat_history,
                                                                  social_network, long_chat_history, question,
                                                                  response_text)
        openai_apikey = settings.EMBEDDING_OPENAI_APIKEY
        model = "gpt-4o-mini"
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
        try:
            json_res = await llm_update_memories(openai_apikey, model, messages)
            response_text = json_res['choices'][0]['message']['content']
            new_memories_json = json.loads(response_text)
            new_memories = new_memories_json.get("updated_important_memories", existing_memories)
            async_app_logger.info(
                f"user_id:{user_id},character_id:{character_id},Updated important memories: {new_memories}")
        except Exception as e:
            await async_error_logger.error(f"Error in updating important memories: {str(e)}")
            new_memories = existing_memories
        await self.redis_manager.set(key, str(new_memories))

    async def get_important_memories(self, user_id, character_id):
        key = f"tw_important_memories_{user_id}_{character_id}"
        return await self.redis_manager.get(key)

    async def rm_importance_memories(self, user_id, character_id):
        key = f"tw_important_memories_{user_id}_{character_id}"
        await self.redis_manager.delete(key)


class ChatHistory:
    def __init__(self, redis_manager: RedisManager, milvus_manager: MilvusManager):
        self.storage = RemoteDBChatHistoryStorage(redis_manager, milvus_manager)

    async def get_recent_chat(self, user_id, character_id):
        return await self.storage.get_recent_chat(user_id, character_id)

    async def put_recent_chat(self, user_id, character_id, data, max_records):
        await self.storage.put_recent_chat(user_id, character_id, data, max_records)

    async def get_long_memory_chat(self, user_id, character_id, question, k, score_threshold):
        return await self.storage.get_long_memory_chat(user_id, character_id, question, k, score_threshold)

    async def rm_recent_chat(self, user_id, character_id):
        await self.storage.rm_recent_chat(user_id, character_id)

    async def rm_long_memory_chat(self, user_id, character_id):
        await self.storage.rm_long_memory_chat(user_id, character_id)

    async def update_important_memories(self, user_id, character_id, character_name, base_prompt,
                                        recent_chat_history, social_network,
                                        long_chat_history, question, response_text):
        await self.storage.update_important_memories(user_id, character_id, character_name, base_prompt,
                                                     recent_chat_history, social_network,
                                                     long_chat_history, question, response_text)

    async def get_important_memories(self, user_id, character_id):
        return await self.storage.get_important_memories(user_id, character_id)

    async def rm_importance_memories(self, user_id, character_id):
        await self.storage.rm_importance_memories(user_id, character_id)


@async_retry(retries=3, delay=1)
async def llm_update_memories(openai_apikey, model, messages, temperature=0, max_tokens=4000, response_format=None):
    if response_format is None:
        response_format = {"type": "json_object"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_apikey}"
    }

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    if response_format:
        data["response_format"] = response_format

    base_url = "https://api.openai.com/v1/chat/completions"

    try:
        connector = ProxyConnector.from_url(settings.PROXY_URL) if settings.IS_USE_PROXY else None

        async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=40)) as session:
            async with session.post(base_url, headers=headers, json=data, timeout=30) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_content = await response.text()
                    error_msg = f"Error in API call: Status {response.status}, Content: {error_content}"
                    await async_error_logger.error(error_msg)
                    raise Exception(error_msg)
    except asyncio.TimeoutError:
        await async_error_logger.error("Request timed out")
        raise
    except aiohttp.ClientError as e:
        await async_error_logger.error(f"aiohttp client error: {str(e)}")
        raise
    except Exception as e:
        await async_error_logger.exception(f"Error in API call: {str(e)}")
        raise
