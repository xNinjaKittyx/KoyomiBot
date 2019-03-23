import asyncio
import logging

import dbl
import discord
import rapidjson

from discord.ext import commands


log = logging.getLogger(__name__)


class DiscordBotUpdates(commands.Cog):

    def __init__(self, bot: discord.Client):
        self.bot = bot
        self._token = self.bot.key_config.DiscordAPIToken
        self._dblclient = dbl.Client(self.bot, self._token)
        self.bot.loop.create_task(self.update_stats())

    async def update_stats(self) -> None:

        while True:
            log.info('Posting Server Count to DiscordBots.org')
            try:
                await self._dblclient.post_server_count()
                log.info('Server Count Success to DiscordBots.org!')
            except Exception as e:
                log.exception('Failed to post server count\n{}: {}'.format(type(e).__name__, e))
            await asyncio.sleep(1800)

            async with self.bot.session.post(
                f'https://discord.bots.gg/api/v1/{self.bot.user.id}/guilds',
                headers={
                    'Authorization': self.bot.key_config.DiscordAPIToken,
                    'Content-Type': 'application/json'
                },
                data=rapidjson.dumps({
                    'shard_id': self.bot.shard_id,
                    'shard_count': self.bot.shard_count,
                    'server_count': len(self.bot.guilds)
                })
            ) as f:
                if f.status != 204:
                    log.error(f'Failed to post server count bots.ondiscord.xyz: {f.text}')
                    log.error(await f.json(loads=rapidjson.loads))
                else:
                    log.error('SUCCESS!')


def setup(bot: discord.Client):
    bot.add_cog(DiscordBotUpdates(bot))
