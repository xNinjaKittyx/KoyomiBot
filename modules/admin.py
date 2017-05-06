
import asyncio
import time
import sys

import aiohttp
import discord
from discord.ext import commands

class Admin:
    def __init__(self, bot):
        self.bot = bot
        self.checkdev = lambda x: x == "82221891191844864"

    @commands.command(pass_context=True, hidden=True)
    async def test(self, ctx, *, code: str):
        """ Tests something :o """
        if not self.checkdev(ctx.message.author.id):
            return
        if code.startswith("```Python\n"):
            code = code[10:-3]
            start_time = time.time()
            try:
                exec(code)
                await self.bot.say("```Code Executed```")
            except (TypeError, SyntaxError):
                await self.bot.say("```\n" + sys.exc_info() + "```")
                print("Syntax Error")
            total_time = time.time() - start_time
            await self.bot.say("This took *" + str(total_time) + "* seconds")

    @commands.command(pass_context=True, hidden=True)
    async def kys(self, ctx):
        """ Bot kills itself """
        if not self.checkdev(ctx.message.author.id):
            return
        await self.bot.say("*Bot is kill in 3 seconds.*")
        await asyncio.sleep(3)
        await self.bot.close()
        #self.bot.cogs['WordDB'].cmdcount('kill')

    @commands.command(pass_context=True, hidden=True)
    async def status(self, ctx, *, s: str):
        """ Changes Status """
        if not self.checkdev(ctx.message.author.id):
            return
        await self.bot.change_presence(game=discord.Game(name=s))
        #self.bot.cogs['WordDB'].cmdcount('status')

    @commands.command(pass_context=True, hidden=True)
    async def changeavatar(self, ctx, *, url: str):
        """ Changes the Avatar"""
        if not self.checkdev(ctx.message.author.id):
            return

        async with aiohttp.get(url) as r:
            if r.status == 200:
                try:
                    await self.bot.edit_profile(avatar=r.content)
                except discord.HTTPException:
                    await self.bot.say("Editing the profile failed.")
                except discord.InvalidArgument:
                    await self.bot.say("Wrong image format was passed.")

    @commands.command(pass_context=True, hidden=True)
    async def changeusername(self, ctx, *, s: str):
        """ Changes the Username """
        if self.checkdev(ctx.message.author.id):
            await self.bot.edit_profile(username=s)
            # bot.cogs['WordDB'].cmdcount('changeusername')

def setup(bot):
    """Setup admin.py"""
    bot.add_cog(Admin(bot))
