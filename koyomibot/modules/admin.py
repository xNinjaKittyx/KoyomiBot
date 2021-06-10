import asyncio
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
os.makedirs(temp_folder)
(Path(temp_folder) / "__init__.py").touch()


class Admin(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot

    def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.author.id == 82221891191844864

    @commands.command(hidden=True)
    async def kys(self, ctx: commands.Context) -> None:
        """ Bot kills itself """
        await ctx.send("Bot is *kill*")
        await asyncio.sleep(3)
        await self.bot.close()

    @commands.command(hidden=True)
    async def status(self, ctx: commands.Context, *, s: str) -> None:
        await self.bot.change_presence(game=discord.Game(name=s))

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
        """ Changes the Avatar"""
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
        """ Changes the Username """
        await self.bot.user.edit(username=s)


#     @commands.command(hidden=True)
#     async def shell(self, ctx: commands.Context, *, s: str) -> None:
#         import shlex

#         args = shlex.split(s)
#         process = await asyncio.create_subprocess_exec(
#             *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
#         )
#         stdout, stderr = await process.communicate()
#         result = stdout.decode().strip()
#         if result:
#             em = dmbd.newembed(ctx.author, "Shell Command", f"```{result}```")
#             await ctx.send(embed=em)

#         if process.returncode == 0:
#             await ctx.message.add_reaction("✅")
#         else:
#             await ctx.message.add_reaction("❌")

#     @commands.command(hidden=True)
#     async def create_command(self, ctx: commands.Context, *, s: str) -> None:
#         s = s.strip("`")
#         random_hex = secrets.token_hex(nbytes=4)
#         filename = f"custom_{random_hex}"
#         with open(os.path.join(temp_folder, f"{filename}.py"), "w") as f:
#             f.write(
#                 f"""

# import asyncio
# import logging

# import discord
# from discord.ext import commands

# from koyomibot.main import MyClient
# from koyomibot.utility import discordembed as dmbd

# log = logging.getLogger(__name__)


# class CustomCommands_{random_hex}(commands.Cog):
#     def __init__(self, bot: MyClient):
#         self.bot = bot

#     def cog_check(self, ctx: commands.Context) -> bool:
#         return ctx.author.id == 82221891191844864

# {s}

# def setup(bot: MyClient) -> None:
#     bot.add_cog(CustomCommands_{random_hex}(bot))
#             """
#             )

#         try:
#             self.bot.load_extension(f"koyomibot.temp.{filename}")
#             await ctx.message.add_reaction("✅")
#         except Exception:
#             await ctx.message.add_reaction("❌")


def setup(bot: MyClient) -> None:
    """Setup admin.py"""
    bot.add_cog(Admin(bot))
