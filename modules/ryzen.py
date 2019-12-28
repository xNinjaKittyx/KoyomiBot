import asyncio
import logging
import re

from bs4 import BeautifulSoup
from discord.ext import commands

import utility.discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


class Ryzen(commands.Cog):
    """ Ryzen Notifier """

    tr_re_compile = re.compile(r"tr.*")
    ryzen_re_compile = re.compile(r"RYZEN [9] 3.*")

    def __init__(self, bot: MyClient):

        self.bot = bot
        self._data = {}
        self.bot.loop.create_task(self.update_values())

    async def update_values(self) -> None:
        url = "https://www.nowinstock.net/computers/processors/amd/"
        while True:
            result = {}
            try:
                async with self.bot.session.get(url) as r:
                    if r.status != 200:
                        log.warning(f"{url} returned {await req.text()}")
                        await asyncio.sleep(5)
                        continue

                    soup = BeautifulSoup(await r.text(), "html.parser")
                    for entry in soup.body.find_all(id="data")[0].find_all(id=self.tr_re_compile):
                        key = entry.td.a.text
                        if self.ryzen_re_compile.findall(key):
                            # This means its a correct Ryzen.
                            result[key] = {
                                "link": entry.td.a["href"],
                                "stock": entry.td.next_sibling.text,
                            }
                            if (
                                result[key]["stock"] == "In Stock"
                                and self._data.get(key, {}).get("stock") != "In Stock"
                            ):
                                c = self.bot.get_channel(546860175005581322)
                                g = self.bot.get_guild(82242522046275584)
                                while c is None:
                                    c = self.bot.get_channel(546860175005581322)
                                    await asyncio.sleep(0)
                                while g is None:
                                    g = self.bot.get_guild(82242522046275584)
                                    await asyncio.sleep(0)
                                await c.send(
                                    f"{g.get_role(603782837996355594).mention}"
                                    f'Holy Shit {key} is IN STOCK: {result[key]["link"]}'
                                )

                if result:
                    self._data = result
                await asyncio.sleep(5)
            except Exception as e:
                log.error(f"ryzen fetch failed {e}")

    @commands.command()
    async def ryzen(self, ctx: commands.Context) -> None:
        em = dmbd.newembed(
            a="EZCLAP RYZENSTOCK",
            u="https://www.nowinstock.net/computers/processors/amd/",
            footer="WHERE IS RYZEN 3900X REEEEEE",
        )
        for key in self._data:
            em.add_field(name=key, value=self._data[key]["stock"])
        await ctx.send(embed=em)


def setup(bot: MyClient) -> None:
    """ Setup Webscrapper Module"""
    bot.add_cog(Ryzen(bot))
