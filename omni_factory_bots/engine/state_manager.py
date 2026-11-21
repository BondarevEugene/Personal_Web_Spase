# engine/state_manager.py
import aioredis
import json

class StateManager:
    def __init__(self, redis_url="redis://localhost"):
        self.redis = None

    async def connect(self):
        self.redis = await aioredis.from_url("redis://localhost", decode_responses=True)

    async def set_state(self, user_id, bot_id, node_id, data=None):
        """Сохраняет текущий узел бота для юзера."""
        state = {"node_id": node_id, "data": data or {}}
        await self.redis.set(f"bot:{bot_id}:user:{user_id}", json.dumps(state))

    async def get_state(self, user_id, bot_id):
        """Возвращает, где сейчас находится юзер."""
        val = await self.redis.get(f"bot:{bot_id}:user:{user_id}")
        return json.loads(val) if val else {"node_id": "start", "data": {}}
