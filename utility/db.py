
from typing import Tuple

import aioredis
import discord
import motor.motor_asyncio


class KoyomiDB:

    def __init__(self) -> None:
        self._client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
        self._db = self._client.koyomibot
        self._guild_collection = self._db.guild_collection
        self._user_collection = self._db.user_collection

    async def close(self) -> None:
        self.redis.close()
        self._client.close()
        await self.redis.wait_closed()

    async def initialize_redis(self) -> None:
        self.redis = await aioredis.create_redis_pool('redis://localhost')

    async def _reset_guild_cache(self, guild_id: int) -> None:
        self.redis.delete(f"{guild_id}_prefix", f"{guild_id}_ignore")

    async def get_guild_info(self, guild: discord.Guild) -> dict:

        result = await self._guild_collection.find_one({'id': guild.id})
        if result is None:
            # Create new Guild Object
            result = {
                'id': guild.id,
                'name': guild.name,
                'prefix': [],
                'ignore': False,
            }
            await self._guild_collection.insert_one(result)
        else:
            if guild.name != result['name']:
                result['name'] = guild.name
                await self._guild_collection.replace_one({'id': guild.id}, {'name': guild.name})

        # Set the Cache
        if result['prefix']:
            self.redis.rpush(f"{guild.id}_prefix", *result['prefix'])
        self.redis.set(f"{guild.id}_ignore", result['ignore'])

        return result

    async def get_user_info(self, user: discord.User) -> dict:
        full_name = user.name + "#" + user.discriminator

        result = await self._user_collection.find_one({'id': user.id})
        if result is None:
            result = {
                'id': user.id,
                'msg_cd': 0,
                'poke_cd': 0,
                'xp': 0,
                'name': full_name,
                'coins': 30,
                'level': 1,
                'pokes_given': 0,
                'pokes_received': 0,
                'description': 'Kamimashita',
                'ignore': False,
            }
            await self._user_collection.insert_one(result)
        else:
            if full_name != result['name']:
                result['name'] = full_name
                await self._user_collection.replace_one({'id': user.id}, {'name': result})

        return result

    async def get_guild_prefixes(self, guild: discord.Guild) -> list:
        cache = await self.redis.lrange(f"{guild.id}_prefix", 0, 9)
        return cache if cache else list((await self.get_guild_info(guild))['prefix'])

    async def set_guild_prefixes(self, guild: discord.Guild, prefix: str) -> Tuple[bool, str]:
        if len(prefix) > 10:
            return False, "Prefix is too long."
        existing_guild_prefixes = await self.get_guild_prefixes(guild)
        if len(existing_guild_prefixes) > 10:
            return False, "10 Prefixes are already set, delete one before."

        if prefix in existing_guild_prefixes or prefix in ['!>', '>']:
            return False, "This prefix already exists."

        existing_guild_prefixes.append(prefix)

        await self._guild_collection.replace_one({'id': guild.id}, {'prefix', existing_guild_prefixes})
        await self.redis.delete(f"{guild.id}_prefix")
        return True, f"Added Prefix {prefix}"

    async def remove_guild_prefixes(self, guild: discord.Guild, prefix: str) -> bool:
        if len(prefix) > 10:
            return False
        existing_guild_prefixes = await self.get_guild_prefixes(guild)
        if len(existing_guild_prefixes) == 0:
            return False
        try:
            existing_guild_prefixes.remove(prefix)
        except ValueError:
            return False

        await self._guild_collection.replace_one({'id': guild.id}, {'prefix', existing_guild_prefixes})
        await self.redis.delete(f"{guild.id}_prefix")
        return True

    async def check_guild_blacklist(self, guild: discord.Guild) -> bool:
        return not (await self.get_guild_info(guild))['ignore']

    async def check_user_blacklist(self, user: discord.User) -> bool:
        return not (await self.get_user_info(user))['ignore']


