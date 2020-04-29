""" Overwatch API usage"""
import asyncio
import logging
import random

from typing import List

import discord
from discord.ext import commands

from utility import discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


class Overwatch(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot
        self.heroes: List[str] = []
        self.bot.loop.create_task(self.gather_heroes())

    async def gather_heroes(self) -> None:
        while True:
            async with self.bot.session.get("https://overwatch-api.net/api/v1/hero") as r:
                if r.status != 200:
                    log.error("Could not get heroes from https://overwatch-api.net/api/v1/hero")
                    await asyncio.sleep(60)
                    continue
                result = await r.json()
            self.heroes = [hero["name"] for hero in result["data"]]
            log.info("Refreshed Overwatch Heroes")
            await asyncio.sleep(3600 * 24)

    @staticmethod
    def display(author: discord.User, player: str, profile: dict) -> discord.Embed:
        em = dmbd.newembed(author, player.replace("-", "#"), footer="OW-API")
        em.set_thumbnail(url=profile.get("ratingIcon", profile["icon"]))
        em.add_field(name="Prestige/Level", value="{prestige}/{level}".format_map(profile))
        em.add_field(name="Comp Rating", value=profile["rating"])
        if profile["competitiveStats"]:
            em.add_field(
                name="Elimination Avg", value=profile["competitiveStats"]["eliminationsAvg"],
            )
            em.add_field(name="Death Avg", value=profile["competitiveStats"]["deathsAvg"])
            em.add_field(
                name="Winrate",
                value=profile["competitiveStats"]["games"]["won"] / profile["competitiveStats"]["games"]["played"],
            )
        if profile["quickPlayStats"]:
            em.add_field(
                name="Elimination Avg", value=profile["quickPlayStats"]["eliminationsAvg"],
            )
            em.add_field(name="Death Avg", value=profile["quickPlayStats"]["deathsAvg"])
            em.add_field(
                name="Winrate",
                value=profile["quickPlayStats"]["games"]["won"] / profile["quickPlayStats"]["games"]["played"],
            )

        return em

    @commands.command()
    async def owstats(self, ctx: commands.Context, region: str, battletag: str) -> None:
        if len(region) != 2:
            return
        if "#" not in battletag:
            return
        battletag = battletag.replace("#", "-")

        async with self.bot.session.get(f"https://ow-api.com/v1/stats/pc/{region}/{battletag}/profile/") as r:
            if r.status != 200:
                self.bot.logger.error(f"ow-api.com failed to return {r.status}")
                return
            profile = await r.json()
        await ctx.send(embed=self.display(ctx.author, battletag, profile))

    @commands.command()
    async def owrng(self, ctx: commands.Context) -> None:
        """ RNG OVERWATCH """
        await ctx.send("Play {}!".format(random.choice(self.heroes)))

    @commands.command()
    async def owteam(self, ctx: commands.Context, num: int = 6) -> None:
        random.shuffle(self.heroes)
        result = self.heroes[:num]
        await ctx.send(f"Here's your teamcomp! Good luck!\n{', '.join(result)}")


def setup(bot: MyClient) -> None:
    """ Setup OW Module"""
    bot.add_cog(Overwatch(bot))
