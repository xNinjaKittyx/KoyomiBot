
import logging

from dataclasses import dataclass
from typing import Optional
from urllib import parse

import discord
from discord.ext import commands

import utility.discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


@dataclass
class OsuPlayer:
    user_id: int
    username: str
    join_date: str
    count300: int
    count100: int
    count50: int
    playcount: int
    ranked_score: int
    total_score: int
    pp_rank: int
    level: float
    pp_raw: int
    accuracy: float
    count_rank_ss: int
    count_rank_ssh: int
    count_rank_s: int
    count_rank_sh: int
    count_rank_a: int
    country: str
    total_seconds_played: int
    pp_country_rank: int
    events: Optional[List[dict]]

    def display(self, author: str) -> discord.Embed:
        title = self.username
        desc = self.country.upper()
        url = 'https://osu.ppy.sh/u/' + self.username
        em = dmbd.newembed(author, title, desc, url)
        em.add_field(name='Performance', value=self.pp_raw + 'pp')
        em.add_field(name='Accuracy', value="{0:.2f}%".format(float(self.accuracy)))
        lvl = int(float(self.level))
        percent = int((float(self.level) - lvl) * 100)
        em.add_field(name='Level', value="{0} ({1}%)".format(lvl, percent))
        em.add_field(name='Rank', value=self.pp_rank)
        em.add_field(name='Country Rank', value=self.pp_country_rank)
        em.add_field(name='Playcount', value=self.playcount)
        em.add_field(name='Total Score', value=self.total_score)
        em.add_field(name='Ranked Score', value=self.ranked_score)
        return em


class Osu(commands.Cog):

    def __init__(self, bot: MyClient):
        self.bot = bot

    async def getlink(self, mode: int, playername: str) -> Optional[dict]:
        cookiezi = self.bot.key_config.OsuAPI
        link = f'http://osu.ppy.sh/api/get_user?k={cookiezi}&u={playername}&m={mode}'

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                self.bot.logger.warning(f'{link} failed with r.status')
                return None
            j = await r.json()
            if j:
                return j[0]
            else:
                log.error(j)
                return None

    @commands.command()
    async def osu(self, ctx: commands.Context, *, name: str) -> None:
        name = parse.quote(name)
        result = await self.getlink(0, name)
        if result is None:
            return
        player = OsuPlayer(**result)
        em = player.display(ctx.author)
        em.set_image(
            url=f"http://lemmmy.pw/osusig/sig.php?colour=hex{em.color}&uname={name}&mode=0&pp=1&countryrank&flagshadow&darkheader&darktriangles&onlineindicator=undefined&xpbar&xpbarhex")

        await ctx.send(embed=em)

    @commands.command()
    async def taiko(self, ctx: commands.Context, *, name: str) -> None:
        result = await self.getlink(1, name)
        if result is None:
            return
        player = OsuPlayer(**result)
        em = player.display(ctx.author)
        em.set_image(
            url=f"http://lemmmy.pw/osusig/sig.php?colour=hex{em.color}&uname={name}&mode=1&pp=1&countryrank&flagshadow&darkheader&darktriangles&onlineindicator=undefined&xpbar&xpbarhex"
        )

        await ctx.send(embed=em)

    @commands.command()
    async def ctb(self, ctx: commands.Context, *, name: str) -> None:
        result = await self.getlink(2, name)
        if result is None:
            return
        player = OsuPlayer(**result)
        em = player.display(ctx.author)
        em.set_image(
            url=f"http://lemmmy.pw/osusig/sig.php?colour=hex{em.color}&uname={name}&mode=2&pp=1&countryrank&flagshadow&darkheader&darktriangles&onlineindicator=undefined&xpbar&xpbarhex"
        )

        await ctx.send(embed=em)

    @commands.command()
    async def mania(self, ctx: commands.Context, *, name: str) -> None:
        result = await self.getlink(3, name)
        if result is None:
            return
        player = OsuPlayer(**result)
        em = player.display(ctx.author)
        em.set_image(
            url=f"http://lemmmy.pw/osusig/sig.php?colour=hex{em.color}&uname={name}&mode=3&pp=1&countryrank&flagshadow&darkheader&darktriangles&onlineindicator=undefined&xpbar&xpbarhex")

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Osu(bot))
