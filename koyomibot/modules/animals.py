import logging

from discord.ext import commands

import koyomibot.utility.discordembed as dmbd
from koyomibot.main import MyClient

log = logging.getLogger(__name__)


class Animals(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot

    @commands.command()
    async def shibe(self, ctx: commands.Context) -> bool:
        result = await self.bot.request_get("https://shibe.online/api/shibes")
        if result is None:
            return False
        em = dmbd.newembed(ctx.author, "Shibes", footer="shibe.online")
        em.set_image(url=result[0])
        await ctx.send(embed=em)
        return True

    @commands.command()
    async def catfact(self, ctx: commands.Context) -> bool:
        result = await self.bot.request_get("https://cat-fact.herokuapp.com/facts/random")
        if result is None:
            return False
        em = dmbd.newembed(ctx.author, "Random Cat Fact", d=result["text"], footer="cat-fact")
        await ctx.send(embed=em)
        return True

    @commands.command()
    async def meow(self, ctx: commands.Context) -> bool:
        result = await self.bot.request_get("https://aws.random.cat/meow")
        if result is None:
            return False
        em = dmbd.newembed(ctx.author, "Random Cat", footer="random.cat")
        em.set_image(url=result["file"])
        await ctx.send(embed=em)
        return True

    @commands.command()
    async def meow2(self, ctx: commands.Context, text: str = "") -> None:
        em = dmbd.newembed(ctx.author, "Random Cat", footer="cataas")
        if text:
            em.set_image(url=f"https://cataas.com/cat/{text}")
        else:
            em.set_image(url="https://cataas.com/cat")
        await ctx.send(embed=em)

    @commands.command()
    async def meowgif(self, ctx: commands.Context, text: str = "") -> None:
        em = dmbd.newembed(ctx.author, "Random Cat", footer="cataas")
        if text:
            em.set_image(url=f"https://cataas.com/cat/gif/{text}")
        else:
            em.set_image(url="https://cataas.com/cat/gif")
        await ctx.send(embed=em)

    @commands.command()
    async def woof(self, ctx: commands.Context) -> bool:
        result = await self.bot.request_get("https://random.dog/woof.json")
        if result is None:
            return False
        if result["url"].endswith(".mp4"):
            log.error("random.dog MP4 link detected, exiting out...")
            return False
        em = dmbd.newembed(ctx.author, "Random Dog", footer="random.dog")
        em.set_image(url=result["url"])
        await ctx.send(embed=em)
        return True

    @commands.command()
    async def floof(self, ctx: commands.Context) -> bool:
        result = await self.bot.request_get("https://randomfox.ca/floof/")
        if result is None:
            return False
        em = dmbd.newembed(ctx.author, "Random Fox", u=result["link"], footer="randomfox.ca")
        em.set_image(url=result["image"])
        await ctx.send(embed=em)
        return True


def setup(bot: MyClient) -> None:
    bot.add_cog(Animals(bot))
