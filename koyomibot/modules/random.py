""" Module for generating a random cat picture"""

import asyncio
import logging
import random

from discord.commands import slash_command
from discord.ext import commands

import koyomibot.utility.discordembed as dmbd
from koyomibot.main import MyClient
from koyomibot.utility.allowed_guilds import ALLOWED_GUILDS

log = logging.getLogger(__name__)


class Random(commands.Cog):
    """Commands that are RANDOM"""

    def __init__(self, bot: MyClient):
        """Initialize Class"""
        self.bot = bot
        self.shinychance = 0
        self.bot.loop.create_task(self.get_max_pokemon())

    async def get_max_pokemon(self) -> None:
        url = "https://pokeapi.co/api/v2/pokemon?limit=1"
        while True:
            async with self.bot.session.get(url) as r:
                if r.status != 200:
                    log.warning("{url} returned {r.text}")
                    await asyncio.sleep(60)
                    continue
                result = await r.json()
            self.max_pokemon = result["count"]
            log.info("Refreshed Pokemon Count")
            await asyncio.sleep(3600 * 24)

    @slash_command(guild_ids=ALLOWED_GUILDS)
    async def pokemon(self, ctx: commands.Context, numid: int = None) -> None:
        """Get a random pokemon!"""
        if numid is None:
            numid = random.randint(1, self.max_pokemon)
        url = f"https://pokeapi.co/api/v2/pokemon/{numid}"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning("{url} returned {r.text}")
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
        await ctx.respond(embed=em)

    @slash_command(guild_ids=ALLOWED_GUILDS)
    async def roll(self, ctx: commands.Context, dice: str = "1d6") -> None:
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split("d"))
        except ValueError:
            await ctx.respond("Format has to be in NdN!")
            return

        title = "Here are your dice results!"
        em = dmbd.newembed(ctx.author, title)
        for r in range(rolls):
            em.add_field(name="Dice #" + str(r + 1), value=str(random.randint(1, limit)))
        # result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.respond(embed=em)

    @slash_command(guild_ids=ALLOWED_GUILDS)
    async def flip(self, ctx: commands.Context) -> None:
        """Flips a coin."""
        em = dmbd.newembed(ctx.author)
        if random.randint(0, 1) == 0:
            em.description = "Heads"
        else:
            em.description = "Tails"

        await ctx.respond(embed=em)

    @slash_command(name="8ball", guild_ids=ALLOWED_GUILDS)
    async def ball(self, ctx: commands.Context) -> None:
        """Ask the 8Ball"""
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
        await ctx.respond(embed=em)

    @slash_command(guild_ids=ALLOWED_GUILDS)
    async def quote(self, ctx: commands.Context) -> None:
        url = "https://animechan.vercel.app/api/random"
        async with self.bot.session.get(url) as r:
            if r.status != 200:
                log.warning("{url} returned {r.text}")
                return
            result = await r.json(content_type="application/json")

        em = dmbd.newembed(
            a=f'{result["character"]} ({result["anime"]})', d=result["quote"], footer="https://animechan.vercel.app/"
        )
        await ctx.respond(embed=em)


def setup(bot: MyClient) -> None:
    """Setup Webscrapper Module"""
    bot.add_cog(Random(bot))
