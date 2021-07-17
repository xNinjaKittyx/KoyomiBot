import asyncio
import logging

import rapidjson as json
from discord.ext import commands

from koyomibot.main import MyClient

log = logging.getLogger(__name__)


class DiscordBotUpdates(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot
        self.bot.loop.create_task(self.update_stats())

    async def update_stats(self) -> None:

        while True:
            while self.bot.user is None:
                await asyncio.sleep(1)

            log.info("Posting Server Count to DiscordBots.org")
            async with self.bot.session.post(
                f"https://discordbots.org/api/bots/{self.bot.user.id}/stats",
                headers={
                    "Authorization": self.bot.key_config.DiscordBots,
                    "Content-Type": "application/json",
                },
                data=json.dumps(
                    {
                        "shard_id": self.bot.shard_id,
                        "shard_count": self.bot.shard_count,
                        "server_count": len(self.bot.guilds),
                    }
                ),
            ) as f:
                if f.status >= 300 or f.status < 200:
                    log.error(f"Failed to post server count discordbots.org: {f.text}")
                else:
                    log.info("SUCCESS!")

            # log.info('Posting Server Count to discord.bots.gg')
            # if self.bot.shard_id:
            #     data = {
            #         'shardId': self.bot.shard_id,
            #         'shardCount': self.bot.shard_count,
            #         'guildCount': len(self.bot.guilds)
            #     }
            # else:
            #     data = {
            #         'guildCount': len(self.bot.guilds)
            #     }

            # async with self.bot.session.post(
            #     f'https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats',
            #     headers={
            #         'Authorization': self.bot.key_config.DiscordBotsGG,
            #         'Content-Type': 'application/json'
            #     },
            #     data=json.dumps(data)
            # ) as f:
            #     if f.status >= 300 or f.status < 200:
            #         log.error(f'Failed to post server count discord.bots.gg: {f.text}')
            #     else:
            #         log.error('SUCCESS!')
            await asyncio.sleep(1800)


def setup(bot: MyClient) -> None:
    bot.add_cog(DiscordBotUpdates(bot))
