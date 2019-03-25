
import logging
import random

from typing import Optional

import discord
from discord.ext import commands

from main import MyClient
from utility import discordembed as dmbd


log = logging.getLogger(__name__)


class Gfycat(commands.Cog):

    def __init__(self, bot: MyClient):
        self.bot = bot

    async def search_gfycat(self, keyword: str, count: int, author: str) -> discord.Embed:
        link = f"https://api.gfycat.com/v1/gfycats/search?search_text={keyword}&count={count}"

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                log.error(f'Gyfcat returned {r.status}')
                return
            giflist = await r.json()
        num = random.randint(0, count-1)
        gif = giflist["gfycats"][num]
        title = gif["title"]
        desc = ""
        if gif["tags"]:
            desc = " #" + " #".join((x for x in gif["tags"]))

        url = f"https://gfycat.com/{title}"
        em = dmbd.newembed(author, title, desc, url, footer='gfycat')
        em.set_image(url=gif['content_urls']['largeGif']['url'])
        return em

    async def get_user(self, ctx: commands.Context, target: str) -> Optional[discord.User]:
        if ctx.message.mentions:
            return ctx.message.mentions[0]
        else:
            return ctx.guild.get_member_named(target)

    @commands.command()
    async def gfy(self, ctx: commands.Context, keyword: str) -> None:
        """Does a search on gyfcat"""
        em = await self.search_gfycat(keyword, 50, ctx.author)
        await ctx.send(embed=em)

    # @commands.command()
    # async def hug(self, ctx: commands.Context, target: str) -> None:
    #     target = await self.get_user(ctx, target)
    #     if target is None:
    #         return

    # @commands.command()
    # async def kiss(self, ctx: commands.Context, target: str) -> None:
    #     target = self.get_user(ctx, target)
    #     if target is None:
    #         return

    # @commands.command()
    # async def cuddle(self, ctx, target):
    #     target = self.get_user(ctx, target)
    #     if target is None:
    #         return

    #     em = await self.get_phrase(ctx.author, 'cuddle', target, True)

    #     await ctx.send(embed=em)
    #     await self.bot.cogs['Wordcount'].cmdcount('cuddle')

    # @commands.command()
    # async def punch(self, ctx, target):
    #     target = self.get_user(ctx, target)
    #     if target is None:
    #         return

    #     em = await self.get_phrase(ctx.author, 'punch', target, False)

    #     await ctx.send(embed=em)
    #     await self.bot.cogs['Wordcount'].cmdcount('punch')

    # @commands.command()
    # async def slap(self, ctx, target):
    #     target = self.get_user(ctx, target)
    #     if target is None:
    #         return

    #     em = await self.get_phrase(ctx.author, 'slap', target, False)

    #     await ctx.send(embed=em)
    #     await self.bot.cogs['Wordcount'].cmdcount('slap')

    # @commands.command()
    # async def kanashi(self, ctx):

    #     em = await self.get_phrase(ctx.author, 'cry', ctx.author, False)

    #     em.description = f"{ctx.author.display_name} is so sad. Cheer up :("
    #     await ctx.send(embed=em)
    #     await self.bot.cogs['Wordcount'].cmdcount('kanashi')




def setup(bot: MyClient) -> None:
    bot.add_cog(Gfycat(bot))
