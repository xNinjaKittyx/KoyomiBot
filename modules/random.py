""" Module for generating a random cat picture"""

import random

from bs4 import BeautifulSoup
from discord.ext import commands
import utility.discordembed as dmbd

import rapidjson


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
            catlink = await r.json(loads=rapidjson.loads)
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
                    count = int((await r.json(loads=rapidjson.loads))['count'])
                else:
                    self.bot.logger('Pokemon did not return status 200')
                    return
            numid = random.randint(1, count)

        async with self.bot.session.get('http://pokeapi.co/api/v2/pokemon/' + str(numid)) as r:
            if r.status == 200:
                pokeman = await r.json(loads=rapidjson.loads)
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
        await self.bot.cogs['Wordcount'].cmdcount('roll')

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

        await self.bot.cogs['Wordcount'].cmdcount('flip')

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
        await self.bot.cogs['Wordcount'].cmdcount('8ball')

    @commands.command()
    async def trump(self, ctx):
        """ Returns a Trump Quote. """
        async with self.bot.session.get('https://api.tronalddump.io/random/quote') as r:
            if r.status != 200:
                self.bot.logger.warning('tronalddump.io request failed')
                return
            request = await r.json(loads=rapidjson.loads, content_type='application/hal+json')
            await ctx.send(request['value'])

    @commands.command()
    async def forismatic(self, ctx):
        """ Get random quote from Forismatic """
        async with self.bot.session.get('http://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en') as r:
            if r.status != 200:
                self.bot.logger.warning('Forimsatic GET Failed')
                return
            request = await r.json(loads=rapidjson.loads)
            em = dmbd.newembed(a=request['quoteAuthor'], d=request['quoteText'], u=request['quoteLink'])
            await ctx.send(embed=em)

    @commands.command()
    async def dadjoke(self, ctx):
        """ Random Dad Joke """
        async with self.bot.session.get('http://icanhazdadjoke.com/', headers={'Accept': 'application/json'}) as r:
            if r.status != 200:
                self.bot.logger.warning('https://icanhazdadjoke.com/api request failed')
                return
            request = await r.json(loads=rapidjson.loads)
            em = dmbd.newembed(a='Dad Joke... Why?', d=request['joke'])
            await ctx.send(embed=em)

    @commands.command()
    async def quotesondesign(self, ctx):
        """ Get Random Quote from Quotes on Design"""
        url = 'http://quotesondesign.com/wp-json/posts?filter[orderby]=rand&filter[posts_per_page]=1'
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                self.bot.logger.warning('Quotes on Design request failed')
                return
            request = (await r.json(loads=rapidjson.loads))[0]
            source = request.get('custom_meta', None)
            if source:
                source = request.get('Source', '')
            else:
                source = ''
            em = dmbd.newembed(
                a=request['title'],
                d=request['content'] + '\n' + 'Source: ' + source,
                u=request['link'])
            await ctx.send(embed=em)


def setup(bot):
    """ Setup Webscrapper Module"""
    bot.add_cog(Random(bot))
