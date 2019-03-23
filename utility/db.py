
import motor.motor_asyncio
import discord


class KoyomiDB:

    def __init__(self):
        self._client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
        self._db = self._client.koyomibot
        self._guild_collection = self._db.guild_collection
        self._user_collection = self._db.user_collection

    async def close(self):
        self.redis.close()
        self._client.close()
        await self.redis.wait_closed()

    async def initialize_redis(self):
        self.redis = await aioredis.create_pool('redis://localhost')

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
                await self._guild_collection.insert_one(result)

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
                await self._user_collection.insert_one(result)

        return result

    async def get_guild_prefixes(self, guild: discord.Guild) -> list:
        return list((await self.get_guild_info(guild))['prefix'])

    async def check_guild_blacklist(self, guild: discord.Guild) -> bool:
        return not (await self.get_guild_info(guild))['ignore']

    async def check_user_blacklist(self, user: discord.User) -> bool:
        return not (await self.get_user_info(user))['ignore']
