
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
            em = dmbd.newembed(ctx.author, "Shibes")
            em.set_image(url=result[0])
            await ctx.send(embed=em)

    @commands.command()
    async def catfact(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('https://cat-fact.herokuapp.com/facts/random') as r:
            if r.status != 200:
                log.error('Could not get info from cat-fact.com')
                return
            result = await r.json()
            em = dmbd.newembed(ctx.author, "Random Cat Fact", d=result['text'])
            await ctx.send(embed=em)

    @commands.command()
    async def meow(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('https://aws.random.cat/meow') as r:
            if r.status != 200:
                log.error('Could not get info from random.cat')
                return
            result = await r.json()
            em = dmbd.newembed(ctx.author, "Random Cat")
            em.set_image(url=result['file'])
            await ctx.send(embed=em)

    @commands.command()
    async def woof(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('https://random.dog/woof.json') as r:
            if r.status != 200:
                log.error('Could not get info from random.dog')
                return
            result = await r.json()
            em = dmbd.newembed(ctx.author, "Random Dog")
            em.set_image(url=result['url'])

    @commands.command()
    async def floof(self, ctx: commands.Context) -> None:
        async with self.bot.session.get('https://randomfox.ca/floof/') as r:
            if r.status != 200:
                log.error('Could not get info from randomfox.ca')
                return
            result = await r.json()
            em = dmbd.newembed(ctx.author, "Random Dog", u=result['link'])
            em.set_image(url=result['image'])


def setup(bot: MyClient):
    bot.add_cog(Animals(bot))
