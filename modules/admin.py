
import asyncio
import time
import sys

import aiohttp
import discord
from discord.ext import commands

class Admin:
    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        try:
            await ctx.bot.is_owner(ctx.author)
            return True
        except discord.ext.commands.errors.CheckFailure:

            self.bot.logger.warning(ctx.author.name + ' tried to use an Admin command!')
            return False

    @commands.command(hidden=True)
    async def test(self, ctx, *, code: str):
        """ Tests something :o """
        if code.startswith("```Python\n"):
            code = code[10:-3]
            start_time = time.time()
            try:
                exec(code)
                await ctx.send("```Code Executed```")
            except (TypeError, SyntaxError):
                await ctx.send("```\n" + sys.exc_info() + "```")
                self.bot.logger.warning("Syntax Error")
            total_time = time.time() - start_time
            await ctx.send("This took *" + str(total_time) + "* seconds")

    @commands.command(hidden=True)
    async def kys(self, ctx):
        """ Bot kills itself """
        await ctx.send("*Bot is kill in 3 seconds...*")
        await asyncio.sleep(3)
        await self.bot.close()

    @commands.command(hidden=True)
    async def status(self, ctx, *, s: str):
        await self.bot.change_presence(game=discord.Game(name=s))

    @commands.command(hidden=True)
    async def changeavatar(self, ctx, *, url: str):
        """ Changes the Avatar"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    try:
                        await self.bot.user.edit(avatar=await r.read())
                    except discord.HTTPException:
                        await ctx.send("Editing the profile failed.")
                    except discord.InvalidArgument:
                        await ctx.send("Wrong image format was passed.")

    @commands.command(hidden=True)
    async def changeusername(self, ctx, *, s: str):
        """ Changes the Username """
        await self.bot.user.edit(username=s)
        """ Changes Status """

    @commands.command(hidden=True)
    async def serverlist(self, ctx):
        result = []
        for x in self.bot.guilds:
            result.append(x.name)
        await ctx.send("\n".join(result))

def setup(bot):
    """Setup admin.py"""
    bot.add_cog(Admin(bot))
