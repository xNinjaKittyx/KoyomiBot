""" Module for generating a random cat picture"""

import random

from bs4 import BeautifulSoup
from discord.ext import commands
import utility.discordembed as dmbd

import ujson


class Random:
    """ Commands that are RANDOM"""

    def __init__(self, bot):
        """ Initialize Class"""
        self.bot = bot
        self.shinychance = 0

    @commands.command()
    async def meow(self, ctx):
        """ When User Types ~meow, return a cat link """

        async with self.bot.session.get('http://random.cat/meow') as r:
            if r.status != 200:
                self.bot.logger.warning("Could not get a meow")
                return
            catlink = await r.json(loads=ujson.loads)
            rngcat = catlink['file']
            title = 'Random.Cat'
            desc = 'Here, have a cat.'
            url = rngcat
            em = dmbd.newembed(ctx.author, title, desc, url)
            em.set_image(url=rngcat)
            await ctx.send(embed=em)
            self.bot.cogs['Wordcount'].cmdcount('meow')

    @commands.command()
    async def woof(self, ctx):
        """When user types ~woof, return a woof link """

        async with self.bot.session.get('http://random.dog/') as r:
            if r.status != 200:
                self.bot.logger.warning("Could not get a woof")
                return
            doglink = BeautifulSoup(await r.text(), 'html.parser')
            rngdog = 'http://random.dog/' + doglink.img['src']
            title = 'Random.Dog'
            desc = 'Here, have a dog.'
            url = rngdog
            em = dmbd.newembed(ctx.author, title, desc, url)
            em.set_image(url=rngdog)
            await ctx.send(embed=em)
            self.bot.cogs['Wordcount'].cmdcount('woof')

    @commands.command()
    async def pokemon(self, ctx, *, numid: int=None):
        """ Get a random pokemon! """
        if numid is None:
            async with self.bot.session.get('http://pokeapi.co/api/v2/pokemon/?limit=0') as r:
                if r.status == 200:
                    count = int((await r.json(loads=ujson.loads))['count'])
            numid = random.randint(1, count)

        async with self.bot.session.get('http://pokeapi.co/api/v2/pokemon/' + str(numid)) as r:
            if r.status == 200:
                pokeman = await r.json(loads=ujson.loads)
                em = dmbd.newembed(ctx.author, pokeman['name'].title())
                shiny = (random.randint(1, 65536) < int(65535/(8200 - self.shinychance * 200)))
                if not shiny:
                    if self.shinychance < 40:
                        self.shinychance += 1
                    em.set_image(url=pokeman['sprites']['front_default'])
                else:
                    em.set_image(url=pokeman['sprites']['front_shiny'])
                    em.description = 'WOW YOU GOT A SHINY :D'
                    self.shinychance = 0
                await ctx.send(embed=em)

    @commands.command()
    async def roll(self, ctx, *, dice: str='1d6'):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except ValueError:
            await ctx.send('Format has to be in NdN!')
            return

        title = 'Here are your dice results!'
        em = dmbd.newembed(ctx.author, title)
        for r in range(rolls):
            em.add_field(name="Dice #" + str(r+1), value=str(random.randint(1, limit)))
        # result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('roll')

    @commands.command()
    async def flip(self, ctx, coins=1):
        """ Flips a coin."""
        em = dmbd.newembed(ctx.author)
        for x in range(coins):
            coin = random.randint(1, 2)
            if coin == 1:
                em.add_field(name="Coin #" + str(x+1), value="Heads")
            elif coin == 2:
                em.add_field(name="Coin #" + str(x+1), value="Tails")

        await ctx.send(embed=em)

        self.bot.cogs['Wordcount'].cmdcount('flip')

    @commands.command(name='8ball')
    async def ball(self, ctx):
        """ Ask the 8Ball """
        answers = ['It is certain', 'It is decidedly so', 'Without a doubt',
                   'Yes, definitely', 'You may rely on it', 'As I see it, yes',
                   'Most likely', 'Outlook good', 'Yes', 'Signs point to yes',
                   'Reply hazy try again', 'Ask again later',
                   'Better not tell you now', 'Cannot predict now',
                   'Concentrate and ask again', 'Don\'t count on it',
                   'My reply is no', 'My sources say no',
                   'Outlook not so good', 'Very doubtful']

        em = dmbd.newembed(ctx.author, random.choice(answers))
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('8ball')

    @commands.command(description='Ask the Bot to choose one')
    async def choose(self, ctx, *choices: str):
        """Chooses between multiple choices."""
        em = dmbd.newembed(ctx.author, random.choice(choices))
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('choose')


def setup(bot):
    """ Setup Webscrapper Module"""
    bot.add_cog(Random(bot))
