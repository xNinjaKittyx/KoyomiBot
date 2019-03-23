
from typing import Callable

from discord.ext import commands

from main import MyClient


def is_guild_owner() -> Callable:
    async def predicate(ctx: commands.Context) -> bool:
        return ctx.author == ctx.guild.owner
    return commands.check(predicate)


class GuildCommands(commands.Cog):

    def __init__(self, bot: MyClient):
        self.bot = bot

    @commands.command()
    @is_guild_owner()
    async def add_prefix(self, ctx: commands.Context, *, prefix: str) -> None:
        result = await self.bot.db.set_guild_prefixes(ctx.guild, prefix)
        await ctx.send(result[1])

    @commands.command()
    @is_guild_owner()
    async def remove_prefix(self, ctx: commands.Context, *, prefix: str) -> None:
        result = await self.bot.db.remove_guild_prefixes(ctx.guild, prefix)
        if result:
            await ctx.send(f"Removed Prefix {prefix}")

    @commands.command()
    async def get_prefix(self, ctx: commands.Context, *, prefix: str) -> None:
        await ctx.send(", ".join(await self.bot.db.get_guild_prefixes(ctx.guild)))
