
import logging

from discord.ext import commands

import utility.discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


class Animals(commands.Cog):

    def __init__(self, bot: MyClient):
        self.bot = bot

    @commands.command()
    async def shibe(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('http://shibe.online/api/shibes') as r:
            if r.status != 200:
                log.error('Could not get info from Shibe.online')
                return
            result = await r.json()
        em = dmbd.newembed(ctx.author, "Shibes", footer="shibe.online")
        em.set_image(url=result[0])
        await ctx.send(embed=em)

    @commands.command()
    async def catfact(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('https://cat-fact.herokuapp.com/facts/random') as r:
            if r.status != 200:
                log.error('Could not get info from cat-fact.com')
                return
            result = await r.json()
        em = dmbd.newembed(ctx.author, "Random Cat Fact", d=result['text'], footer="cat-fact")
        await ctx.send(embed=em)

    @commands.command()
    async def meow(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('https://aws.random.cat/meow') as r:
            if r.status != 200:
                log.error('Could not get info from random.cat')
                return
            result = await r.json()
        em = dmbd.newembed(ctx.author, "Random Cat", footer="random.cat")
        em.set_image(url=result['file'])
        await ctx.send(embed=em)

    @commands.command()
    async def meow2(self, ctx: commands.Context, text: str = '') -> None:
        em = dmbd.newembed(ctx.author, "Random Cat", footer="cataas")
        if text:
            em.set_image(url=f"https://cataas.com/cat/{text}")
        else:
            em.set_image(url=f"https://cataas.com/cat")
        await ctx.send(embed=em)

    @commands.command()
    async def meowgif(self, ctx: commands.Context, text: str = '') -> None:
        em = dmbd.newembed(ctx.author, "Random Cat", footer="cataas")
        if text:
            em.set_image(url=f"https://cataas.com/cat/gif/{text}")
        else:
            em.set_image(url=f"https://cataas.com/cat/gif")
        await ctx.send(embed=em)

    @commands.command()
    async def woof(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('https://random.dog/woof.json') as r:
            if r.status != 200:
                log.error('Could not get info from random.dog')
                return
            result = await r.json()
            if result['url'].endswith('.mp4'):
                log.error('MP4 link detected, exiting out...')
                return
        em = dmbd.newembed(ctx.author, "Random Dog", footer="random.dog")
        em.set_image(url=result['url'])

    @commands.command()
    async def floof(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('https://randomfox.ca/floof/') as r:
            if r.status != 200:
                log.error('Could not get info from randomfox.ca')
                return
            result = await r.json()
        em = dmbd.newembed(ctx.author, "Random Dog", u=result['link'], footer="randomfox.ca")
        em.set_image(url=result['image'])


def setup(bot: MyClient) -> None:
    bot.add_cog(Animals(bot))
