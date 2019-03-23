
import logging
import random
import os

import aiohttp
import discord
import rapidjson

from discord.ext import commands
from utility.config import Config
from utility.db import KoyomiDB


log = logging.getLogger(__name__)


description = """
KoyomiBot: Lots of Fun, Minimal Moderation, No bullshit, SFW.
"""

modules = {
    'modules.discordbots'
    # 'modules.admin',
    # 'modules.anime',
    # 'modules.animehangman',
    # 'modules.blackjack',
    # 'modules.cleverbot',
    # 'modules.comics',
    # 'modules.forex',
    # 'modules.image',
    # 'modules.info',
    # 'modules.interactions',
    # 'modules.log',
    # 'modules.mail',
    # 'modules.musicplayer',
    # 'modules.osu',
    # 'modules.overwatch',
    # 'modules.pad',
    # 'modules.profile',
    # 'modules.random',
    # 'modules.search',
    # 'modules.slots',
    # 'modules.tags',
    # 'modules.todo',
    # 'modules.weather',
    # 'modules.wordcount',
}


# Quick snippet from Danny's code.
async def _get_prefix(bot, msg):
    user_id = bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ']

    if bot.key_config.debug:
        base.append('!>')
    else:
        base.append('>')
    if msg.guild is not None:
        base.extend(await bot.db.get_guild_prefixes(msg.guild))

    return base


class MyClient(commands.AutoShardedBot):

    def __init__(self):
        super().__init__(
            command_prefix=_get_prefix, description=description,
            pm_help=True, help_attrs=dict(hidden=True), fetch_offline_members=False
        )
        self.db = KoyomiDB()

        self.session = aiohttp.ClientSession(
            loop=self.loop,
            json_serialize=rapidjson.dumps,
            headers={'User-Agent': 'Koyomi Discord Bot (https://github.com/xNinjaKittyx/KoyomiBot/)'}
        )
        self.key_config = Config('config.toml')
        self.load_all_modules()

    def run(self):
        log.info('Starting Bot'.center(30, '-'))
        loop.run_until_complete(self.db.initialize_redis())
        try:
            super().run(self.key_config.DiscordToken)
        except KeyboardInterrupt:
            log.info('Detected KeyboardInterrupt')
        loop.run_until_complete(self.close())
        loop.run_until_complete(self.session.close())

    def load_all_modules(self):
        log.info('Loading all Modules'.center(30).replace(' ', '-'))
        for mod in modules:
            try:
                self.load_extension(mod)
                log.info(f'Load Successful: {mod}')
            except ImportError as e:
                log.warning(e)
                log.warning(f'[WARNING]: Module {mod} did not load')

    async def check_blacklist(self, msg):
        if msg.author.bot:
            return False
        if msg.guild:
            return await self.db.check_guild_blacklist(msg.guild)
        return await self.db.check_user_blacklist(msg.author)

    async def on_message(self, msg):
        if await self.check_blacklist(msg):
            await self.process_commands(msg)

    async def on_guild_join(self, guild):
        log.info(f'KoyomiBot joined a new guild! {guild}')

    async def on_ready(self):
        random.seed()
        log.info('Logged in as')
        log.info(f"Username {self.user.name}")
        log.info(f"ID: {self.user.id}")
        url = f"https://discordapp.com/api/oauth2/authorize?client_id={self.user.id}&scope=bot&permissions=0"
        log.info(f"Invite Link: {url}")
        try:
            if not discord.opus.is_loaded() and os.name == 'nt':
                discord.opus.load_opus("libopus0.x64.dll")

            if not discord.opus.is_loaded() and os.name == 'posix':
                discord.opus.load_opus("/usr/local/lib/libopus.so")
            log.info("Loaded Opus Library")
        except Exception as e:
            log.error(e)
            log.warning("Opus library did not load. Voice may not work.")
