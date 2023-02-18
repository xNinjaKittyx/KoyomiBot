import logging
import os

# import secrets
from pathlib import Path

import discord
from discord.ext import commands

from koyomibot.main import MyClient
from koyomibot.utility import discordembed as dmbd

log = logging.getLogger(__name__)
temp_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "temp"))
os.makedirs(temp_folder, exist_ok=True)
(Path(temp_folder) / "__init__.py").touch()


class Admin(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot

    def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.author.id == 82221891191844864

    @commands.command(hidden=True)
    async def kys(self, ctx: commands.Context) -> None:
        """Bot kills itself"""
        await self.bot.close()

    @commands.command(hidden=True)
    async def status(self, ctx: commands.Context, *, s: str) -> None:
        await self.bot.change_presence(activity=discord.Game(name=s))

    @commands.command(hidden=True)
    async def redisinfo(self, ctx: commands.Context) -> None:
        em = dmbd.newembed(ctx.author, "Redis Info")
        info = await self.bot.db.redis.info()
        em.add_field(name="Version", value=info["server"]["redis_version"])
        em.add_field(name="Uptime", value=info["server"]["uptime_in_seconds"])
        em.add_field(
            name="Memory Usage",
            value=f"{int(info['memory']['used_memory']) / int(info['memory']['total_system_memory']):.6f}%",
        )
        em.add_field(name="Memory Usage", value=info["memory"]["used_memory_human"])
        em.add_field(name="Peak Memory Usage", value=info["memory"]["used_memory_peak_human"])
        await ctx.send(embed=em)

    @commands.command(hidden=True)
    async def changeavatar(self, ctx: commands.Context, *, url: str) -> None:
        """Changes the Avatar"""
        async with self.bot.session.get(url) as r:
            if r.status == 200:
                try:
                    await self.bot.user.edit(avatar=await r.read())
                except discord.HTTPException:
                    await ctx.send("Editing the profile failed.")
                except discord.InvalidArgument:
                    await ctx.send("Wrong image format was passed.")

    @commands.command(hidden=True)
    async def changeusername(self, ctx: commands.Context, *, s: str) -> None:
        """Changes the Username"""
        await self.bot.user.edit(username=s)


def setup(bot: MyClient) -> None:
    """Setup admin.py"""
    bot.add_cog(Admin(bot))
