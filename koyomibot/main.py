import asyncio
import logging
import os
import random
from datetime import datetime
from typing import Optional

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

modules = [
    item[:-3] for item in os.listdir(os.path.join(os.path.dirname(__file__), "modules")) if not item.startswith("__")
]


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

    async def request_get(self, url: str, cache_str: str = "", return_as_json: bool = True) -> Optional[dict]:
        if cache_str:
            cached_obj = await self.db.redis.get(cache_str)
            if cached_obj:
                if return_as_json:
                    return json.loads(cached_obj)
                else:
                    return cached_obj.decode("utf-8")
        async with self.session.get(url) as r:
            if r.status != 200:
                log.error(f"HTTPSession: {r.status} on {url}")
                return None
            if return_as_json:
                result = await r.json()
            else:
                result = await r.text()
        if cache_str:
            await self.db.redis.set(cache_str, json.dumps(result))
        return result

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

    async def push_to_splunk(self, ctx: discord.ext.commands.Context) -> None:
        data = {
            "host": "koyomi",
            "sourcetype": "discord-commands",
            "event": {
                "author": ctx.author.id,
                "message": ctx.message.content,
                "args": str(ctx.args),
                "kwargs": str(ctx.kwargs),
                "prefix": ctx.prefix,
                "command": ctx.command.name,
                "guild_id": ctx.guild.id if ctx.guild else None,
                "guild_name": ctx.guild.name if ctx.guild else None,
                "timestamp": datetime.now().isoformat(),
                "failed": ctx.command_failed,
            },
        }
        log.info(f"Pushing to splunk: {data}")

        await self.session.post(
            "https://splunk:8088/services/collector/event",
            headers={"Authorization": f"Splunk {self.key_config.SplunkAuth}"},
            json=data,
            verify_ssl=False,
        )

    async def process_commands(self, msg: discord.Message) -> None:
        ctx = await self.get_context(msg)

        if ctx.command is None:
            return

        log.info(f"User: {ctx.author} attempted to use command {msg.content}")

        if await self.check_blacklist(ctx):
            await self.invoke(ctx)
            try:
                await self.push_to_splunk(ctx)
            except Exception:
                log.exception("Failed to push to splunk.")

    async def on_command_error(self, ctx, error) -> None:
        try:
            raise error
        except discord.ext.commands.errors.MissingRequiredArgument:
            log.error(f"{ctx.command} failed with {error}")
        except Exception:
            log.exception(f"{ctx.command} failed with {error}")

    async def on_message(self, msg: discord.Message) -> None:
        if msg.author.bot:
            return
        return await self.process_commands(msg)

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
