import asyncio
import logging
import os
import random

import aiohttp
import discord
import rapidjson as json
from discord.ext import commands

from koyomibot.utility.config import Config
from koyomibot.utility.db import KoyomiDB

log = logging.getLogger(__name__)


description = """
KoyomiBot: Lots of Fun, Minimal Moderation, No bullshit, SFW.
"""

modules = {
    "admin",
    "animals",
    "anime",
    "comics",
    "discordbots",
    "forex",
    "gfycat",
    "dragalia",
    "guild",
    # "modules.image",
    "info",
    "music",
    "osu",
    # "modules.overwatch",
    # "modules.pad",
    "random",
    # 'modules.ryzen',  # Not used. Was used when 3900X's were rare to get!
    "search",
}


# Quick snippet from Danny's code.
async def _get_prefix(bot: discord.Client, msg: discord.Message) -> list:
    user_id = bot.user.id
    base = [f"<@!{user_id}> ", f"<@{user_id}> "]

    if bot.koyomi_debug:
        base = ["k!>"]
    else:
        base.append("k>")
        if msg.guild is not None:
            base.extend(await bot.db.get_guild_prefixes(msg.guild))

    return base


class MyClient(commands.AutoShardedBot):
    def __init__(self, debug: bool = False):
        super().__init__(
            command_prefix=_get_prefix,
            description=description,
            pm_help=True,
            help_attrs=dict(hidden=True),
            fetch_offline_members=False,
        )
        self.key_config = Config("config.toml")
        self.db = KoyomiDB(self.key_config)
        self.koyomi_debug = debug

        self.session = aiohttp.ClientSession(
            loop=self.loop,
            json_serialize=json.dumps,
            headers={"User-Agent": "Koyomi Discord Bot (https://github.com/xNinjaKittyx/KoyomiBot/)"},
        )

    def run(self) -> None:
        log.info("Starting Bot".center(30, "-"))
        self.loop.run_until_complete(self.db.initialize_redis())
        self.load_all_modules()
        try:
            self.loop.run_until_complete(self.start(self.key_config.DiscordToken))
        except KeyboardInterrupt:
            log.info("Detected KeyboardInterrupt")
            self.loop.run_until_complete(self.logout())
        finally:
            for task in asyncio.Task.all_tasks():
                task.cancel()
            self.loop.run_until_complete(self.session.close())
            self.loop.run_until_complete(self.db.close())
            self.loop.run_until_complete(self.close())
            self.loop.close()

    def load_all_modules(self) -> None:
        log.info("Loading all Modules".center(30, "-"))
        for mod in modules:
            try:
                self.load_extension(f"koyomibot.modules.{mod}")
                log.info(f"Load Successful: {mod}")
            except discord.ext.commands.errors.ExtensionFailed:
                log.exception(f"[WARNING]: Module {mod} did not load")

    async def check_blacklist(self, ctx: discord.ext.commands.Context) -> bool:
        if ctx.author.bot:
            return False
        return await self.db.check_user_blacklist(ctx.author)

    async def process_commands(self, msg: discord.Message) -> None:
        ctx = await self.get_context(msg)

        if ctx.command is None:
            return

        log.info("User: {ctx.author} attempted to use command {msg.content}")

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
        log.info(f"KoyomiBot joined a new guild! {guild.name}")

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        log.info(f"KoyomiBot left a guild :( {guild.name}")

    async def on_ready(self) -> None:
        random.seed()
        log.info("Logged in as")
        log.info(f"Username {self.user.name}")
        log.info(f"ID: {self.user.id}")
        url = f"https://discordapp.com/api/oauth2/authorize?client_id={self.user.id}&scope=bot&permissions=0"
        log.info(f"Invite Link: {url}")
        try:
            log.info(os.name)
            if not discord.opus.is_loaded() and os.name == "nt":
                discord.opus.load_opus("libopus0.x64.dll")

            if not discord.opus.is_loaded() and os.name == "posix":
                discord.opus.load_opus("/usr/lib/libopus.so.0")
            log.info("Loaded Opus Library")
        except Exception as e:
            log.error(e)
            log.warning("Opus library did not load. Voice may not work.")
