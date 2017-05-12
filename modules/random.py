""" Module for generating a random cat picture"""

import random

import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands
import utility.discordembed as dmbd


class Random:
    """ Commands that are RANDOM"""

    def __init__(self, bot):
        """ Initialize Class"""
        self.bot = bot

    @commands.command(pass_context=True)
    async def meow(self, ctx):
        """ When User Types ~meow, return a cat link """

        async with aiohttp.get('http://random.cat/meow') as r:
            if r.status != 200:
                self.bot.cogs['Log'].output("Could not get a meow")
                return
            catlink = await r.json()
            rngcat = catlink['file']
            author = ctx.message.author
            title = 'Random.Cat'
            desc = 'Here, have a cat.'
            url = rngcat
            em = dmbd.newembed(author, title, desc, url)
            em.set_image(url=rngcat)
            await self.bot.say(embed=em)
            self.bot.cogs['Wordcount'].cmdcount('meow')

    @commands.command(pass_context=True)
    async def woof(self, ctx):
        """When user types ~woof, return a woof link """

        async with aiohttp.get('http://random.dog/') as r:
            if r.status != 200:
                self.bot.cogs['Log'].output("Could not get a woof")
                return
            doglink = BeautifulSoup(r.text, 'html.parser')
            rngdog = 'http://random.dog/' + doglink.img['src']
            author = ctx.message.author
            title = 'Random.Dog'
            desc = 'Here, have a dog.'
            url = rngdog
            em = dmbd.newembed(author, title, desc, url)
            em.set_image(url=rngdog)
            await self.bot.say(embed=em)
            self.bot.cogs['Wordcount'].cmdcount('woof')

    @commands.command(pass_context=True)
    async def roll(self, ctx, *, dice: str ='1d6'):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except ValueError:
            await self.bot.say('Format has to be in NdN!')
            return

        author = ctx.message.author
        title = 'Here are your dice results!'
        em = dmbd.newembed(author, title)
        for r in range(rolls):
            em.add_field(name="Dice #" + str(r+1), value=str(random.randint(1, limit)))
        # result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await self.bot.say(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('roll')

    @commands.command(pass_context=True)
    async def flip(self, ctx, coins=1):
        """ Flips a coin."""
        author = ctx.message.author
        em = dmbd.newembed(author)
        for x in range(coins):
            coin = random.randint(1, 2)
            if coin == 1:
                em.add_field(name="Coin #" + str(x+1), value="Heads")
            elif coin == 2:
                em.add_field(name="Coin #" + str(x+1), value="Tails")

        await self.bot.say(embed=em)

        self.bot.cogs['Wordcount'].cmdcount('flip')

    @commands.command(pass_context=True, name='8ball')
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

        author = ctx.message.author
        em = dmbd.newembed(author, random.choice(answers))
        await self.bot.say(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('8ball')

    @commands.command(pass_context=True, description='Ask the Bot to choose one')
    async def choose(self, ctx, *choices: str):
        """Chooses between multiple choices."""
        author = ctx.message.author
        em = dmbd.newembed(author, random.choice(choices))
        await self.bot.say(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('choose')


def setup(bot):
    """ Setup Webscrapper Module"""
    bot.add_cog(Random(bot))
