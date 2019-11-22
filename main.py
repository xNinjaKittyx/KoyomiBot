
import asyncio
import logging
import random
import os

import aiohttp
import discord
import rapidjson

from discord.ext import commands
from discord.utils import find

from utility.config import Config
from utility.db import KoyomiDB


log = logging.getLogger(__name__)


description = """
KoyomiBot: Lots of Fun, Minimal Moderation, No bullshit, SFW.
"""

modules = {
    'modules.admin',
    'modules.animals',
    'modules.anime',
    'modules.comics',
    'modules.discordbots',
    'modules.forex',
    'modules.gfycat',
    'modules.guild',
    'modules.image',
    'modules.info',
    'modules.music',
    'modules.osu',
    'modules.overwatch',
    'modules.pad',
    'modules.random',
    # 'modules.ryzen',  # Not used. Was used when 3900X's were rare to get!
    'modules.search',
    # 'modules.animehangman',
    # 'modules.blackjack',
    # 'modules.cleverbot',
    # 'modules.comics',
    # 'modules.image',
    # 'modules.interactions',
    # 'modules.log',
    # 'modules.mail',
    # 'modules.pad',
    # 'modules.profile',
    # 'modules.slots',
    # 'modules.tags',
    # 'modules.todo',
    # 'modules.weather',
    # 'modules.wordcount',
}


# Quick snippet from Danny's code.
async def _get_prefix(bot: discord.Client, msg: discord.Message) -> list:
    user_id = bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ']

    if bot.key_config.debug:
        base = ['k!>']
    else:
        base.append('k>')
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

    def run(self) -> None:
        log.info('Starting Bot'.center(30, '-'))
        self.loop.run_until_complete(self.db.initialize_redis())
        self.load_all_modules()
        try:
            self.loop.run_until_complete(self.start(self.key_config.DiscordToken))
        except KeyboardInterrupt:
            log.info('Detected KeyboardInterrupt')
            self.loop.run_until_complete(self.logout())
        finally:
            for task in asyncio.Task.all_tasks():
                task.cancel()
            self.loop.run_until_complete(self.session.close())
            self.loop.run_until_complete(self.db.close())
            self.loop.run_until_complete(self.close())
            self.loop.close()

    def load_all_modules(self) -> None:
        log.info('Loading all Modules'.center(30).replace(' ', '-'))
        for mod in modules:
            try:
                self.load_extension(mod)
                log.info(f'Load Successful: {mod}')
            except discord.ext.commands.errors.ExtensionFailed as e:
                log.warning(e)
                log.warning(f'[WARNING]: Module {mod} did not load')

    async def check_blacklist(self, ctx: discord.ext.commands.Context) -> bool:
        if ctx.author.bot:
            return False
        return await self.db.check_user_blacklist(ctx.author)

    async def process_commands(self, msg: discord.Message) -> None:
        ctx = await self.get_context(msg)

        if ctx.command is None:
            return

        log.info(f'User: {ctx.author} attempted to use command {msg.content}')

        if await self.check_blacklist(ctx):
            await self.invoke(ctx)

    async def on_message(self, msg: discord.Message) -> None:
        if msg.author.bot:
            return
        await self.process_commands(msg)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        if not await self.db.check_guild_blacklist(guild):
            await guild.leave()
            return
        log.info(f'KoyomiBot joined a new guild! {guild.name}')

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        log.info(f'KoyomiBot left a guild :( {guild.name}')

    async def on_member_join(self, member: discord.Member) -> None:
        log.debug(f"{member.name}/{member.id} has joined the guild {member.guild.name}/{member.guild.id}")

    async def on_member_remove(self, member: discord.Member) -> None:
        log.debug(f"{member.name}/{member.id} has left the guild {member.guild.name}/{member.guild.id}")

    async def on_message_delete(self, msg: discord.Message) -> None:
        if msg.author.bot:
            return
        if msg.guild:
            mod_log = find(lambda c: c.name == "koyomilog", msg.guild.channels)
            if mod_log is None:
                return
            await mod_log.send(f"{msg.author.name} deleted the message: {msg.content}")

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.author.bot:
            return
        if before.guild:
            mod_log = find(lambda c: c.name == "koyomilog", before.guild.channels)
            if mod_log is None:
                return
            await mod_log.send(
                f"{before.author.name} edited the message: \n Before: {before.content}\n After: {after.content}")

    async def on_ready(self) -> None:
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
