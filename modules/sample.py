

from discord.ext import commands

class Sample:

    def __init__(self, bot):
        self.bot = bot
        # Insert any other class variables you want.

    @commands.command()
    async def exampleCommand(self):
        await ctx.send("Dennis is gay.")

    @commands.command() # there are different parameters you can pass into this
