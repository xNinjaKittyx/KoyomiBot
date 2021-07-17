import asyncio
import logging
import random
from typing import List, Optional

from bs4 import BeautifulSoup
from discord.ext import commands

from koyomibot.main import MyClient
from koyomibot.utility import discordembed as dmbd

log = logging.getLogger(__name__)


class Comics(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot
        self.bot.loop.create_task(self.refreshxkcd())
        self.bot.loop.create_task(self.refreshcyanide())
        self.dead_cyanide: List[int] = []

    async def refreshxkcd(self) -> None:
        while True:
            log.info("Refreshing XKCD Comics.")
            result = await self.bot.request_get("https://xkcd.com/info.0.json")
            if result is None:
                log.warning("XKCD did not return successfully, trying again in 1 min")
                await asyncio.sleep(60)
            else:
                self.highest_xkcd = result["num"]
                await asyncio.sleep(3600)

    async def getxkcd(self, num: int) -> Optional[dict]:
        """Num should be passed as an INT"""
        cache_str = f"xkcd:{num}"
        result = await self.bot.request_get(f"https://xkcd.com/{num}/info.0.json", cache_str=cache_str)
        return result if result else {}

    @commands.command()
    async def xkcd(self, ctx: commands.Context) -> None:
        """Gives a random XKCD Comic"""
        number = random.randint(1, self.highest_xkcd)
        result = await self.getxkcd(number)
        if not result:
            return

        em = dmbd.newembed(
            ctx.author,
            result["safe_title"],
            u=f"https://xkcd.com/{number}",
            footer="XKCD",
        )
        em.set_image(url=result["img"])
        em.add_field(name=result["alt"], value="{month}/{day}/{year}".format_map(result))
        await ctx.send(embed=em)

    async def refreshcyanide(self) -> None:
        while True:
            log.info("Refreshing C&H Comics.")
            result = await self.bot.request_get("https://explosm.net/comics/latest", return_as_json=False)
            if result is None:
                log.warning("C&H did not return successfully, trying again in 1 min")
                await asyncio.sleep(60)
            else:
                soup = BeautifulSoup(result, "html.parser")
                self.cyanidemax = int(soup.find(property="og:url").get("content").split("/")[-2])
                await asyncio.sleep(3600)

    async def getcyanide(self, num: int) -> Optional[str]:
        cache_str = f"cyanide:{num}"
        # Redis space can definitely be optimized.
        result = await self.bot.request_get(
            f"https://explosm.net/comics/{num}", cache_str=cache_str, return_as_json=False
        )
        if result is None:
            return None

        soup = BeautifulSoup(result, "html.parser")
        if soup.prettify().startswith("Could not"):
            self.dead_cyanide.append(num)
            return None
        return f'http:{soup.find(id="main-comic")["src"]}'

    @commands.command()
    async def cyanide(self, ctx: commands.Context) -> None:
        """Gives a random Cyanide & Happiness Comic"""
        img = None
        while img is None:
            number = random.randint(39, self.cyanidemax)
            if number in self.dead_cyanide:
                continue
            img = await self.getcyanide(number)
        # whatever reason, comics 1 - 38 don't exist.
        em = dmbd.newembed(
            ctx.author,
            "Cyanide and Happiness",
            str(number),
            u=f"https://explosm.net/comics/{number}",
            footer="Explosm",
        )
        em.set_image(url=img)
        await ctx.send(embed=em)

    @commands.command()
    async def cyanidercg(self, ctx: commands.Context) -> None:
        """Gives a randomly generated Cyanide & Happiness Comic"""
        result = await self.bot.request_get("https://explosm.net/rcg", return_as_json=False)
        if result is None:
            return None
        soup = BeautifulSoup(result, "html.parser")
        img = soup.find(id="rcg-image").value
        em = dmbd.newembed(ctx.author, "Cyanide and Happiness RCG", u=img, footer="Explosm")
        em.set_image(url=img)
        await ctx.send(embed=em)


def setup(bot: MyClient) -> None:
    bot.add_cog(Comics(bot))
