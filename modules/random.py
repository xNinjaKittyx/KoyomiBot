""" Module for generating a random cat picture"""

import asyncio
import logging
import random

from bs4 import BeautifulSoup
from discord.ext import commands

import utility.discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


class Random(commands.Cog):
    """ Commands that are RANDOM"""

    def __init__(self, bot: MyClient):
        """ Initialize Class"""
        self.bot = bot
        self.shinychance = 0
        self.bot.loop.create_task(self.get_max_pokemon())

    async def get_max_pokemon(self) -> None:
        url = "https://pokeapi.co/api/v2/pokemon?limit=1"
        while True:
            async with self.bot.session.get(url) as r:
                if r.status != 200:
                    log.warning(f"{url} returned {r.text}")
                    await asyncio.sleep(60)
                    continue
                result = await r.json()
            self.max_pokemon = result["count"]
            log.info("Refreshed Pokemon Count")
            await asyncio.sleep(3600 * 24)

    @commands.command()
    async def prime(self, ctx: commands.Context) -> None:
        await ctx.send(
            "Hey there! Do you want to know about Twitch Prime? Oh! You may be asking, "
            '"What\'s Twitch Prime?" Let me tell ya! When you connect your Amazon account '
            "to your Twitch account, you can get 1 free sub to ANY streamer on Twitch, every "
            "month! Yup, and along with that, get yourself some Twitch loot! With Twitch loot, "
            "you can go ahead and get yourself some exclusive Twitch gear and your favorite games! "
        )

    @commands.command()
    async def pokemon(self, ctx: commands.Context, numid: int = None) -> None:
        """ Get a random pokemon! """
        if numid is None:
            numid = random.randint(1, self.max_pokemon)
        url = f"https://pokeapi.co/api/v2/pokemon/{numid}"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning(f"{url} returned {r.text}")
                return
            pokeman = await r.json()
        em = dmbd.newembed(ctx.author, pokeman["name"].title(), footer="PokeAPI")
        shiny = random.randint(1, 65536) < int(65535 / (8200 - self.shinychance * 200))
        gender = random.randint(0, 1)
        if shiny:
            em.description = "WOW YOU GOT A SHINY :D"
            self.shinychance = 0
            sprite = "front_shiny"
        else:
            if self.shinychance < 40:
                self.shinychance += 1
            sprite = "front_default"

        if gender:
            sprite_link = pokeman["sprites"].get(sprite + "_female", pokeman["sprites"][sprite])
        else:
            sprite_link = pokeman["sprites"][sprite]

        em.set_image(url=sprite_link)
        await ctx.send(embed=em)

    @commands.command()
    async def roll(self, ctx: commands.Context, dice: str = "1d6") -> None:
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split("d"))
        except ValueError:
            await ctx.send("Format has to be in NdN!")
            return

        title = "Here are your dice results!"
        em = dmbd.newembed(ctx.author, title)
        for r in range(rolls):
            em.add_field(name="Dice #" + str(r + 1), value=str(random.randint(1, limit)))
        # result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.send(embed=em)

    @commands.command()
    async def flip(self, ctx: commands.Context, coins: int = 1) -> None:
        """ Flips a coin."""
        em = dmbd.newembed(ctx.author)
        for x in range(coins):
            if random.randint(0, 1):
                em.add_field(name="Coin #" + str(x + 1), value="Heads")
            else:
                em.add_field(name="Coin #" + str(x + 1), value="Tails")

        await ctx.send(embed=em)

    @commands.command(name="8ball")
    async def ball(self, ctx: commands.Context) -> None:
        """ Ask the 8Ball """
        answers = [
            "It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes, definitely",
            "You may rely on it",
            "As I see it, yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Reply hazy try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful",
        ]

        em = dmbd.newembed(ctx.author, random.choice(answers))
        await ctx.send(embed=em)

    @commands.command()
    async def trump(self, ctx: commands.Context) -> None:
        """ Returns a Trump Quote. """
        url = "https://api.tronalddump.io/random/quote"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning(f"{url} returned {r.text}")
                return
            result = await r.json(content_type="application/hal+json")
        await ctx.send(result["value"])

    @commands.command()
    async def forismatic(self, ctx: commands.Context) -> None:
        """ Get random quote from Forismatic """
        url = "http://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning(f"{url} returned {r.text}")
                return
            result = await r.json()
        em = dmbd.newembed(a=result["quoteAuthor"], d=result["quoteText"], u=result["quoteLink"], footer="forismatic",)
        await ctx.send(embed=em)

    @commands.command()
    async def dadjoke(self, ctx: commands.Context) -> None:
        """ Random Dad Joke """
        url = "http://icanhazdadjoke.com/"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning(f"{url} returned {r.text}")
                return
            result = await r.json()
        em = dmbd.newembed(a="Dad Joke... Why?", d=result["joke"], footer="ICanHazDadJoke")
        await ctx.send(embed=em)

    @commands.command()
    async def quotesondesign(self, ctx: commands.Context) -> None:
        """ Get Random Quote from Quotes on Design"""
        url = "http://quotesondesign.com/wp-json/posts?filter[orderby]=rand&filter[posts_per_page]=1"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning(f"{url} returned {r.text}")
                return
            result = (await r.json())[0]
        source = result.get("custom_meta", None)
        if source:
            source = result.get("Source", "")
        else:
            source = ""
        em = dmbd.newembed(
            a=result["title"],
            d=BeautifulSoup(result["content"], "html.parser").get_text().strip() + "\n" + "Source: " + source,
            u=result["link"],
            footer="QuotesOnDesign",
        )
        await ctx.send(embed=em)

    @commands.command()
    async def givemeadvice(self, ctx: commands.Context) -> None:
        url = "https://api.adviceslip.com/advice"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning(f"{url} returned {r.text}")
                return
            result = await r.json(content_type="text/html")

        em = dmbd.newembed(a="Here's some advice", d=result["slip"]["advice"], footer="AdviceSlip")
        await ctx.send(embed=em)

    @commands.command(aliases=["norris"])
    async def chuck(self, ctx: commands.Context) -> None:
        url = "https://api.chucknorris.io/jokes/random"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning(f"{url} returned {r.text}")
                return
            result = await r.json()

        em = dmbd.newembed(a="Chuck Norris", d=result["value"], u=result["url"], footer="ChuckNorris.io",)
        em.set_thumbnail(url=result["icon_url"])
        await ctx.send(embed=em)


def setup(bot: MyClient) -> None:
    """ Setup Webscrapper Module"""
    bot.add_cog(Random(bot))
